#!/bin/bash
# Build script - creates and prepares a virtual environment efficiently.

set -e # Exit immediately if a command fails.

# If run with the "clean" argument, remove the old venv
if [ "$1" == "clean" ]; then
  echo "Cleaning old virtual environment..."
  rm -rf venv
fi

# Create the virtual environment only if it doesn't exist
if [ ! -d "venv" ]; then
  echo "Creating virtual environment..."
  python3 -m venv venv
else
  echo "Virtual environment already exists, skipping creation."
fi

# Activate the virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies from requirements.txt
echo "Installing dependencies..."
pip install -r requirements.txt

echo "Build complete."