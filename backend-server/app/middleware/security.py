"""
Security middleware for FastAPI application.
"""
import time
import json
from datetime import datetime
from typing import Callable, Optional, List
from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import logging

from app.core.security import SecurityHeaders
from app.core.rate_limiting import rate_limiter, abuse_detector
from app.core.auth import get_current_user_optional

logger = logging.getLogger(__name__)

class SecurityMiddleware(BaseHTTPMiddleware):
    """Comprehensive security middleware"""
    
    def __init__(self, app, enable_rate_limiting: bool = True, enable_abuse_detection: bool = True):
        super().__init__(app)
        self.enable_rate_limiting = enable_rate_limiting
        self.enable_abuse_detection = enable_abuse_detection
        self.security_headers = SecurityHeaders()
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request through security checks"""
        start_time = time.time()
        
        try:
            # Get client information
            client_ip = self._get_client_ip(request)
            user_agent = request.headers.get("user-agent", "")
            
            # Get user ID if authenticated
            user_id = await self._get_user_id(request)
            
            # Apply rate limiting
            if self.enable_rate_limiting:
                rate_limit_result = await self._check_rate_limits(
                    request, client_ip, user_id
                )
                if not rate_limit_result["allowed"]:
                    return self._create_rate_limit_response(rate_limit_result)
            
            # Process the request
            response = await call_next(request)
            
            # Apply security headers
            self._apply_security_headers(response)
            
            # Detect abuse patterns
            if self.enable_abuse_detection:
                await self._detect_abuse(request, user_id, response.status_code)
            
            # Log request
            self._log_request(request, response, start_time, client_ip, user_id)
            
            return response
            
        except HTTPException as e:
            # Handle HTTP exceptions
            response = JSONResponse(
                status_code=e.status_code,
                content={"error": {"message": e.detail, "code": e.status_code}}
            )
            self._apply_security_headers(response)
            return response
            
        except Exception as e:
            # Handle unexpected errors
            logger.error(f"Security middleware error: {e}")
            response = JSONResponse(
                status_code=500,
                content={"error": {"message": "Internal server error", "code": 500}}
            )
            self._apply_security_headers(response)
            return response
    
    async def _check_rate_limits(
        self,
        request: Request,
        client_ip: str,
        user_id: Optional[str]
    ) -> dict:
        """Check rate limits for the request"""
        # Determine rate limit type based on endpoint
        path = request.url.path
        method = request.method
        
        limit_type = self._get_rate_limit_type(path, method)
        
        # Create rate limit key
        if user_id:
            key = f"user:{user_id}"
        else:
            key = f"ip:{client_ip}"
        
        # Check rate limits
        return await rate_limiter.check_rate_limit(
            key=key,
            limit_type=limit_type,
            user_id=user_id,
            ip_address=client_ip
        )
    
    def _get_rate_limit_type(self, path: str, method: str) -> str:
        """Determine rate limit type based on endpoint"""
        if "/auth/" in path:
            return "auth"
        elif "/upload" in path or method == "POST" and "file" in path:
            return "upload"
        elif any(ai_endpoint in path for ai_endpoint in [
            "/agents/", "/interview/", "/resume/optimize", "/skills/analyze"
        ]):
            return "ai_processing"
        elif "/search" in path or method == "GET" and "/jobs" in path:
            return "search"
        else:
            return "api"
    
    def _create_rate_limit_response(self, rate_limit_info: dict) -> JSONResponse:
        """Create rate limit exceeded response"""
        headers = {
            "X-RateLimit-Limit": str(rate_limit_info.get("limit", 0)),
            "X-RateLimit-Remaining": str(rate_limit_info.get("remaining", 0)),
            "X-RateLimit-Reset": str(int(rate_limit_info.get("reset_time", 0))),
            "Retry-After": str(rate_limit_info.get("window", 3600))
        }
        
        response = JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                "error": {
                    "message": "Rate limit exceeded",
                    "code": 429,
                    "details": {
                        "limit_type": rate_limit_info.get("limit_type"),
                        "retry_after": rate_limit_info.get("window")
                    }
                }
            },
            headers=headers
        )
        
        self._apply_security_headers(response)
        return response
    
    async def _detect_abuse(
        self,
        request: Request,
        user_id: Optional[str],
        status_code: int
    ):
        """Detect and log abuse patterns"""
        try:
            abuse_result = await abuse_detector.detect_abuse(
                request=request,
                user_id=user_id,
                response_status=status_code
            )
            
            if abuse_result["is_suspicious"]:
                logger.warning(
                    f"Suspicious activity detected: {abuse_result['detected_patterns']} "
                    f"from IP {abuse_result['ip_address']} "
                    f"(Score: {abuse_result['abuse_score']})"
                )
                
                # Record violation for monitoring
                await rate_limiter.record_violation(
                    key=f"abuse:{abuse_result['ip_address']}",
                    violation_type="suspicious_activity",
                    details=abuse_result
                )
                
        except Exception as e:
            logger.error(f"Abuse detection failed: {e}")
    
    def _apply_security_headers(self, response: Response):
        """Apply security headers to response"""
        headers = self.security_headers.get_security_headers()
        for header, value in headers.items():
            response.headers[header] = value
    
    async def _get_user_id(self, request: Request) -> Optional[str]:
        """Extract user ID from request if authenticated"""
        try:
            # This would typically use your auth system
            # For now, we'll try to get it from the Authorization header
            auth_header = request.headers.get("authorization")
            if auth_header and auth_header.startswith("Bearer "):
                # You would decode the JWT token here
                # For now, return None to indicate anonymous user
                return None
            return None
        except Exception:
            return None
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address"""
        # Check for forwarded headers
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else "unknown"
    
    def _log_request(
        self,
        request: Request,
        response: Response,
        start_time: float,
        client_ip: str,
        user_id: Optional[str]
    ):
        """Log request details for monitoring"""
        duration = time.time() - start_time
        
        log_data = {
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration": round(duration, 3),
            "client_ip": client_ip,
            "user_id": user_id,
            "user_agent": request.headers.get("user-agent", ""),
            "content_length": request.headers.get("content-length", 0)
        }
        
        if response.status_code >= 400:
            logger.warning(f"HTTP {response.status_code}: {json.dumps(log_data)}")
        else:
            logger.info(f"Request processed: {json.dumps(log_data)}")

class InputValidationMiddleware(BaseHTTPMiddleware):
    """Middleware for input validation and sanitization"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Validate and sanitize request input"""
        try:
            # Validate request size
            content_length = request.headers.get("content-length")
            if content_length:
                size = int(content_length)
                max_size = 10 * 1024 * 1024  # 10MB
                if size > max_size:
                    return JSONResponse(
                        status_code=413,
                        content={
                            "error": {
                                "message": "Request entity too large",
                                "code": 413,
                                "max_size": max_size
                            }
                        }
                    )
            
            # Validate content type for POST/PUT requests
            if request.method in ["POST", "PUT", "PATCH"]:
                content_type = request.headers.get("content-type", "")
                if content_type and not self._is_allowed_content_type(content_type):
                    return JSONResponse(
                        status_code=415,
                        content={
                            "error": {
                                "message": "Unsupported media type",
                                "code": 415,
                                "allowed_types": [
                                    "application/json",
                                    "multipart/form-data",
                                    "application/x-www-form-urlencoded"
                                ]
                            }
                        }
                    )
            
            # Process request
            response = await call_next(request)
            return response
            
        except Exception as e:
            logger.error(f"Input validation error: {e}")
            return JSONResponse(
                status_code=400,
                content={
                    "error": {
                        "message": "Invalid request format",
                        "code": 400
                    }
                }
            )
    
    def _is_allowed_content_type(self, content_type: str) -> bool:
        """Check if content type is allowed"""
        allowed_types = [
            "application/json",
            "multipart/form-data",
            "application/x-www-form-urlencoded",
            "text/plain"
        ]
        
        return any(allowed in content_type.lower() for allowed in allowed_types)

class CSRFProtectionMiddleware(BaseHTTPMiddleware):
    """CSRF protection middleware"""
    
    def __init__(self, app, exempt_paths: list = None):
        super().__init__(app)
        self.exempt_paths = exempt_paths or ["/docs", "/redoc", "/openapi.json"]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Check CSRF token for state-changing requests"""
        # Skip CSRF check for exempt paths
        if any(request.url.path.startswith(path) for path in self.exempt_paths):
            return await call_next(request)
        
        # Skip CSRF check for safe methods
        if request.method in ["GET", "HEAD", "OPTIONS"]:
            return await call_next(request)
        
        # Check CSRF token for state-changing requests
        csrf_token = request.headers.get("x-csrf-token")
        if not csrf_token:
            return JSONResponse(
                status_code=403,
                content={
                    "error": {
                        "message": "CSRF token required",
                        "code": 403
                    }
                }
            )
        
        # Validate CSRF token (implement your validation logic)
        if not self._validate_csrf_token(csrf_token, request):
            return JSONResponse(
                status_code=403,
                content={
                    "error": {
                        "message": "Invalid CSRF token",
                        "code": 403
                    }
                }
            )
        
        return await call_next(request)
    
    def _validate_csrf_token(self, token: str, request: Request) -> bool:
        """Validate CSRF token (implement based on your token generation strategy)"""
        # This is a placeholder - implement your CSRF validation logic
        # You might validate against a session-stored token or use double-submit cookies
        return len(token) > 10  # Placeholder validation

class ContentSecurityPolicyMiddleware(BaseHTTPMiddleware):
    """Enhanced Content Security Policy middleware"""
    
    def __init__(self, app, csp_policy: dict = None):
        super().__init__(app)
        self.csp_policy = csp_policy or {
            "default-src": ["'self'"],
            "script-src": ["'self'", "'unsafe-inline'", "https://cdn.jsdelivr.net"],
            "style-src": ["'self'", "'unsafe-inline'", "https://fonts.googleapis.com"],
            "font-src": ["'self'", "https://fonts.gstatic.com"],
            "img-src": ["'self'", "data:", "https:"],
            "connect-src": ["'self'", "wss:", "https:"],
            "frame-ancestors": ["'none'"],
            "base-uri": ["'self'"],
            "form-action": ["'self'"]
        }
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Apply Content Security Policy headers"""
        response = await call_next(request)
        
        # Build CSP header value
        csp_directives = []
        for directive, sources in self.csp_policy.items():
            sources_str = " ".join(sources)
            csp_directives.append(f"{directive} {sources_str}")
        
        csp_header = "; ".join(csp_directives)
        response.headers["Content-Security-Policy"] = csp_header
        
        return response

class DataLeakPreventionMiddleware(BaseHTTPMiddleware):
    """Prevent sensitive data leakage in responses"""
    
    def __init__(self, app):
        super().__init__(app)
        self.sensitive_patterns = [
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Email
            r'\b\d{3}-?\d{2}-?\d{4}\b',  # SSN
            r'\b(?:\d{4}[-\s]?){3}\d{4}\b',  # Credit card
            r'\b(?:\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}\b',  # Phone
        ]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Check response for sensitive data leakage"""
        response = await call_next(request)
        
        # Only check JSON responses
        if response.headers.get("content-type", "").startswith("application/json"):
            try:
                # Get response body
                body = b""
                async for chunk in response.body_iterator:
                    body += chunk
                
                body_str = body.decode('utf-8')
                
                # Check for sensitive patterns
                for pattern in self.sensitive_patterns:
                    import re
                    if re.search(pattern, body_str, re.IGNORECASE):
                        logger.warning(f"Potential data leak detected in response to {request.url.path}")
                        # In production, you might want to sanitize or block the response
                
                # Recreate response with same body
                from fastapi.responses import Response as FastAPIResponse
                return FastAPIResponse(
                    content=body,
                    status_code=response.status_code,
                    headers=dict(response.headers),
                    media_type=response.headers.get("content-type")
                )
                
            except Exception as e:
                logger.error(f"Data leak prevention check failed: {e}")
        
        return response

class RequestSizeMiddleware(BaseHTTPMiddleware):
    """Limit request size to prevent DoS attacks"""
    
    def __init__(self, app, max_size: int = 10 * 1024 * 1024):  # 10MB default
        super().__init__(app)
        self.max_size = max_size
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Check request size limits"""
        content_length = request.headers.get("content-length")
        
        if content_length:
            try:
                size = int(content_length)
                if size > self.max_size:
                    return JSONResponse(
                        status_code=413,
                        content={
                            "error": {
                                "message": "Request entity too large",
                                "code": 413,
                                "max_size": self.max_size,
                                "received_size": size
                            }
                        }
                    )
            except ValueError:
                return JSONResponse(
                    status_code=400,
                    content={
                        "error": {
                            "message": "Invalid Content-Length header",
                            "code": 400
                        }
                    }
                )
        
        return await call_next(request)

class IPWhitelistMiddleware(BaseHTTPMiddleware):
    """IP whitelist/blacklist middleware"""
    
    def __init__(self, app, whitelist: List[str] = None, blacklist: List[str] = None):
        super().__init__(app)
        self.whitelist = set(whitelist or [])
        self.blacklist = set(blacklist or [])
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Check IP whitelist/blacklist"""
        client_ip = self._get_client_ip(request)
        
        # Check blacklist first
        if self.blacklist and client_ip in self.blacklist:
            logger.warning(f"Blocked request from blacklisted IP: {client_ip}")
            return JSONResponse(
                status_code=403,
                content={
                    "error": {
                        "message": "Access denied",
                        "code": 403
                    }
                }
            )
        
        # Check whitelist if configured
        if self.whitelist and client_ip not in self.whitelist:
            logger.warning(f"Blocked request from non-whitelisted IP: {client_ip}")
            return JSONResponse(
                status_code=403,
                content={
                    "error": {
                        "message": "Access denied",
                        "code": 403
                    }
                }
            )
        
        return await call_next(request)
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address"""
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else "unknown"

class SecurityAuditMiddleware(BaseHTTPMiddleware):
    """Security audit logging middleware"""
    
    def __init__(self, app):
        super().__init__(app)
        self.security_events = [
            "authentication_failure",
            "authorization_failure",
            "rate_limit_exceeded",
            "suspicious_activity",
            "data_access",
            "admin_action"
        ]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Log security-relevant events"""
        start_time = time.time()
        
        # Process request
        response = await call_next(request)
        
        # Log security events
        await self._log_security_event(request, response, start_time)
        
        return response
    
    async def _log_security_event(self, request: Request, response: Response, start_time: float):
        """Log security-relevant events"""
        try:
            duration = time.time() - start_time
            client_ip = request.client.host if request.client else "unknown"
            
            # Determine if this is a security-relevant event
            is_security_event = (
                response.status_code in [401, 403, 429] or  # Auth/rate limit failures
                "/auth/" in request.url.path or  # Authentication endpoints
                "/admin/" in request.url.path or  # Admin endpoints
                "/gdpr/" in request.url.path or  # Data access endpoints
                request.method in ["DELETE", "PUT", "PATCH"]  # Data modification
            )
            
            if is_security_event:
                security_log = {
                    "timestamp": datetime.utcnow().isoformat(),
                    "event_type": self._classify_security_event(request, response),
                    "client_ip": client_ip,
                    "user_agent": request.headers.get("user-agent", ""),
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "duration": round(duration, 3),
                    "request_size": request.headers.get("content-length", 0)
                }
                
                # Log to security audit log
                security_logger = logging.getLogger("security_audit")
                security_logger.info(f"Security Event: {json.dumps(security_log)}")
                
        except Exception as e:
            logger.error(f"Security audit logging failed: {e}")
    
    def _classify_security_event(self, request: Request, response: Response) -> str:
        """Classify the type of security event"""
        if response.status_code == 401:
            return "authentication_failure"
        elif response.status_code == 403:
            return "authorization_failure"
        elif response.status_code == 429:
            return "rate_limit_exceeded"
        elif "/auth/" in request.url.path:
            return "authentication_attempt"
        elif "/admin/" in request.url.path:
            return "admin_action"
        elif "/gdpr/" in request.url.path:
            return "data_access"
        elif request.method in ["DELETE", "PUT", "PATCH"]:
            return "data_modification"
        else:
            return "general_access"