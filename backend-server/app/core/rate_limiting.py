"""
Rate limiting and API abuse prevention middleware.
"""
import time
import asyncio
from typing import Dict, Optional, Tuple
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
import redis
import json
import logging
from datetime import datetime, timedelta
import hashlib
from app.core.config import settings

logger = logging.getLogger(__name__)

class RateLimitConfig:
    """Rate limiting configuration"""
    
    # Default rate limits (requests per time window)
    DEFAULT_LIMITS = {
        "auth": {"requests": 5, "window": 300},  # 5 requests per 5 minutes
        "api": {"requests": 100, "window": 3600},  # 100 requests per hour
        "upload": {"requests": 10, "window": 3600},  # 10 uploads per hour
        "ai_processing": {"requests": 20, "window": 3600},  # 20 AI requests per hour
        "search": {"requests": 50, "window": 3600},  # 50 searches per hour
    }
    
    # Burst limits for short time windows
    BURST_LIMITS = {
        "api": {"requests": 10, "window": 60},  # 10 requests per minute
        "auth": {"requests": 3, "window": 60},  # 3 auth requests per minute
    }
    
    # IP-based limits for anonymous users
    IP_LIMITS = {
        "anonymous": {"requests": 20, "window": 3600},  # 20 requests per hour
        "registration": {"requests": 3, "window": 86400},  # 3 registrations per day
    }

class RateLimiter:
    """Redis-based rate limiter with sliding window"""
    
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self.redis = redis_client or self._get_redis_client()
        self.config = RateLimitConfig()
    
    def _get_redis_client(self) -> redis.Redis:
        """Get Redis client for rate limiting"""
        try:
            return redis.Redis(
                host=getattr(settings, 'REDIS_HOST', 'localhost'),
                port=getattr(settings, 'REDIS_PORT', 6379),
                db=getattr(settings, 'REDIS_DB', 1),
                decode_responses=True
            )
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            # Fallback to in-memory storage (not recommended for production)
            return InMemoryRateLimiter()
    
    async def check_rate_limit(
        self,
        key: str,
        limit_type: str,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> Tuple[bool, Dict[str, any]]:
        """
        Check if request is within rate limits
        Returns (is_allowed, rate_limit_info)
        """
        try:
            # Get rate limit configuration
            limits = self._get_limits_for_type(limit_type, user_id)
            
            # Check each limit type
            for limit_name, limit_config in limits.items():
                allowed, info = await self._check_sliding_window(
                    f"{key}:{limit_name}",
                    limit_config["requests"],
                    limit_config["window"]
                )
                
                if not allowed:
                    return False, {
                        "allowed": False,
                        "limit_type": limit_name,
                        "limit": limit_config["requests"],
                        "window": limit_config["window"],
                        "reset_time": info["reset_time"],
                        "remaining": info["remaining"]
                    }
            
            # All limits passed
            return True, {
                "allowed": True,
                "limits": limits
            }
            
        except Exception as e:
            logger.error(f"Rate limit check failed: {e}")
            # Fail open - allow request if rate limiting fails
            return True, {"allowed": True, "error": str(e)}
    
    async def _check_sliding_window(
        self,
        key: str,
        limit: int,
        window: int
    ) -> Tuple[bool, Dict[str, any]]:
        """Check sliding window rate limit"""
        now = time.time()
        pipeline = self.redis.pipeline()
        
        # Remove expired entries
        pipeline.zremrangebyscore(key, 0, now - window)
        
        # Count current requests
        pipeline.zcard(key)
        
        # Add current request
        pipeline.zadd(key, {str(now): now})
        
        # Set expiration
        pipeline.expire(key, window)
        
        results = await pipeline.execute()
        current_count = results[1]
        
        remaining = max(0, limit - current_count - 1)
        reset_time = now + window
        
        return current_count < limit, {
            "remaining": remaining,
            "reset_time": reset_time,
            "current_count": current_count
        }
    
    def _get_limits_for_type(self, limit_type: str, user_id: Optional[str]) -> Dict[str, Dict]:
        """Get rate limits based on type and user status"""
        limits = {}
        
        # Add default limits
        if limit_type in self.config.DEFAULT_LIMITS:
            limits["default"] = self.config.DEFAULT_LIMITS[limit_type]
        
        # Add burst limits
        if limit_type in self.config.BURST_LIMITS:
            limits["burst"] = self.config.BURST_LIMITS[limit_type]
        
        # Add IP limits for anonymous users
        if not user_id and limit_type in self.config.IP_LIMITS:
            limits["ip"] = self.config.IP_LIMITS[limit_type]
        
        return limits
    
    async def record_violation(
        self,
        key: str,
        violation_type: str,
        details: Dict[str, any]
    ):
        """Record rate limit violation for monitoring"""
        violation_key = f"violations:{key}"
        violation_data = {
            "timestamp": time.time(),
            "type": violation_type,
            "details": json.dumps(details)
        }
        
        try:
            await self.redis.lpush(violation_key, json.dumps(violation_data))
            await self.redis.ltrim(violation_key, 0, 99)  # Keep last 100 violations
            await self.redis.expire(violation_key, 86400)  # Expire after 24 hours
        except Exception as e:
            logger.error(f"Failed to record violation: {e}")

class InMemoryRateLimiter:
    """Fallback in-memory rate limiter (not recommended for production)"""
    
    def __init__(self):
        self.storage = {}
        self.cleanup_interval = 300  # 5 minutes
        self.last_cleanup = time.time()
    
    async def check_rate_limit(self, key: str, limit: int, window: int) -> Tuple[bool, Dict]:
        """Simple in-memory rate limiting"""
        now = time.time()
        
        # Cleanup old entries periodically
        if now - self.last_cleanup > self.cleanup_interval:
            await self._cleanup_expired(now)
            self.last_cleanup = now
        
        # Get or create entry
        if key not in self.storage:
            self.storage[key] = []
        
        # Remove expired requests
        self.storage[key] = [
            timestamp for timestamp in self.storage[key]
            if now - timestamp < window
        ]
        
        # Check limit
        current_count = len(self.storage[key])
        if current_count >= limit:
            return False, {
                "remaining": 0,
                "reset_time": now + window,
                "current_count": current_count
            }
        
        # Add current request
        self.storage[key].append(now)
        
        return True, {
            "remaining": limit - current_count - 1,
            "reset_time": now + window,
            "current_count": current_count + 1
        }
    
    async def _cleanup_expired(self, now: float):
        """Remove expired entries from memory"""
        keys_to_remove = []
        for key, timestamps in self.storage.items():
            # Remove entries older than 1 hour
            self.storage[key] = [
                ts for ts in timestamps
                if now - ts < 3600
            ]
            if not self.storage[key]:
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self.storage[key]

class AbuseDetector:
    """Detect and prevent API abuse patterns"""
    
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self.redis = redis_client or redis.Redis(decode_responses=True)
        self.suspicious_patterns = {
            "rapid_requests": {"threshold": 50, "window": 60},
            "failed_auth": {"threshold": 10, "window": 300},
            "large_payloads": {"threshold": 5, "window": 3600},
            "unusual_endpoints": {"threshold": 20, "window": 3600},
        }
    
    async def detect_abuse(
        self,
        request: Request,
        user_id: Optional[str] = None,
        response_status: Optional[int] = None
    ) -> Dict[str, any]:
        """Detect potential abuse patterns"""
        ip_address = self._get_client_ip(request)
        user_agent = request.headers.get("user-agent", "")
        
        abuse_score = 0
        detected_patterns = []
        
        # Check for rapid requests
        if await self._check_rapid_requests(ip_address, user_id):
            abuse_score += 30
            detected_patterns.append("rapid_requests")
        
        # Check for failed authentication attempts
        if response_status == 401:
            if await self._check_failed_auth(ip_address):
                abuse_score += 40
                detected_patterns.append("failed_auth")
        
        # Check for suspicious user agent
        if self._is_suspicious_user_agent(user_agent):
            abuse_score += 20
            detected_patterns.append("suspicious_user_agent")
        
        # Check for large payload attacks
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > 1024 * 1024:  # 1MB
            if await self._check_large_payloads(ip_address):
                abuse_score += 25
                detected_patterns.append("large_payloads")
        
        return {
            "abuse_score": abuse_score,
            "is_suspicious": abuse_score >= 50,
            "detected_patterns": detected_patterns,
            "ip_address": ip_address,
            "user_agent": user_agent
        }
    
    async def _check_rapid_requests(self, ip_address: str, user_id: Optional[str]) -> bool:
        """Check for rapid request patterns"""
        key = f"rapid:{ip_address}:{user_id or 'anonymous'}"
        pattern = self.suspicious_patterns["rapid_requests"]
        
        try:
            count = await self.redis.incr(key)
            if count == 1:
                await self.redis.expire(key, pattern["window"])
            
            return count > pattern["threshold"]
        except:
            return False
    
    async def _check_failed_auth(self, ip_address: str) -> bool:
        """Check for failed authentication patterns"""
        key = f"failed_auth:{ip_address}"
        pattern = self.suspicious_patterns["failed_auth"]
        
        try:
            count = await self.redis.incr(key)
            if count == 1:
                await self.redis.expire(key, pattern["window"])
            
            return count > pattern["threshold"]
        except:
            return False
    
    async def _check_large_payloads(self, ip_address: str) -> bool:
        """Check for large payload attack patterns"""
        key = f"large_payload:{ip_address}"
        pattern = self.suspicious_patterns["large_payloads"]
        
        try:
            count = await self.redis.incr(key)
            if count == 1:
                await self.redis.expire(key, pattern["window"])
            
            return count > pattern["threshold"]
        except:
            return False
    
    def _is_suspicious_user_agent(self, user_agent: str) -> bool:
        """Check for suspicious user agent patterns"""
        suspicious_patterns = [
            "bot", "crawler", "spider", "scraper",
            "curl", "wget", "python-requests",
            "postman", "insomnia"
        ]
        
        user_agent_lower = user_agent.lower()
        return any(pattern in user_agent_lower for pattern in suspicious_patterns)
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address from request"""
        # Check for forwarded headers
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else "unknown"

# Global instances
rate_limiter = RateLimiter()
abuse_detector = AbuseDetector()