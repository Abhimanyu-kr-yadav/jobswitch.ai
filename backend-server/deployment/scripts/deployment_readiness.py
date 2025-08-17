#!/usr/bin/env python3
"""
Deployment Readiness Check for JobSwitch.ai
Final verification before production deployment.
"""

import os
import sys
import json
import subprocess
import time
from typing import Dict, List, Any
import logging
from datetime import datetime

# Add the backend-server directory to Python path
sys.path.insert(0, os.path.abspath('.'))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/deployment_readiness.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DeploymentReadinessChecker:
    """Check deployment readiness for JobSwitch.ai"""
    
    def __init__(self):
        self.checks = {}
        self.critical_issues = []
        self.warnings = []
        self.passed_checks = 0
        self.total_checks = 0
        
    def run_all_checks(self) -> Dict[str, Any]:
        """Run all deployment readiness checks"""
        logger.info("Starting deployment readiness checks...")
        
        # Infrastructure checks
        self.check_docker_environment()
        self.check_database_readiness()
        self.check_redis_readiness()
        
        # Application checks
        self.check_application_structure()
        self.check_configuration_files()
        self.check_security_configuration()
        
        # Performance checks
        self.check_performance_configuration()
        self.check_monitoring_setup()
        
        # Deployment checks
        self.check_deployment_scripts()
        self.check_backup_procedures()
        
        # Generate final report
        report = self.generate_readiness_report()
        
        logger.info("Deployment readiness checks completed")
        return report
    
    def check_docker_environment(self):
        """Check Docker environment readiness"""
        logger.info("Checking Docker environment...")
        
        docker_check = {
            'docker_installed': False,
            'docker_compose_installed': False,
            'docker_running': False,
            'required_images': {},
            'status': 'fail'
        }
        
        try:
            # Check Docker installation
            result = subprocess.run(['docker', '--version'], capture_output=True, text=True, timeout=10)
            docker_check['docker_installed'] = result.returncode == 0
            if result.returncode == 0:
                docker_check['docker_version'] = result.stdout.strip()
            
            # Check Docker Compose installation
            result = subprocess.run(['docker-compose', '--version'], capture_output=True, text=True, timeout=10)
            docker_check['docker_compose_installed'] = result.returncode == 0
            if result.returncode == 0:
                docker_check['docker_compose_version'] = result.stdout.strip()
            
            # Check if Docker daemon is running
            result = subprocess.run(['docker', 'info'], capture_output=True, text=True, timeout=10)
            docker_check['docker_running'] = result.returncode == 0
            
            # Check required files exist
            required_files = [
                'deployment/docker-compose.prod.yml',
                'deployment/Dockerfile.prod',
                'deployment/nginx/nginx.conf'
            ]
            
            missing_files = []
            for file_path in required_files:
                if not os.path.exists(file_path):
                    missing_files.append(file_path)
            
            docker_check['missing_files'] = missing_files
            
            # Overall status
            if (docker_check['docker_installed'] and 
                docker_check['docker_compose_installed'] and 
                docker_check['docker_running'] and 
                not missing_files):
                docker_check['status'] = 'pass'
                self.passed_checks += 1
            else:
                self.critical_issues.append("Docker environment not ready for deployment")
            
        except Exception as e:
            docker_check['error'] = str(e)
            self.critical_issues.append(f"Docker environment check failed: {e}")
        
        self.checks['docker_environment'] = docker_check
        self.total_checks += 1
    
    def check_database_readiness(self):
        """Check database readiness"""
        logger.info("Checking database readiness...")
        
        db_check = {
            'migration_files_exist': False,
            'models_defined': False,
            'connection_config': False,
            'status': 'fail'
        }
        
        try:
            # Check for Alembic migration files
            alembic_dir = 'alembic'
            versions_dir = os.path.join(alembic_dir, 'versions')
            
            db_check['migration_files_exist'] = (
                os.path.exists('alembic.ini') and 
                os.path.exists(versions_dir)
            )
            
            # Check model files exist
            model_files = [
                'app/models/user.py',
                'app/models/job.py',
                'app/models/resume.py',
                'app/models/interview.py',
                'app/models/networking.py',
                'app/models/career_strategy.py'
            ]
            
            existing_models = [f for f in model_files if os.path.exists(f)]
            db_check['models_defined'] = len(existing_models) >= 4  # At least 4 core models
            db_check['existing_models'] = existing_models
            
            # Check database configuration
            config_files = [
                'app/core/database.py',
                'deployment/.env.production.example'
            ]
            
            db_check['connection_config'] = all(os.path.exists(f) for f in config_files)
            
            # Overall status
            if (db_check['migration_files_exist'] and 
                db_check['models_defined'] and 
                db_check['connection_config']):
                db_check['status'] = 'pass'
                self.passed_checks += 1
            else:
                self.critical_issues.append("Database not ready for deployment")
            
        except Exception as e:
            db_check['error'] = str(e)
            self.critical_issues.append(f"Database readiness check failed: {e}")
        
        self.checks['database_readiness'] = db_check
        self.total_checks += 1
    
    def check_redis_readiness(self):
        """Check Redis cache readiness"""
        logger.info("Checking Redis readiness...")
        
        redis_check = {
            'cache_module_exists': False,
            'redis_config': False,
            'status': 'fail'
        }
        
        try:
            # Check cache module
            redis_check['cache_module_exists'] = os.path.exists('app/core/cache.py')
            
            # Check Redis configuration in docker-compose
            compose_file = 'deployment/docker-compose.prod.yml'
            if os.path.exists(compose_file):
                with open(compose_file, 'r') as f:
                    content = f.read()
                    redis_check['redis_config'] = 'redis:' in content
            
            # Overall status
            if redis_check['cache_module_exists'] and redis_check['redis_config']:
                redis_check['status'] = 'pass'
                self.passed_checks += 1
            else:
                self.warnings.append("Redis cache configuration incomplete")
            
        except Exception as e:
            redis_check['error'] = str(e)
            self.warnings.append(f"Redis readiness check failed: {e}")
        
        self.checks['redis_readiness'] = redis_check
        self.total_checks += 1
    
    def check_application_structure(self):
        """Check application structure"""
        logger.info("Checking application structure...")
        
        app_check = {
            'core_files': {},
            'api_endpoints': {},
            'agent_implementations': {},
            'status': 'fail'
        }
        
        try:
            # Check core application files
            core_files = [
                'app/main.py',
                'app/core/config.py',
                'app/core/auth.py',
                'app/core/exceptions.py'
            ]
            
            for file_path in core_files:
                app_check['core_files'][file_path] = os.path.exists(file_path)
            
            # Check API endpoint files
            api_files = [
                'app/api/auth.py',
                'app/api/user.py',
                'app/api/jobs.py',
                'app/api/dashboard.py'
            ]
            
            for file_path in api_files:
                app_check['api_endpoints'][file_path] = os.path.exists(file_path)
            
            # Check agent implementations
            agent_files = [
                'app/agents/base.py',
                'app/agents/job_discovery.py',
                'app/agents/skills_analysis.py',
                'app/agents/resume_optimization.py'
            ]
            
            for file_path in agent_files:
                app_check['agent_implementations'][file_path] = os.path.exists(file_path)
            
            # Calculate completion percentage
            all_files = list(app_check['core_files'].values()) + \
                       list(app_check['api_endpoints'].values()) + \
                       list(app_check['agent_implementations'].values())
            
            completion_rate = sum(all_files) / len(all_files) if all_files else 0
            app_check['completion_rate'] = round(completion_rate * 100, 2)
            
            # Overall status
            if completion_rate >= 0.8:  # 80% completion
                app_check['status'] = 'pass'
                self.passed_checks += 1
            else:
                self.critical_issues.append(f"Application structure incomplete ({completion_rate*100:.1f}%)")
            
        except Exception as e:
            app_check['error'] = str(e)
            self.critical_issues.append(f"Application structure check failed: {e}")
        
        self.checks['application_structure'] = app_check
        self.total_checks += 1
    
    def check_configuration_files(self):
        """Check configuration files"""
        logger.info("Checking configuration files...")
        
        config_check = {
            'environment_files': {},
            'deployment_configs': {},
            'monitoring_configs': {},
            'status': 'fail'
        }
        
        try:
            # Check environment files
            env_files = [
                '.env.example',
                'deployment/.env.production.example'
            ]
            
            for file_path in env_files:
                config_check['environment_files'][file_path] = os.path.exists(file_path)
            
            # Check deployment configurations
            deployment_configs = [
                'deployment/docker-compose.prod.yml',
                'deployment/Dockerfile.prod',
                'deployment/nginx/nginx.conf'
            ]
            
            for file_path in deployment_configs:
                config_check['deployment_configs'][file_path] = os.path.exists(file_path)
            
            # Check monitoring configurations
            monitoring_configs = [
                'deployment/monitoring/prometheus.yml'
            ]
            
            for file_path in monitoring_configs:
                config_check['monitoring_configs'][file_path] = os.path.exists(file_path)
            
            # Overall status
            all_configs = list(config_check['environment_files'].values()) + \
                         list(config_check['deployment_configs'].values()) + \
                         list(config_check['monitoring_configs'].values())
            
            completion_rate = sum(all_configs) / len(all_configs) if all_configs else 0
            
            if completion_rate >= 0.9:  # 90% completion
                config_check['status'] = 'pass'
                self.passed_checks += 1
            else:
                self.warnings.append("Some configuration files missing")
            
        except Exception as e:
            config_check['error'] = str(e)
            self.warnings.append(f"Configuration check failed: {e}")
        
        self.checks['configuration_files'] = config_check
        self.total_checks += 1
    
    def check_security_configuration(self):
        """Check security configuration"""
        logger.info("Checking security configuration...")
        
        security_check = {
            'auth_implementation': False,
            'rate_limiting': False,
            'input_validation': False,
            'https_config': False,
            'status': 'fail'
        }
        
        try:
            # Check authentication implementation
            security_check['auth_implementation'] = os.path.exists('app/core/auth.py')
            
            # Check rate limiting
            rate_limit_file = 'app/core/rate_limiting.py'
            security_check['rate_limiting'] = os.path.exists(rate_limit_file)
            
            # Check input validation
            validation_file = 'app/schemas/validation.py'
            security_check['input_validation'] = os.path.exists(validation_file)
            
            # Check HTTPS configuration in nginx
            nginx_config = 'deployment/nginx/nginx.conf'
            if os.path.exists(nginx_config):
                with open(nginx_config, 'r') as f:
                    content = f.read()
                    security_check['https_config'] = 'ssl_certificate' in content
            
            # Overall status
            security_features = [
                security_check['auth_implementation'],
                security_check['rate_limiting'],
                security_check['input_validation']
            ]
            
            if sum(security_features) >= 2:  # At least 2 out of 3
                security_check['status'] = 'pass'
                self.passed_checks += 1
            else:
                self.critical_issues.append("Security configuration incomplete")
            
        except Exception as e:
            security_check['error'] = str(e)
            self.critical_issues.append(f"Security check failed: {e}")
        
        self.checks['security_configuration'] = security_check
        self.total_checks += 1
    
    def check_performance_configuration(self):
        """Check performance configuration"""
        logger.info("Checking performance configuration...")
        
        perf_check = {
            'caching_implemented': False,
            'database_optimization': False,
            'monitoring_setup': False,
            'status': 'fail'
        }
        
        try:
            # Check caching
            perf_check['caching_implemented'] = os.path.exists('app/core/cache.py')
            
            # Check database optimization
            db_opt_file = 'app/core/database_optimization.py'
            perf_check['database_optimization'] = os.path.exists(db_opt_file)
            
            # Check monitoring setup
            monitoring_file = 'app/core/monitoring.py'
            perf_check['monitoring_setup'] = os.path.exists(monitoring_file)
            
            # Overall status
            perf_features = [
                perf_check['caching_implemented'],
                perf_check['monitoring_setup']
            ]
            
            if sum(perf_features) >= 1:  # At least basic performance features
                perf_check['status'] = 'pass'
                self.passed_checks += 1
            else:
                self.warnings.append("Performance optimization features missing")
            
        except Exception as e:
            perf_check['error'] = str(e)
            self.warnings.append(f"Performance check failed: {e}")
        
        self.checks['performance_configuration'] = perf_check
        self.total_checks += 1
    
    def check_monitoring_setup(self):
        """Check monitoring and logging setup"""
        logger.info("Checking monitoring setup...")
        
        monitoring_check = {
            'logging_configured': False,
            'health_checks': False,
            'metrics_collection': False,
            'status': 'fail'
        }
        
        try:
            # Check logging configuration
            logging_file = 'app/core/logging_config.py'
            monitoring_check['logging_configured'] = os.path.exists(logging_file)
            
            # Check health checks
            # Look for health endpoint in main.py or separate health module
            main_file = 'app/main.py'
            if os.path.exists(main_file):
                with open(main_file, 'r') as f:
                    content = f.read()
                    monitoring_check['health_checks'] = '/health' in content or 'health' in content.lower()
            
            # Check metrics collection
            monitoring_file = 'app/core/monitoring.py'
            monitoring_check['metrics_collection'] = os.path.exists(monitoring_file)
            
            # Overall status
            monitoring_features = [
                monitoring_check['logging_configured'],
                monitoring_check['health_checks']
            ]
            
            if sum(monitoring_features) >= 1:
                monitoring_check['status'] = 'pass'
                self.passed_checks += 1
            else:
                self.warnings.append("Monitoring setup incomplete")
            
        except Exception as e:
            monitoring_check['error'] = str(e)
            self.warnings.append(f"Monitoring check failed: {e}")
        
        self.checks['monitoring_setup'] = monitoring_check
        self.total_checks += 1
    
    def check_deployment_scripts(self):
        """Check deployment scripts"""
        logger.info("Checking deployment scripts...")
        
        deploy_check = {
            'deployment_script': False,
            'integration_tests': False,
            'performance_optimization': False,
            'status': 'fail'
        }
        
        try:
            # Check deployment script
            deploy_script = 'deployment/scripts/deploy.sh'
            deploy_check['deployment_script'] = os.path.exists(deploy_script)
            
            # Check integration tests
            test_files = [
                'tests/integration/test_complete_system_integration.py',
                'tests/acceptance/test_user_acceptance_scenarios.py'
            ]
            
            deploy_check['integration_tests'] = any(os.path.exists(f) for f in test_files)
            
            # Check performance optimization script
            perf_script = 'deployment/scripts/optimize_performance.py'
            deploy_check['performance_optimization'] = os.path.exists(perf_script)
            
            # Overall status
            deploy_features = [
                deploy_check['deployment_script'],
                deploy_check['integration_tests']
            ]
            
            if sum(deploy_features) >= 1:
                deploy_check['status'] = 'pass'
                self.passed_checks += 1
            else:
                self.warnings.append("Deployment automation incomplete")
            
        except Exception as e:
            deploy_check['error'] = str(e)
            self.warnings.append(f"Deployment scripts check failed: {e}")
        
        self.checks['deployment_scripts'] = deploy_check
        self.total_checks += 1
    
    def check_backup_procedures(self):
        """Check backup procedures"""
        logger.info("Checking backup procedures...")
        
        backup_check = {
            'backup_scripts': False,
            'backup_config': False,
            'recovery_procedures': False,
            'status': 'fail'
        }
        
        try:
            # Check for backup-related files
            backup_files = [
                'app/core/backup_manager.py',
                'deployment/scripts/deploy.sh'  # Should contain backup procedures
            ]
            
            backup_check['backup_scripts'] = any(os.path.exists(f) for f in backup_files)
            
            # Check backup configuration in docker-compose
            compose_file = 'deployment/docker-compose.prod.yml'
            if os.path.exists(compose_file):
                with open(compose_file, 'r') as f:
                    content = f.read()
                    backup_check['backup_config'] = 'backup' in content.lower()
            
            # Check for recovery documentation
            docs = ['README.md', 'deployment/README.md']
            backup_check['recovery_procedures'] = any(os.path.exists(f) for f in docs)
            
            # Overall status (backup is important but not critical for initial deployment)
            if backup_check['backup_scripts'] or backup_check['backup_config']:
                backup_check['status'] = 'pass'
                self.passed_checks += 1
            else:
                self.warnings.append("Backup procedures not fully implemented")
            
        except Exception as e:
            backup_check['error'] = str(e)
            self.warnings.append(f"Backup procedures check failed: {e}")
        
        self.checks['backup_procedures'] = backup_check
        self.total_checks += 1
    
    def generate_readiness_report(self) -> Dict[str, Any]:
        """Generate deployment readiness report"""
        
        # Calculate readiness score
        readiness_score = (self.passed_checks / self.total_checks * 100) if self.total_checks > 0 else 0
        
        # Determine deployment readiness
        if len(self.critical_issues) == 0 and readiness_score >= 80:
            deployment_ready = True
            readiness_status = "READY"
        elif len(self.critical_issues) == 0 and readiness_score >= 60:
            deployment_ready = True
            readiness_status = "READY_WITH_WARNINGS"
        else:
            deployment_ready = False
            readiness_status = "NOT_READY"
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'deployment_ready': deployment_ready,
            'readiness_status': readiness_status,
            'readiness_score': round(readiness_score, 2),
            'summary': {
                'total_checks': self.total_checks,
                'passed_checks': self.passed_checks,
                'critical_issues': len(self.critical_issues),
                'warnings': len(self.warnings)
            },
            'critical_issues': self.critical_issues,
            'warnings': self.warnings,
            'detailed_checks': self.checks,
            'deployment_recommendations': self.generate_deployment_recommendations()
        }
        
        # Save report
        os.makedirs('logs', exist_ok=True)
        report_file = f"logs/deployment_readiness_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Deployment readiness report saved to {report_file}")
        return report
    
    def generate_deployment_recommendations(self) -> List[str]:
        """Generate deployment recommendations"""
        recommendations = []
        
        if self.critical_issues:
            recommendations.append("❌ CRITICAL: Fix all critical issues before deployment")
            recommendations.extend([f"   - {issue}" for issue in self.critical_issues[:3]])
        
        if len(self.warnings) > 0:
            recommendations.append("⚠️  Address warnings to improve deployment reliability")
        
        # Specific recommendations based on checks
        if 'docker_environment' in self.checks:
            docker_check = self.checks['docker_environment']
            if docker_check['status'] != 'pass':
                recommendations.append("🐳 Ensure Docker and Docker Compose are properly installed and running")
        
        if 'security_configuration' in self.checks:
            security_check = self.checks['security_configuration']
            if security_check['status'] != 'pass':
                recommendations.append("🔒 Complete security configuration (auth, rate limiting, validation)")
        
        if 'monitoring_setup' in self.checks:
            monitoring_check = self.checks['monitoring_setup']
            if monitoring_check['status'] != 'pass':
                recommendations.append("📊 Set up monitoring and logging for production visibility")
        
        return recommendations

def main():
    """Main deployment readiness check"""
    checker = DeploymentReadinessChecker()
    report = checker.run_all_checks()
    
    print("\n" + "="*70)
    print("JOBSWITCH.AI DEPLOYMENT READINESS REPORT")
    print("="*70)
    print(f"Status: {report['readiness_status']}")
    print(f"Readiness Score: {report['readiness_score']}%")
    print(f"Checks Passed: {report['summary']['passed_checks']}/{report['summary']['total_checks']}")
    print(f"Critical Issues: {report['summary']['critical_issues']}")
    print(f"Warnings: {report['summary']['warnings']}")
    
    if report['deployment_ready']:
        print(f"\n✅ DEPLOYMENT READY")
        if report['readiness_status'] == "READY_WITH_WARNINGS":
            print("   (with warnings - review before proceeding)")
    else:
        print(f"\n❌ NOT READY FOR DEPLOYMENT")
    
    if report['critical_issues']:
        print("\nCRITICAL ISSUES TO FIX:")
        for issue in report['critical_issues'][:5]:
            print(f"  ❌ {issue}")
        if len(report['critical_issues']) > 5:
            print(f"  ... and {len(report['critical_issues']) - 5} more critical issues")
    
    if report['warnings']:
        print("\nWARNINGS:")
        for warning in report['warnings'][:3]:
            print(f"  ⚠️  {warning}")
        if len(report['warnings']) > 3:
            print(f"  ... and {len(report['warnings']) - 3} more warnings")
    
    if report['deployment_recommendations']:
        print("\nDEPLOYMENT RECOMMENDATIONS:")
        for rec in report['deployment_recommendations']:
            print(f"  {rec}")
    
    print(f"\nDetailed report: logs/deployment_readiness_*.json")
    
    # Exit with appropriate code
    if not report['deployment_ready']:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()