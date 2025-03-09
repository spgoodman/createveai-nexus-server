#!/bin/bash
# Start script for Createve.AI API Server

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
    if [ $? -ne 0 ]; then
        echo "Failed to create virtual environment, trying with python..."
        python -m venv .venv
        if [ $? -ne 0 ]; then
            echo "Failed to create virtual environment. Please install Python 3."
            exit 1
        fi
    fi
fi

# Activate virtual environment
source .venv/bin/activate

# Install requirements
echo "Installing requirements..."
pip install -r requirements.txt

# Create required directories
mkdir -p logs
mkdir -p processing/tmp

# Start server
echo "Starting API server..."
python main.py "$@"
