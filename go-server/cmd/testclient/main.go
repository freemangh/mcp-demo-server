package main

import (
	"bufio"
	"context"
	"encoding/json"
	"flag"
	"fmt"
	"log"
	"os"
	"strings"
	"time"

	"github.com/modelcontextprotocol/go-sdk/mcp"
)

const (
	version        = "v1.1.0"
	defaultTimeout = 30 * time.Second
)

type Config struct {
	ServerURL string
	Timeout   time.Duration
}

func main() {
	// Parse command-line flags
	serverURL := flag.String("url", "http://localhost:8080/mcp", "MCP server Streamable HTTP endpoint URL")
	timeout := flag.Duration("timeout", defaultTimeout, "Request timeout duration")
	interactive := flag.Bool("i", false, "Interactive mode (REPL)")
	tool := flag.String("tool", "", "Tool name to call (echotest, timeserver, fetch)")
	args := flag.String("args", "{}", "Tool arguments as JSON string")
	flag.Parse()

	config := Config{
		ServerURL: *serverURL,
		Timeout:   *timeout,
	}

	if *interactive {
		runInteractive(config)
	} else if *tool != "" {
		runSingleCommand(config, *tool, *args)
	} else {
		fmt.Println("MCP Test Client")
		fmt.Println()
		fmt.Println("Usage:")
		fmt.Println("  Interactive mode: testclient -i [-url http://localhost:8080/mcp]")
		fmt.Println("  Single command:   testclient -tool timeserver -args '{\"timezone\":\"Europe/Kyiv\"}'")
		fmt.Println()
		fmt.Println("Flags:")
		flag.PrintDefaults()
	}
}

func runSingleCommand(config Config, toolName, argsJSON string) {
	ctx, cancel := context.WithTimeout(context.Background(), config.Timeout)
	defer cancel()

	// Parse arguments
	var toolArgs map[string]interface{}
	if err := json.Unmarshal([]byte(argsJSON), &toolArgs); err != nil {
		log.Fatalf("Failed to parse arguments: %v", err)
	}

	// Connect to server
	fmt.Printf("Connecting to %s...\n", config.ServerURL)
	session, err := connectToServer(ctx, config.ServerURL)
	if err != nil {
		log.Fatalf("Failed to connect: %v", err)
	}
	defer session.Close()

	// Call tool
	result, err := callTool(ctx, session, toolName, toolArgs)
	if err != nil {
		log.Fatalf("Tool call failed: %v", err)
	}

	// Print result
	fmt.Println("\n=== Result ===")
	fmt.Println(result)
}

func runInteractive(config Config) {
	fmt.Printf("MCP Test Client %s - Interactive Mode\n", version)
	fmt.Printf("Connecting to %s...\n", config.ServerURL)

	ctx := context.Background()
	session, err := connectToServer(ctx, config.ServerURL)
	if err != nil {
		log.Fatalf("Failed to connect: %v", err)
	}
	defer session.Close()

	fmt.Println("Connected successfully!")
	fmt.Println()
	printHelp()

	scanner := bufio.NewScanner(os.Stdin)
	for {
		fmt.Print("\nmcp> ")
		if !scanner.Scan() {
			break
		}

		line := strings.TrimSpace(scanner.Text())
		if line == "" {
			continue
		}

		if err := handleCommand(ctx, session, line); err != nil {
			fmt.Printf("Error: %v\n", err)
		}
	}

	if err := scanner.Err(); err != nil {
		log.Printf("Scanner error: %v", err)
	}
}

func handleCommand(ctx context.Context, session *mcp.ClientSession, line string) error {
	parts := strings.Fields(line)
	if len(parts) == 0 {
		return nil
	}

	cmd := strings.ToLower(parts[0])

	switch cmd {
	case "help", "h", "?":
		printHelp()
		return nil

	case "quit", "exit", "q":
		fmt.Println("Goodbye!")
		os.Exit(0)
		return nil

	case "list", "ls":
		return listTools(ctx, session)

	case "echo", "echotest":
		if len(parts) < 2 {
			return fmt.Errorf("usage: echo <message>")
		}
		message := strings.Join(parts[1:], " ")
		return runEchoTest(ctx, session, message)

	case "time", "timeserver":
		timezone := ""
		if len(parts) > 1 {
			timezone = parts[1]
		}
		return runTimeServer(ctx, session, timezone)

	case "fetch":
		if len(parts) < 2 {
			return fmt.Errorf("usage: fetch <url> [max_bytes]")
		}
		url := parts[1]
		maxBytes := 0
		if len(parts) > 2 {
			fmt.Sscanf(parts[2], "%d", &maxBytes)
		}
		return runFetch(ctx, session, url, maxBytes)

	default:
		return fmt.Errorf("unknown command: %s (type 'help' for available commands)", cmd)
	}
}

func printHelp() {
	fmt.Println("Available commands:")
	fmt.Println("  help, h, ?              Show this help message")
	fmt.Println("  list, ls                List available tools")
	fmt.Println("  echo <message>          Test echotest tool")
	fmt.Println("  time [timezone]         Test timeserver tool (e.g., time Europe/Kyiv)")
	fmt.Println("  fetch <url> [max_bytes] Test fetch tool (e.g., fetch https://ifconfig.co/json 1024)")
	fmt.Println("  quit, exit, q           Exit the client")
}

func connectToServer(ctx context.Context, serverURL string) (*mcp.ClientSession, error) {
	// Create MCP client
	client := mcp.NewClient(&mcp.Implementation{
		Name:    "mcp-test-client",
		Version: version,
	}, nil)

	// Create Streamable HTTP transport
	transport := &mcp.StreamableClientTransport{
		Endpoint:   serverURL,
		MaxRetries: 3,
	}

	// Connect to server
	session, err := client.Connect(ctx, transport, nil)
	if err != nil {
		return nil, fmt.Errorf("connection failed: %w", err)
	}

	return session, nil
}

func listTools(ctx context.Context, session *mcp.ClientSession) error {
	fmt.Println("\n=== Listing available tools ===")

	result, err := session.ListTools(ctx, &mcp.ListToolsParams{})
	if err != nil {
		return fmt.Errorf("failed to list tools: %w", err)
	}

	if len(result.Tools) == 0 {
		fmt.Println("No tools available")
		return nil
	}

	for i, tool := range result.Tools {
		fmt.Printf("%d. %s\n", i+1, tool.Name)
		if tool.Description != "" {
			fmt.Printf("   Description: %s\n", tool.Description)
		}
	}

	return nil
}

func callTool(ctx context.Context, session *mcp.ClientSession, name string, args map[string]interface{}) (string, error) {
	result, err := session.CallTool(ctx, &mcp.CallToolParams{
		Name:      name,
		Arguments: args,
	})
	if err != nil {
		return "", fmt.Errorf("tool call failed: %w", err)
	}

	if result.IsError {
		return "", fmt.Errorf("tool returned error")
	}

	// Extract text content from result
	var output strings.Builder
	for _, content := range result.Content {
		if textContent, ok := content.(*mcp.TextContent); ok {
			output.WriteString(textContent.Text)
		}
	}

	return output.String(), nil
}

func runEchoTest(ctx context.Context, session *mcp.ClientSession, message string) error {
	fmt.Println("\n=== Calling echotest ===")
	fmt.Printf("Message: %s\n", message)

	args := map[string]interface{}{
		"message": message,
	}

	result, err := callTool(ctx, session, "echotest", args)
	if err != nil {
		return err
	}

	fmt.Println("\n=== Result ===")
	fmt.Println(result)
	return nil
}

func runTimeServer(ctx context.Context, session *mcp.ClientSession, timezone string) error {
	fmt.Println("\n=== Calling timeserver ===")
	if timezone != "" {
		fmt.Printf("Timezone: %s\n", timezone)
	} else {
		fmt.Println("Timezone: Local")
	}

	args := map[string]interface{}{}
	if timezone != "" {
		args["timezone"] = timezone
	}

	result, err := callTool(ctx, session, "timeserver", args)
	if err != nil {
		return err
	}

	fmt.Println("\n=== Result ===")
	fmt.Println(result)
	return nil
}

func runFetch(ctx context.Context, session *mcp.ClientSession, url string, maxBytes int) error {
	fmt.Println("\n=== Calling fetch ===")
	fmt.Printf("URL: %s\n", url)
	if maxBytes > 0 {
		fmt.Printf("Max bytes: %d\n", maxBytes)
	}

	args := map[string]interface{}{
		"url": url,
	}
	if maxBytes > 0 {
		args["max_bytes"] = maxBytes
	}

	result, err := callTool(ctx, session, "fetch", args)
	if err != nil {
		return err
	}

	fmt.Println("\n=== Result ===")
	fmt.Println(result)
	return nil
}
