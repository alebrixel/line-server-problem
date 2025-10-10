from flask import Flask, request, Response, jsonify
import logging
import os

app = Flask(__name__)

file_path = None
line_offsets = []
BLOCK_SIZE = 1024  # default, will be adjusted dynamically


def setup_logging():
    """Configure basic logging to both file and console."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler("access.log"),
            logging.StreamHandler()
        ]
    )


def calculate_block_size(path):
    """Set block size dynamically based on file size."""
    global BLOCK_SIZE
    size = os.path.getsize(path)

    if size < 500 * 1024**2:          # < 500 MB
        BLOCK_SIZE = 256
    elif size < 5 * 1024**3:          # < 5 GB
        BLOCK_SIZE = 1024
    elif size < 20 * 1024**3:         # < 20 GB
        BLOCK_SIZE = 4096
    else:                             # 20 GB+
        BLOCK_SIZE = 8192

    logging.info(f"Dynamic BLOCK_SIZE set to {BLOCK_SIZE}")


def index_file(path):
    """Create an index of byte offsets for each line in the file."""
    global line_offsets
    line_offsets = [0]

    with open(path, "rb") as f:
        offset = 0
        while True:
            block = f.readlines(BLOCK_SIZE)
            if not block:
                break
            for line in block:
                offset += len(line)
                line_offsets.append(offset)
    logging.info(f"Indexed {len(line_offsets)-1} lines from {path}")


@app.route("/lines/<line_number>", methods=["GET"])
def get_line(line_number):
    """Return a specific line from the file."""
    global file_path, line_offsets

    client_ip = request.remote_addr
    logging.info(f"GET /lines/{line_number} from {client_ip}")

    try:
        n = int(line_number)
    except ValueError:
        logging.warning(f"Invalid line number: {line_number}")
        return jsonify({"error": "Line number must be an integer"}), 400

    if n < 0 or n >= len(line_offsets) - 1:
        logging.warning(f"Line {n} out of range")
        return jsonify({"error": "Line number out of range"}), 404

    with open(file_path, "rb") as f:
        f.seek(line_offsets[n])
        line = f.readline().decode("ascii", errors="ignore").rstrip("\n")

    return Response(line, mimetype="text/plain")


def start_server():
    """Initialize logging, dynamic block size, and indexing before starting Flask."""
    global file_path

    setup_logging()
    file_path = os.environ.get("TEXT_FILE_PATH", "dummy.txt")

    if not os.path.exists(file_path):
        logging.error(f"File not found: {file_path}")
        raise FileNotFoundError(f"{file_path} does not exist")

    calculate_block_size(file_path)
    index_file(file_path)
    app.run(host="0.0.0.0", port=8080)


if __name__ == "__main__":
    start_server()
