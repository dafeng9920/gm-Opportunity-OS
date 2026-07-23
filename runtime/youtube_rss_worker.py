"""Standalone public YouTube RSS worker; Scrapling is imported outside Opportunity OS Core."""
from __future__ import annotations
import json, sys
from urllib.parse import urlparse
from scrapling.fetchers import Fetcher
def main() -> None:
    request = json.loads(sys.stdin.read())
    target = request["target"]
    parsed = urlparse(target)
    if parsed.scheme != "https" or parsed.hostname != "www.youtube.com" or parsed.path != "/feeds/videos.xml":
        raise ValueError("worker only permits public YouTube channel RSS")
    response = Fetcher.get(target)
    body = response.body.decode("utf-8", errors="replace") if isinstance(response.body, bytes) else response.body
    print(json.dumps({"body": body}))
if __name__ == "__main__": main()
