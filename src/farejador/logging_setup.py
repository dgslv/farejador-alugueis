"""Single logging configuration: the terminal in development, app.log in the packaged app."""

import logging
import sys
from pathlib import Path
from typing import Optional

FORMAT = "%(asctime)s %(levelname)-7s %(name)s: %(message)s"
DATEFMT = "%Y-%m-%d %H:%M:%S"


def setup_logging(log_file: Optional[Path] = None, level: int = logging.INFO) -> None:
    """Call once from the entry point. With `log_file`, everything (including the
    stdout/stderr of libraries that only print) goes to the file."""
    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(level)
    if log_file is None:
        handler: logging.Handler = logging.StreamHandler(sys.stderr)
    else:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        handler = logging.FileHandler(log_file, encoding="utf-8")
        stream = open(log_file, "a", buffering=1, encoding="utf-8")  # noqa: SIM115 (lives as long as the process)
        sys.stdout = sys.stderr = stream
    handler.setFormatter(logging.Formatter(FORMAT, DATEFMT))
    root.addHandler(handler)
    logging.getLogger("werkzeug").setLevel(logging.WARNING)  # Flask logs every request at INFO
