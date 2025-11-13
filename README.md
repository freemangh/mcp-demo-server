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
│       └── testclient/         # MCP test client
│           └── main.go         # Test client code
├── python-server/              # Python implementation
│   ├── mcp_server.py           # Server code
│   ├── requirements.txt        # Python dependencies
│   └── Dockerfile              # Docker build file
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

### Option 1: Built-in Test Client (Recommended)

This repository includes a test client in `go-server/cmd/testclient/` that supports both Go and Python servers.

**Build the test client:**
```bash
cd go-server
go build -o testclient ./cmd/testclient
```

**Usage:**

Single command mode:
```bash
# Test echotest tool
./testclient -tool echotest -args '{"message":"Hello"}' -url http://localhost:8080/sse

# Test timeserver tool
./testclient -tool timeserver -args '{}' -url http://localhost:8080/sse
./testclient -tool timeserver -args '{"timezone":"Europe/Kyiv"}' -url http://localhost:8080/sse

# Test fetch tool
./testclient -tool fetch -args '{"url":"https://ifconfig.co/json","max_bytes":1024}' -url http://localhost:8080/sse
```

Interactive mode:
```bash
./testclient -i -url http://localhost:8080/sse
```

In interactive mode, you can use these commands:
- `help` - Show available commands
- `list` - List available tools on the server
- `echo <message>` - Test echotest tool
- `time [timezone]` - Test timeserver tool
- `fetch <url> [max_bytes]` - Test fetch tool
- `quit` - Exit

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