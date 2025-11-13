package main

import (
	"context"
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

/* ---------- Shared fetch helper ---------- */

type FetchArgs struct {
	// Max bytes of the response body to return (defaults to 4096, [256..65536]).
	MaxBytes int `json:"max_bytes,omitempty" jsonschema:"Limit response body bytes (default 4096, min 256, max 65536)"`
	// Optional path override (e.g. "/" or "/json"); defaults to "/".
	Path string `json:"path,omitempty" jsonschema:"Optional path override (e.g. / or /json)"`
}

func fetchURL(ctx context.Context, baseURL string, maxBytes int, path string) (string, error) {
	if path == "" {
		path = "/"
	}
	url := baseURL
	if path != "/" {
		url = baseURL + path
	}

	req, err := http.NewRequestWithContext(ctx, http.MethodGet, url, nil)
	if err != nil {
		return "", err
	}
	req.Header.Set("User-Agent", "mcp-server-demo-go/1.0 (+https://example.local)")

	resp, err := httpClient.Do(req)
	if err != nil {
		return "", err
	}
	defer resp.Body.Close()

	limited := io.LimitReader(resp.Body, int64(maxBytes))
	body, err := io.ReadAll(limited)
	if err != nil {
		return "", err
	}

	truncatedNote := ""
	// If content-length unknown or larger than maxBytes, we can't detect strict truncation reliably.
	// Add a best-effort note when server advertises size.
	if resp.ContentLength > 0 && resp.ContentLength > int64(maxBytes) {
		truncatedNote = " (truncated)"
	}

	return fmt.Sprintf("URL: %s\nStatus: %s\nBytes: %d%s\n\n%s",
		url, resp.Status, len(body), truncatedNote, string(body)), nil
}

/* ---------- Tool: fetch_ifconfig ---------- */

func FetchIfconfigTool(ctx context.Context, req *mcp.CallToolRequest, in FetchArgs) (*mcp.CallToolResult, any, error) {
	max := clamp(in.MaxBytes, minCapBytes, maxCapBytes)
	body, err := fetchURL(ctx, "https://ifconfig.co", max, in.Path)
	if err != nil {
		return &mcp.CallToolResult{
			IsError: true,
			Content: []mcp.Content{&mcp.TextContent{Text: "fetch_ifconfig error: " + err.Error()}},
		}, nil, nil
	}
	return &mcp.CallToolResult{
		Content: []mcp.Content{&mcp.TextContent{Text: body}},
	}, nil, nil
}

/* ---------- Tool: fetch_google ---------- */

func FetchGoogleTool(ctx context.Context, req *mcp.CallToolRequest, in FetchArgs) (*mcp.CallToolResult, any, error) {
	max := clamp(in.MaxBytes, minCapBytes, maxCapBytes)
	body, err := fetchURL(ctx, "https://www.google.com", max, in.Path)
	if err != nil {
		return &mcp.CallToolResult{
			IsError: true,
			Content: []mcp.Content{&mcp.TextContent{Text: "fetch_google error: " + err.Error()}},
		}, nil, nil
	}
	return &mcp.CallToolResult{
		Content: []mcp.Content{&mcp.TextContent{Text: body}},
	}, nil, nil
}

/* ---------- main ---------- */

func main() {
	server := mcp.NewServer(&mcp.Implementation{
		Name:    "mcp-server-demo-go",
		Version: "v0.1.0",
	}, nil)

	mcp.AddTool(server, &mcp.Tool{
		Name:        "timeserver",
		Description: "Return current time; optional IANA tz via timezone arg",
	}, TimeServerTool)

	mcp.AddTool(server, &mcp.Tool{
		Name:        "fetch_ifconfig",
		Description: "Fetch https://ifconfig.co/ (HTML by default). Optional max_bytes and path (e.g. /json)",
	}, FetchIfconfigTool)

	mcp.AddTool(server, &mcp.Tool{
		Name:        "fetch_google",
		Description: "Fetch https://www.google.com/ (HTML). Optional max_bytes and path",
	}, FetchGoogleTool)

	if err := server.Run(context.Background(), &mcp.StdioTransport{}); err != nil {
		log.Fatal(err)
	}
}
