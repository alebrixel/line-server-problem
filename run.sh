#!/bin/bash
# Usage: ./run.sh <filename>
# Starts the line server for the specified file.

set -e

if [ $# -ne 1 ]; then
  echo "Usage: $0 <filename>"
  exit 1
fi

FILE_TO_SERVE="$1"
WORKERS=4
HOST="0.0.0.0"
PORT=8080
TIMEOUT=120

# Activate virtual environment
source venv/bin/activate

# Pass the filename via an environment variable.
export DATA_FILE_PATH="$FILE_TO_SERVE"

# Ensure logs directory exists
mkdir -p logs

echo "Starting Gunicorn server for file '$FILE_TO_SERVE' on $HOST:$PORT..."
gunicorn --preload \
    --config gunicorn_conf.py \
    --workers "$WORKERS" \
    --bind "$HOST:$PORT" \
    --timeout "$TIMEOUT" \
    --log-file logs/run.log \
    --error-logfile logs/run.log \
    "app:app"