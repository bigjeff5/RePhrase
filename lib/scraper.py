#!/usr/bin/env python3
import argparse
import time
import json
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup
from pathlib import Path

DEFAULT_USER_AGENT = "MyChapterArchiver/1.0 (+contact@example.com)"

def fetch_page(session, url, timeout=15):
    """Fetch a page and return (response_text, final_url) or (None, None) on error."""
    try:
        resp = session.get(url, timeout=timeout)
        resp.raise_for_status()
        return resp.text, resp.url  # resp.url = final URL after redirects
    except requests.RequestException as e:
        print(f"[ERROR] Failed to fetch {url}: {e}")
        return None, None


def parse_chapter_entry(html, url):
    """
    Extract the chapter content and next-chapter link from the HTML.
    Returns: (content_text, next_url_relative_or_none)
    """
    soup = BeautifulSoup(html, "html.parser")

    # Grab main content
    content_div = soup.find("div", id="chapter-content")
    if content_div is None:
        print(f"[WARN] No #chapter-content div found for {url}")
        content_text = ""
    else:
        content_text = content_div.get_text("\n\t", strip=False)

    # Find the "next" chapter link – per your example: <a id="next_chapter" ...>
    next_link = soup.find("a", id="next_chap")
    next_href = next_link.get("href") if next_link else None

    return content_text, next_href


def slugify_from_url(url):
    """
    Create a simple filename slug from a URL path.
    Example: https://mywebpage.net/daily-chapter/2025-6-15.html -> 2025-6-15.html
    """
    path = urlparse(url).path
    if not path or path == "/":
        return "index.html"

    name = path.rstrip("/").split("/")[-1]
    # basic sanitization
    for ch in ["?", "&", "=", ":", "#"]:
        name = name.replace(ch, "_")
    return name or "page.html"


def save_entry(output_dir, url, content_text, save_metadata=False):
    """
    Save the chapter entry as a text file plus optional metadata JSON.
    """
    raw_dir = Path(f"{output_dir}")

    if not raw_dir.exists():
        raw_dir.mkdir()
    slug = slugify_from_url(url)
    base_name = Path(slug).stem or "page"

    txt_path = raw_dir.joinpath(f"{base_name}.txt")
    meta_path = output_dir.joinpath(f"{base_name}.json")

    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(content_text)

    data = {
        "url": url,
        "text_file": txt_path,
    }
    if save_metadata:
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"[INFO] Saved {url} -> {txt_path}")

def load_state(output_dir):
    STATE_FILE = Path(f"{output_dir}/state.json")
    if not STATE_FILE.exists():
        return set(), None
    data = json.loads(STATE_FILE.read_text())
    visited = set(data.get("visited", []))
    next_url = data.get("next_url")
    return visited, next_url

def save_state(visited, next_url, output_dir):
    STATE_FILE = Path(f"{output_dir}/state.json")
    data = {
        "visited": list(visited),
        "next_url": next_url
    }
    STATE_FILE.write_text(json.dumps(data, indent=2))

def crawl(start_url, delay, max_requests, output_dir, base_url=None, save_metadata=False):
    """
    Crawl chapter entries starting from start_url, following the `next_chapter` link,
    up to max_requests pages, waiting `delay` seconds between each request.
    """
    session = requests.Session()
    session.headers.update({"User-Agent": DEFAULT_USER_AGENT})

    if base_url is None:
        # Default base to the scheme+netloc of start_url
        parsed = urlparse(start_url)
        base_url = f"{parsed.scheme}://{parsed.netloc}"


    visited, current_url = load_state(output_dir)
    if not current_url:
        current_url = start_url
    requests_made = 0


    while current_url and requests_made < max_requests:
        if current_url in visited:
            print(f"[WARN] Already visited {current_url}, stopping to avoid loop.")
            break

        visited.add(current_url)
        print(f"[INFO] Fetching ({requests_made+1}/{max_requests}): {current_url}")

        html, final_url = fetch_page(session, current_url)
        if html is None:
            print("[ERROR] Stopping due to fetch error.")
            break

        content_text, next_href = parse_chapter_entry(html, final_url)
        save_entry(output_dir, final_url, content_text, save_metadata)

        requests_made += 1

        # Determine next URL to visit
        if not next_href:
            print("[INFO] No next_chapter link found; stopping crawl.")
            break

        next_url = urljoin(base_url, next_href)

        # Politeness delay
        if requests_made < max_requests:
            print(f"[INFO] Sleeping for {delay} seconds before next request...")
            time.sleep(delay)

        current_url = next_url

    save_state(visited, current_url, output_dir)

    print(f"[INFO] Crawl finished. Pages fetched: {requests_made}")


def main():
    parser = argparse.ArgumentParser(
        description="Simple chapter archiver that follows next_chapter links."
    )
    parser.add_argument(
        "start_url",
        help="URL of the first chapter entry to start scraping from "
             "(e.g., https://mywebpage.net/daily-chapter/2025-6-16.html)",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=5.0,
        help="Delay in seconds between requests (default: 5.0)",
    )
    parser.add_argument(
        "--max-requests",
        type=int,
        default=100,
        help="Maximum number of pages/requests to fetch (default: 100)",
    )
    parser.add_argument(
        "--output-dir",
        default="chapter_archive",
        help="Directory where archived files will be saved (default: chapter_archive)",
    )
    parser.add_argument(
        "--base-url",
        default=None,
        help="Base URL for resolving relative links (default: derived from start_url)",
    )

    parser.add_argument(
        "--save-metadata",
        default=False,
        help="Store metadata for html in JSON file along with text (default: False)",
    )
    args = parser.parse_args()

    if args.max_requests <= 0:
        parser.error("--max-requests must be a positive integer.")
    if args.delay < 0:
        parser.error("--delay must be non-negative.")

    crawl(
        start_url=args.start_url,
        delay=args.delay,
        max_requests=args.max_requests,
        output_dir=args.output_dir,
        base_url=args.base_url,
        save_metadata=args.save_metadata,
    )


if __name__ == "__main__":
    main()
