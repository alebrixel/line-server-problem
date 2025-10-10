#!/bin/bash
# Run script using the virtual environment

if [ -z "$1" ]; then
  echo "Usage: ./run.sh <file_to_serve>"
  exit 1
fi

FILE_PATH="$1"

if [ ! -d "venv" ]; then
  echo "Virtual environment not found. Please run ./build.sh first."
  exit 1
fi

source venv/bin/activate

export TEXT_FILE_PATH="$FILE_PATH"

echo "Starting Line Server for file: $FILE_PATH"
python3 -c "from app import start_server; start_server()"
