# Line Server System

This project is a high-performance network server designed to serve individual lines from very large, immutable text files over a REST API. It is built with Python and the Flask framework and is designed to be efficient in both memory usage and request latency.

## Table of contents

- [How to Run](#how-to-run-the-system)
- [How it works](#how-does-your-system-work)
- [How will permform](#how-will-your-system-perform)
- [Dev Journey](#development-journey-challenges-and-solutions)
- [Documentation](#what-documentation-websites-papers-etc-did-you-consult)
- [Tools](#what-third-party-libraries-or-other-tools-does-the-system-use)
- [Development Duration](#how-long-did-you-spend-on-this-exercise)
- [What if unlimited time?](#if-you-had-unlimited-more-time-how-would-you-spend-it)
- [Critique](#if-you-were-to-critique-your-code-what-would-you-have-to-say-about-it)

## How to Run the System

Prerequisites

```
A Unix-like environment (Linux, macOS, or WSL on Windows).
Python 3.x and the venv module.
curl for testing the API.
```

- Step 1: Generate a Test File (Optional)

A utility script (generate_dummy.py) is provided to generate test files.

```
python3 generate_dummy.py <Num of lines>
python3 generate_dummy.py 1000000
```

- Step 2: Make the scripts executable

```
chmod +x build.sh run.sh
```

- Step 3: Build the Environment and Install Dependencies

```
./build.sh
```

- Step 4: Run the Server

```
./run.sh dummy.txt
```

- Step 5: Send request
  
```
curl -l http://127.0.0.1:8080/<line number>
curl -l http://127.0.0.1:8080/1
```

## How does your system work?

The system is built around one main idea: never load the full data file into memory. To get fast random access to any line, it creates an index first.

1. **On-Disk Binary Index:**
   Instead of keeping all line offsets in memory, the server writes them to a binary index file (e.g., dummy.txt.index). Each line’s start position is stored as an 8-byte integer. Memory use stays tiny no matter how big the file is.

2. **Memory-Mapped Index:**
   Workers don’t read the index from disk every time. They use mmap to map it into memory, which is much faster and lets the OS handle caching.

3. **Atomic Indexing on Startup:**
   The first time the server runs, it scans the file and builds the index in a temporary file (.tmp). Once done, it atomically renames it with os.replace. On future runs, it checks timestamps and skips rebuilding if the index is still valid, so startup is almost instant.

4. **Concurrency and Pre-loading:**
   We run the server with Gunicorn using --preload so indexing happens once in the master process. Workers then map the index file safely with the post_fork hook.

5. **Security:**

- **Path Validation:** The server makes sure the file is inside the working directory. Paths like `../../etc/passwd` are rejected.
- **Error Handling:** Bad requests (e.g., /lines/abc) get a `400`. Internal errors are logged and return a generic `500` without leaking stack traces.

## How will your system perform?

### With Large Files (1 GB, 10 GB, 100 GB)

The system scales really well with file size.

- **Memory Usage:** Constant and tiny. The data file and its full index never live in RAM, so a 100 GB file is no problem on a modest machine.
- **Startup Time:**
  - _First Run (cold cache):_ Scans the file once, so it depends on disk read speed.
  - _Later Runs (warm cache):_ Instant, because the index already exists.
- **Request Latency:** Almost constant. A request just looks up the offset in the memory-mapped index and does a single disk seek.

### With Many Users (100, 10,000, 1,000,000)

- **100 / 10,000 Users**: A single server with 4 Gunicorn workers can easily handle hundreds or thousands of requests per second. The limit is usually CPU or network, not the code.
- **1,000,000 Users:** No single machine can handle that. But the server is stateless, so scaling out is easy. Just run multiple instances behind a load balancer and point them to a shared filesystem (NFS, EFS, etc.) with the data and index.

## Development Journey: Challenges and Solutions

Building this server was an iterative process of encountering and solving several real-world engineering challenges.

1.  **Challenge: The Out-of-Memory Index:** My first design used an in-memory list of offsets. This failed on large files, as the index itself consumed gigabytes of RAM.

    - **Solution:** I re-architected the system to create a persistent **binary index file** on disk, keeping the server's memory footprint at a constant `O(1)`.

2.  **Challenge: Gunicorn's Worker Timeouts:** With an on-disk index, the long-running indexing task caused Gunicorn's workers to time out on startup, creating a crash-restart loop. There was also a race condition with multiple workers trying to build the index at once.

    - **Solution:** The definitive solution was to use Gunicorn's `--preload` flag. This instructs the master process to run the indexing logic **once**, _before_ any workers are forked. This elegantly solved both the race condition and the timeout issue.

3.  **Challenge: Gunicorn `AppImportError`:** My initial attempts to pass the filename to the application factory in the Gunicorn command failed with `AppImportError`.

    - **Solution:** I adopted the industry-standard approach of using **environment variables**. The `run.sh` script exports the filename to `DATA_FILE_PATH`, and the Python application reads this variable. This decouples the server from the script and is a more robust deployment pattern.

4.  **Challenge: Misleading Console Output (I/O Buffering):** Even with `--preload`, the console _looked_ like it was failing because Gunicorn's "Booting worker..." messages appeared before my application's "Rebuilding index..." messages. This made it impossible to know when the indexing was finished.

    - **Solution:** I replaced all startup `print()` statements with a proper `logging` setup that includes a `StreamHandler`. This provides immediate, unbuffered feedback to the console, offering crucial visibility into the startup process.

5.  **Challenge: Off-by-One and Boundary Check Bugs:** Early tests revealed that requests for out-of-bounds line numbers were returning empty `200 OK` responses.
    - **Solution:** This was traced back to a bug in the index-building logic, which was writing one extra offset to the index file. I replaced the complex implementation with a simpler, more robust `for line in file:` loop, which guaranteed the creation of a correct index and fixed the off-by-one error.

## What documentation, websites, papers, etc did you consult?

1. Official Documentation (main source of truth):

- **Python Docs:** os, struct, mmap, logging, and other core modules.
- **Flask Docs:** setup, routing, and using the g object.
- **Gunicorn Docs:** process model, worker management, --preload, and post_fork hooks.

2. Tutorials & Guides:

- **YouTube channels** like ArjanCodes ([link](https://www.youtube.com/watch?v=8a6dWenA8Hs)).
- Blogs like _Real Python_ and _GeeksForGeeks_ for practical examples and implementation tips.

3. Community Q&A:

- **Stack Overflow** for troubleshooting specific errors, especially with Gunicorn and shell scripts.
- **Reddit** communities like _r/learnpython, r/flask, r/Python_ for advice and best practices.

4. AI Tools:

- Used AI assistants to scaffold boilerplate code (like generate_dummy.py), suggest refactors, and debug tricky issues like I/O buffering.

## What third-party libraries or other tools does the system use?

- **Flask:** A lightweight Python web framework.
- **Gunicorn:** A production-ready WSGI server for Python.

## How long did you spend on this exercise?

**Around 8 hours total:** designing, implementing, testing with large files, debugging concurrency issues (like Gunicorn timeouts), and writing the docs.

## If you had unlimited more time, how would you spend it?

With more time, I’d focus on making the system more robust and production-ready:

1. **Containerization with Docker:** Create a Dockerfile so the app runs consistently anywhere.
2. **Automated Testing:** Build a pytest suite with unit tests for indexing and integration tests for the API.
3. **API Docs:** Use Flask-Swagger-UI to generate interactive docs so other developers can easily understand and use the API.
4. **Health Check Endpoint:** Add GET /health returning 200 OK for monitoring and load balancers.
5. **Config via Environment Variables:** Refactor run.sh to get port, worker count, etc., from env vars following the Twelve-Factor App approach.
6. **Observability & Structured Logging:** Switch logs to JSON for easy parsing and integration with centralized logging (ELK Stack), dashboards, and alerts.

## If you were to critique your code, what would you have to say about it?

- **Lack of Automated Tests:** No test suite yet. Manual testing works, but proper unit and integration tests would improve reliability and maintainability.
- **API Design Choice:** Returning HTTP 413 for out-of-bounds lines is non-standard. 404 Not Found would be more conventional.
- **Logging Configuration:** Logging works but is hardcoded. In production, it should be configurable via environment variables for level and format.


