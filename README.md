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
└── README.md                   # This file
```

Each server exposes the following tools for testing the MCP protocol:

-   **`echotest`**: Echoes back the provided message
-   **`timeserver`**: Returns the current time with optional IANA timezone support (e.g., "Europe/Kyiv", "America/New_York")
-   **`fetch`**: Fetches content from any HTTP/HTTPS URL with optional size limit

## CLI Alignment

Both servers support consistent command-line arguments:

| Argument | Go Server | Python Server | Description |
|----------|-----------|---------------|-------------|
| `--mode` | `stdio` \| `http` | `stdio` \| `http` | Transport mode |
| `--host` | default: `0.0.0.0` | default: `0.0.0.0` | Bind address |
| `--port` | default: `8080` | default: `8080` | Listen port |

**Transport Modes:**
- **Go**: `stdio` (default, local) or `http` (HTTP/SSE for network)
- **Python**: `stdio` (default, local) or `http` (HTTP/SSE for network)
    

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
./testclient -tool echotest -args '{"message":"Hello"}' -url http://localhost:8080/sse
./testclient -tool timeserver -args '{"timezone":"Europe/Kyiv"}' -url http://localhost:8080/sse
./testclient -tool fetch -args '{"url":"https://ifconfig.co/json","max_bytes":1024}' -url http://localhost:8080/sse

# Interactive mode
./testclient -i -url http://localhost:8080/sse
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
python3 cmd/testclient/testclient.py -tool echotest -args '{"message":"Hello"}' -url http://localhost:8080/sse
python3 cmd/testclient/testclient.py -tool timeserver -args '{"timezone":"Europe/Kyiv"}' -url http://localhost:8080/sse
python3 cmd/testclient/testclient.py -tool fetch -args '{"url":"https://ifconfig.co/json","max_bytes":1024}' -url http://localhost:8080/sse

# Interactive mode
python3 cmd/testclient/testclient.py -i -url http://localhost:8080/sse
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

    **HTTP/SSE mode (for network access):**
    ```bash
    go run . --mode=http --host=0.0.0.0 --port=8080
    # Server: mcp-server-demo-go listening on 0.0.0.0:8080 (HTTP/SSE)
    ```
    

### Test (Locally)

**For HTTP/SSE mode:**

The server exposes an SSE endpoint at `/sse` for MCP protocol communication. You can verify the server is running:

```bash
curl -I http://localhost:8080/sse
# Should return 200 OK with SSE headers
```

To interact with the MCP server, use an MCP-compatible client that supports SSE transport, such as:
- The official MCP SDKs (Python, TypeScript, Go)
- Custom clients implementing the [MCP SSE transport specification](https://modelcontextprotocol.io/specification/2024-11-05/basic/transports)

**Example with MCP Python SDK:**
```python
from mcp import ClientSession, SSEClientTransport

async with ClientSession(SSEClientTransport("http://localhost:8080/sse")) as session:
    result = await session.call_tool("timeserver", arguments={})
    print(result)
```

**For stdio mode:** Use with MCP clients that support stdio transport (like the official mcp-cli with command transport)
    

### Dockerize

1.  **Build the Docker Image:**

    ```bash
    cd go-server
    docker build -t mcp-server-demo-go:latest .
    ```

2.  **Run the Docker Container (HTTP/SSE mode - default):**

    ```bash
    docker run -d -p 8080:8080 --name go-mcp mcp-server-demo-go:latest
    # Server runs in HTTP/SSE mode by default in Docker
    ```

3.  **Verify the container is running:**

    ```bash
    docker logs go-mcp
    # Should show: mcp-server-demo-go listening on 0.0.0.0:8080 (HTTP/SSE)

    curl -I http://localhost:8080/sse
    # Should return 200 OK
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

    **HTTP/SSE mode (for network access):**
    ```bash
    python3 mcp_server.py --mode=http --host=0.0.0.0 --port=8080
    # Output: INFO - mcp-server-demo-python listening on 0.0.0.0:8080 (HTTP/SSE)
    ```
    

### Test (Locally)

**For HTTP/SSE mode:**

The server exposes an SSE endpoint at `/sse` for MCP protocol communication. You can verify the server is running:

```bash
curl -I http://localhost:8080/sse
# Should return 200 OK with SSE headers
```

To interact with the MCP server, use an MCP-compatible client that supports SSE transport, such as:
- The official MCP SDKs (Python, TypeScript, Go)
- Custom clients implementing the [MCP SSE transport specification](https://modelcontextprotocol.io/specification/2024-11-05/basic/transports)

**Example with MCP Python SDK:**
```python
from mcp import ClientSession, StdioServerParameters
from mcp.client.sse import sse_client

async with sse_client("http://localhost:8080/sse") as (read, write):
    async with ClientSession(read, write) as session:
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

2.  **Run the Docker Container (HTTP/SSE mode - default):**

    ```bash
    docker run -d -p 8080:8080 --name py-mcp mcp-server-demo-python:latest
    # Server runs in HTTP/SSE mode by default in Docker
    ```

3.  **Verify the container is running:**

    ```bash
    docker logs py-mcp
    # Should show: mcp-server-demo-python listening on 0.0.0.0:8080 (HTTP/SSE)

    curl -I http://localhost:8080/sse
    # Should return 200 OK
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

# Build with version tag
VERSION=v1.0.0
docker build -t mcp-server-demo-go:${VERSION} -t mcp-server-demo-go:latest .

# Tag for your container registry (replace with your registry)
# For Docker Hub:
docker tag mcp-server-demo-go:${VERSION} yourusername/mcp-server-demo-go:${VERSION}
docker tag mcp-server-demo-go:latest yourusername/mcp-server-demo-go:latest

# For Google Container Registry (GCR):
docker tag mcp-server-demo-go:${VERSION} gcr.io/your-project-id/mcp-server-demo-go:${VERSION}
docker tag mcp-server-demo-go:latest gcr.io/your-project-id/mcp-server-demo-go:latest

# For Amazon ECR:
docker tag mcp-server-demo-go:${VERSION} 123456789012.dkr.ecr.us-east-1.amazonaws.com/mcp-server-demo-go:${VERSION}
docker tag mcp-server-demo-go:latest 123456789012.dkr.ecr.us-east-1.amazonaws.com/mcp-server-demo-go:latest
```

**Python Server:**

```bash
cd python-server

# Build with version tag
VERSION=v1.0.0
docker build -t mcp-server-demo-python:${VERSION} -t mcp-server-demo-python:latest .

# Tag for your container registry (replace with your registry)
# For Docker Hub:
docker tag mcp-server-demo-python:${VERSION} yourusername/mcp-server-demo-python:${VERSION}
docker tag mcp-server-demo-python:latest yourusername/mcp-server-demo-python:latest

# For Google Container Registry (GCR):
docker tag mcp-server-demo-python:${VERSION} gcr.io/your-project-id/mcp-server-demo-python:${VERSION}
docker tag mcp-server-demo-python:latest gcr.io/your-project-id/mcp-server-demo-python:latest

# For Amazon ECR:
docker tag mcp-server-demo-python:${VERSION} 123456789012.dkr.ecr.us-east-1.amazonaws.com/mcp-server-demo-python:${VERSION}
docker tag mcp-server-demo-python:latest 123456789012.dkr.ecr.us-east-1.amazonaws.com/mcp-server-demo-python:latest
```

#### Pushing to Container Registry

**Docker Hub:**

```bash
# Login to Docker Hub
docker login

# Push images
docker push yourusername/mcp-server-demo-go:v1.0.0
docker push yourusername/mcp-server-demo-go:latest
docker push yourusername/mcp-server-demo-python:v1.0.0
docker push yourusername/mcp-server-demo-python:latest
```

**Google Container Registry (GCR):**

```bash
# Authenticate with GCR
gcloud auth configure-docker

# Push images
docker push gcr.io/your-project-id/mcp-server-demo-go:v1.0.0
docker push gcr.io/your-project-id/mcp-server-demo-go:latest
docker push gcr.io/your-project-id/mcp-server-demo-python:v1.0.0
docker push gcr.io/your-project-id/mcp-server-demo-python:latest
```

**Amazon ECR:**

```bash
# Authenticate with ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 123456789012.dkr.ecr.us-east-1.amazonaws.com

# Create repositories if they don't exist
aws ecr create-repository --repository-name mcp-server-demo-go --region us-east-1
aws ecr create-repository --repository-name mcp-server-demo-python --region us-east-1

# Push images
docker push 123456789012.dkr.ecr.us-east-1.amazonaws.com/mcp-server-demo-go:v1.0.0
docker push 123456789012.dkr.ecr.us-east-1.amazonaws.com/mcp-server-demo-go:latest
docker push 123456789012.dkr.ecr.us-east-1.amazonaws.com/mcp-server-demo-python:v1.0.0
docker push 123456789012.dkr.ecr.us-east-1.amazonaws.com/mcp-server-demo-python:latest
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
# For go-server-deployment.yaml, change:
# image: mcp-server-demo-go:latest
# to:
# image: yourusername/mcp-server-demo-go:v1.0.0

# For python-server-deployment.yaml, change:
# image: mcp-server-demo-python:latest
# to:
# image: yourusername/mcp-server-demo-python:v1.0.0
```

Or use `sed` to update:
```bash
cd k8s
sed -i 's|mcp-server-demo-go:latest|yourusername/mcp-server-demo-go:v1.0.0|g' go-server-deployment.yaml
sed -i 's|mcp-server-demo-python:latest|yourusername/mcp-server-demo-python:v1.0.0|g' python-server-deployment.yaml
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
curl -I http://localhost:8080/sse
# Should return 200 OK

# Test with built-in test client
cd go-server
./testclient -tool timeserver -args '{}' -url http://localhost:8080/sse

# Forward Python server port (use a different local port)
kubectl port-forward svc/mcp-server-demo-python 8081:8080

# Test Python server
curl -I http://localhost:8081/sse
cd python-server
python3 cmd/testclient/testclient.py -tool timeserver -args '{}' -url http://localhost:8081/sse
```

**Method 2: From within the cluster (create a test pod)**

```bash
# Create a temporary test pod
kubectl run test-client --image=curlimages/curl:latest -it --rm --restart=Never -- sh

# Inside the pod, test the services
curl -I http://mcp-server-demo-go:8080/sse
curl -I http://mcp-server-demo-python:8080/sse
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
curl -I http://mcp-go.example.com/sse
curl -I http://mcp-python.example.com/sse

# Or use the test clients
./testclient -tool timeserver -args '{}' -url http://mcp-go.example.com/sse
```

**Method 4: Interactive Testing**

```bash
# Port forward and use interactive mode
kubectl port-forward svc/mcp-server-demo-go 8080:8080

# In another terminal
cd go-server
./testclient -i -url http://localhost:8080/sse

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
kubectl set image deployment/mcp-server-demo-go mcp-server=yourusername/mcp-server-demo-go:v1.1.0
kubectl set image deployment/mcp-server-demo-python mcp-server=yourusername/mcp-server-demo-python:v1.1.0

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
kubectl run test --image=curlimages/curl -it --rm --restart=Never -- curl http://mcp-server-demo-go:8080/sse
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