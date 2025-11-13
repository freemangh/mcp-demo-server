#!/usr/bin/env python3
"""
MCP Test Client - Python Implementation

A test client for MCP (Model Context Protocol) servers that supports
interactive REPL mode and single command execution.
"""

import argparse
import asyncio
import json
import sys
from typing import Any, Dict, Optional

from mcp import ClientSession
from mcp.client.sse import sse_client


class MCPTestClient:
    """MCP test client with interactive and command-line modes."""

    def __init__(self, server_url: str):
        """
        Initialize the MCP test client.

        Args:
            server_url: SSE endpoint URL of the MCP server
        """
        self.server_url = server_url
        self.session: Optional[ClientSession] = None

    async def connect(self) -> None:
        """Connect to the MCP server via SSE transport."""
        print(f"Connecting to {self.server_url}...")
        # The sse_client context manager handles connection setup
        # We'll connect in the context where we use it

    async def list_tools(self) -> None:
        """List available tools on the server."""
        print("\n=== Listing available tools ===")

        result = await self.session.list_tools()

        if not result.tools:
            print("No tools available")
            return

        for i, tool in enumerate(result.tools, 1):
            print(f"{i}. {tool.name}")
            if tool.description:
                print(f"   Description: {tool.description}")

    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> str:
        """
        Call a tool on the server.

        Args:
            name: Tool name
            arguments: Tool arguments as dictionary

        Returns:
            Tool result as string

        Raises:
            Exception: If tool call fails
        """
        result = await self.session.call_tool(name, arguments=arguments)

        # Extract text content from result
        output = []
        for content in result.content:
            if hasattr(content, 'text'):
                output.append(content.text)

        return '\n'.join(output)

    async def run_echotest(self, message: str) -> None:
        """Test the echotest tool."""
        print("\n=== Calling echotest ===")
        print(f"Message: {message}")

        result = await self.call_tool("echotest", {"message": message})

        print("\n=== Result ===")
        print(result)

    async def run_timeserver(self, timezone: Optional[str] = None) -> None:
        """Test the timeserver tool."""
        print("\n=== Calling timeserver ===")
        if timezone:
            print(f"Timezone: {timezone}")
        else:
            print("Timezone: Local")

        args = {}
        if timezone:
            args["timezone"] = timezone

        result = await self.call_tool("timeserver", args)

        print("\n=== Result ===")
        print(result)

    async def run_fetch(self, url: str, max_bytes: Optional[int] = None) -> None:
        """Test the fetch tool."""
        print("\n=== Calling fetch ===")
        print(f"URL: {url}")
        if max_bytes:
            print(f"Max bytes: {max_bytes}")

        args = {"url": url}
        if max_bytes:
            args["max_bytes"] = max_bytes

        result = await self.call_tool("fetch", args)

        print("\n=== Result ===")
        print(result)

    async def handle_command(self, line: str) -> bool:
        """
        Handle a single command from interactive mode.

        Args:
            line: Command line input

        Returns:
            True to continue, False to exit
        """
        parts = line.strip().split()
        if not parts:
            return True

        cmd = parts[0].lower()

        try:
            if cmd in ('help', 'h', '?'):
                self.print_help()
            elif cmd in ('quit', 'exit', 'q'):
                print("Goodbye!")
                return False
            elif cmd in ('list', 'ls'):
                await self.list_tools()
            elif cmd in ('echo', 'echotest'):
                if len(parts) < 2:
                    print("Error: usage: echo <message>")
                else:
                    message = ' '.join(parts[1:])
                    await self.run_echotest(message)
            elif cmd in ('time', 'timeserver'):
                timezone = parts[1] if len(parts) > 1 else None
                await self.run_timeserver(timezone)
            elif cmd == 'fetch':
                if len(parts) < 2:
                    print("Error: usage: fetch <url> [max_bytes]")
                else:
                    url = parts[1]
                    max_bytes = int(parts[2]) if len(parts) > 2 else None
                    await self.run_fetch(url, max_bytes)
            else:
                print(f"Error: unknown command: {cmd} (type 'help' for available commands)")
        except Exception as e:
            print(f"Error: {e}")

        return True

    @staticmethod
    def print_help() -> None:
        """Print help message for interactive mode."""
        print("Available commands:")
        print("  help, h, ?              Show this help message")
        print("  list, ls                List available tools")
        print("  echo <message>          Test echotest tool")
        print("  time [timezone]         Test timeserver tool (e.g., time Europe/Kyiv)")
        print("  fetch <url> [max_bytes] Test fetch tool (e.g., fetch https://ifconfig.co/json 1024)")
        print("  quit, exit, q           Exit the client")

    async def run_interactive(self) -> None:
        """Run in interactive REPL mode."""
        print("MCP Test Client - Interactive Mode")

        async with sse_client(self.server_url) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                self.session = session

                # Initialize connection
                await session.initialize()

                print("Connected successfully!")
                print()
                self.print_help()

                # Interactive loop
                while True:
                    try:
                        line = input("\nmcp> ")
                        if not await self.handle_command(line):
                            break
                    except EOFError:
                        print("\nGoodbye!")
                        break
                    except KeyboardInterrupt:
                        print("\n\nUse 'quit' to exit")
                        continue

    async def run_single_command(self, tool: str, args_json: str) -> None:
        """
        Run a single tool command and exit.

        Args:
            tool: Tool name
            args_json: JSON string of tool arguments
        """
        try:
            arguments = json.loads(args_json)
        except json.JSONDecodeError as e:
            print(f"Error: Failed to parse arguments: {e}")
            sys.exit(1)

        async with sse_client(self.server_url) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                self.session = session

                # Initialize connection
                await session.initialize()

                # Call tool
                result = await self.call_tool(tool, arguments)

                # Print result
                print("\n=== Result ===")
                print(result)


async def main():
    """Main entry point for the test client."""
    parser = argparse.ArgumentParser(
        description='MCP Test Client (Python)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive mode
  %(prog)s -i

  # Single command
  %(prog)s -tool timeserver -args '{}'
  %(prog)s -tool echotest -args '{"message":"Hello"}'
  %(prog)s -tool fetch -args '{"url":"https://ifconfig.co/json","max_bytes":1024}'
        """
    )

    parser.add_argument(
        '-url', '--url',
        type=str,
        default='http://localhost:8080/sse',
        help='MCP server SSE endpoint URL (default: http://localhost:8080/sse)'
    )
    parser.add_argument(
        '-i', '--interactive',
        action='store_true',
        help='Interactive mode (REPL)'
    )
    parser.add_argument(
        '-tool', '--tool',
        type=str,
        help='Tool name to call (echotest, timeserver, fetch)'
    )
    parser.add_argument(
        '-args', '--args',
        type=str,
        default='{}',
        help='Tool arguments as JSON string (default: {})'
    )

    args = parser.parse_args()

    client = MCPTestClient(args.url)

    if args.interactive:
        await client.run_interactive()
    elif args.tool:
        await client.run_single_command(args.tool, args.args)
    else:
        parser.print_help()
        print("\nError: Either -i (interactive) or -tool must be specified")
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(0)
