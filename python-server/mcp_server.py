import argparse
import logging
import json
from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
import urllib.request
import urllib.error

from mcp.server import Server
from mcp.types import Tool, TextContent
from mcp.server.streamable_http import create_streamable_http_app
from starlette.applications import Starlette
from starlette.routing import Route
from starlette.requests import Request
from starlette.responses import Response
from starlette.middleware.base import BaseHTTPMiddleware
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

# Constants
VERSION = "v1.1.0"
DEFAULT_MODE = 'stdio'
DEFAULT_HOST = '0.0.0.0'
DEFAULT_PORT = 8080
DEFAULT_MAX_BYTES = 4096
MIN_BYTES = 256
MAX_BYTES = 65536

def clamp(value, min_val, max_val):
    """Clamp value between min and max."""
    if value <= 0:
        return DEFAULT_MAX_BYTES
    return max(min_val, min(value, max_val))

# Create MCP server instance
app = Server("mcp-server-demo-python")

@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools."""
    return [
        Tool(
            name="echotest",
            description="Echo back the provided message",
            inputSchema={
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string",
                        "description": "Message to echo back"
                    }
                },
                "required": ["message"]
            }
        ),
        Tool(
            name="timeserver",
            description="Return current time; optional IANA tz via timezone arg",
            inputSchema={
                "type": "object",
                "properties": {
                    "timezone": {
                        "type": "string",
                        "description": "IANA timezone, e.g. Europe/Kyiv"
                    }
                }
            }
        ),
        Tool(
            name="fetch",
            description="Fetch content from a URL (HTTP/HTTPS). Optional max_bytes to limit response size",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "URL to fetch (must be http or https)"
                    },
                    "max_bytes": {
                        "type": "integer",
                        "description": "Limit response body bytes (default 4096, min 256, max 65536)"
                    }
                },
                "required": ["url"]
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls."""
    if name == "echotest":
        message = arguments.get("message", "")
        logging.info(f"TOOL: echotest -> {message}")
        return [TextContent(type="text", text=message)]

    elif name == "timeserver":
        timezone = arguments.get("timezone", "")

        if timezone:
            try:
                tz = ZoneInfo(timezone)
                now_local = datetime.now(tz)
                loc_str = timezone
            except ZoneInfoNotFoundError:
                error_msg = f"Error: invalid timezone '{timezone}'"
                logging.error(error_msg)
                return [TextContent(type="text", text=error_msg)]
        else:
            now_local = datetime.now()
            loc_str = "Local"

        now_utc = datetime.now(ZoneInfo('UTC'))

        result = (
            f"now_local={now_local.isoformat()} (tz={loc_str})\n"
            f"now_utc={now_utc.isoformat()}\n"
            f"unix={int(now_local.timestamp())}"
        )

        logging.info(f"TOOL: timeserver (tz={loc_str})")
        return [TextContent(type="text", text=result)]

    elif name == "fetch":
        url = arguments.get("url", "")
        max_bytes = clamp(arguments.get("max_bytes", 0), MIN_BYTES, MAX_BYTES)

        if not url:
            return [TextContent(type="text", text="Error: URL is required")]

        if not (url.startswith('http://') or url.startswith('https://')):
            return [TextContent(type="text", text="Error: URL must start with http:// or https://")]

        # Create request with custom user agent
        req = urllib.request.Request(
            url,
            headers={'User-Agent': 'mcp-server-demo-python/1.0 (+https://example.local)'}
        )

        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                content_length = response.getheader('Content-Length')
                body = response.read(max_bytes)
                status = f"{response.status} {response.reason}"

                truncated_note = ""
                if content_length and int(content_length) > max_bytes:
                    truncated_note = " (truncated)"

                result = (
                    f"URL: {url}\n"
                    f"Status: {status}\n"
                    f"Bytes: {len(body)}{truncated_note}\n\n"
                    f"{body.decode('utf-8', errors='replace')}"
                )

                logging.info(f"TOOL: fetch -> {url} ({len(body)} bytes)")
                return [TextContent(type="text", text=result)]

        except urllib.error.HTTPError as e:
            error_msg = f"HTTP Error {e.code}: {e.reason}"
            logging.error(f"fetch error: {error_msg}")
            return [TextContent(type="text", text=error_msg)]
        except urllib.error.URLError as e:
            error_msg = f"URL Error: {str(e.reason)}"
            logging.error(f"fetch error: {error_msg}")
            return [TextContent(type="text", text=error_msg)]
        except Exception as e:
            error_msg = f"Fetch error: {str(e)}"
            logging.error(f"fetch error: {error_msg}")
            return [TextContent(type="text", text=error_msg)]

    else:
        return [TextContent(type="text", text=f"Unknown tool: {name}")]

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log all HTTP requests and responses."""

    async def dispatch(self, request: Request, call_next):
        # Log incoming request
        logging.info(f"[REQUEST] Method={request.method} Path={request.url.path} "
                    f"RemoteAddr={request.client.host}:{request.client.port} "
                    f"UserAgent={request.headers.get('user-agent', 'Unknown')}")

        # Log query parameters if present
        if request.url.query:
            logging.info(f"[QUERY] {request.url.query}")

        # Log all headers
        headers_dict = dict(request.headers)
        logging.info(f"[HEADERS] {headers_dict}")

        # Call the next middleware/endpoint
        response = await call_next(request)

        # Log response
        logging.info(f"[RESPONSE] Path={request.url.path} Status={response.status_code}")

        return response

def create_streamable_http_server(host: str, port: int):
    """Create Streamable HTTP server with Starlette."""

    async def handle_health(request: Request) -> Response:
        """Health check endpoint."""
        return Response(
            content=json.dumps({
                "status": "ok",
                "service": "mcp-server-demo-python",
                "version": VERSION
            }),
            media_type="application/json",
            status_code=200
        )

    # Create Streamable HTTP app with stateful sessions (in-memory)
    # This provides session management with session IDs
    mcp_app = create_streamable_http_app(
        app,
        path="/mcp",
        stateless=False,  # Stateful sessions with session ID management
        json_response=False,  # Use SSE streaming for responses
        session_timeout=30 * 60  # 30 minutes timeout for idle sessions
    )

    # Create Starlette app with logging middleware
    from starlette.middleware import Middleware
    from starlette.routing import Mount

    starlette_app = Starlette(
        debug=True,
        routes=[
            Route("/health", endpoint=handle_health, methods=["GET"]),
            Route("/healthz", endpoint=handle_health, methods=["GET"]),
            Mount("/mcp", app=mcp_app),
        ],
        middleware=[
            Middleware(RequestLoggingMiddleware)
        ]
    )

    return starlette_app

async def run_stdio():
    """Run server in stdio mode."""
    from mcp.server.stdio import stdio_server

    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )

def main():
    """
    Main function to start the MCP server.
    """
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='MCP Demo Server (Python)')
    parser.add_argument('--mode', type=str, default=DEFAULT_MODE, choices=['stdio', 'http'],
                        help=f'Transport mode: stdio or http (default: {DEFAULT_MODE})')
    parser.add_argument('--host', type=str, default=DEFAULT_HOST,
                        help=f'Host address to bind to for HTTP mode (default: {DEFAULT_HOST})')
    parser.add_argument('--port', type=int, default=DEFAULT_PORT,
                        help=f'Port to listen on for HTTP mode (default: {DEFAULT_PORT})')
    args = parser.parse_args()

    if args.mode == 'stdio':
        logging.info(f"mcp-server-demo-python {VERSION} starting...")
        logging.info("Transport: stdio")
        import anyio
        anyio.run(run_stdio)

    elif args.mode == 'http':
        # Create and run Streamable HTTP server
        starlette_app = create_streamable_http_server(args.host, args.port)

        logging.info(f"mcp-server-demo-python {VERSION} starting...")
        logging.info("Transport: Streamable HTTP (MCP spec 2025-03-26)")
        logging.info(f"Registered tools: echotest, timeserver, fetch")
        logging.info(f"Server listening on {args.host}:{args.port}")
        logging.info(f"MCP endpoint: http://{args.host}:{args.port}/mcp")
        logging.info(f"Health check endpoints: /health and /healthz")

        uvicorn.run(
            starlette_app,
            host=args.host,
            port=args.port,
            log_level="info"
        )

if __name__ == "__main__":
    main()
