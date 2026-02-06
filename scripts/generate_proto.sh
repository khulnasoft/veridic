#!/bin/bash
# Generate Python protobuf files from proto definitions

set -e

echo "Generating protobuf files..."

# Generate from ai_service.proto
python -m grpc_tools.protoc \
    -I./mcp-server/proto \
    --python_out=./ai-service/src/proto \
    --grpc_python_out=./ai-service/src/proto \
    ./mcp-server/proto/ai_service.proto

echo "✓ Protobuf files generated"
