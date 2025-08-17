#!/usr/bin/env python3
"""Simple test to debug monitoring module"""

print("Starting monitoring module test...")

try:
    print("Step 1: Testing basic imports...")
    import asyncio
    import time
    import psutil
    import logging
    from typing import Dict, Any, List, Optional, Callable
    from datetime import datetime, timedelta
    from dataclasses import dataclass, field
    from enum import Enum
    import json
    print("✅ Basic imports OK")
    
    print("Step 2: Testing core imports...")
    from app.core.exceptions import JobSwitchException, ErrorCode
    from app.core.logging_config import get_logger, logging_manager
    from app.core.retry import get_retry_stats
    from app.core.fallback import get_fallback_stats
    print("✅ Core imports OK")
    
    print("Step 3: Executing monitoring module content manually...")
    
    # Define the classes manually to test
    class HealthStatus(Enum):
        HEALTHY = "healthy"
        DEGRADED = "degraded"
        UNHEALTHY = "unhealthy"
        CRITICAL = "critical"
    
    @dataclass
    class HealthCheckResult:
        name: str
        status: HealthStatus
        message: str
        details: Dict[str, Any] = field(default_factory=dict)
        timestamp: datetime = field(default_factory=datetime.utcnow)
        response_time_ms: Optional[float] = None
    
    print("✅ Classes defined OK")
    
    # Try to create a simple MonitoringManager
    class SimpleMonitoringManager:
        def __init__(self):
            self.health_checkers = []
            self.is_running = False
            print("SimpleMonitoringManager created")
    
    simple_manager = SimpleMonitoringManager()
    print("✅ Simple manager created OK")
    
    print("Step 4: Now trying to import the actual module...")
    
    # Try to read the monitoring file and see what happens
    with open('app/core/monitoring.py', 'r') as f:
        content = f.read()
        print(f"File length: {len(content)} characters")
        
        # Check if monitoring_manager is defined
        if 'monitoring_manager = MonitoringManager()' in content:
            print("✅ monitoring_manager definition found in file")
        else:
            print("❌ monitoring_manager definition NOT found in file")
    
    print("Step 5: Attempting module import...")
    import app.core.monitoring as mon
    print(f"Module imported. Available attributes: {[attr for attr in dir(mon) if not attr.startswith('_')]}")
    
except Exception as e:
    print(f"❌ Error at step: {e}")
    import traceback
    traceback.print_exc()