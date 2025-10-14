#!/bin/bash
# Build script - creates a virtual environment and installs dependencies.
# All output is logged to logs/build.log.

set -e # Exit immediately if a command fails.

# --- Logging Setup ---
LOG_DIR="logs"
LOG_FILE="$LOG_DIR/build.log"
mkdir -p "$LOG_DIR" # Create the logs directory if it doesn't exist

# --- Check if Python and venv are available ---
check_venv() {
    echo "Checking Python and venv availability..."

    if ! command -v python3 &> /dev/null; then
        echo "Python3 not found. Please install Python 3 and try again."
        exit 1
    fi

    # Try running the venv module to check if it's available
    if ! python3 -m venv --help &> /dev/null; then
        echo "Python venv module not found. Attempting to install it..."

        # Detect OS type for package manager
        if [ -f /etc/debian_version ]; then
            sudo apt update && sudo apt install -y python3-venv
        elif [ -f /etc/redhat-release ]; then
            sudo yum install -y python3-venv
        else
            echo "Automatic installation not supported on this system. Please install python3-venv manually."
            exit 1
        fi
    fi
}

# --- Main Logic ---
main() {
    check_venv

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

    # Upgrade pip to avoid install issues
    echo "Upgrading pip..."
    pip install --upgrade pip

    # Install dependencies from requirements.txt
    echo "Installing dependencies..."
    pip install -r requirements.txt

    echo "Build complete."
}

# --- Execution ---
main "$@" | tee -a "$LOG_FILE"
