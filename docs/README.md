# Veridic Documentation

Welcome to the Veridic documentation! This directory contains comprehensive guides, architecture documentation, and API references.

## 📚 Directory Structure

```
docs/
├── README.md            # This file
├── architecture/        # System architecture documentation
├── phases/             # Phase implementation documentation
├── guides/             # User and developer guides
├── api/                # API documentation
└── archive/            # Historical documentation
```

## 🚀 Quick Start

### New Users
1. **[Quick Start Validation](guides/quick-start-validation.md)** - Get started in 5 minutes
2. **[System Overview](architecture/system-overview.md)** - Understand the architecture
3. **[Installation Guide](../README.md#installation)** - Set up your environment

### Developers
1. **[Development Setup](guides/phase-1-validation-execution.md)** - Configure your dev environment
2. **[Testing Guide](guides/validation-testing.md)** - Run tests and validation
3. **[Contributing](../CONTRIBUTING.md)** - How to contribute

## 📖 Documentation Index

### Architecture

Understand how Veridic is built:

- **[System Overview](architecture/system-overview.md)** - High-level architecture
- **[Architecture Index](architecture/index.md)** - Complete architecture guide
- **[Phase 2 Architecture](architecture/phase-2.md)** - Runtime monitoring architecture
- **[Phase 2.1 Details](architecture/phase-2-1.md)** - eBPF integration

### Implementation Phases

Learn about each development phase:

- **[Phase 1: Static Analysis](phases/phase-1.md)** - Multi-language static analysis pipeline
- **[Phase 2.1: eBPF Runtime](phases/phase-2-1.md)** - Runtime syscall monitoring
- **[Phase 2.2: Evidence Chains](phases/phase-2-2.md)** - Vulnerability validation
- **[Phase 2.3: AI Reasoning](phases/phase-2-3-week-1.md)** - Enhanced AI correlation
- **[Phase 2.4: Production](phases/phase-2-4.md)** - Production deployment

### User Guides

Practical guides for using Veridic:

- **[Quick Reference](guides/quick-reference.md)** - Common commands and workflows
- **[Quick Start Validation](guides/quick-start-validation.md)** - Get started quickly
- **[Validation Testing](guides/validation-testing.md)** - Comprehensive testing guide
- **[Determinism & Tool Attribution](guides/determinism-tool-attribution.md)** - Understanding metrics
- **[Web Frontend](guides/web-frontend.md)** - Using the Next.js interface

### Developer Guides

For contributors and developers:

- **[Phase 1 Validation Roadmap](guides/phase-1-validation-roadmap.md)** - Validation strategy
- **[Phase 1 Validation Execution](guides/phase-1-validation-execution.md)** - Running validation
- **[Phase 2 Implementation](guides/phase-2-implementation.md)** - Implementing Phase 2

### API Documentation

Technical API references:

- **[MCP Protocol](api/mcp-protocol.md)** - gRPC protocol specification

### Archive

Historical documentation and summaries:

- [Enhanced Infrastructure Summary](archive/ENHANCED_INFRASTRUCTURE_SUMMARY.md)
- [Execution Ready](archive/EXECUTION_READY.md)
- [Executive Summary](archive/EXECUTIVE_SUMMARY.md)
- [Implementation Complete](archive/IMPLEMENTATION_COMPLETE.md)
- And more...

## 🎯 Common Tasks

### Running Tests

```bash
# Run all tests
make test

# Run Phase 1 tests
make test-phase1

# Run validation suite
make validate
```

### Generating Reports

```bash
# Generate baseline metrics
make metrics

# Generate specific reports
make report-determinism
make report-complementarity
make report-attribution
```

### Building and Deployment

```bash
# Build services
make build

# Run locally
make run

# Stop services
make stop
```

## 🔍 Finding Documentation

### By Topic

- **Getting Started**: [Quick Start](guides/quick-start-validation.md)
- **Architecture**: [System Overview](architecture/system-overview.md)
- **Testing**: [Validation Testing](guides/validation-testing.md)
- **Contributing**: [Contributing Guide](../CONTRIBUTING.md)
- **Security**: [Security Policy](../SECURITY.md)
- **API**: [MCP Protocol](api/mcp-protocol.md)

### By Role

#### Security Researcher
- [Quick Start Validation](guides/quick-start-validation.md)
- [Phase 1 Overview](phases/phase-1.md)
- [Tool Attribution](guides/determinism-tool-attribution.md)

#### Developer
- [System Architecture](architecture/system-overview.md)
- [Phase 2 Implementation](guides/phase-2-implementation.md)
- [Contributing Guide](../CONTRIBUTING.md)

#### DevOps Engineer
- [Docker Setup](../README.md#installation)
- [Deployment Guide](phases/phase-2-4.md)

## 📝 Contributing to Documentation

Found an error or want to improve the docs?

1. Check the [Contributing Guide](../CONTRIBUTING.md)
2. Follow the documentation style guide
3. Submit a pull request

### Documentation Style Guide

- Use clear, concise language
- Include code examples where helpful
- Keep lines under 100 characters
- Use markdown formatting consistently
- Include a table of contents for long documents

## 🆘 Need Help?

- **Issues**: [GitHub Issues](https://github.com/khulnasoft/veridic/issues)
- **Discussions**: [GitHub Discussions](https://github.com/khulnasoft/veridic/discussions)
- **Security**: security@khulnasoft.com

## 📊 Documentation Metrics

- Total documentation files: 30+
- Architecture docs: 5
- Phase docs: 6
- User guides: 8
- API docs: 1
- Archive: 9

---

**Last Updated**: February 9, 2026  
**Maintained by**: Veridic Team
