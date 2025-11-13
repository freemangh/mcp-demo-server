# MCP (Model Context Protocol) SDK Demo Servers

This project provides two simple MCP servers (in Go and Python) using the official SDKs.

## Repository Structure

```
mcp-demo-server/
├── go-server/        # Go implementation
├── python-server/    # Python implementation
└── README.md         # This file
```

Each server exposes tools for testing the MCP protocol:

-   `time_server`: Returns the current server time in ISO/RFC3339 format.

-   `echotest`: Echoes back any data sent to it.
    

## Testing Client: `mcp-cli`

Because these servers now use the real MCP protocol, you can't test them with `netcat` anymore. You must use an MCP client. The official `mcp-cli` is perfect for this.

**Install `mcp-cli` (one time):**

```
go install [github.com/modelcontextprotocol/mcp-cli@latest](https://github.com/modelcontextprotocol/mcp-cli@latest)

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

    ```bash
    go run .
    # Server: mcp-server-demo-go (uses stdio transport, not TCP)
    ```
    

### Test (Locally)

Open a new terminal.

1.  **Test `echotest`:**
    
    ```
    mcp-cli call localhost:8080 echotest "hello from mcp-cli"
    
    ```
    
    **Expected Output:**
    
    ```
    hello from mcp-cli
    
    ```
    
2.  **Test `time_server`:**
    
    ```
    mcp-cli call localhost:8080 time_server
    
    ```
    
    **Expected Output:** (The time will vary)
    
    ```
    2025-10-29T15:00:00Z
    
    ```
    

### Dockerize

1.  **Build the Docker Image:**

    ```bash
    cd go-server
    docker build -t mcp-server-demo-go:latest .
    ```

2.  **Run the Docker Container:**

    ```bash
    docker run -it --name go-mcp mcp-server-demo-go:latest
    ```

3.  **Test** the container using the same `mcp-cli` commands.

4.  **Stop/Remove:** `docker stop go-mcp && docker rm go-mcp`
    

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

    ```bash
    python3 mcp_server.py
    # Output: INFO - mcp-server-demo-python listening on 0.0.0.0:8080
    ```
    

### Test (Locally)

Open a new terminal.

1.  **Test `echotest`:**
    
    ```
    mcp-cli call localhost:8080 echotest "hello from python"
    
    ```
    
    **Expected Output:**
    
    ```
    hello from python
    
    ```
    
2.  **Test `time_server`:**
    
    ```
    mcp-cli call localhost:8080 time_server
    
    ```
    
    **Expected Output:** (The time will vary)
    
    ```
    2025-10-29T15:01:00.123456
    
    ```
    

### Dockerize

1.  **Build the Docker Image:**

    ```bash
    cd python-server
    docker build -t mcp-server-demo-python:latest .
    ```

2.  **Run the Docker Container:**

    ```bash
    docker run -d -p 8080:8080 --name py-mcp mcp-server-demo-python:latest
    ```

3.  **Test** the container using the same `mcp-cli` commands.

4.  **Stop/Remove:** `docker stop py-mcp && docker rm py-mcp`