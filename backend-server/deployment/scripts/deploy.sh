#!/bin/bash

# JobSwitch.ai Production Deployment Script
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
ENVIRONMENT=${ENVIRONMENT:-production}
BACKUP_DIR="./backups/$(date +%Y%m%d_%H%M%S)"
LOG_FILE="./logs/deployment_$(date +%Y%m%d_%H%M%S).log"

echo -e "${GREEN}Starting JobSwitch.ai deployment...${NC}"

# Create log directory
mkdir -p logs backups

# Function to log messages
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."
    
    if ! command_exists docker; then
        echo -e "${RED}Error: Docker is not installed${NC}"
        exit 1
    fi
    
    if ! command_exists docker-compose; then
        echo -e "${RED}Error: Docker Compose is not installed${NC}"
        exit 1
    fi
    
    if [ ! -f ".env.production" ]; then
        echo -e "${RED}Error: .env.production file not found${NC}"
        exit 1
    fi
    
    log "Prerequisites check passed"
}

# Backup existing data
backup_data() {
    log "Creating backup..."
    mkdir -p "$BACKUP_DIR"
    
    # Backup database
    if docker-compose -f docker-compose.prod.yml ps db | grep -q "Up"; then
        log "Backing up database..."
        docker-compose -f docker-compose.prod.yml exec -T db pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB" > "$BACKUP_DIR/database.sql"
    fi
    
    # Backup Redis data
    if docker-compose -f docker-compose.prod.yml ps redis | grep -q "Up"; then
        log "Backing up Redis data..."
        docker-compose -f docker-compose.prod.yml exec -T redis redis-cli BGSAVE
        docker cp $(docker-compose -f docker-compose.prod.yml ps -q redis):/data/dump.rdb "$BACKUP_DIR/redis_dump.rdb"
    fi
    
    # Backup application logs
    if [ -d "logs" ]; then
        log "Backing up logs..."
        cp -r logs "$BACKUP_DIR/"
    fi
    
    log "Backup completed: $BACKUP_DIR"
}

# Run tests before deployment
run_tests() {
    log "Running tests..."
    
    # Build test image
    docker build -f deployment/Dockerfile.test -t jobswitch-test .
    
    # Run unit tests
    if ! docker run --rm jobswitch-test python -m pytest tests/unit/ -v; then
        echo -e "${RED}Unit tests failed. Deployment aborted.${NC}"
        exit 1
    fi
    
    # Run integration tests
    if ! docker run --rm jobswitch-test python -m pytest tests/integration/ -v; then
        echo -e "${RED}Integration tests failed. Deployment aborted.${NC}"
        exit 1
    fi
    
    log "All tests passed"
}

# Deploy application
deploy_application() {
    log "Deploying application..."
    
    # Load environment variables
    export $(cat .env.production | xargs)
    
    # Pull latest images
    docker-compose -f docker-compose.prod.yml pull
    
    # Build application image
    docker-compose -f docker-compose.prod.yml build api
    
    # Start services
    docker-compose -f docker-compose.prod.yml up -d
    
    # Wait for services to be healthy
    log "Waiting for services to be healthy..."
    sleep 30
    
    # Check service health
    check_service_health
    
    log "Application deployed successfully"
}

# Check service health
check_service_health() {
    log "Checking service health..."
    
    # Check API health
    for i in {1..30}; do
        if curl -f http://localhost:8000/api/v1/health >/dev/null 2>&1; then
            log "API service is healthy"
            break
        fi
        if [ $i -eq 30 ]; then
            echo -e "${RED}API service health check failed${NC}"
            exit 1
        fi
        sleep 10
    done
    
    # Check database connection
    if ! docker-compose -f docker-compose.prod.yml exec -T db pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB" >/dev/null 2>&1; then
        echo -e "${RED}Database health check failed${NC}"
        exit 1
    fi
    
    # Check Redis connection
    if ! docker-compose -f docker-compose.prod.yml exec -T redis redis-cli ping >/dev/null 2>&1; then
        echo -e "${RED}Redis health check failed${NC}"
        exit 1
    fi
    
    log "All services are healthy"
}

# Run database migrations
run_migrations() {
    log "Running database migrations..."
    
    docker-compose -f docker-compose.prod.yml exec api alembic upgrade head
    
    log "Database migrations completed"
}

# Setup monitoring
setup_monitoring() {
    log "Setting up monitoring..."
    
    # Start monitoring services
    docker-compose -f docker-compose.prod.yml up -d prometheus grafana
    
    # Wait for services to start
    sleep 20
    
    # Import Grafana dashboards
    if [ -d "deployment/monitoring/grafana/dashboards" ]; then
        log "Importing Grafana dashboards..."
        # Dashboard import logic would go here
    fi
    
    log "Monitoring setup completed"
}

# Cleanup old resources
cleanup() {
    log "Cleaning up old resources..."
    
    # Remove unused Docker images
    docker image prune -f
    
    # Remove old backups (keep last 7 days)
    find backups/ -type d -mtime +7 -exec rm -rf {} + 2>/dev/null || true
    
    # Remove old logs (keep last 30 days)
    find logs/ -name "*.log" -mtime +30 -delete 2>/dev/null || true
    
    log "Cleanup completed"
}

# Rollback function
rollback() {
    log "Rolling back deployment..."
    
    # Stop current services
    docker-compose -f docker-compose.prod.yml down
    
    # Restore from backup
    if [ -n "$1" ] && [ -d "$1" ]; then
        log "Restoring from backup: $1"
        
        # Restore database
        if [ -f "$1/database.sql" ]; then
            docker-compose -f docker-compose.prod.yml up -d db
            sleep 10
            docker-compose -f docker-compose.prod.yml exec -T db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" < "$1/database.sql"
        fi
        
        # Restore Redis
        if [ -f "$1/redis_dump.rdb" ]; then
            docker-compose -f docker-compose.prod.yml up -d redis
            sleep 10
            docker cp "$1/redis_dump.rdb" $(docker-compose -f docker-compose.prod.yml ps -q redis):/data/dump.rdb
            docker-compose -f docker-compose.prod.yml restart redis
        fi
    fi
    
    log "Rollback completed"
}

# Main deployment flow
main() {
    case "${1:-deploy}" in
        "deploy")
            check_prerequisites
            backup_data
            run_tests
            deploy_application
            run_migrations
            setup_monitoring
            cleanup
            echo -e "${GREEN}Deployment completed successfully!${NC}"
            ;;
        "rollback")
            if [ -z "$2" ]; then
                echo -e "${RED}Error: Please specify backup directory for rollback${NC}"
                echo "Usage: $0 rollback <backup_directory>"
                exit 1
            fi
            rollback "$2"
            ;;
        "health")
            check_service_health
            ;;
        "backup")
            backup_data
            ;;
        "test")
            run_tests
            ;;
        *)
            echo "Usage: $0 {deploy|rollback|health|backup|test}"
            echo "  deploy   - Full deployment process"
            echo "  rollback - Rollback to specified backup"
            echo "  health   - Check service health"
            echo "  backup   - Create backup only"
            echo "  test     - Run tests only"
            exit 1
            ;;
    esac
}

# Handle script interruption
trap 'echo -e "${RED}Deployment interrupted${NC}"; exit 1' INT TERM

# Run main function
main "$@"