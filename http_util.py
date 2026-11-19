"""Shared read-only GitHub JSON fetch with bounded retries."""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request


def get_json(url: str, *, user_agent: str, timeout: int = 25, attempts: int = 3):
    """Return ``(data, latency_ms)`` of the successful attempt.

    Retries only network errors, timeouts, 408, 429 and 5xx with exponential
    backoff; other HTTP errors and the final failure are raised unchanged.
    """
    headers = {"Accept": "application/vnd.github+json", "User-Agent": user_agent}
    if os.environ.get("GITHUB_TOKEN"):
        headers["Authorization"] = f"Bearer {os.environ['GITHUB_TOKEN']}"
    for attempt in range(attempts):
        started = time.perf_counter()
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=timeout) as response:
                data = json.load(response)
            return data, round(1000 * (time.perf_counter() - started), 1)
        except (urllib.error.URLError, TimeoutError) as exc:
            if isinstance(exc, urllib.error.HTTPError) and exc.code < 500 and exc.code not in (408, 429):
                raise
            if attempt == attempts - 1:
                raise
            time.sleep(2 ** attempt)
