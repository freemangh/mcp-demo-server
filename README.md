# MCP (Model Context Protocol) SDK Demo Servers

This project provides two simple MCP servers (in Go and Python) using the official SDKs.

## Repository Structure

```
mcp-demo-server/
├── go-server/                  # Go implementation
│   ├── main.go                 # Server code
│   ├── go.mod                  # Go dependencies
│   ├── Dockerfile              # Docker build file
│   └── cmd/
│       └── testclient/         # MCP test client (Go)
│           └── main.go         # Test client code
├── python-server/              # Python implementation
│   ├── mcp_server.py           # Server code
│   ├── requirements.txt        # Python dependencies
│   ├── Dockerfile              # Docker build file
│   └── cmd/
│       └── testclient/         # MCP test client (Python)
│           └── testclient.py   # Test client code
├── k8s/                        # Kubernetes manifests
│   ├── go-server-deployment.yaml      # Go server Deployment & Service
│   ├── python-server-deployment.yaml  # Python server Deployment & Service
│   └── ingress.yaml            # Optional Ingress configuration
├── helm/                       # Helm charts
│   ├── mcp-server-go/          # Go server Helm chart
│   │   ├── Chart.yaml          # Chart metadata
│   │   ├── values.yaml         # Default values
│   │   └── templates/          # Kubernetes templates
│   └── mcp-server-python/      # Python server Helm chart
│       ├── Chart.yaml          # Chart metadata
│       ├── values.yaml         # Default values
│       └── templates/          # Kubernetes templates
└── README.md                   # This file
```

Each server exposes the following tools for testing the MCP protocol:

-   **`echotest`**: Echoes back the provided message
-   **`timeserver`**: Returns the current time with optional IANA timezone support (e.g., "Europe/Kyiv", "America/New_York")
-   **`fetch`**: Fetches content from any HTTP/HTTPS URL with optional size limit

## HTTP Endpoints

When running in HTTP mode, both servers expose the following endpoints:

| Endpoint | Purpose | Method | Response |
|----------|---------|--------|----------|
| `/mcp` | MCP Streamable HTTP endpoint | GET/POST/DELETE | Streamable HTTP transport for MCP protocol (MCP spec 2025-03-26) |
| `/health` | Health check | GET | JSON status: `{"status":"ok","service":"...","version":"v1.1.0"}` |
| `/healthz` | Health check (K8s style) | GET | JSON status: `{"status":"ok","service":"...","version":"v1.1.0"}` |

The health check endpoints (`/health` and `/healthz`) are designed for:
- Kubernetes liveness and readiness probes
- Load balancer health checks
- Monitoring systems
- Quick service status verification

**Transport Protocol:** Both servers use the modern **Streamable HTTP transport** (MCP specification 2025-03-26) which provides:
- Single unified `/mcp` endpoint for all operations
- Stateful session management with `Mcp-Session-Id` header
- Session affinity support for production deployments
- 30-minute session timeout for idle connections

## CLI Alignment

Both servers support consistent command-line arguments:

| Argument | Go Server | Python Server | Description |
|----------|-----------|---------------|-------------|
| `--mode` | `stdio` \| `http` | `stdio` \| `http` | Transport mode |
| `--host` | default: `0.0.0.0` | default: `0.0.0.0` | Bind address |
| `--port` | default: `8080` | default: `8080` | Listen port |

**Transport Modes:**
- **Go**: `stdio` (default, local) or `http` (Streamable HTTP for network)
- **Python**: `stdio` (default, local) or `http` (Streamable HTTP for network)
    

## Testing Clients

Because these servers use the real MCP protocol, you need an MCP client to test them. You have two options:

### Option 1: Built-in Test Clients (Recommended)

This repository includes test clients in both Go and Python that support both servers.

#### Go Test Client

**Build:**
```bash
cd go-server
go build -o testclient ./cmd/testclient
```

**Usage:**
```bash
# Single command mode
./testclient -tool echotest -args '{"message":"Hello"}' -url http://localhost:8080/mcp
./testclient -tool timeserver -args '{"timezone":"Europe/Kyiv"}' -url http://localhost:8080/mcp
./testclient -tool fetch -args '{"url":"https://ifconfig.co/json","max_bytes":1024}' -url http://localhost:8080/mcp

# Interactive mode
./testclient -i -url http://localhost:8080/mcp
```

#### Python Test Client

**Setup:**
```bash
cd python-server
# Ensure dependencies are installed (mcp package required)
source venv/bin/activate  # if using venv
pip install -r requirements.txt
```

**Usage:**
```bash
# Single command mode
python3 cmd/testclient/testclient.py -tool echotest -args '{"message":"Hello"}' -url http://localhost:8080/mcp
python3 cmd/testclient/testclient.py -tool timeserver -args '{"timezone":"Europe/Kyiv"}' -url http://localhost:8080/mcp
python3 cmd/testclient/testclient.py -tool fetch -args '{"url":"https://ifconfig.co/json","max_bytes":1024}' -url http://localhost:8080/mcp

# Interactive mode
python3 cmd/testclient/testclient.py -i -url http://localhost:8080/mcp
```

#### Interactive Mode Commands

Both clients support the same interactive commands:
- `help`, `h`, `?` - Show available commands
- `list`, `ls` - List available tools on the server
- `echo <message>` - Test echotest tool
- `time [timezone]` - Test timeserver tool
- `fetch <url> [max_bytes]` - Test fetch tool
- `quit`, `exit`, `q` - Exit

### Option 2: Official `mcp-cli`

You can also use the official MCP CLI tool:

```bash
go install github.com/modelcontextprotocol/mcp-cli@latest
```

(Ensure your Go bin directory, e.g., `~/go/bin`, is in your `$PATH`)

## 1. Go (Golang) Server

**Location:** `go-server/`

**Files:**

-   `main.go` (Server Code)
-   `go.mod` / `go.sum` (Dependencies)
-   `Dockerfile` (Docker Build File)


### Build and Run (Locally)

1.  **Navigate to the Go server directory:**

    ```bash
    cd go-server
    ```

2.  **Install dependencies (if needed):**

    ```bash
    go mod download
    ```

3.  **Run the Server:**

    **Stdio mode (default):**
    ```bash
    go run .
    # Server: mcp-server-demo-go running in stdio mode
    ```

    **HTTP mode (Streamable HTTP for network access):**
    ```bash
    go run . --mode=http --host=0.0.0.0 --port=8080
    # Server: mcp-server-demo-go v1.1.0 starting...
    # Transport: Streamable HTTP (MCP spec 2025-03-26)
    # Server listening on 0.0.0.0:8080
    ```


### Test (Locally)

**For HTTP mode:**

The server exposes multiple endpoints. You can verify the server is running:

```bash
# Test health check endpoint
curl http://localhost:8080/health
# Should return: {"status":"ok","service":"mcp-server-demo-go","version":"v1.1.0"}

# Test Kubernetes-style health check
curl http://localhost:8080/healthz
# Should return: {"status":"ok","service":"mcp-server-demo-go","version":"v1.1.0"}

# Test MCP endpoint (Streamable HTTP transport)
curl -X GET http://localhost:8080/mcp
# MCP protocol communication (requires proper MCP client)
```

To interact with the MCP server, use an MCP-compatible client that supports Streamable HTTP transport:
- The built-in test clients (Go/Python) included in this repository
- The official MCP SDKs with Streamable HTTP support (Go SDK v1.1.0+, Python SDK v1.21.2+)
- Custom clients implementing the [MCP Streamable HTTP specification (2025-03-26)](https://spec.modelcontextprotocol.io/)

**Example with built-in Go test client:**
```bash
cd go-server
./testclient -i -url http://localhost:8080/mcp
```

**Example with MCP Go SDK:**
```go
import "github.com/modelcontextprotocol/go-sdk/mcp"

transport := &mcp.StreamableClientTransport{
    Endpoint: "http://localhost:8080/mcp",
    MaxRetries: 3,
}
session, err := client.Connect(ctx, transport, nil)
```

**For stdio mode:** Use with MCP clients that support stdio transport (like the official mcp-cli with command transport)
    

### Dockerize

1.  **Build the Docker Image:**

    ```bash
    cd go-server
    docker build -t mcp-server-demo-go:latest .
    ```

2.  **Run the Docker Container (HTTP mode - default):**

    ```bash
    docker run -d -p 8080:8080 --name go-mcp mcp-server-demo-go:latest
    # Server runs in HTTP mode (Streamable HTTP transport) by default in Docker
    ```

3.  **Verify the container is running:**

    ```bash
    docker logs go-mcp
    # Should show:
    # mcp-server-demo-go v1.1.0 starting...
    # Transport: Streamable HTTP (MCP spec 2025-03-26)
    # Server listening on 0.0.0.0:8080

    curl http://localhost:8080/health
    # Should return: {"status":"ok","service":"mcp-server-demo-go","version":"v1.1.0"}
    ```

4.  **Run in stdio mode (if needed):**

    ```bash
    docker run -it --name go-mcp mcp-server-demo-go:latest --mode=stdio
    ```

5.  **Stop/Remove:** `docker stop go-mcp && docker rm go-mcp`
    

## 2. Python Server

**Location:** `python-server/`

**Files:**

-   `mcp_server.py` (Server Code)
-   `requirements.txt` (Dependencies)
-   `Dockerfile` (Docker Build File)


### Build and Run (Locally)

1.  **Navigate to the Python server directory:**

    ```bash
    cd python-server
    ```

2.  **Create a Virtual Environment (recommended):**

    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Install Dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

4.  **Run the Server:**

    **Stdio mode (default):**
    ```bash
    python3 mcp_server.py
    # Output: INFO - mcp-server-demo-python running in stdio mode
    ```

    **HTTP mode (Streamable HTTP for network access):**
    ```bash
    python3 mcp_server.py --mode=http --host=0.0.0.0 --port=8080
    # Output:
    # INFO - mcp-server-demo-python v1.1.0 starting...
    # INFO - Transport: Streamable HTTP (MCP spec 2025-03-26)
    # INFO - Server listening on 0.0.0.0:8080
    ```


### Test (Locally)

**For HTTP mode:**

The server exposes multiple endpoints. You can verify the server is running:

```bash
# Test health check endpoint
curl http://localhost:8080/health
# Should return: {"status":"ok","service":"mcp-server-demo-python","version":"v1.1.0"}

# Test Kubernetes-style health check
curl http://localhost:8080/healthz
# Should return: {"status":"ok","service":"mcp-server-demo-python","version":"v1.1.0"}

# Test MCP endpoint (Streamable HTTP transport)
curl -X GET http://localhost:8080/mcp
# MCP protocol communication (requires proper MCP client)
```

To interact with the MCP server, use an MCP-compatible client that supports Streamable HTTP transport:
- The built-in test clients (Go/Python) included in this repository
- The official MCP SDKs with Streamable HTTP support (Go SDK v1.1.0+, Python SDK v1.21.2+)
- Custom clients implementing the [MCP Streamable HTTP specification (2025-03-26)](https://spec.modelcontextprotocol.io/)

**Example with built-in Python test client:**
```bash
cd python-server
python3 cmd/testclient/testclient.py -i -url http://localhost:8080/mcp
```

**Example with MCP Python SDK:**
```python
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

async with streamablehttp_client("http://localhost:8080/mcp") as (read, write):
    async with ClientSession(read, write) as session:
        await session.initialize()
        result = await session.call_tool("timeserver", arguments={})
        print(result)
```

**For stdio mode:** Use with MCP clients that support stdio transport (like the official mcp-cli with command transport)
    

### Dockerize

1.  **Build the Docker Image:**

    ```bash
    cd python-server
    docker build -t mcp-server-demo-python:latest .
    ```

2.  **Run the Docker Container (HTTP mode - default):**

    ```bash
    docker run -d -p 8080:8080 --name py-mcp mcp-server-demo-python:latest
    # Server runs in HTTP mode (Streamable HTTP transport) by default in Docker
    ```

3.  **Verify the container is running:**

    ```bash
    docker logs py-mcp
    # Should show:
    # INFO - mcp-server-demo-python v1.1.0 starting...
    # INFO - Transport: Streamable HTTP (MCP spec 2025-03-26)
    # INFO - Server listening on 0.0.0.0:8080

    curl http://localhost:8080/health
    # Should return: {"status":"ok","service":"mcp-server-demo-python","version":"v1.1.0"}
    ```

4.  **Run in stdio mode (if needed):**

    ```bash
    docker run -it --name py-mcp mcp-server-demo-python:latest --mode=stdio
    ```

5.  **Stop/Remove:** `docker stop py-mcp && docker rm py-mcp`

## 3. Production Deployment

This section covers building production-ready Docker images and deploying to Kubernetes.

### Docker Image Build for Production

#### Building and Tagging Images

For production deployments, it's recommended to use semantic versioning and push images to a container registry.

**Go Server:**

```bash
cd go-server

# Set version and registry configuration
VERSION=v1.1.0
REGISTRY_USER=yourusername              # For Docker Hub
# REGISTRY=gcr.io/your-project-id       # For GCR
# REGISTRY=123456789012.dkr.ecr.us-east-1.amazonaws.com  # For ECR

# Build with version tag
docker build -t mcp-server-demo-go:${VERSION} -t mcp-server-demo-go:latest .

# Tag for your container registry
# For Docker Hub:
docker tag mcp-server-demo-go:${VERSION} ${REGISTRY_USER}/mcp-server-demo-go:${VERSION}
docker tag mcp-server-demo-go:latest ${REGISTRY_USER}/mcp-server-demo-go:latest

# For Google Container Registry (GCR) or Amazon ECR:
# docker tag mcp-server-demo-go:${VERSION} ${REGISTRY}/mcp-server-demo-go:${VERSION}
# docker tag mcp-server-demo-go:latest ${REGISTRY}/mcp-server-demo-go:latest
```

**Python Server:**

```bash
cd python-server

# Set version and registry configuration
VERSION=v1.1.0
REGISTRY_USER=yourusername              # For Docker Hub
# REGISTRY=gcr.io/your-project-id       # For GCR
# REGISTRY=123456789012.dkr.ecr.us-east-1.amazonaws.com  # For ECR

# Build with version tag
docker build -t mcp-server-demo-python:${VERSION} -t mcp-server-demo-python:latest .

# Tag for your container registry
# For Docker Hub:
docker tag mcp-server-demo-python:${VERSION} ${REGISTRY_USER}/mcp-server-demo-python:${VERSION}
docker tag mcp-server-demo-python:latest ${REGISTRY_USER}/mcp-server-demo-python:latest

# For Google Container Registry (GCR) or Amazon ECR:
# docker tag mcp-server-demo-python:${VERSION} ${REGISTRY}/mcp-server-demo-python:${VERSION}
# docker tag mcp-server-demo-python:latest ${REGISTRY}/mcp-server-demo-python:latest
```

#### Pushing to Container Registry

**Docker Hub:**

```bash
# Login to Docker Hub
docker login

# Push images
docker push ${REGISTRY_USER}/mcp-server-demo-go:${VERSION}
docker push ${REGISTRY_USER}/mcp-server-demo-go:latest
docker push ${REGISTRY_USER}/mcp-server-demo-python:${VERSION}
docker push ${REGISTRY_USER}/mcp-server-demo-python:latest
```

**Google Container Registry (GCR):**

```bash
# Authenticate with GCR
gcloud auth configure-docker

# Push images
docker push ${REGISTRY}/mcp-server-demo-go:${VERSION}
docker push ${REGISTRY}/mcp-server-demo-go:latest
docker push ${REGISTRY}/mcp-server-demo-python:${VERSION}
docker push ${REGISTRY}/mcp-server-demo-python:latest
```

**Amazon ECR:**

```bash
# Set AWS region
AWS_REGION=us-east-1

# Authenticate with ECR
aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${REGISTRY}

# Create repositories if they don't exist
aws ecr create-repository --repository-name mcp-server-demo-go --region ${AWS_REGION}
aws ecr create-repository --repository-name mcp-server-demo-python --region ${AWS_REGION}

# Push images
docker push ${REGISTRY}/mcp-server-demo-go:${VERSION}
docker push ${REGISTRY}/mcp-server-demo-go:latest
docker push ${REGISTRY}/mcp-server-demo-python:${VERSION}
docker push ${REGISTRY}/mcp-server-demo-python:latest
```

### Kubernetes Deployment

This project includes ready-to-use Kubernetes manifests in the `k8s/` directory.

#### Prerequisites

1. **Kubernetes cluster** - You can use:
   - Local: Minikube, Kind, Docker Desktop with Kubernetes
   - Cloud: GKE, EKS, AKS, or any other Kubernetes cluster

2. **kubectl** - Kubernetes CLI tool configured to access your cluster

3. **Container images** - Either:
   - Use local images (for Minikube/Kind with `imagePullPolicy: IfNotPresent`)
   - Push images to a registry and update image references in manifests

#### Deployment Manifests Overview

The `k8s/` directory contains:

- `go-server-deployment.yaml` - Go server Deployment and Service
- `python-server-deployment.yaml` - Python server Deployment and Service
- `ingress.yaml` - Optional Ingress for external access

Each deployment includes:
- **2 replicas** for high availability
- **Health checks** (liveness and readiness probes)
- **Resource limits** (CPU and memory)
- **Security context** (non-root user, dropped capabilities)
- **ClusterIP Service** for internal cluster communication

#### Step-by-Step Deployment

**1. Prepare your cluster:**

For local testing with Minikube:
```bash
# Start Minikube
minikube start

# Load local images into Minikube (if not using a registry)
minikube image load mcp-server-demo-go:latest
minikube image load mcp-server-demo-python:latest
```

For Kind:
```bash
# Create Kind cluster
kind create cluster --name mcp-demo

# Load local images into Kind (if not using a registry)
kind load docker-image mcp-server-demo-go:latest --name mcp-demo
kind load docker-image mcp-server-demo-python:latest --name mcp-demo
```

**2. Update image references (if using a registry):**

Edit the manifest files to use your registry images:

```bash
# Set your registry and version
REGISTRY_USER=yourusername
VERSION=v1.1.0

# For go-server-deployment.yaml, change:
# image: mcp-server-demo-go:latest
# to:
# image: ${REGISTRY_USER}/mcp-server-demo-go:${VERSION}

# For python-server-deployment.yaml, change:
# image: mcp-server-demo-python:latest
# to:
# image: ${REGISTRY_USER}/mcp-server-demo-python:${VERSION}
```

Or use `sed` to update:
```bash
cd k8s
sed -i "s|mcp-server-demo-go:latest|${REGISTRY_USER}/mcp-server-demo-go:${VERSION}|g" go-server-deployment.yaml
sed -i "s|mcp-server-demo-python:latest|${REGISTRY_USER}/mcp-server-demo-python:${VERSION}|g" python-server-deployment.yaml
```

**3. Deploy to Kubernetes:**

```bash
# Deploy Go server
kubectl apply -f k8s/go-server-deployment.yaml

# Deploy Python server
kubectl apply -f k8s/python-server-deployment.yaml

# Optional: Deploy Ingress (requires Ingress controller)
kubectl apply -f k8s/ingress.yaml
```

**4. Verify deployments:**

```bash
# Check deployment status
kubectl get deployments
kubectl get pods
kubectl get services

# Wait for pods to be ready
kubectl wait --for=condition=ready pod -l app=mcp-server-demo-go --timeout=60s
kubectl wait --for=condition=ready pod -l app=mcp-server-demo-python --timeout=60s

# Check pod logs
kubectl logs -l app=mcp-server-demo-go
kubectl logs -l app=mcp-server-demo-python
```

Expected output:
```
NAME                                    READY   STATUS    RESTARTS   AGE
mcp-server-demo-go-xxxxxxxxxx-xxxxx     1/1     Running   0          30s
mcp-server-demo-go-xxxxxxxxxx-xxxxx     1/1     Running   0          30s
mcp-server-demo-python-xxxxxxxxxx-xxxx  1/1     Running   0          30s
mcp-server-demo-python-xxxxxxxxxx-xxxx  1/1     Running   0          30s
```

#### Testing Kubernetes Deployments

**Method 1: Port Forwarding (Quick Test)**

```bash
# Forward Go server port
kubectl port-forward svc/mcp-server-demo-go 8080:8080

# In another terminal, test the server
curl http://localhost:8080/health
# Should return 200 OK

# Test with built-in test client
cd go-server
./testclient -tool timeserver -args '{}' -url http://localhost:8080/mcp

# Forward Python server port (use a different local port)
kubectl port-forward svc/mcp-server-demo-python 8081:8080

# Test Python server
curl http://localhost:8081/health
cd python-server
python3 cmd/testclient/testclient.py -tool timeserver -args '{}' -url http://localhost:8081/mcp
```

**Method 2: From within the cluster (create a test pod)**

```bash
# Create a temporary test pod
kubectl run test-client --image=curlimages/curl:latest -it --rm --restart=Never -- sh

# Inside the pod, test the services
curl http://mcp-server-demo-go:8080/health
curl http://mcp-server-demo-python:8080/health
```

**Method 3: Using Ingress (External Access)**

If you deployed the Ingress:

```bash
# Get Ingress address
kubectl get ingress

# For Minikube, enable Ingress addon
minikube addons enable ingress

# Get Minikube IP
minikube ip

# Test with Ingress (update /etc/hosts to point domain to Minikube IP)
# Add line: <minikube-ip> mcp-demo.example.com mcp-go.example.com mcp-python.example.com
curl http://mcp-go.example.com/health
curl http://mcp-python.example.com/health

# Or use the test clients
./testclient -tool timeserver -args '{}' -url http://mcp-go.example.com/mcp
```

**Method 4: Interactive Testing**

```bash
# Port forward and use interactive mode
kubectl port-forward svc/mcp-server-demo-go 8080:8080

# In another terminal
cd go-server
./testclient -i -url http://localhost:8080/mcp

# Interactive commands:
mcp> list
mcp> echo Hello from Kubernetes!
mcp> time Europe/Kyiv
mcp> fetch https://ifconfig.co/json 1024
```

#### Health Checks and Monitoring

**Check pod health:**

```bash
# View pod status and ready state
kubectl get pods -l app=mcp-server-demo-go -o wide
kubectl get pods -l app=mcp-server-demo-python -o wide

# Describe pod to see health check results
kubectl describe pod -l app=mcp-server-demo-go | grep -A 5 "Liveness\|Readiness"

# View events
kubectl get events --sort-by=.metadata.creationTimestamp
```

**Check resource usage:**

```bash
# View resource consumption
kubectl top pods -l app=mcp-server-demo-go
kubectl top pods -l app=mcp-server-demo-python

# View resource limits
kubectl describe deployment mcp-server-demo-go | grep -A 5 "Limits\|Requests"
```

#### Scaling Deployments

```bash
# Scale Go server to 3 replicas
kubectl scale deployment mcp-server-demo-go --replicas=3

# Scale Python server to 3 replicas
kubectl scale deployment mcp-server-demo-python --replicas=3

# Verify scaling
kubectl get pods -l app=mcp-server-demo-go
kubectl get pods -l app=mcp-server-demo-python

# Auto-scaling (HPA - requires metrics-server)
kubectl autoscale deployment mcp-server-demo-go --cpu-percent=70 --min=2 --max=10
kubectl autoscale deployment mcp-server-demo-python --cpu-percent=70 --min=2 --max=10
```

#### Updating Deployments

```bash
# Update to a new version
NEW_VERSION=v1.1.0
kubectl set image deployment/mcp-server-demo-go mcp-server=${REGISTRY_USER}/mcp-server-demo-go:${NEW_VERSION}
kubectl set image deployment/mcp-server-demo-python mcp-server=${REGISTRY_USER}/mcp-server-demo-python:${NEW_VERSION}

# Check rollout status
kubectl rollout status deployment/mcp-server-demo-go
kubectl rollout status deployment/mcp-server-demo-python

# Rollback if needed
kubectl rollout undo deployment/mcp-server-demo-go
kubectl rollout undo deployment/mcp-server-demo-python

# View rollout history
kubectl rollout history deployment/mcp-server-demo-go
```

#### Troubleshooting

**Pods not starting:**

```bash
# Check pod status
kubectl get pods -l app=mcp-server-demo-go

# View pod events and logs
kubectl describe pod <pod-name>
kubectl logs <pod-name>

# Common issues:
# - Image pull errors: Check image name and registry authentication
# - CrashLoopBackOff: Check logs for application errors
# - Pending: Check resource availability (CPU/memory)
```

**Health checks failing:**

```bash
# Check endpoint manually from within cluster
kubectl run test --image=curlimages/curl -it --rm --restart=Never -- curl -I http://mcp-server-demo-go:8080/sse

# Adjust health check timing if needed (edit deployment)
kubectl edit deployment mcp-server-demo-go
# Increase initialDelaySeconds or failureThreshold
```

**Service not accessible:**

```bash
# Verify service endpoints
kubectl get endpoints mcp-server-demo-go

# Check if pods are ready
kubectl get pods -l app=mcp-server-demo-go

# Test service from within cluster
kubectl run test --image=curlimages/curl -it --rm --restart=Never -- curl http://mcp-server-demo-go:8080/mcp
```

#### Cleanup

```bash
# Delete all resources
kubectl delete -f k8s/go-server-deployment.yaml
kubectl delete -f k8s/python-server-deployment.yaml
kubectl delete -f k8s/ingress.yaml

# Or delete by label
kubectl delete all -l app=mcp-server-demo-go
kubectl delete all -l app=mcp-server-demo-python

# Delete Minikube cluster (if used)
minikube delete

# Delete Kind cluster (if used)
kind delete cluster --name mcp-demo
```

### Helm Deployment

This project includes Helm charts for simplified deployment and management of both MCP servers.

#### Prerequisites

1. **Helm 3.x** installed ([Installation guide](https://helm.sh/docs/intro/install/))
2. **Kubernetes cluster** with kubectl configured
3. **Container images** built and accessible (local or registry)

#### Helm Charts Overview

The `helm/` directory contains two Helm charts:

- `helm/mcp-server-go/` - Helm chart for Go server
- `helm/mcp-server-python/` - Helm chart for Python server

Each chart includes:
- Configurable deployment with replicas, resources, and security contexts
- Service configuration (ClusterIP, NodePort, LoadBalancer)
- Optional Ingress with TLS support
- Optional Horizontal Pod Autoscaler (HPA)
- Customizable health probes
- NOTES with post-installation instructions

#### Installing with Helm

**Install Go Server:**

```bash
# Install with default values (uses local image)
helm install mcp-go ./helm/mcp-server-go

# Install with custom values
helm install mcp-go ./helm/mcp-server-go \
  --set image.repository=${REGISTRY_USER}/mcp-server-demo-go \
  --set image.tag=${VERSION} \
  --set replicaCount=3

# Install with Ingress enabled
helm install mcp-go ./helm/mcp-server-go \
  --set ingress.enabled=true \
  --set ingress.hosts[0].host=mcp-go.example.com \
  --set ingress.hosts[0].paths[0].path=/ \
  --set ingress.hosts[0].paths[0].pathType=Prefix

# Install with autoscaling enabled
helm install mcp-go ./helm/mcp-server-go \
  --set autoscaling.enabled=true \
  --set autoscaling.minReplicas=2 \
  --set autoscaling.maxReplicas=10 \
  --set autoscaling.targetCPUUtilizationPercentage=70
```

**Install Python Server:**

```bash
# Install with default values (uses local image)
helm install mcp-python ./helm/mcp-server-python

# Install with custom values
helm install mcp-python ./helm/mcp-server-python \
  --set image.repository=${REGISTRY_USER}/mcp-server-demo-python \
  --set image.tag=${VERSION} \
  --set replicaCount=3

# Install with Ingress enabled
helm install mcp-python ./helm/mcp-server-python \
  --set ingress.enabled=true \
  --set ingress.hosts[0].host=mcp-python.example.com \
  --set ingress.hosts[0].paths[0].path=/ \
  --set ingress.hosts[0].paths[0].pathType=Prefix
```

**Install to a specific namespace:**

```bash
# Create namespace
kubectl create namespace mcp-servers

# Install both servers to the namespace
helm install mcp-go ./helm/mcp-server-go -n mcp-servers
helm install mcp-python ./helm/mcp-server-python -n mcp-servers
```

#### Using a Custom Values File

Create a custom values file to override defaults:

**custom-values-go.yaml:**
```yaml
replicaCount: 3

image:
  repository: ${REGISTRY_USER}/mcp-server-demo-go
  tag: "v1.0.3"
  pullPolicy: Always

resources:
  limits:
    cpu: 1000m
    memory: 256Mi
  requests:
    cpu: 200m
    memory: 128Mi

ingress:
  enabled: true
  className: nginx
  hosts:
    - host: mcp-go.example.com
      paths:
        - path: /
          pathType: Prefix
  tls:
    - secretName: mcp-go-tls
      hosts:
        - mcp-go.example.com

autoscaling:
  enabled: true
  minReplicas: 2
  maxReplicas: 10
  targetCPUUtilizationPercentage: 70
```

**Install with custom values:**
```bash
helm install mcp-go ./helm/mcp-server-go -f custom-values-go.yaml
```

#### Managing Helm Releases

**List installed releases:**
```bash
helm list
helm list -n mcp-servers  # In specific namespace
```

**Get release status:**
```bash
helm status mcp-go
helm status mcp-python
```

**Upgrade a release:**
```bash
# Upgrade with new image version
helm upgrade mcp-go ./helm/mcp-server-go \
  --set image.tag=v1.1.0

# Upgrade with custom values file
helm upgrade mcp-go ./helm/mcp-server-go -f custom-values-go.yaml

# Upgrade with reuse of previous values
helm upgrade mcp-go ./helm/mcp-server-go --reuse-values --set replicaCount=5
```

**Rollback a release:**
```bash
# Rollback to previous revision
helm rollback mcp-go

# Rollback to specific revision
helm rollback mcp-go 2

# View rollback history
helm history mcp-go
```

**Uninstall a release:**
```bash
helm uninstall mcp-go
helm uninstall mcp-python

# Uninstall from specific namespace
helm uninstall mcp-go -n mcp-servers
```

#### Testing Helm Deployments

**Dry run (validate without installing):**
```bash
helm install mcp-go ./helm/mcp-server-go --dry-run --debug
```

**Template rendering (see generated manifests):**
```bash
helm template mcp-go ./helm/mcp-server-go
helm template mcp-go ./helm/mcp-server-go -f custom-values-go.yaml
```

**Lint chart (check for issues):**
```bash
helm lint ./helm/mcp-server-go
helm lint ./helm/mcp-server-python
```

**Test the deployed application:**
```bash
# Port forward to access the service
kubectl port-forward svc/mcp-go-mcp-server-go 8080:8080

# In another terminal, test with the test client
cd go-server
./testclient -i -url http://localhost:8080/mcp
```

#### Packaging and Distributing Helm Charts

**Package charts:**
```bash
# Package individual charts
helm package ./helm/mcp-server-go
helm package ./helm/mcp-server-python

# This creates mcp-server-go-1.0.0.tgz and mcp-server-python-1.0.0.tgz
```

**Install from packaged chart:**
```bash
helm install mcp-go mcp-server-go-1.0.0.tgz
```

**Create Helm repository index:**
```bash
# Create index file for multiple charts
helm repo index . --url https://example.com/charts

# This generates index.yaml for hosting as a chart repository
```

#### Common Helm Values Configurations

**For Production Environments:**

```yaml
# Production configuration example
replicaCount: 3

image:
  repository: your-registry.io/mcp-server-demo-go
  tag: "v1.1.0"
  pullPolicy: Always

imagePullSecrets:
  - name: registry-secret

resources:
  limits:
    cpu: 1000m
    memory: 256Mi
  requests:
    cpu: 200m
    memory: 128Mi

autoscaling:
  enabled: true
  minReplicas: 3
  maxReplicas: 20
  targetCPUUtilizationPercentage: 70

ingress:
  enabled: true
  className: nginx
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/proxy-read-timeout: "3600"
    nginx.ingress.kubernetes.io/proxy-send-timeout: "3600"
  hosts:
    - host: mcp-go.prod.example.com
      paths:
        - path: /
          pathType: Prefix
  tls:
    - secretName: mcp-go-tls
      hosts:
        - mcp-go.prod.example.com

podAnnotations:
  prometheus.io/scrape: "true"
  prometheus.io/port: "8080"

affinity:
  podAntiAffinity:
    preferredDuringSchedulingIgnoredDuringExecution:
      - weight: 100
        podAffinityTerm:
          labelSelector:
            matchExpressions:
              - key: app.kubernetes.io/name
                operator: In
                values:
                  - mcp-server-go
          topologyKey: kubernetes.io/hostname
```

**For Development Environments:**

```yaml
# Development configuration example
replicaCount: 1

image:
  repository: mcp-server-demo-go
  tag: "latest"
  pullPolicy: IfNotPresent

resources:
  limits:
    cpu: 500m
    memory: 128Mi
  requests:
    cpu: 100m
    memory: 64Mi

service:
  type: NodePort

autoscaling:
  enabled: false
```

#### Helm Values Reference

Key configuration options available in `values.yaml`:

| Parameter | Description | Default |
|-----------|-------------|---------|
| `replicaCount` | Number of replicas | `2` |
| `image.repository` | Image repository | `mcp-server-demo-go` |
| `image.tag` | Image tag | `latest` |
| `image.pullPolicy` | Image pull policy | `IfNotPresent` |
| `service.type` | Service type | `ClusterIP` |
| `service.port` | Service port | `8080` |
| `ingress.enabled` | Enable Ingress | `false` |
| `ingress.className` | Ingress class | `nginx` |
| `resources.limits.cpu` | CPU limit | `500m` |
| `resources.limits.memory` | Memory limit | `128Mi` (Go) / `256Mi` (Python) |
| `autoscaling.enabled` | Enable HPA | `false` |
| `autoscaling.minReplicas` | Minimum replicas | `2` |
| `autoscaling.maxReplicas` | Maximum replicas | `10` |
| `config.mode` | Server mode | `http` |
| `config.host` | Bind address | `0.0.0.0` |
| `config.port` | Server port | `8080` |

For complete values reference, see the `values.yaml` file in each chart directory.

### Production Best Practices

1. **Use specific version tags** instead of `latest` in production
2. **Enable resource limits** to prevent resource exhaustion
3. **Configure horizontal pod autoscaling** based on metrics
4. **Set up monitoring** with Prometheus/Grafana
5. **Configure logging** with ELK stack or cloud-native solutions
6. **Use secrets management** for sensitive configuration
7. **Implement network policies** to restrict traffic
8. **Regular security updates** - rebuild images with updated base images
9. **Backup configurations** - store manifests in version control
10. **Test rollback procedures** before production deployment