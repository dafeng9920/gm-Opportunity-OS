"""Standalone process entry point. This module deliberately imports Scrapling outside Core."""
from __future__ import annotations

import json
import sys
from urllib.parse import urlparse

from scrapling.fetchers import Fetcher


def main() -> None:
    request = json.loads(sys.stdin.read())
    target = request["target"]
    parsed = urlparse(target)
    if parsed.scheme != "https" or parsed.hostname != "example.com":
        raise ValueError("experimental worker only permits https://example.com")
    response = Fetcher.get(target)
    body = response.body
    if isinstance(body, bytes):
        body = body.decode("utf-8", errors="replace")
    print(json.dumps({"body": body}))


if __name__ == "__main__":
    main()
