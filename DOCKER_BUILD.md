# Docker Build & Push Guide

This guide explains how to build and push Docker images for the MCP demo servers to Docker Hub using the automated `build-and-push.sh` script.

## Prerequisites

1. **Docker** installed and running
2. **Docker Hub account** (create one at https://hub.docker.com)
3. **Docker CLI** logged in to your account

## Quick Start

### 1. Login to Docker Hub

```bash
docker login
# Enter your Docker Hub username and password
```

### 2. Build and Push Images

**Using current logged-in user:**
```bash
./build-and-push.sh v1.1.0
```

**Specifying Docker Hub username:**
```bash
./build-and-push.sh v1.1.0 myusername
```

**Using environment variables:**
```bash
DOCKER_USERNAME=myusername DOCKER_PASSWORD=mytoken ./build-and-push.sh v1.1.0
```

## Script Usage

### Basic Syntax

```bash
./build-and-push.sh <version> [docker-username]
```

### Arguments

| Argument | Required | Description | Example |
|----------|----------|-------------|---------|
| `version` | Yes | Version tag for the images | `v1.1.0`, `1.1.0` |
| `docker-username` | No | Docker Hub username | `myusername` |

### Options

| Option | Description |
|--------|-------------|
| `-h, --help` | Show help message |
| `--no-push` | Build images locally but don't push to registry |
| `--go-only` | Build only the Go server image |
| `--python-only` | Build only the Python server image |

### Environment Variables

| Variable | Description |
|----------|-------------|
| `DOCKER_USERNAME` | Docker Hub username (alternative to CLI argument) |
| `DOCKER_PASSWORD` | Docker Hub password/token for non-interactive login |

## Usage Examples

### Example 1: Build and Push Both Images

Build both Go and Python servers with version `v1.1.0`:

```bash
./build-and-push.sh v1.1.0
```

**Output:**
- `username/mcp-server-demo-go:1.1.0`
- `username/mcp-server-demo-go:latest`
- `username/mcp-server-demo-python:1.1.0`
- `username/mcp-server-demo-python:latest`

### Example 2: Build Only Go Server

```bash
./build-and-push.sh v1.1.0 --go-only
```

### Example 3: Build Only Python Server

```bash
./build-and-push.sh v1.1.0 --python-only
```

### Example 4: Build Locally Without Pushing

Test builds without pushing to Docker Hub:

```bash
./build-and-push.sh v1.1.0 --no-push
```

### Example 5: Automated CI/CD Pipeline

```bash
# Using token for non-interactive authentication
DOCKER_USERNAME=myuser \
DOCKER_PASSWORD=dckr_pat_abc123... \
./build-and-push.sh v1.1.0
```

### Example 6: Build with Different Username

```bash
./build-and-push.sh v1.1.0 myorganization
```

## What the Script Does

### 1. **Validation**
- ✅ Checks if Docker is running
- ✅ Validates Docker Hub authentication
- ✅ Verifies version parameter
- ✅ Strips 'v' prefix from version tags

### 2. **Building**
- 🔨 Builds Go server Docker image
- 🔨 Builds Python server Docker image
- 🏷️ Tags with version (e.g., `1.1.0`)
- 🏷️ Tags as `latest`

### 3. **Pushing**
- 📤 Pushes versioned tags to Docker Hub
- 📤 Pushes `latest` tags to Docker Hub

### 4. **Output**
- 📊 Colored progress messages
- ✅ Success/error indicators
- 📋 Summary of built images
- 💡 Usage examples

## Script Output Example

```
[INFO] ================================
[INFO] Docker Build & Push Configuration
[INFO] ================================
[INFO] Version: 1.1.0
[INFO] Docker Hub User: myusername
[INFO] Go Image: myusername/mcp-server-demo-go:1.1.0
[INFO] Python Image: myusername/mcp-server-demo-python:1.1.0
[INFO] Push to Registry: YES
[INFO] Build Go: YES
[INFO] Build Python: YES
[INFO] ================================

[SUCCESS] Already logged in to Docker Hub

[INFO] ================================
[INFO] Building Go Server
[INFO] ================================
[INFO] Building myusername/mcp-server-demo-go:1.1.0...
[SUCCESS] Built myusername/mcp-server-demo-go:1.1.0
[INFO] Tagging myusername/mcp-server-demo-go:latest...
[SUCCESS] Tagged myusername/mcp-server-demo-go:latest
[INFO] Pushing myusername/mcp-server-demo-go:1.1.0 to Docker Hub...
[SUCCESS] Pushed myusername/mcp-server-demo-go:1.1.0
[INFO] Pushing myusername/mcp-server-demo-go:latest to Docker Hub...
[SUCCESS] Pushed myusername/mcp-server-demo-go:latest

[INFO] ================================
[INFO] Building Python Server
[INFO] ================================
[INFO] Building myusername/mcp-server-demo-python:1.1.0...
[SUCCESS] Built myusername/mcp-server-demo-python:1.1.0
[INFO] Tagging myusername/mcp-server-demo-python:latest...
[SUCCESS] Tagged myusername/mcp-server-demo-python:latest
[INFO] Pushing myusername/mcp-server-demo-python:1.1.0 to Docker Hub...
[SUCCESS] Pushed myusername/mcp-server-demo-python:1.1.0
[INFO] Pushing myusername/mcp-server-demo-python:latest to Docker Hub...
[SUCCESS] Pushed myusername/mcp-server-demo-python:latest

[INFO] ================================
[SUCCESS] Build Complete!
[INFO] ================================
[INFO] Go Server Images:
[INFO]   - myusername/mcp-server-demo-go:1.1.0
[INFO]   - myusername/mcp-server-demo-go:latest
[INFO] Python Server Images:
[INFO]   - myusername/mcp-server-demo-python:1.1.0
[INFO]   - myusername/mcp-server-demo-python:latest

[SUCCESS] All images have been pushed to Docker Hub!
[INFO] View your images at: https://hub.docker.com/u/myusername

[INFO] Usage examples:
[INFO]   docker pull myusername/mcp-server-demo-go:1.1.0
[INFO]   docker run -p 8080:8080 myusername/mcp-server-demo-go:1.1.0
[INFO]   docker pull myusername/mcp-server-demo-python:1.1.0
[INFO]   docker run -p 8080:8080 myusername/mcp-server-demo-python:1.1.0

[SUCCESS] Done! 🚀
```

## Image Names

### Go Server
- **Repository**: `<username>/mcp-server-demo-go`
- **Tags**: `<version>`, `latest`
- **Size**: ~20 MB (distroless base)

### Python Server
- **Repository**: `<username>/mcp-server-demo-python`
- **Tags**: `<version>`, `latest`
- **Size**: ~150 MB (python:3.11-slim base)

## Running the Images

### Go Server

```bash
# Pull the image
docker pull myusername/mcp-server-demo-go:1.1.0

# Run in HTTP mode (default)
docker run -p 8080:8080 myusername/mcp-server-demo-go:1.1.0

# Test the server
curl http://localhost:8080/health
```

### Python Server

```bash
# Pull the image
docker pull myusername/mcp-server-demo-python:1.1.0

# Run in HTTP mode (default)
docker run -p 8080:8080 myusername/mcp-server-demo-python:1.1.0

# Test the server
curl http://localhost:8080/health
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Build and Push Docker Images

on:
  push:
    tags:
      - 'v*'

jobs:
  docker:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v3

      - name: Extract version
        id: version
        run: echo "VERSION=${GITHUB_REF#refs/tags/}" >> $GITHUB_OUTPUT

      - name: Build and Push
        env:
          DOCKER_USERNAME: ${{ secrets.DOCKER_USERNAME }}
          DOCKER_PASSWORD: ${{ secrets.DOCKER_PASSWORD }}
        run: |
          chmod +x ./build-and-push.sh
          ./build-and-push.sh ${{ steps.version.outputs.VERSION }}
```

### GitLab CI Example

```yaml
docker-build:
  stage: build
  only:
    - tags
  script:
    - chmod +x ./build-and-push.sh
    - export DOCKER_USERNAME=$CI_REGISTRY_USER
    - export DOCKER_PASSWORD=$CI_REGISTRY_PASSWORD
    - ./build-and-push.sh $CI_COMMIT_TAG
```

## Troubleshooting

### Error: "Docker is not running"

**Solution**: Start Docker Desktop or Docker daemon

```bash
# macOS/Linux
sudo systemctl start docker

# Or open Docker Desktop application
```

### Error: "Not logged in to Docker Hub"

**Solution**: Login to Docker Hub

```bash
docker login
```

### Error: "Failed to push"

**Possible causes:**
1. Not logged in → Run `docker login`
2. Wrong credentials → Check username/password
3. Repository doesn't exist → Create it on Docker Hub first (auto-created on first push)
4. No permission → Check repository access rights

### Error: "Permission denied"

**Solution**: Make script executable

```bash
chmod +x ./build-and-push.sh
```

## Advanced Usage

### Using Personal Access Tokens

For better security, use Docker Hub Personal Access Tokens instead of passwords:

1. Go to https://hub.docker.com/settings/security
2. Create a new access token
3. Use it as password:

```bash
DOCKER_PASSWORD=dckr_pat_your_token_here ./build-and-push.sh v1.1.0
```

### Multi-Architecture Builds

For multi-architecture support (amd64, arm64), use `docker buildx`:

```bash
# Enable buildx
docker buildx create --use

# Modify the script or build manually
docker buildx build --platform linux/amd64,linux/arm64 \
  -t myusername/mcp-server-demo-go:1.1.0 \
  --push \
  ./go-server
```

### Custom Registry

To use a different registry (not Docker Hub):

```bash
# Login to custom registry
docker login registry.example.com

# Build with custom registry prefix
# (Edit script to change image names)
```

## Version Tagging Best Practices

### Recommended Version Formats

- ✅ `v1.1.0` - Full semantic version with 'v' prefix
- ✅ `1.1.0` - Full semantic version without prefix
- ✅ `v1.1.0-beta.1` - Pre-release version
- ❌ `latest` - Don't use as input (auto-tagged)
- ❌ `dev` - Use version numbers instead

### Tagging Strategy

The script automatically creates two tags:
1. **Version tag**: `1.1.0` - Immutable, specific version
2. **Latest tag**: `latest` - Points to most recent build

**When to use each:**
- **Production**: Always use version tags (`1.1.0`)
- **Development**: Can use `latest` for testing
- **CI/CD**: Always use version tags for reproducibility

## Security Notes

1. ⚠️ **Never commit** Docker credentials to git
2. ✅ Use environment variables for automation
3. ✅ Use access tokens instead of passwords
4. ✅ Rotate tokens regularly
5. ✅ Use least-privilege access for CI/CD

## Support

For issues or questions:
- Check the main README.md
- Review Docker logs: `docker logs <container-id>`
- Verify Dockerfile syntax
- Check Docker Hub status: https://status.docker.com

## References

- Docker Hub: https://hub.docker.com
- Docker CLI Reference: https://docs.docker.com/engine/reference/commandline/cli/
- Dockerfile Best Practices: https://docs.docker.com/develop/develop-images/dockerfile_best-practices/
