# ---- Build stage ----
FROM golang:1.23-alpine AS build
WORKDIR /src

# Copy go.mod and go.sum from parent directory
COPY go.mod go.sum ./
RUN go mod download

# Copy all source files
COPY . .

# Build the test client binary
ENV CGO_ENABLED=0
RUN go build -trimpath -ldflags="-s -w" -o /out/mcp-testclient ./cmd/testclient

# ---- Runtime stage ----
FROM gcr.io/distroless/static:nonroot
WORKDIR /
COPY --from=build /out/mcp-testclient /mcp-testclient
USER 65532:65532
ENTRYPOINT ["/mcp-testclient"]
CMD ["-i", "-url", "http://localhost:8080/mcp"]
