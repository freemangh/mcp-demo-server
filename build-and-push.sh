#!/usr/bin/env bash

set -e  # Exit on error
set -u  # Exit on undefined variable

# Script to build and push MCP server Docker images to Docker Hub
# Usage: ./build-and-push.sh <version> [docker-username]
# Example: ./build-and-push.sh v1.1.0 myusername

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to print usage
usage() {
    cat << EOF
Usage: $0 <version> [docker-username]

Arguments:
  version          Version tag (e.g., v1.1.0, 1.1.0)
  docker-username  Docker Hub username (optional, defaults to current user)

Environment Variables:
  DOCKER_USERNAME  Docker Hub username (alternative to argument)
  DOCKER_PASSWORD  Docker Hub password/token (for non-interactive login)

Examples:
  $0 v1.1.0                    # Uses current Docker Hub user
  $0 v1.1.0 myusername         # Uses specified username
  DOCKER_USERNAME=user $0 1.1.0  # Uses environment variable

Options:
  -h, --help       Show this help message
  --no-push        Build images but don't push to registry
  --go-only        Build only Go server
  --python-only    Build only Python server

EOF
    exit 1
}

# Parse command line arguments
NO_PUSH=false
GO_ONLY=false
PYTHON_ONLY=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            usage
            ;;
        --no-push)
            NO_PUSH=true
            shift
            ;;
        --go-only)
            GO_ONLY=true
            shift
            ;;
        --python-only)
            PYTHON_ONLY=true
            shift
            ;;
        *)
            break
            ;;
    esac
done

# Check arguments
if [ $# -lt 1 ]; then
    print_error "Version argument is required"
    usage
fi

VERSION=$1
DOCKER_USERNAME=${2:-${DOCKER_USERNAME:-}}

# Strip 'v' prefix if present for Docker tags
VERSION_TAG=${VERSION#v}

# Docker image names
GO_IMAGE_NAME="mcp-server-demo-go"
PYTHON_IMAGE_NAME="mcp-server-demo-python"

# Get Docker username if not provided
if [ -z "$DOCKER_USERNAME" ]; then
    CURRENT_USER=$(docker info 2>/dev/null | grep Username | awk '{print $2}')
    if [ -z "$CURRENT_USER" ]; then
        print_error "Docker username not found. Please provide it as argument or login to Docker Hub first."
        print_info "Run: docker login"
        exit 1
    fi
    DOCKER_USERNAME=$CURRENT_USER
    print_info "Using Docker Hub username: $DOCKER_USERNAME"
fi

# Full image names with registry
GO_IMAGE_FULL="${DOCKER_USERNAME}/${GO_IMAGE_NAME}"
PYTHON_IMAGE_FULL="${DOCKER_USERNAME}/${PYTHON_IMAGE_NAME}"

# Print configuration
print_info "================================"
print_info "Docker Build & Push Configuration"
print_info "================================"
print_info "Version: ${VERSION_TAG}"
print_info "Docker Hub User: ${DOCKER_USERNAME}"
print_info "Go Image: ${GO_IMAGE_FULL}:${VERSION_TAG}"
print_info "Python Image: ${PYTHON_IMAGE_FULL}:${VERSION_TAG}"
print_info "Push to Registry: $([ "$NO_PUSH" = true ] && echo "NO" || echo "YES")"
print_info "Build Go: $([ "$PYTHON_ONLY" = true ] && echo "NO" || echo "YES")"
print_info "Build Python: $([ "$GO_ONLY" = true ] && echo "NO" || echo "YES")"
print_info "================================"
echo

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
    print_error "Docker is not running. Please start Docker and try again."
    exit 1
fi

# Check if user is logged in to Docker Hub (only if push is enabled)
if [ "$NO_PUSH" = false ]; then
    print_info "Checking Docker Hub authentication..."
    if ! docker info 2>/dev/null | grep -q "Username"; then
        print_warning "Not logged in to Docker Hub"

        # Try to login if DOCKER_PASSWORD is set
        if [ -n "${DOCKER_PASSWORD:-}" ]; then
            print_info "Attempting automatic login..."
            if echo "$DOCKER_PASSWORD" | docker login -u "$DOCKER_USERNAME" --password-stdin; then
                print_success "Logged in to Docker Hub"
            else
                print_error "Failed to login to Docker Hub"
                exit 1
            fi
        else
            print_info "Please login to Docker Hub:"
            docker login -u "$DOCKER_USERNAME"
        fi
    else
        print_success "Already logged in to Docker Hub"
    fi
fi

# Function to build and push an image
build_and_push() {
    local BUILD_DIR=$1
    local IMAGE_NAME=$2
    local SERVER_NAME=$3

    print_info "================================"
    print_info "Building ${SERVER_NAME} Server"
    print_info "================================"

    # Change to build directory
    cd "$BUILD_DIR"

    # Build image with version tag
    print_info "Building ${IMAGE_NAME}:${VERSION_TAG}..."
    if docker build -t "${IMAGE_NAME}:${VERSION_TAG}" .; then
        print_success "Built ${IMAGE_NAME}:${VERSION_TAG}"
    else
        print_error "Failed to build ${IMAGE_NAME}:${VERSION_TAG}"
        exit 1
    fi

    # Tag as latest
    print_info "Tagging ${IMAGE_NAME}:latest..."
    if docker tag "${IMAGE_NAME}:${VERSION_TAG}" "${IMAGE_NAME}:latest"; then
        print_success "Tagged ${IMAGE_NAME}:latest"
    else
        print_error "Failed to tag ${IMAGE_NAME}:latest"
        exit 1
    fi

    # Push to registry if enabled
    if [ "$NO_PUSH" = false ]; then
        print_info "Pushing ${IMAGE_NAME}:${VERSION_TAG} to Docker Hub..."
        if docker push "${IMAGE_NAME}:${VERSION_TAG}"; then
            print_success "Pushed ${IMAGE_NAME}:${VERSION_TAG}"
        else
            print_error "Failed to push ${IMAGE_NAME}:${VERSION_TAG}"
            exit 1
        fi

        print_info "Pushing ${IMAGE_NAME}:latest to Docker Hub..."
        if docker push "${IMAGE_NAME}:latest"; then
            print_success "Pushed ${IMAGE_NAME}:latest"
        else
            print_error "Failed to push ${IMAGE_NAME}:latest"
            exit 1
        fi
    else
        print_warning "Skipping push to registry (--no-push enabled)"
    fi

    # Return to root directory
    cd - >/dev/null

    echo
}

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Build Go server (unless --python-only)
if [ "$PYTHON_ONLY" = false ]; then
    build_and_push "${SCRIPT_DIR}/go-server" "${GO_IMAGE_FULL}" "Go"
fi

# Build Python server (unless --go-only)
if [ "$GO_ONLY" = false ]; then
    build_and_push "${SCRIPT_DIR}/python-server" "${PYTHON_IMAGE_FULL}" "Python"
fi

# Print summary
print_info "================================"
print_success "Build Complete!"
print_info "================================"

if [ "$PYTHON_ONLY" = false ]; then
    print_info "Go Server Images:"
    print_info "  - ${GO_IMAGE_FULL}:${VERSION_TAG}"
    print_info "  - ${GO_IMAGE_FULL}:latest"
fi

if [ "$GO_ONLY" = false ]; then
    print_info "Python Server Images:"
    print_info "  - ${PYTHON_IMAGE_FULL}:${VERSION_TAG}"
    print_info "  - ${PYTHON_IMAGE_FULL}:latest"
fi

if [ "$NO_PUSH" = false ]; then
    echo
    print_success "All images have been pushed to Docker Hub!"
    print_info "View your images at: https://hub.docker.com/u/${DOCKER_USERNAME}"
else
    echo
    print_warning "Images built locally but not pushed (--no-push enabled)"
fi

echo
print_info "Usage examples:"
if [ "$PYTHON_ONLY" = false ]; then
    print_info "  docker pull ${GO_IMAGE_FULL}:${VERSION_TAG}"
    print_info "  docker run -p 8080:8080 ${GO_IMAGE_FULL}:${VERSION_TAG}"
fi
if [ "$GO_ONLY" = false ]; then
    print_info "  docker pull ${PYTHON_IMAGE_FULL}:${VERSION_TAG}"
    print_info "  docker run -p 8080:8080 ${PYTHON_IMAGE_FULL}:${VERSION_TAG}"
fi

echo
print_success "Done! 🚀"
