# Stage 1: Build
FROM rust:1.75 AS builder
WORKDIR /app

COPY Cargo.toml Cargo.lock ./
COPY mcp-server ./mcp-server

RUN cargo build --release --bin mcp-server

# Stage 2: Runtime
FROM debian:bookworm-slim
RUN apt-get update && apt-get install -y ca-certificates && rm -rf /var/lib/apt/lists/*

COPY --from=builder /app/target/release/mcp-server /usr/local/bin/

EXPOSE 50051
CMD ["mcp-server"]
