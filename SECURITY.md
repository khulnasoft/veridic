# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.x.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

We take security vulnerabilities seriously. If you discover a security issue, please follow these steps:

### DO NOT

- Open a public GitHub issue
- Disclose the vulnerability publicly before it's been addressed

### DO

1. **Email us privately**: security@khulnasoft.com
2. **Include**:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)
   - Your contact information

### What to Expect

- **Acknowledgment**: Within 48 hours
- **Initial Assessment**: Within 5 business days
- **Regular Updates**: Every 7 days until resolved
- **Resolution Timeline**: Varies by severity
  - Critical: 7-14 days
  - High: 14-30 days
  - Medium: 30-60 days
  - Low: 60-90 days

### Disclosure Policy

After a fix is released:
1. We'll coordinate with you on disclosure timing
2. You'll be credited (unless you prefer to remain anonymous)
3. We'll publish a security advisory

### Bug Bounty

We currently do not offer a bug bounty program, but we deeply appreciate responsible disclosure and will publicly acknowledge your contribution.

## Security Best Practices

### For Users

- Always use the latest stable version
- Keep dependencies up to date
- Use environment variables for sensitive data
- Enable authentication in production
- Review security advisories regularly

### For Contributors

- Never commit secrets or credentials
- Use `.env.example` for environment templates
- Run security scans before submitting PRs
- Follow OWASP guidelines for web security
- Validate all user inputs

## Known Security Considerations

### AI Service
- API keys stored in environment variables only
- Rate limiting recommended for production
- Input validation on all code analysis requests

### MCP Server
- gRPC authentication should be enabled in production
- TLS encryption recommended for network communication
- Resource limits to prevent DoS

### Docker Deployment
- Use non-root users in containers
- Scan images for vulnerabilities regularly
- Keep base images updated

## Security Contact

For security-related questions or concerns:
- Email: security@khulnasoft.com
- PGP Key: [Link to PGP key if available]

## Acknowledgments

We thank the following researchers for responsible disclosure:
- [Name] - [Vulnerability] - [Date]

---

**Last Updated**: February 9, 2026
