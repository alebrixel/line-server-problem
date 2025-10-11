#!/bin/bash
# Build script - creates a virtual environment and installs dependencies.
# All output is logged to logs/build.log.

set -e # Exit immediately if a command fails.

# --- Logging Setup ---
LOG_DIR="logs"
LOG_FILE="$LOG_DIR/build.log"
mkdir -p "$LOG_DIR" # Create the logs directory if it doesn't exist

# This function will execute the main logic and tee its output to the log file
main() {
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
      echo "Virtual environment already exists."
    fi

    # Activate the virtual environment
    echo "Activating virtual environment..."
    source venv/bin/activate

    # Install dependencies from requirements.txt
    echo "Installing dependencies..."
    pip install -r requirements.txt

    echo "Build complete."
}

# --- Execution ---
# Redirects all stdout and stderr from the main function to the tee command.
# 'tee -a' appends to the log file instead of overwriting it.
main "$@" | tee -a "$LOG_FILE"