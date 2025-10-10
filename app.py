import os
from flask import Flask, Response
from filelock import FileLock, Timeout
import logging

os.makedirs("logs", exist_ok=True)

logging.basicConfig(
    filename="logs/server.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

app = Flask(__name__)

line_offsets = []
file_path = None


def build_index(path):
    """
    Build an index of byte offsets for each line in the file.
    This allows fast random access without loading the whole file into memory.
    """
    global line_offsets
    offsets = []
    offset = 0
    with open(path, 'rb') as f:
        for line in f:
            offsets.append(offset)
            offset += len(line)
    line_offsets = offsets
    # Save the index for future use
    index_file = f"{path}.index"
    with open(index_file, 'w') as idx:
        for o in line_offsets:
            idx.write(f"{o}\n")
    logging.info(f"Index built with {len(line_offsets)} lines.")


def load_index(path):
    """
    Load the line offsets from the .index file if it exists.
    """
    global line_offsets
    index_file = f"{path}.index"
    if not os.path.exists(index_file):
        return False
    offsets = []
    with open(index_file, 'r') as f:
        for line in f:
            offsets.append(int(line.strip()))
    line_offsets = offsets
    logging.info(f"Loaded index from '{index_file}' with {len(line_offsets)} lines.")
    return True


@app.route("/lines/<line_number>", methods=["GET"])
def get_line(line_number):
    """
    Return a specific line from the file by its index.
    """
    global file_path, line_offsets

    # Validate input
    if not str(line_number).isdigit():
        logging.warning(f"Invalid line index requested: {line_number}")
        return Response("Invalid line index. Must be a positive integer.\n", status=400)

    index = int(line_number)
    if index < 0 or index >= len(line_offsets):
        logging.warning(f"Line index out of range requested: {index}")
        return Response("Requested line is beyond the end of the file.\n", status=413)

    try:
        with open(file_path, 'rb') as f:
            f.seek(line_offsets[index])
            line = f.readline().decode('ascii', errors='replace').rstrip('\n')
        logging.info(f"Served line {index}")
        return Response(line + "\n", status=200, mimetype='text/plain')
    except Exception as e:
        logging.error(f"Error reading line {index}: {e}")
        return Response("Internal server error.\n", status=500)


@app.errorhandler(404)
def not_found(e):
    return Response("Not found.\n", status=404)


@app.errorhandler(500)
def internal_error(e):
    return Response("Internal server error.\n", status=500)


def create_app(path):
    """
    Main entry point for Gunicorn. Initializes the server with the given file.
    """
    global file_path
    if not os.path.exists(path):
        print(f"Error: file '{path}' not found.")
        exit(1)

    file_path = path
    os.makedirs("logs", exist_ok=True)

    # Use a file lock to prevent multiple workers from rebuilding the index at the same time
    index_lock_path = f"{file_path}.lock"
    lock = FileLock(index_lock_path, timeout=600)  # wait up to 10 minutes

    try:
        with lock:
            if not load_index(file_path):
                print(f"Index not found or outdated. Building index for '{file_path}'...")
                build_index(file_path)
            else:
                print(f"Valid index found for '{file_path}', using it.")
    except Timeout:
        print(f"Timeout waiting for lock on '{file_path}.index'. Using existing index if present.")
        load_index(file_path)

    print(f"Server ready. {len(line_offsets)} lines indexed.")
    logging.info(f"Server started for '{file_path}' with {len(line_offsets)} lines indexed.")

    return app


# The script should be run via run.sh using Gunicorn
if __name__ == "__main__":
    print("This script should be started via run.sh with Gunicorn.")