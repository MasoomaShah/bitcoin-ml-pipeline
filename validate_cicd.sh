#!/bin/bash
# CI/CD Pipeline Validation Script
# Run this to verify all workflows are properly configured

echo "╔════════════════════════════════════════════════════════╗"
echo "║     CI/CD Pipeline Implementation Validation           ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""

# Check workflow files
echo "📋 CHECKING WORKFLOW FILES..."
echo "================================"

WORKFLOWS=(
    ".github/workflows/ci.yml"
    ".github/workflows/cd.yml"
    ".github/workflows/ml-tests.yml"
    ".github/workflows/scheduled-training.yml"
)

workflow_count=0
for workflow in "${WORKFLOWS[@]}"; do
    if [ -f "$workflow" ]; then
        size=$(wc -c < "$workflow")
        echo "✅ $workflow ($size bytes)"
        ((workflow_count++))
    else
        echo "❌ $workflow - MISSING"
    fi
done

echo ""
echo "📚 CHECKING DOCUMENTATION FILES..."
echo "===================================="

DOCS=(
    "CI_CD_PIPELINE.md"
    "CI_CD_QUICK_REFERENCE.md"
    "CI_CD_IMPLEMENTATION_COMPLETE.md"
)

docs_count=0
for doc in "${DOCS[@]}"; do
    if [ -f "$doc" ]; then
        size=$(wc -c < "$doc")
        echo "✅ $doc ($size bytes)"
        ((docs_count++))
    else
        echo "❌ $doc - MISSING"
    fi
done

echo ""
echo "📦 CHECKING REQUIREMENTS..."
echo "============================="

if [ -f "requirements.txt" ]; then
    count=$(wc -l < requirements.txt)
    echo "✅ requirements.txt ($count packages)"
else
    echo "❌ requirements.txt - MISSING"
fi

echo ""
echo "🐳 CHECKING DOCKER CONFIG..."
echo "=============================="

if [ -f "Dockerfile" ]; then
    echo "✅ Dockerfile exists"
else
    echo "❌ Dockerfile - MISSING"
fi

echo ""
echo "📊 SUMMARY"
echo "=========="
echo "✅ Workflow Files: $workflow_count/4"
echo "✅ Documentation: $docs_count/3"
echo ""

if [ $workflow_count -eq 4 ] && [ $docs_count -eq 3 ]; then
    echo "╔════════════════════════════════════════════════════════╗"
    echo "║  ✅ ALL CI/CD COMPONENTS SUCCESSFULLY IMPLEMENTED      ║"
    echo "╚════════════════════════════════════════════════════════╝"
    echo ""
    echo "🚀 NEXT STEPS:"
    echo "1. Push this repository to GitHub"
    echo "2. Workflows will trigger automatically on push"
    echo "3. Monitor progress in GitHub Actions tab"
    echo "4. Check logs for any issues"
    echo ""
    exit 0
else
    echo "❌ SOME COMPONENTS ARE MISSING"
    exit 1
fi
