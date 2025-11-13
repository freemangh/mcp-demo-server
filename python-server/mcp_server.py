import argparse
import logging
import mcp
import json
from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
import urllib.request
import urllib.error

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

# Constants
DEFAULT_MODE = 'tcp'
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

def handle_echotest(ctx: mcp.Context):
    """
    Handles the 'echotest' tool.
    Echoes back the received message.
    """
    try:
        # Try to parse as JSON first for structured arguments
        try:
            args = json.loads(ctx.data.decode('utf-8'))
            message = args.get('message', ctx.data.decode('utf-8'))
        except (json.JSONDecodeError, KeyError):
            # Fall back to raw data
            message = ctx.data.decode('utf-8')

        logging.info(f"TOOL: echotest -> {message}")
        ctx.send(message)
    except Exception as e:
        logging.error(f"echotest error: {e}")
        ctx.send(f"Error: {str(e)}")

def handle_timeserver(ctx: mcp.Context):
    """
    Handles the 'timeserver' tool.
    Returns the current time with optional timezone support.
    """
    try:
        # Try to parse arguments
        timezone = ''
        try:
            args = json.loads(ctx.data.decode('utf-8'))
            timezone = args.get('timezone', '')
        except (json.JSONDecodeError, KeyError):
            pass

        if timezone:
            try:
                tz = ZoneInfo(timezone)
                now_local = datetime.now(tz)
                loc_str = timezone
            except ZoneInfoNotFoundError:
                ctx.send(f"Error: invalid timezone '{timezone}'")
                logging.error(f"Invalid timezone: {timezone}")
                return
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
        ctx.send(result)
    except Exception as e:
        logging.error(f"timeserver error: {e}")
        ctx.send(f"Error: {str(e)}")

def handle_fetch(ctx: mcp.Context):
    """
    Handles the 'fetch' tool.
    Fetches content from a given URL with optional size limit.
    """
    try:
        args = json.loads(ctx.data.decode('utf-8'))
        url = args.get('url', '')
        max_bytes = clamp(args.get('max_bytes', 0), MIN_BYTES, MAX_BYTES)

        if not url:
            ctx.send("Error: URL is required")
            return

        if not (url.startswith('http://') or url.startswith('https://')):
            ctx.send("Error: URL must start with http:// or https://")
            return

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
                ctx.send(result)

        except urllib.error.HTTPError as e:
            error_msg = f"HTTP Error {e.code}: {e.reason}"
            logging.error(f"fetch error: {error_msg}")
            ctx.send(error_msg)
        except urllib.error.URLError as e:
            error_msg = f"URL Error: {str(e.reason)}"
            logging.error(f"fetch error: {error_msg}")
            ctx.send(error_msg)
        except Exception as e:
            error_msg = f"Fetch error: {str(e)}"
            logging.error(f"fetch error: {error_msg}")
            ctx.send(error_msg)

    except json.JSONDecodeError:
        ctx.send("Error: Invalid JSON arguments")
    except Exception as e:
        logging.error(f"fetch error: {e}")
        ctx.send(f"Error: {str(e)}")

def main():
    """
    Main function to start the MCP server.
    """
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='MCP Demo Server (Python)')
    parser.add_argument('--mode', type=str, default=DEFAULT_MODE, choices=['stdio', 'tcp'],
                        help=f'Transport mode: stdio or tcp (default: {DEFAULT_MODE})')
    parser.add_argument('--host', type=str, default=DEFAULT_HOST,
                        help=f'Host address to bind to for TCP mode (default: {DEFAULT_HOST})')
    parser.add_argument('--port', type=int, default=DEFAULT_PORT,
                        help=f'Port to listen on for TCP mode (default: {DEFAULT_PORT})')
    args = parser.parse_args()

    if args.mode == 'stdio':
        logging.info("mcp-server-demo-python running in stdio mode")
        logging.info("Note: stdio mode requires MCP SDK integration (not implemented in this demo)")
        logging.info("Falling back to TCP mode for now...")
        logging.warning("Full stdio support will be added in a future update")
        # For now, fall back to TCP
        args.mode = 'tcp'

    if args.mode == 'tcp':
        # Create a new MCP server instance for TCP transport
        server = mcp.Server(host=args.host, port=args.port)

        # Register our tool handlers
        server.register("echotest", handle_echotest)
        server.register("timeserver", handle_timeserver)
        server.register("fetch", handle_fetch)

        logging.info(f"mcp-server-demo-python listening on {args.host}:{args.port} (TCP)")
        logging.info(f"Registered tools: echotest, timeserver, fetch")

        try:
            # Start the server
            server.serve_forever()
        except KeyboardInterrupt:
            logging.info("Server shutting down.")
            server.shutdown()

if __name__ == "__main__":
    main()
