# MCP (Model Context Protocol) SDK Demo Servers

This project provides two simple MCP servers (in Go and Python) using the official SDKs.

## Repository Structure

```
mcp-demo-server/
├── go-server/        # Go implementation
├── python-server/    # Python implementation
└── README.md         # This file
```

Each server exposes the following tools for testing the MCP protocol:

-   **`echotest`**: Echoes back the provided message
-   **`timeserver`**: Returns the current time with optional IANA timezone support (e.g., "Europe/Kyiv", "America/New_York")
-   **`fetch`**: Fetches content from any HTTP/HTTPS URL with optional size limit

## CLI Alignment

Both servers support consistent command-line arguments:

| Argument | Go Server | Python Server | Description |
|----------|-----------|---------------|-------------|
| `--mode` | `stdio` \| `http` | `stdio` \| `tcp` | Transport mode |
| `--host` | default: `0.0.0.0` | default: `0.0.0.0` | Bind address |
| `--port` | default: `8080` | default: `8080` | Listen port |

**Transport Modes:**
- **Go**: `stdio` (default, local) or `http` (HTTP/SSE for network)
- **Python**: `tcp` (default, network) or `stdio` (planned)
    

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

    **TCP mode (default - network access):**
    ```bash
    python3 mcp_server.py
    # Output: INFO - mcp-server-demo-python listening on 0.0.0.0:8080 (TCP)
    ```

    **TCP mode with custom host/port:**
    ```bash
    python3 mcp_server.py --mode=tcp --host=127.0.0.1 --port=9000
    # Output: INFO - mcp-server-demo-python listening on 127.0.0.1:9000 (TCP)
    ```

    **Stdio mode (for local use):**
    ```bash
    python3 mcp_server.py --mode=stdio
    # Note: stdio mode support is planned for future release
    # Currently falls back to TCP mode
    ```
    

### Test (Locally)

The Python server uses TCP socket transport. Use an MCP-compatible client to test:

**Example test commands** (using mcp-cli or similar):

1.  **Test `echotest` tool:**
    ```bash
    mcp-cli call localhost:8080 echotest '{"message":"Hello from Python!"}'
    # Expected: Hello from Python!
    ```

2.  **Test `timeserver` tool:**
    ```bash
    mcp-cli call localhost:8080 timeserver '{}'
    # Expected: Current time with local timezone

    mcp-cli call localhost:8080 timeserver '{"timezone":"Europe/Kyiv"}'
    # Expected: Current time in Europe/Kyiv timezone
    ```

3.  **Test `fetch` tool:**
    ```bash
    mcp-cli call localhost:8080 fetch '{"url":"https://ifconfig.co/json","max_bytes":1024}'
    # Expected: JSON response from ifconfig.co
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