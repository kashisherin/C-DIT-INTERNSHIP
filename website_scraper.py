
import time
import re
import hashlib
from pathlib import Path
from urllib.parse import (
    urljoin,
    urlparse,
    urlunparse,
    urldefrag,
)

import requests
from bs4 import BeautifulSoup
from markdownify import markdownify


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
DOCUMENTS_DIR = BASE_DIR / "documents"

MAX_PAGES_PER_SITE = 20
REQUEST_TIMEOUT = 30
REQUEST_DELAY = 0.5

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/131.0.0.0 Safari/537.36"
)

WEBSITES = {
    "kerala_cm": {
        "url": "https://keralacm.gov.in/",
        "output": "kerala_cm.md",
    },
    "cmo_kerala": {
        "url": "https://cmo.kerala.gov.in/index-en.html",
        "output": "cmo_kerala.md",
    },
}


# These pages returned 404 during your previous crawl.
# Keep them excluded unless you later confirm they work.
SKIP_URLS = {
    "https://keralacm.gov.in/6684",
    "https://keralacm.gov.in/6700",
    "https://keralacm.gov.in/6702",
    "https://keralacm.gov.in/6704",
    "https://keralacm.gov.in/6707",
    "https://keralacm.gov.in/5699",
}


# ============================================================
# SESSION
# ============================================================

session = requests.Session()

session.headers.update({
    "User-Agent": USER_AGENT,
    "Accept": (
        "text/html,application/xhtml+xml,"
        "application/xml;q=0.9,*/*;q=0.8"
    ),
    "Accept-Language": "ml,en;q=0.9",
})


# ============================================================
# URL NORMALIZATION
# ============================================================

def normalize_url(url):
    """
    Normalize URLs so equivalent links are treated as one page.

    Examples:
    / and no path -> /
    /about/ -> /about
    Remove fragments.
    Preserve query parameters.
    """

    url, _ = urldefrag(url)

    parsed = urlparse(url)

    scheme = parsed.scheme.lower()
    netloc = parsed.netloc.lower()

    path = parsed.path or "/"

    if path != "/":
        path = path.rstrip("/")

    # Remove default ports
    if netloc.endswith(":443") and scheme == "https":
        netloc = netloc[:-4]

    if netloc.endswith(":80") and scheme == "http":
        netloc = netloc[:-3]

    normalized = urlunparse((
        scheme,
        netloc,
        path,
        "",
        parsed.query,
        "",
    ))

    return normalized


# ============================================================
# URL VALIDATION
# ============================================================

def is_internal_url(url, base_url):
    """
    Allow only links belonging to the current website.
    """

    parsed_url = urlparse(url)
    parsed_base = urlparse(base_url)

    if parsed_url.scheme not in ("http", "https"):
        return False

    if parsed_url.netloc.lower() != parsed_base.netloc.lower():
        return False

    return True


def should_skip_url(url):
    """
    Skip known broken pages and non-HTML files.
    """

    url = normalize_url(url)

    if url in SKIP_URLS:
        return True

    parsed = urlparse(url)

    path = parsed.path.lower()

    excluded_extensions = (
        ".pdf",
        ".jpg",
        ".jpeg",
        ".png",
        ".gif",
        ".webp",
        ".svg",
        ".mp4",
        ".mp3",
        ".zip",
        ".doc",
        ".docx",
        ".xls",
        ".xlsx",
        ".ppt",
        ".pptx",
        ".css",
        ".js",
        ".xml",
        ".json",
    )

    if path.endswith(excluded_extensions):
        return True

    # Avoid crawling form submission and login pages.
    excluded_paths = (
        "/login",
        "/logout",
        "/register",
        "/submit",
        "/complaint",
        "/grievance",
    )

    if any(
        excluded in path
        for excluded in excluded_paths
    ):
        return True

    return False


# ============================================================
# TEXT CLEANING
# ============================================================

def remove_duplicate_lines(text):
    """
    Remove repeated lines while preserving their original order.
    """

    lines = text.splitlines()

    seen = set()
    result = []

    for line in lines:
        cleaned = line.strip()

        if not cleaned:
            result.append("")
            continue

        normalized = re.sub(
            r"\s+",
            " ",
            cleaned
        ).casefold()

        if normalized in seen:
            continue

        seen.add(normalized)

        result.append(cleaned)

    return "\n".join(result)


def remove_duplicate_paragraphs(text):
    """
    Remove repeated paragraphs.
    """

    paragraphs = re.split(
        r"\n\s*\n",
        text
    )

    seen = set()
    result = []

    for paragraph in paragraphs:
        paragraph = paragraph.strip()

        if not paragraph:
            continue

        normalized = re.sub(
            r"\s+",
            " ",
            paragraph
        ).casefold()

        if normalized in seen:
            continue

        seen.add(normalized)

        result.append(paragraph)

    return "\n\n".join(result)


def clean_text(text):
    """
    Normalize whitespace without damaging Malayalam characters.
    """

    text = text.replace("\r\n", "\n")
    text = text.replace("\r", "\n")

    text = re.sub(
        r"[ \t]+",
        " ",
        text
    )

    text = re.sub(
        r"\n{3,}",
        "\n\n",
        text
    )

    return text.strip()


# ============================================================
# ENCODING HANDLING
# ============================================================

def repair_mojibake(text):
    """
    Repair common UTF-8 Malayalam text that was incorrectly
    decoded using Latin-1 or Windows-1252.

    Only attempts repair when common mojibake indicators exist.
    """

    indicators = (
        "à´",
        "àµ",
        "â",
        "Ã",
    )

    if not any(
        indicator in text
        for indicator in indicators
    ):
        return text

    # First try Latin-1 repair.
    try:
        repaired = text.encode(
            "latin-1"
        ).decode("utf-8")

        if repaired != text:
            return repaired

    except (
        UnicodeEncodeError,
        UnicodeDecodeError,
    ):
        pass

    # Then try Windows-1252 repair.
    try:
        repaired = text.encode(
            "cp1252"
        ).decode("utf-8")

        if repaired != text:
            return repaired

    except (
        UnicodeEncodeError,
        UnicodeDecodeError,
    ):
        pass

    return text


def decode_response(response):
    """
    Decode HTML using the response encoding and BeautifulSoup.

    The response bytes are parsed directly so BeautifulSoup
    can inspect HTML charset declarations.

    Common Malayalam mojibake is repaired afterward.
    """

    response.encoding = (
        response.apparent_encoding
        or "utf-8"
    )

    soup = BeautifulSoup(
        response.content,
        "html.parser"
    )

    text = soup.decode()

    text = repair_mojibake(text)

    return text


# ============================================================
# HTML EXTRACTION
# ============================================================

def extract_page_content(html, page_url):
    """
    Extract meaningful text and links from a webpage.

    Returns:
        title
        markdown content
        internal links
    """

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    # Remove unwanted elements.
    unwanted_tags = [
        "script",
        "style",
        "noscript",
        "iframe",
        "svg",
        "canvas",
        "video",
        "audio",
        "form",
        "nav",
        "footer",
        "header",
        "aside",
    ]

    for tag in soup.find_all(unwanted_tags):
        tag.decompose()

    # Remove hidden elements.
    for tag in soup.find_all(
        style=True
    ):
        style = tag.get("style", "").lower()

        if (
            "display:none" in style
            or "visibility:hidden" in style
        ):
            tag.decompose()

    # Remove empty elements.
    for tag in soup.find_all(
        ["div", "section", "article"]
    ):
        if not tag.get_text(
            strip=True
        ) and not tag.find("img"):
            tag.decompose()

    # Extract page title.
    title = ""

    if soup.title:
        title = soup.title.get_text(
            " ",
            strip=True
        )

    if not title:
        title = "Untitled Page"

    # Collect internal links before converting content.
    internal_links = []

    for anchor in soup.find_all(
        "a",
        href=True
    ):
        href = anchor.get("href", "").strip()

        if not href:
            continue

        if href.startswith((
            "mailto:",
            "tel:",
            "javascript:",
            "data:",
        )):
            continue

        absolute_url = urljoin(
            page_url,
            href
        )

        absolute_url = normalize_url(
            absolute_url
        )

        if not is_internal_url(
            absolute_url,
            page_url
        ):
            continue

        if should_skip_url(
            absolute_url
        ):
            continue

        internal_links.append(
            absolute_url
        )

    # Select the main content area.
    main_content = (
        soup.find("main")
        or soup.find("article")
        or soup.find(id="content")
        or soup.find(
            class_=re.compile(
                r"content|main|article",
                re.I
            )
        )
        or soup.body
        or soup
    )

    # Convert HTML to Markdown.
    markdown_text = markdownify(
        str(main_content),
        heading_style="ATX",
        bullets="-",
    )

    markdown_text = clean_text(
        markdown_text
    )

    # Remove duplicate lines and paragraphs.
    markdown_text = remove_duplicate_lines(
        markdown_text
    )

    markdown_text = remove_duplicate_paragraphs(
        markdown_text
    )

    return (
        title,
        markdown_text,
        list(dict.fromkeys(internal_links)),
    )


# ============================================================
# PAGE FETCHING
# ============================================================

def fetch_page(url):
    """
    Fetch a webpage and return its decoded HTML.

    Returns None for failed requests.
    """

    try:
        response = session.get(
            url,
            timeout=REQUEST_TIMEOUT,
        )

        response.raise_for_status()

        content_type = response.headers.get(
            "Content-Type",
            ""
        ).lower()

        if (
            "text/html" not in content_type
            and "application/xhtml+xml"
            not in content_type
        ):
            print(
                f"Skipped non-HTML page: {url}"
            )

            return None

        html = decode_response(
            response
        )

        return html

    except requests.RequestException as error:
        print(
            f"Could not fetch {url}"
        )

        print(
            f"Reason: {error}"
        )

        return None

    except Exception as error:
        print(
            f"Unexpected error fetching {url}"
        )

        print(
            f"Reason: {error}"
        )

        return None


# ============================================================
# CONTENT VALIDATION
# ============================================================

def has_meaningful_content(text):
    """
    Reject empty pages and obvious placeholder content.
    """

    if not text:
        return False

    normalized = text.casefold()

    placeholders = [
        "lorem ipsum",
        "join us and achieve business goal",
        "no posts found",
    ]

    if all(
        placeholder in normalized
        for placeholder in placeholders
    ):
        return False

    # Remove Markdown punctuation and whitespace.
    plain_text = re.sub(
        r"[#*\-_\[\]()!>`]",
        " ",
        text
    )

    plain_text = re.sub(
        r"\s+",
        " ",
        plain_text
    ).strip()

    # Reject pages containing almost no text.
    if len(plain_text) < 80:
        return False

    return True


# ============================================================
# WEBSITE SCRAPER
# ============================================================

def scrape_website(
    website_name,
    website_config,
):
    """
    Crawl one website and save extracted content.

    MAX_PAGES_PER_SITE applies to successful pages.
    Failed URLs do not consume the successful-page limit.
    """

    base_url = normalize_url(
        website_config["url"]
    )

    output_file = (
        DOCUMENTS_DIR
        / website_config["output"]
    )

    DOCUMENTS_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    print("\n" + "=" * 60)

    print(
        f"Starting website: {base_url}"
    )

    print("=" * 60)

    pending = [base_url]

    visited = set()

    pages_saved = 0
    pages_failed = 0

    # Track page content hashes to avoid repeated content.
    content_hashes = set()

    with open(
        output_file,
        "w",
        encoding="utf-8",
    ) as file:

        file.write(
            f"# {website_name.replace('_', ' ').title()}\n\n"
        )

        file.write(
            f"Source website: {base_url}\n\n"
        )

        while (
            pending
            and pages_saved < MAX_PAGES_PER_SITE
        ):

            url = normalize_url(
                pending.pop(0)
            )

            # Skip previously visited pages.
            if url in visited:
                continue

            # Skip known broken and non-HTML URLs.
            if should_skip_url(url):
                visited.add(url)

                print(
                    f"Skipped URL: {url}"
                )

                continue

            # Mark before fetching to prevent retry loops.
            visited.add(url)

            print(
                f"\nFetching "
                f"({pages_saved + 1}/"
                f"{MAX_PAGES_PER_SITE}): {url}"
            )

            html = fetch_page(
                url
            )

            if html is None:
                pages_failed += 1

                time.sleep(
                    REQUEST_DELAY
                )

                continue

            title, content, links = (
                extract_page_content(
                    html,
                    url
                )
            )

            # Reject empty or low-quality pages.
            if not has_meaningful_content(
                content
            ):
                print(
                    f"Skipped empty/placeholder page: {url}"
                )

                pages_failed += 1

                time.sleep(
                    REQUEST_DELAY
                )

                continue

            # Detect identical content across different URLs.
            content_hash = hashlib.sha256(
                content.encode("utf-8")
            ).hexdigest()

            if content_hash in content_hashes:
                print(
                    f"Skipped duplicate content: {url}"
                )

            else:
                content_hashes.add(
                    content_hash
                )

                file.write(
                    f"\n\n# Page: {title}\n\n"
                )

                file.write(
                    f"Source URL: {url}\n\n"
                )

                file.write(
                    content
                )

                file.write(
                    "\n\n---\n"
                )

                file.flush()

                pages_saved += 1

                print(
                    f"Saved page: {title}"
                )

            # Add new internal links.
            for link in links:

                link = normalize_url(
                    link
                )

                if link in visited:
                    continue

                if link in pending:
                    continue

                if should_skip_url(link):
                    continue

                if not is_internal_url(
                    link,
                    base_url
                ):
                    continue

                pending.append(
                    link
                )

            time.sleep(
                REQUEST_DELAY
            )

    print("\n" + "=" * 60)

    print(
        f"Website completed: {website_name}"
    )

    print(
        f"Pages visited: {len(visited)}"
    )

    print(
        f"Pages saved: {pages_saved}"
    )

    print(
        f"Pages failed/skipped: {pages_failed}"
    )

    print(
        f"Output file: {output_file}"
    )

    print("=" * 60)

    return {
        "website": website_name,
        "visited": len(visited),
        "saved": pages_saved,
        "failed": pages_failed,
        "output": str(output_file),
    }


# ============================================================
# MAIN
# ============================================================

def main():

    DOCUMENTS_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    results = []

    for website_name, website_config in (
        WEBSITES.items()
    ):

        result = scrape_website(
            website_name,
            website_config
        )

        results.append(
            result
        )

    print("\n" + "=" * 60)

    print(
        "WEBSITE SCRAPING SUMMARY"
    )

    print("=" * 60)

    total_saved = 0
    total_failed = 0

    for result in results:

        print(
            f"\nWebsite: {result['website']}"
        )

        print(
            f"Visited: {result['visited']}"
        )

        print(
            f"Saved: {result['saved']}"
        )

        print(
            f"Failed/skipped: {result['failed']}"
        )

        total_saved += result["saved"]

        total_failed += result["failed"]

    print("\n" + "-" * 60)

    print(
        f"Total successfully saved pages: {total_saved}"
    )

    print(
        f"Total failed/skipped pages: {total_failed}"
    )

    print(
        f"Documents directory: {DOCUMENTS_DIR}"
    )

    print("-" * 60)

    print(
        "\nWebsite scraping completed."
    )


if __name__ == "__main__":
    main()
