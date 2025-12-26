#!/bin/bash
# Newman test runner with comprehensive reporting

set -e

COLLECTION=${1:-"collection.json"}
ENVIRONMENT=${2:-"environment.json"}
OUTPUT_DIR=${3:-"./newman-results"}

echo "Running Newman tests..."
echo "Collection: $COLLECTION"
echo "Environment: $ENVIRONMENT"

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Run Newman with multiple reporters
newman run "$COLLECTION" \
    -e "$ENVIRONMENT" \
    -r cli,html,json \
    --reporter-html-export "$OUTPUT_DIR/report.html" \
    --reporter-json-export "$OUTPUT_DIR/results.json" \
    --timeout-request 10000 \
    --color on

# Check exit code
if [ $? -eq 0 ]; then
    echo "All tests passed!"
    echo "Report: $OUTPUT_DIR/report.html"
else
    echo "Tests failed!"
    exit 1
fi