# Gunicorn config: use post_fork to initialize per-worker mmap/FD
import logging

def post_fork(server, worker):
    try:
        # import here so module state is the same as gunicorn-loaded app
        import app
        app.init_worker()
        server.log.info(f"post_fork: initialized worker pid={worker.pid}")
    except Exception as e:
        server.log.error(f"post_fork: failed to init worker: {e}")