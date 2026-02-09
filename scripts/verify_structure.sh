#!/bin/bash
# Verify repository structure and standards

set -e

echo "🔍 Verifying Veridic Repository Structure..."
echo ""

# Check for required files
echo "📋 Checking required files..."
required_files=(
    "README.md"
    "LICENSE"
    "CONTRIBUTING.md"
    "SECURITY.md"
    "CHANGELOG.md"
    ".gitignore"
    ".editorconfig"
    "Makefile"
    "docker-compose.yml"
)

for file in "${required_files[@]}"; do
    if [ -f "$file" ]; then
        echo "  ✅ $file"
    else
        echo "  ❌ $file (missing)"
    fi
done

echo ""

# Check for GitHub templates
echo "📁 Checking GitHub templates..."
github_files=(
    ".github/PULL_REQUEST_TEMPLATE.md"
    ".github/ISSUE_TEMPLATE/bug_report.md"
    ".github/ISSUE_TEMPLATE/feature_request.md"
)

for file in "${github_files[@]}"; do
    if [ -f "$file" ]; then
        echo "  ✅ $file"
    else
        echo "  ❌ $file (missing)"
    fi
done

echo ""

# Check documentation structure
echo "📚 Checking documentation structure..."
doc_dirs=(
    "docs/architecture"
    "docs/phases"
    "docs/guides"
    "docs/api"
    "docs/archive"
)

for dir in "${doc_dirs[@]}"; do
    if [ -d "$dir" ]; then
        count=$(find "$dir" -type f -name "*.md" | wc -l | tr -d ' ')
        echo "  ✅ $dir ($count files)"
    else
        echo "  ❌ $dir (missing)"
    fi
done

echo ""

# Check for build artifacts (should be clean)
echo "🧹 Checking for build artifacts..."
artifacts=(
    "*.log"
    "build_errors*.log"
    "*_new.*"
    "protoc_temp"
)

found_artifacts=0
for pattern in "${artifacts[@]}"; do
    if ls $pattern 2>/dev/null | grep -q .; then
        echo "  ⚠️  Found: $pattern"
        found_artifacts=1
    fi
done

if [ $found_artifacts -eq 0 ]; then
    echo "  ✅ No build artifacts found"
fi

echo ""

# Check project structure
echo "🏗️  Checking project structure..."
core_dirs=(
    "mcp-server"
    "ai-service"
    "tests"
    "scripts"
    "docs"
)

for dir in "${core_dirs[@]}"; do
    if [ -d "$dir" ]; then
        echo "  ✅ $dir/"
    else
        echo "  ❌ $dir/ (missing)"
    fi
done

echo ""

# Summary
echo "✨ Verification complete!"
echo ""
echo "Next steps:"
echo "  1. Run: make setup"
echo "  2. Run: make test"
echo "  3. Run: make validate"
echo ""
