# app.py
from flask import Flask, Response, request
import os
import logging
import sys

app = Flask(__name__)

# -------------------------
# Simple logging
# -------------------------
logging.basicConfig(
    filename="access.log",  # log file
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s"
)

# -------------------------
# Global variables
# -------------------------
line_offsets = []
file_path = None

# -------------------------
# Function to build line index
# -------------------------
def build_index(path):
    """
    Creates a list of byte offsets for each line in the file.
    Allows fast random access without loading the entire file.
    """
    global line_offsets
    offsets = []
    offset = 0
    try:
        with open(path, 'rb') as f:
            for line in f:
                offsets.append(offset)
                offset += len(line)
        line_offsets = offsets
        logging.info(f"Indexed {len(line_offsets)} lines from {path}")
    except Exception as e:
        logging.error(f"Failed to index file {path}: {e}")
        sys.exit(1)

# -------------------------
# Route to get a specific line
# -------------------------
@app.route("/lines/<line_number>", methods=["GET"])
def get_line(line_number):
    """
    Returns the requested line by its index.
    """
    global file_path, line_offsets

    client_ip = request.remote_addr
    logging.info(f"Request: GET /lines/{line_number} from {client_ip}")

    # Validate input
    if not line_number.isdigit():
        logging.warning(f"Invalid line number from {client_ip}: {line_number}")
        return Response("Invalid line index. Must be a positive integer.\n", status=400)

    index = int(line_number)

    # Out of range line
    if index < 0 or index >= len(line_offsets):
        logging.warning(f"Out of range line request from {client_ip}: {index}")
        return Response("Requested line is beyond the end of the file.\n", status=413)

    try:
        # Open file per request for thread-safety
        with open(file_path, 'rb') as f:
            f.seek(line_offsets[index])
            line = f.readline().decode('ascii', errors='replace').rstrip('\n')
        return Response(line + "\n", status=200, mimetype='text/plain')
    except Exception as e:
        logging.error(f"Error reading line {index} from {client_ip}: {e}")
        return Response("Internal server error.\n", status=500)

# -------------------------
# Error handlers
# -------------------------
@app.errorhandler(404)
def not_found(e):
    return Response("Not found.\n", status=404)

@app.errorhandler(500)
def internal_error(e):
    return Response("Internal server error.\n", status=500)

# -------------------------
# Server startup
# -------------------------
def start_server(path):
    global file_path

    if not os.path.exists(path):
        logging.error(f"File not found: {path}")
        sys.exit(1)

    file_path = path
    build_index(file_path)

    logging.info(f"Starting server on 0.0.0.0:8080")
    app.run(host="0.0.0.0", port=8080, threaded=True)

# -------------------------
# Main
# -------------------------
if __name__ == "__main__":
    print("This script should be started via run.sh")
