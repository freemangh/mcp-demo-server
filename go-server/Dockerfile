# ---- Build stage ----
FROM golang:1.23-alpine AS build
WORKDIR /src
COPY go.mod go.sum ./
RUN go mod download

COPY . .
ENV CGO_ENABLED=0
RUN go build -trimpath -ldflags="-s -w" -o /out/mcp-demo-server .

# ---- Runtime stage ----
FROM gcr.io/distroless/static:nonroot
WORKDIR /
COPY --from=build /out/mcp-demo-server /mcp-demo-server
USER 65532:65532
EXPOSE 8080
ENTRYPOINT ["/mcp-demo-server"]
CMD ["--mode=http", "--host=0.0.0.0", "--port=8080"]
