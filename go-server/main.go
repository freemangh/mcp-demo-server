package main

import (
	"context"
	"flag"
	"fmt"
	"io"
	"log"
	"net/http"
	"time"

	"github.com/modelcontextprotocol/go-sdk/mcp"
)

const (
	defaultMaxBytes = 4096
	maxCapBytes     = 65536
	minCapBytes     = 256
)

// responseWriter wraps http.ResponseWriter to capture the status code
// It also implements http.Flusher to support SSE streaming
type responseWriter struct {
	http.ResponseWriter
	statusCode int
}

func (rw *responseWriter) WriteHeader(code int) {
	rw.statusCode = code
	rw.ResponseWriter.WriteHeader(code)
}

// Flush implements http.Flusher for SSE support
func (rw *responseWriter) Flush() {
	if flusher, ok := rw.ResponseWriter.(http.Flusher); ok {
		flusher.Flush()
	}
}

var httpClient = &http.Client{
	Timeout: 10 * time.Second,
}

func clamp(n, lo, hi int) int {
	if n <= 0 {
		return defaultMaxBytes
	}
	if n < lo {
		return lo
	}
	if n > hi {
		return hi
	}
	return n
}

/* ---------- Tool: echotest ---------- */

type EchoArgs struct {
	// Message to echo back
	Message string `json:"message" jsonschema:"Message to echo back"`
}

func EchotestTool(ctx context.Context, req *mcp.CallToolRequest, in EchoArgs) (*mcp.CallToolResult, any, error) {
	return &mcp.CallToolResult{
		Content: []mcp.Content{&mcp.TextContent{Text: in.Message}},
	}, nil, nil
}

/* ---------- Tool: timeserver ---------- */

type TimeArgs struct {
	// IANA timezone, e.g. "Europe/Kyiv". Empty -> system local tz.
	Timezone string `json:"timezone,omitempty" jsonschema:"IANA timezone, e.g. Europe/Kyiv"`
}

func TimeServerTool(ctx context.Context, req *mcp.CallToolRequest, in TimeArgs) (*mcp.CallToolResult, any, error) {
	loc := time.Local
	var err error
	if in.Timezone != "" {
		loc, err = time.LoadLocation(in.Timezone)
		if err != nil {
			return &mcp.CallToolResult{
				IsError: true,
				Content: []mcp.Content{
					&mcp.TextContent{Text: fmt.Sprintf("invalid timezone %q: %v", in.Timezone, err)},
				},
			}, nil, nil
		}
	}

	nowLocal := time.Now().In(loc)
	nowUTC := time.Now().UTC()

	out := fmt.Sprintf(
		"now_local=%s (tz=%s)\nnow_utc=%s\nunix=%d",
		nowLocal.Format(time.RFC3339Nano),
		loc.String(),
		nowUTC.Format(time.RFC3339Nano),
		nowLocal.Unix(),
	)

	return &mcp.CallToolResult{
		Content: []mcp.Content{&mcp.TextContent{Text: out}},
	}, nil, nil
}

/* ---------- Tool: fetch ---------- */

type FetchArgs struct {
	// URL to fetch
	URL string `json:"url" jsonschema:"URL to fetch (must be http or https)"`
	// Max bytes of the response body to return (defaults to 4096, [256..65536]).
	MaxBytes int `json:"max_bytes,omitempty" jsonschema:"Limit response body bytes (default 4096, min 256, max 65536)"`
}

func FetchTool(ctx context.Context, req *mcp.CallToolRequest, in FetchArgs) (*mcp.CallToolResult, any, error) {
	// Validate URL
	if in.URL == "" {
		return &mcp.CallToolResult{
			IsError: true,
			Content: []mcp.Content{&mcp.TextContent{Text: "URL is required"}},
		}, nil, nil
	}

	// Validate URL scheme
	if len(in.URL) < 7 || (in.URL[:7] != "http://" && in.URL[:8] != "https://") {
		return &mcp.CallToolResult{
			IsError: true,
			Content: []mcp.Content{&mcp.TextContent{Text: "URL must start with http:// or https://"}},
		}, nil, nil
	}

	maxBytes := clamp(in.MaxBytes, minCapBytes, maxCapBytes)

	httpReq, err := http.NewRequestWithContext(ctx, http.MethodGet, in.URL, nil)
	if err != nil {
		return &mcp.CallToolResult{
			IsError: true,
			Content: []mcp.Content{&mcp.TextContent{Text: "Invalid URL: " + err.Error()}},
		}, nil, nil
	}
	httpReq.Header.Set("User-Agent", "mcp-server-demo-go/1.0 (+https://example.local)")

	resp, err := httpClient.Do(httpReq)
	if err != nil {
		return &mcp.CallToolResult{
			IsError: true,
			Content: []mcp.Content{&mcp.TextContent{Text: "Fetch error: " + err.Error()}},
		}, nil, nil
	}
	defer resp.Body.Close()

	limited := io.LimitReader(resp.Body, int64(maxBytes))
	body, err := io.ReadAll(limited)
	if err != nil {
		return &mcp.CallToolResult{
			IsError: true,
			Content: []mcp.Content{&mcp.TextContent{Text: "Read error: " + err.Error()}},
		}, nil, nil
	}

	truncatedNote := ""
	if resp.ContentLength > 0 && resp.ContentLength > int64(maxBytes) {
		truncatedNote = " (truncated)"
	}

	result := fmt.Sprintf("URL: %s\nStatus: %s\nBytes: %d%s\n\n%s",
		in.URL, resp.Status, len(body), truncatedNote, string(body))

	return &mcp.CallToolResult{
		Content: []mcp.Content{&mcp.TextContent{Text: result}},
	}, nil, nil
}

/* ---------- main ---------- */

func main() {
	// Command-line flags
	mode := flag.String("mode", "stdio", "Transport mode: stdio or http")
	port := flag.String("port", "8080", "HTTP port for network mode")
	host := flag.String("host", "0.0.0.0", "Host address to bind to")
	flag.Parse()

	server := mcp.NewServer(&mcp.Implementation{
		Name:    "mcp-server-demo-go",
		Version: "v1.0.1",
	}, nil)

	mcp.AddTool(server, &mcp.Tool{
		Name:        "echotest",
		Description: "Echo back the provided message",
	}, EchotestTool)

	mcp.AddTool(server, &mcp.Tool{
		Name:        "timeserver",
		Description: "Return current time; optional IANA tz via timezone arg",
	}, TimeServerTool)

	mcp.AddTool(server, &mcp.Tool{
		Name:        "fetch",
		Description: "Fetch content from a URL (HTTP/HTTPS). Optional max_bytes to limit response size",
	}, FetchTool)

	var err error
	ctx := context.Background()

	if *mode == "http" {
		addr := fmt.Sprintf("%s:%s", *host, *port)

		// Create SSE handler for MCP over HTTP
		mcpHandler := mcp.NewSSEHandler(func(*http.Request) *mcp.Server {
			return server
		}, nil)

		// Create a mux to handle both MCP and health check endpoints
		mux := http.NewServeMux()

		// Logging middleware to trace ALL incoming requests
		loggingMux := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			log.Printf("[REQUEST] Method=%s Path=%s RemoteAddr=%s UserAgent=%s",
				r.Method, r.URL.Path, r.RemoteAddr, r.Header.Get("User-Agent"))
			log.Printf("[HEADERS] %v", r.Header)

			// Create a response writer wrapper to capture status code
			wrappedWriter := &responseWriter{ResponseWriter: w, statusCode: http.StatusOK}

			// Serve the request
			mux.ServeHTTP(wrappedWriter, r)

			log.Printf("[RESPONSE] Path=%s Status=%d", r.URL.Path, wrappedWriter.statusCode)
		})

		// Health check endpoint
		mux.HandleFunc("/health", func(w http.ResponseWriter, r *http.Request) {
			w.Header().Set("Content-Type", "application/json")
			w.WriteHeader(http.StatusOK)
			fmt.Fprintf(w, `{"status":"ok","service":"mcp-server-demo-go","version":"v1.0.1"}`)
		})

		// Alternative health check endpoint (common Kubernetes convention)
		mux.HandleFunc("/healthz", func(w http.ResponseWriter, r *http.Request) {
			w.Header().Set("Content-Type", "application/json")
			w.WriteHeader(http.StatusOK)
			fmt.Fprintf(w, `{"status":"ok","service":"mcp-server-demo-go","version":"v1.0.1"}`)
		})

		// MCP SSE handler on /sse path (consistent with Python implementation)
		mux.Handle("/sse", mcpHandler)

		// Catch-all handler for unmatched routes (will show 404s)
		mux.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
			if r.URL.Path != "/" {
				log.Printf("[UNHANDLED] Method=%s Path=%s - returning 404", r.Method, r.URL.Path)
			}
			http.NotFound(w, r)
		})

		// Create HTTP server with logging middleware
		httpServer := &http.Server{
			Addr:    addr,
			Handler: loggingMux,
		}

		log.Printf("mcp-server-demo-go listening on %s (HTTP/SSE)", addr)
		log.Printf("SSE endpoint: http://%s/sse", addr)
		log.Printf("Health check endpoints: /health and /healthz")
		err = httpServer.ListenAndServe()
	} else {
		log.Printf("mcp-server-demo-go running in stdio mode")
		err = server.Run(ctx, &mcp.StdioTransport{})
	}

	if err != nil {
		log.Fatal(err)
	}
}
