#!/usr/bin/env python3
"""
System Verification Script for JobSwitch.ai
Verifies all system components are working correctly before deployment.
"""

import sys
import os
import importlib
import subprocess
import json
import time
from typing import Dict, List, Any, Tuple
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/system_verification.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SystemVerifier:
    """Comprehensive system verification"""
    
    def __init__(self):
        self.results = {}
        self.errors = []
        self.warnings = []
        
    def run_verification(self) -> Dict[str, Any]:
        """Run complete system verification"""
        logger.info("Starting system verification...")
        
        # Verify Python environment
        self.verify_python_environment()
        
        # Verify dependencies
        self.verify_dependencies()
        
        # Verify application modules
        self.verify_application_modules()
        
        # Verify database models
        self.verify_database_models()
        
        # Verify API endpoints
        self.verify_api_structure()
        
        # Verify agent implementations
        self.verify_agents()
        
        # Verify configuration
        self.verify_configuration()
        
        # Verify file structure
        self.verify_file_structure()
        
        # Generate verification report
        report = self.generate_report()
        
        logger.info("System verification completed")
        return report
    
    def verify_python_environment(self):
        """Verify Python environment and version"""
        logger.info("Verifying Python environment...")
        
        python_version = sys.version_info
        
        self.results['python_environment'] = {
            'version': f"{python_version.major}.{python_version.minor}.{python_version.micro}",
            'executable': sys.executable,
            'platform': sys.platform,
            'path': sys.path[:3]  # First 3 paths
        }
        
        # Check Python version
        if python_version < (3, 8):
            self.errors.append("Python version 3.8+ required")
        elif python_version < (3, 9):
            self.warnings.append("Python 3.9+ recommended")
    
    def verify_dependencies(self):
        """Verify required dependencies are installed"""
        logger.info("Verifying dependencies...")
        
        required_packages = [
            'fastapi',
            'uvicorn',
            'sqlalchemy',
            'alembic',
            'pydantic',
            'redis',
            'psycopg2',
            'requests',
            'python-jose',
            'passlib',
            'python-multipart',
            'websockets'
        ]
        
        optional_packages = [
            'pytest',
            'langchain',
            'openai',
            'boto3',
            'celery'
        ]
        
        installed_packages = {}
        missing_required = []
        missing_optional = []
        
        for package in required_packages:
            try:
                module = importlib.import_module(package.replace('-', '_'))
                version = getattr(module, '__version__', 'unknown')
                installed_packages[package] = version
            except ImportError:
                missing_required.append(package)
        
        for package in optional_packages:
            try:
                module = importlib.import_module(package.replace('-', '_'))
                version = getattr(module, '__version__', 'unknown')
                installed_packages[package] = version
            except ImportError:
                missing_optional.append(package)
        
        self.results['dependencies'] = {
            'installed': installed_packages,
            'missing_required': missing_required,
            'missing_optional': missing_optional
        }
        
        if missing_required:
            self.errors.extend([f"Missing required package: {pkg}" for pkg in missing_required])
        
        if missing_optional:
            self.warnings.extend([f"Missing optional package: {pkg}" for pkg in missing_optional])
    
    def verify_application_modules(self):
        """Verify application modules can be imported"""
        logger.info("Verifying application modules...")
        
        core_modules = [
            'app.main',
            'app.core.config',
            'app.core.auth',
            'app.core.database',
            'app.core.cache',
            'app.core.exceptions',
            'app.core.logging_config'
        ]
        
        api_modules = [
            'app.api.auth',
            'app.api.user',
            'app.api.jobs',
            'app.api.dashboard'
        ]
        
        agent_modules = [
            'app.agents.base',
            'app.agents.job_discovery',
            'app.agents.skills_analysis',
            'app.agents.resume_optimization'
        ]
        
        all_modules = core_modules + api_modules + agent_modules
        
        importable_modules = {}
        failed_imports = []
        
        for module_name in all_modules:
            try:
                module = importlib.import_module(module_name)
                importable_modules[module_name] = 'success'
            except Exception as e:
                failed_imports.append((module_name, str(e)))
                importable_modules[module_name] = f'failed: {str(e)}'
        
        self.results['application_modules'] = {
            'importable': importable_modules,
            'failed_imports': failed_imports
        }
        
        if failed_imports:
            self.errors.extend([f"Failed to import {mod}: {err}" for mod, err in failed_imports])
    
    def verify_database_models(self):
        """Verify database models are properly defined"""
        logger.info("Verifying database models...")
        
        model_modules = [
            'app.models.user',
            'app.models.job',
            'app.models.resume',
            'app.models.interview',
            'app.models.networking',
            'app.models.career_strategy'
        ]
        
        model_verification = {}
        
        for module_name in model_modules:
            try:
                module = importlib.import_module(module_name)
                
                # Check for SQLAlchemy models
                models = []
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if hasattr(attr, '__tablename__'):
                        models.append(attr_name)
                
                model_verification[module_name] = {
                    'status': 'success',
                    'models': models
                }
                
            except Exception as e:
                model_verification[module_name] = {
                    'status': 'failed',
                    'error': str(e)
                }
                self.errors.append(f"Database model verification failed for {module_name}: {e}")
        
        self.results['database_models'] = model_verification
    
    def verify_api_structure(self):
        """Verify API endpoint structure"""
        logger.info("Verifying API structure...")
        
        try:
            from app.main import app
            
            # Get all routes
            routes = []
            for route in app.routes:
                if hasattr(route, 'path') and hasattr(route, 'methods'):
                    routes.append({
                        'path': route.path,
                        'methods': list(route.methods) if route.methods else [],
                        'name': getattr(route, 'name', 'unknown')
                    })
            
            # Categorize routes
            api_routes = [r for r in routes if r['path'].startswith('/api/')]
            auth_routes = [r for r in routes if '/auth/' in r['path']]
            agent_routes = [r for r in routes if '/agents/' in r['path']]
            
            self.results['api_structure'] = {
                'total_routes': len(routes),
                'api_routes': len(api_routes),
                'auth_routes': len(auth_routes),
                'agent_routes': len(agent_routes),
                'routes': routes[:10]  # First 10 routes for inspection
            }
            
            # Check for essential routes
            essential_paths = ['/api/v1/health', '/api/v1/auth/login', '/api/v1/auth/register']
            missing_essential = []
            
            for essential in essential_paths:
                if not any(r['path'] == essential for r in routes):
                    missing_essential.append(essential)
            
            if missing_essential:
                self.warnings.extend([f"Missing essential route: {path}" for path in missing_essential])
            
        except Exception as e:
            self.results['api_structure'] = {'error': str(e)}
            self.errors.append(f"API structure verification failed: {e}")
    
    def verify_agents(self):
        """Verify AI agent implementations"""
        logger.info("Verifying AI agents...")
        
        agent_classes = [
            ('app.agents.job_discovery', 'JobDiscoveryAgent'),
            ('app.agents.skills_analysis', 'SkillsAnalysisAgent'),
            ('app.agents.resume_optimization', 'ResumeOptimizationAgent'),
            ('app.agents.interview_preparation', 'InterviewPreparationAgent'),
            ('app.agents.networking', 'NetworkingAgent'),
            ('app.agents.career_strategy', 'CareerStrategyAgent')
        ]
        
        agent_verification = {}
        
        for module_name, class_name in agent_classes:
            try:
                module = importlib.import_module(module_name)
                agent_class = getattr(module, class_name)
                
                # Check if it has required methods
                required_methods = ['process_request', 'get_recommendations']
                available_methods = [method for method in required_methods if hasattr(agent_class, method)]
                missing_methods = [method for method in required_methods if not hasattr(agent_class, method)]
                
                agent_verification[class_name] = {
                    'status': 'success',
                    'available_methods': available_methods,
                    'missing_methods': missing_methods
                }
                
                if missing_methods:
                    self.warnings.append(f"{class_name} missing methods: {missing_methods}")
                
            except Exception as e:
                agent_verification[class_name] = {
                    'status': 'failed',
                    'error': str(e)
                }
                self.errors.append(f"Agent verification failed for {class_name}: {e}")
        
        self.results['agents'] = agent_verification
    
    def verify_configuration(self):
        """Verify configuration files and environment variables"""
        logger.info("Verifying configuration...")
        
        config_verification = {}
        
        # Check configuration module
        try:
            from app.core.config import settings
            
            config_verification['settings_module'] = {
                'status': 'success',
                'environment': getattr(settings, 'ENVIRONMENT', 'unknown'),
                'debug': getattr(settings, 'DEBUG', 'unknown')
            }
            
        except Exception as e:
            config_verification['settings_module'] = {
                'status': 'failed',
                'error': str(e)
            }
            self.errors.append(f"Configuration module verification failed: {e}")
        
        # Check environment files
        env_files = ['.env', '.env.example', 'deployment/.env.production.example']
        
        for env_file in env_files:
            if os.path.exists(env_file):
                config_verification[env_file] = {'status': 'exists'}
            else:
                config_verification[env_file] = {'status': 'missing'}
                if env_file == '.env':
                    self.warnings.append(f"Environment file {env_file} not found")
        
        self.results['configuration'] = config_verification
    
    def verify_file_structure(self):
        """Verify required file and directory structure"""
        logger.info("Verifying file structure...")
        
        required_directories = [
            'app',
            'app/api',
            'app/agents',
            'app/core',
            'app/models',
            'app/integrations',
            'tests',
            'logs',
            'deployment'
        ]
        
        required_files = [
            'app/main.py',
            'requirements.txt',
            'README.md',
            'deployment/docker-compose.prod.yml',
            'deployment/Dockerfile.prod'
        ]
        
        directory_status = {}
        file_status = {}
        
        for directory in required_directories:
            directory_status[directory] = os.path.isdir(directory)
            if not os.path.isdir(directory):
                self.warnings.append(f"Missing directory: {directory}")
        
        for file_path in required_files:
            file_status[file_path] = os.path.isfile(file_path)
            if not os.path.isfile(file_path):
                self.warnings.append(f"Missing file: {file_path}")
        
        self.results['file_structure'] = {
            'directories': directory_status,
            'files': file_status
        }
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive verification report"""
        
        # Calculate overall status
        overall_status = 'healthy'
        if self.errors:
            overall_status = 'critical'
        elif self.warnings:
            overall_status = 'warning'
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'overall_status': overall_status,
            'summary': {
                'errors': len(self.errors),
                'warnings': len(self.warnings),
                'checks_performed': len(self.results)
            },
            'errors': self.errors,
            'warnings': self.warnings,
            'detailed_results': self.results,
            'recommendations': self.generate_recommendations()
        }
        
        # Save report
        report_file = f"logs/system_verification_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        os.makedirs('logs', exist_ok=True)
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"System verification report saved to {report_file}")
        return report
    
    def generate_recommendations(self) -> List[str]:
        """Generate recommendations based on verification results"""
        recommendations = []
        
        if self.errors:
            recommendations.append("Fix all critical errors before deployment")
        
        if 'dependencies' in self.results:
            missing_required = self.results['dependencies'].get('missing_required', [])
            if missing_required:
                recommendations.append(f"Install missing required packages: {', '.join(missing_required)}")
        
        if 'application_modules' in self.results:
            failed_imports = self.results['application_modules'].get('failed_imports', [])
            if failed_imports:
                recommendations.append("Fix module import errors")
        
        if len(self.warnings) > 5:
            recommendations.append("Address warnings to improve system reliability")
        
        return recommendations

def main():
    """Main verification function"""
    verifier = SystemVerifier()
    report = verifier.run_verification()
    
    print("\n" + "="*60)
    print("SYSTEM VERIFICATION REPORT")
    print("="*60)
    print(f"Overall Status: {report['overall_status'].upper()}")
    print(f"Errors: {report['summary']['errors']}")
    print(f"Warnings: {report['summary']['warnings']}")
    print(f"Checks Performed: {report['summary']['checks_performed']}")
    
    if report['errors']:
        print("\nCRITICAL ERRORS:")
        for error in report['errors']:
            print(f"  ❌ {error}")
    
    if report['warnings']:
        print("\nWARNINGS:")
        for warning in report['warnings'][:5]:  # Show first 5 warnings
            print(f"  ⚠️  {warning}")
        if len(report['warnings']) > 5:
            print(f"  ... and {len(report['warnings']) - 5} more warnings")
    
    if report['recommendations']:
        print("\nRECOMMENDATIONS:")
        for rec in report['recommendations']:
            print(f"  💡 {rec}")
    
    print(f"\nDetailed report saved to logs/system_verification_*.json")
    
    # Exit with appropriate code
    if report['errors']:
        print("\n❌ System verification FAILED - Critical errors found")
        sys.exit(1)
    elif report['warnings']:
        print("\n⚠️  System verification PASSED with warnings")
        sys.exit(0)
    else:
        print("\n✅ System verification PASSED - All checks successful")
        sys.exit(0)

if __name__ == "__main__":
    main()