#!/usr/bin/env python3
"""Debug script to test monitoring module imports"""

try:
    print("Testing basic imports...")
    import asyncio
    import time
    import psutil
    import logging
    from typing import Dict, Any, List, Optional, Callable
    from datetime import datetime, timedelta
    from dataclasses import dataclass, field
    from enum import Enum
    import json
    print("✅ Basic imports successful")
    
    print("Testing app.core imports...")
    from app.core.exceptions import JobSwitchException, ErrorCode
    print("✅ Exceptions import successful")
    
    from app.core.logging_config import get_logger, logging_manager
    print("✅ Logging config import successful")
    
    from app.core.retry import get_retry_stats
    print("✅ Retry import successful")
    
    from app.core.fallback import get_fallback_stats
    print("✅ Fallback import successful")
    
    print("Testing monitoring module classes...")
    
    # Test HealthStatus enum
    class HealthStatus(Enum):
        HEALTHY = "healthy"
        DEGRADED = "degraded"
        UNHEALTHY = "unhealthy"
        CRITICAL = "critical"
    print("✅ HealthStatus enum created")
    
    # Test dataclasses
    @dataclass
    class HealthCheckResult:
        name: str
        status: HealthStatus
        message: str
        details: Dict[str, Any] = field(default_factory=dict)
        timestamp: datetime = field(default_factory=datetime.utcnow)
        response_time_ms: Optional[float] = None
    print("✅ HealthCheckResult dataclass created")
    
    @dataclass
    class MetricPoint:
        timestamp: datetime
        value: float
        labels: Dict[str, str] = field(default_factory=dict)
    print("✅ MetricPoint dataclass created")
    
    print("All imports and classes work individually!")
    
    print("Now testing full monitoring module import...")
    import app.core.monitoring
    print("✅ Monitoring module imported successfully")
    
    print("Testing monitoring_manager import...")
    from app.core.monitoring import monitoring_manager
    print("✅ monitoring_manager imported successfully")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()