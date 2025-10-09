from flask import Flask, Response
import os

app = Flask(__name__)

# Global variables
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


@app.route("/lines/<line_number>", methods=["GET"])
def get_line(line_number):
    """
    Return a specific line from the file by its index.
    """
    global file_path, line_offsets

    # Validate the input
    if not line_number.isdigit():
        return Response("Invalid line index. Must be a positive integer.\n", status=400)

    index = int(line_number)

    # Check if the requested line exists
    if index < 0 or index >= len(line_offsets):
        return Response("Requested line is beyond the end of the file.\n", status=413)

    try:
        with open(file_path, 'rb') as f:
            f.seek(line_offsets[index])
            line = f.readline().decode('ascii', errors='replace').rstrip('\n')
        return Response(line + "\n", status=200, mimetype='text/plain')
    except Exception as e:
        app.logger.error(f"Error reading line {index}: {e}")
        return Response("Internal server error.\n", status=500)


@app.errorhandler(404)
def not_found(e):
    return Response("Not found.\n", status=404)


@app.errorhandler(500)
def internal_error(e):
    return Response("Internal server error.\n", status=500)


def start_server(path):
    """
    Initialize and start the server.
    """
    global file_path
    if not os.path.exists(path):
        print(f"Error: file '{path}' not found.")
        exit(1)

    file_path = path
    build_index(file_path)
    print(f"Indexed {len(line_offsets)} lines from {file_path}")
    app.run(host="0.0.0.0", port=8080, threaded=True)


if __name__ == "__main__":
    print("This script should be started via run.sh")
