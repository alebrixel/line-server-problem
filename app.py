# app.py (Final, Corrected Version)

import os
import sys
import logging
import struct
import mmap
from flask import Flask, Response, request

# --- Global variables ---
file_path = None
index_path = None
total_lines = 0
data_file_size = 0
index_mmap = None
index_fd = None  # Keep file descriptor open for mmap lifetime

server_logger = logging.getLogger('server')
access_logger = logging.getLogger('access')


def setup_loggers():
    """Configures server and access loggers."""
    os.makedirs("logs", exist_ok=True)
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] [PID:%(process)d] %(message)s")

    # Limpa handlers existentes para evitar logs duplicados
    if server_logger.hasHandlers():
        server_logger.handlers.clear()
    if access_logger.hasHandlers():
        access_logger.handlers.clear()

    # --- Configurar o Server Logger (para ficheiro E console) ---
    server_logger.setLevel(logging.INFO)
    server_logger.propagate = False
    
    # 1. Handler para o ficheiro (logs/server.log)
    server_file_handler = logging.FileHandler("logs/server.log")
    server_file_handler.setFormatter(formatter)
    server_logger.addHandler(server_file_handler)
    
    ## NEW: 2. Handler para o console (stderr)
    # Isto irá espelhar os logs do servidor para o seu terminal.
    server_console_handler = logging.StreamHandler()
    server_console_handler.setFormatter(formatter)
    server_logger.addHandler(server_console_handler)

    # --- Configurar o Access Logger (apenas para ficheiro) ---
    access_logger.setLevel(logging.INFO)
    access_logger.propagate = False
    
    access_file_handler = logging.FileHandler("logs/access.log")
    access_file_handler.setFormatter(formatter)
    access_logger.addHandler(access_file_handler)


def create_app():
    """
    Application factory. Called by Gunicorn to create the Flask app instance.
    --preload ensures the main logic runs only in the master process.
    """
    filepath_to_serve = os.environ.get('DATA_FILE_PATH')
    if not filepath_to_serve:
        print("CRITICAL ERROR: DATA_FILE_PATH environment variable not set. Aborting.", file=sys.stderr, flush=True)
        sys.exit(1)

    setup_loggers()
    server_logger.info(f"Master process (PID: {os.getpid()}) starting app configuration...")

    # Path traversal security check
    try:
        requested_path = os.path.realpath(filepath_to_serve)
        base_dir = os.getcwd()
        if not requested_path.startswith(base_dir):
            raise Exception(f"Path Traversal Attempt: Cannot serve files outside of '{base_dir}'.")
    except Exception as e:
        server_logger.critical(f"SECURITY ALERT: {e}")
        sys.exit(1)

    # Master process builds the index. Workers will rely on the post_fork hook.
    ensure_index_exists(filepath_to_serve)
    load_index_mmap() # Master loads its own mmap

    server_logger.info(f"Master configuration complete. {total_lines} lines indexed.")

    app = Flask(__name__)

    @app.route("/lines/<line_number>", methods=["GET"])
    def get_line(line_number):
        try:
            n = int(line_number)
        except ValueError:
            access_logger.warning(f"{request.remote_addr} INVALID_LINE_NUMBER '{line_number}'")
            return Response("Invalid line index. Must be a positive integer.\n", status=400)

        if n < 0 or n >= total_lines:
            access_logger.warning(f"{request.remote_addr} LINE_OUT_OF_RANGE {n} (total: {total_lines})")
            return Response("Requested line is beyond the end of the file.\n", status=413)

        try:
            # Read the offset for the requested line n
            offset_start_bytes = n * 8
            offset_bytes = index_mmap[offset_start_bytes : offset_start_bytes + 8]
            offset = struct.unpack("<Q", offset_bytes)[0]
            
            # To find the length, we need the offset of the *next* line.
            # For the very last line, the length is from its offset to the end of the file.
            if n + 1 == total_lines:
                next_offset = data_file_size
            else:
                next_offset_start_bytes = (n + 1) * 8
                next_offset_bytes = index_mmap[next_offset_start_bytes : next_offset_start_bytes + 8]
                next_offset = struct.unpack("<Q", next_offset_bytes)[0]
            
            length = next_offset - offset

            with open(file_path, "rb") as df:
                df.seek(offset)
                data = df.read(length)

            access_logger.info(f"{request.remote_addr} GET /lines/{n} -> 200 (len={len(data)})")
            return Response(data.decode("ascii", errors="replace"), status=200, mimetype="text/plain")

        except Exception as e:
            server_logger.exception(f"Error serving line {n}: {e}")
            return Response("Internal server error", status=500)

    @app.errorhandler(404)
    def not_found_error(error):
        access_logger.warning(f"Request to non-existent route from {request.remote_addr}")
        return Response("Not Found\n", status=404)

    return app


def ensure_index_exists(filepath_to_serve):
    """Checks index validity and rebuilds it atomically if necessary."""
    global file_path, index_path, total_lines, data_file_size
    file_path = os.path.abspath(filepath_to_serve)
    index_path = file_path + ".index"

    if not os.path.exists(file_path):
        server_logger.critical(f"Data file not found at '{file_path}'. Shutting down.")
        sys.exit(1)

    data_file_size = os.path.getsize(file_path)
    index_is_valid = False
    if os.path.exists(index_path):
        if (os.path.getsize(index_path) > 0 and 
            os.path.getmtime(index_path) >= os.path.getmtime(file_path)):
            index_is_valid = True
            total_lines = os.path.getsize(index_path) // 8
    
    if not index_is_valid:
        server_logger.info(f"Index not found or outdated. Rebuilding index for '{os.path.basename(file_path)}'...")
        line_count = build_index_on_disk(file_path, index_path)
        total_lines = line_count
    else:
        server_logger.info(f"Using existing index with {total_lines} lines.")


def load_index_mmap(force_reopen=False):
    """Memory-map the index file. Safe to call in worker processes."""
    global index_mmap, index_path, total_lines, data_file_size, index_fd, file_path

    if index_mmap and not force_reopen: return

    if index_mmap: index_mmap.close()
    if index_fd: index_fd.close()

    if not file_path: file_path = os.path.abspath(os.environ['DATA_FILE_PATH'])
    if not index_path: index_path = file_path + ".index"
    
    index_fd = open(index_path, "rb")
    index_mmap = mmap.mmap(index_fd.fileno(), 0, access=mmap.ACCESS_READ)
    total_lines = len(index_mmap) // 8
    data_file_size = os.path.getsize(file_path)
    server_logger.info(f"Loaded index mmap in PID {os.getpid()}: {total_lines} lines.")


def init_worker():
    """Called in each worker process after forking to re-initialize resources."""
    setup_loggers()
    server_logger.info(f"Worker PID {os.getpid()} initializing...")
    try:
        load_index_mmap(force_reopen=True)
    except Exception as e:
        server_logger.exception(f"Worker PID {os.getpid()} failed to initialize mmap: {e}")


def build_index_on_disk(data_path, idx_path):
    """
    FINAL, CORRECTED VERSION: Builds the index using a robust `for line in file` loop.
    This guarantees exactly one offset is written per line that exists.
    """
    count = 0
    offset = 0
    # Use little-endian as it's more common and avoids network byte order overhead
    struct_q = struct.Struct("<Q") 
    tmp_idx_path = idx_path + ".tmp"

    server_logger.info(f"Building index into temporary file: {tmp_idx_path}")
    with open(data_path, "rb") as f_data, open(tmp_idx_path, "wb") as f_index:
        # This is the most robust and Pythonic way to read a file line by line.
        for line in f_data:
            # Write the offset of the line we just started processing.
            f_index.write(struct_q.pack(offset))
            count += 1
            # The next offset is the current one plus the length of the line.
            offset += len(line)

    # Atomically replace the old index with the new one.
    os.replace(tmp_idx_path, idx_path)
    server_logger.info(f"Finished building index: {count} lines")
    return count


# Gunicorn will find this 'app' object, created by our factory.
app = create_app()