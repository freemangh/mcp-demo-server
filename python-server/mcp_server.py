import logging
import mcp
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

HOST = '0.0.0.0'  # Listen on all available interfaces
PORT = 8080

def handle_time(ctx: mcp.Context):
    """
    Handles the 'time_server' tool.
    Returns the current time in ISO format.
    """
    current_time = datetime.now().isoformat()
    logging.info(f"TOOL: time_server -> {current_time}")
    # Send the time string back to the client
    ctx.send(current_time)

def handle_echo(ctx: mcp.Context):
    """
    Handles the 'echotest' tool.
    Echoes back the received data.
    """
    # The incoming data is in ctx.data as bytes
    input_data = ctx.data.decode('utf-8')
    logging.info(f"TOOL: echotest -> {input_data}")
    # Send the same data back
    ctx.send(input_data)

def main():
    """
    Main function to start the MCP server.
    """
    # Create a new MCP server instance
    server = mcp.Server(host=HOST, port=PORT)

    # Register our tool handlers
    server.register("time_server", handle_time)
    server.register("echotest", handle_echo)

    logging.info(f"mcp-server-demo-python listening on {HOST}:{PORT}")
    
    try:
        # Start the server
        server.serve_forever()
    except KeyboardInterrupt:
        logging.info("Server shutting down.")
        server.shutdown()

if __name__ == "__main__":
    main()

