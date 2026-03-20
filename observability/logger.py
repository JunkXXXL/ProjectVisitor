import json
import logging
import os
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        extra = getattr(record, "extra_fields", None)
        if isinstance(extra, dict):
            payload.update(extra)

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload, ensure_ascii=False)


_LOGGER_CACHE: dict[str, logging.Logger] = {}


def get_metrics_logger(name: str = "metrics") -> logging.Logger:
    logger_name = f"project_visitor.{name}"
    if logger_name in _LOGGER_CACHE:
        return _LOGGER_CACHE[logger_name]

    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.INFO)
    logger.propagate = False

    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(JsonFormatter())
        logger.addHandler(handler)

    _LOGGER_CACHE[logger_name] = logger
    return logger


def log_event(logger: logging.Logger, event: str, **fields: Any) -> None:
    logger.info(event, extra={"extra_fields": {"event": event, **fields}})


@contextmanager
def measure_time(logger: logging.Logger, event: str, **fields: Any):
    started_at = time.perf_counter()
    try:
        yield
    finally:
        duration_ms = round((time.perf_counter() - started_at) * 1000, 3)
        log_event(logger, event, duration_ms=duration_ms, **fields)


def get_cpu_load_percent() -> float | None:
    try:
        import psutil  # type: ignore

        return round(psutil.cpu_percent(interval=None), 2)
    except Exception:
        if hasattr(os, "getloadavg"):
            try:
                load_avg = os.getloadavg()[0]
                cpu_count = os.cpu_count() or 1
                return round((load_avg / cpu_count) * 100, 2)
            except OSError:
                return None
        return None
