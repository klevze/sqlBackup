#!/bin/bash
# Quick installation script for sqlBackup

set -e

echo "Installing sqlBackup..."

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed or not in PATH"
    exit 1
fi

# Check if pip is available
if ! command -v pip &> /dev/null && ! command -v pip3 &> /dev/null; then
    echo "Error: pip is not installed or not in PATH"
    exit 1
fi

# Use pip3 if available, otherwise use pip
PIP_CMD="pip"
if command -v pip3 &> /dev/null; then
    PIP_CMD="pip3"
fi

echo "Using $PIP_CMD for installation..."

# Install dependencies
echo "Installing dependencies..."
$PIP_CMD install -r requirements.txt

# Make the main script executable
chmod +x sqlBackup

echo "Installation complete!"
echo ""
echo "Next steps:"
echo "1. Copy config.ini.default to config.ini"
echo "2. Edit config.ini to match your environment"
echo "3. Run: ./sqlBackup or python3 sqlBackup"
echo ""
echo "For development installation, run: $PIP_CMD install -e ."
