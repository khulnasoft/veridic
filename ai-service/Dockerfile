FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for Phase 1 static analysis and AST extraction
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    wget \
    nodejs \
    npm \
    golang-go \
    rustc \
    cargo \
    && rm -rf /var/lib/apt/lists/*

# Install Semgrep for pattern-based analysis
RUN pip install --no-cache-dir semgrep

# Install CodeQL CLI
RUN wget -q https://github.com/github/codeql-cli-binaries/releases/latest/download/codeql-linux64.zip && \
    unzip -q codeql-linux64.zip && \
    mv codeql /usr/local/bin/ && \
    rm codeql-linux64.zip

# Install Node.js packages for TypeScript AST extraction
RUN npm install -g typescript @typescript-eslint/parser

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000
CMD ["python", "src/grpc_server.py"]
