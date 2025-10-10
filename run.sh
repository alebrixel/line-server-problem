#!/bin/bash
# Run script - starts the Gunicorn server.

set -e  # Exit immediately if a command fails.

# Check if a filename was provided
if [ -z "$1" ]; then
  echo "Usage: $0 <filename>"
  exit 1
fi

FILE_TO_SERVE="$1"
HOST="0.0.0.0"
PORT="8080"
WORKERS=4
# Set a generous timeout (in seconds) for the master process to build the index if needed.
TIMEOUT=600 

# Check if the file to be served exists
if [ ! -f "$FILE_TO_SERVE" ]; then
  echo "Error: file '$FILE_TO_SERVE' not found."
  exit 1
fi

# Check if the venv exists, otherwise run the build script
if [ ! -d "venv" ]; then
  echo "Virtual environment not found. Running build.sh..."
  ./build.sh
fi

# Activate the virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Start the server with Gunicorn
echo "Starting Gunicorn server for file '$FILE_TO_SERVE' on $HOST:$PORT..."
echo "The index will be built now if it's missing or outdated. This might take a while for large files."

# --preload: Loads the application code in the master process before forking workers.
#            This ensures the index is built only ONCE.
# --timeout: Gives the master process enough time to complete the initial indexing.
exec gunicorn --preload --workers "$WORKERS" --bind "$HOST:$PORT" --timeout "$TIMEOUT" "app:create_app('$FILE_TO_SERVE')"