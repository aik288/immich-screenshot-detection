#!/bin/bash

# Immich Screenshot Categorizer - Run Script
# This script helps with running the application in different modes

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if Docker is running
check_docker() {
    if ! docker info >/dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker and try again."
        exit 1
    fi
}

# Function to check if environment file exists
check_env_file() {
    if [ ! -f .env ]; then
        if [ -f config.env.example ]; then
            print_warning "No .env file found. Creating from example..."
            cp config.env.example .env
            print_warning "Please edit .env with your configuration before continuing."
            exit 1
        else
            print_error "No .env file found and no example file available."
            exit 1
        fi
    fi
}

# Function to build the Docker image
build_image() {
    print_status "Building Docker image..."
    docker build -t immich-screenshot-categorizer .
    print_status "Docker image built successfully."
}

# Function to run the application
run_application() {
    print_status "Running Immich Screenshot Categorizer..."

    # Load environment variables
    source .env

    # Check required variables
    if [ -z "$IMMICH_API_KEY" ] || [ -z "$IMMICH_USER_ID" ]; then
        print_error "Required environment variables not set. Please check your .env file."
        exit 1
    fi

    # Run the container
    docker run --rm \
        --env-file .env \
        --name immich-screenshot-categorizer \
        -v "$(pwd)/logs:/app/logs" \
        immich-screenshot-categorizer
}

# Function to run with docker-compose
run_compose() {
    print_status "Running with Docker Compose..."

    if [ ! -f docker-compose.yml ]; then
        print_error "docker-compose.yml not found."
        exit 1
    fi

    docker-compose up -d
    print_status "Service started. Use 'docker-compose logs -f' to view logs."
}

# Function to stop docker-compose services
stop_compose() {
    print_status "Stopping Docker Compose services..."
    docker-compose down
    print_status "Services stopped."
}

# Function to view logs
view_logs() {
    if docker-compose ps | grep -q immich-screenshot-categorizer; then
        docker-compose logs -f immich-screenshot-categorizer
    else
        print_error "Service not running with docker-compose."
        exit 1
    fi
}

# Function to run tests
run_tests() {
    print_status "Running tests..."
    docker run --rm \
        -v "$(pwd):/app" \
        -w /app \
        python:3.11-slim \
        bash -c "pip install -r requirements.txt && python -m pytest tests/ -v"
}

# Function to show help
show_help() {
    echo "Immich Screenshot Categorizer - Run Script"
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  build          Build the Docker image"
    echo "  run            Run the application once"
    echo "  start          Start services with docker-compose"
    echo "  stop           Stop docker-compose services"
    echo "  logs           View logs from running service"
    echo "  test           Run tests"
    echo "  help           Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 build       # Build the Docker image"
    echo "  $0 run         # Run the application once"
    echo "  $0 start       # Start with docker-compose"
    echo "  $0 logs        # View logs"
    echo ""
}

# Main script logic
main() {
    case ${1:-""} in
    "build")
        check_docker
        build_image
        ;;
    "run")
        check_docker
        check_env_file
        build_image
        run_application
        ;;
    "start")
        check_docker
        check_env_file
        run_compose
        ;;
    "stop")
        check_docker
        stop_compose
        ;;
    "logs")
        check_docker
        view_logs
        ;;
    "test")
        check_docker
        run_tests
        ;;
    "help" | "")
        show_help
        ;;
    *)
        print_error "Unknown command: $1"
        show_help
        exit 1
        ;;
    esac
}

# Run main function with all arguments
main "$@"
