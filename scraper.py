import hashlib
import os
import re
import sys
from urllib.parse import urlparse
import json

import requests
from bs4 import BeautifulSoup
from markdownify import markdownify

DOCS_FOLDER = "documents" 
#project name and email
HEADERS={
    "User-agent" : "RAGStudentLab/1.0 (educational project; ggauthamsureshh@gmail.com)"
}

#Junk Tags
JUNK_TAGS = ["script" , "style" , "noscript" , "nav" , "header" , "header" , "footer" , 
             "aside" , "form" , "iframe" , "svg" , "button" , "img"]
JUNK_SELECTORS = [
    ".mw-editsection", "sup.reference", ".reflist", ".navbox", ".hatnote",
    ".mw-references-wrap", "#toc", ".noprint", ".metadata", ".sidebar",".printfooter",
]

#MAIN TEXT
CONTENT_SELECTORS = ["#mw-content-text" , "main" , "#main-content" , "article"]

#download the page
def download(url):
    response = requests.get(url , headers = HEADERS, timeout=30)
    response.raise_for_status()
    response.encoding = response.apparent_encoding
    return response.text

#Useful part of HTML
def extract_content(html):
    soup = BeautifulSoup(html, "html.parser")
    h1 = soup.find("h1")
    if h1:
        title = h1.get_text(strip=True)
    else:
        title = soup.title.string if soup.title else "Untitled"

    for tag in soup(JUNK_TAGS):
        tag.decompose()
    for selector in JUNK_SELECTORS:
        for tag in soup.select(selector):
            tag.decompose()
    content = soup.body or soup
    for selector in CONTENT_SELECTORS:
        found = soup.select_one(selector)
        # skip empty matches (some sites put the id on an empty anchor)
        if found and len(found.get_text(strip=True)) > 200:
            content = found
            break
    return title.strip(), content

#HTML to clean Markdown
def to_markdown(content):
    text = markdownify(str(content), heading_style="ATX", strip=["a"])
    text = re.sub(r"\n{3,}", "\n\n", text)       # no more than one blank line
    text = re.sub(r"[ \t]+\n", "\n", text)        # no spaces at line ends
    return text.strip()

# Save it in the documents folder
def make_filename(url, title):
    name = re.sub(
        r"[^a-z0-9]+",
        "_",
        title.lower()
    ).strip("_")[:50]

    if not name:
        name = re.sub(
            r"[^a-z0-9]+",
            "_",
            urlparse(url).netloc.lower()
        ).strip("_")

    short_id = hashlib.md5(url.encode()).hexdigest()[:6]

    return f"web_{name}_{short_id}.json"

def fetch_and_save(url):
    html = download(url)

    title, content = extract_content(html)

    markdown_content = to_markdown(content)

    os.makedirs(DOCS_FOLDER, exist_ok=True)

    filename = make_filename(url, title)

    data = {
        "title": title,
        "source": url,
        "language": "English and Malayalam",
        "content": markdown_content
    }

    output_path = os.path.join(DOCS_FOLDER, filename)

    with open(output_path, "w", encoding="utf-8") as file:
        json.dump(
            data,
            file,
            ensure_ascii=False,
            indent=4
        )

    return {
        "url": url,
        "title": title,
        "file": filename,
        "characters": len(markdown_content)
    }

# python scraper.py 
if __name__ == "__main__":
    urls_file = sys.argv[1] if len(sys.argv) > 1 else "urls.txt"
    with open(urls_file, encoding="utf-8") as file:
        urls = [line.strip() for line in file
                if line.strip() and not line.startswith("#")]
    for url in urls:
        try:
            result = fetch_and_save(url)
            print(f"Saved {result['file']} ({result['characters']} characters)")
        except Exception as error:
            print(f"Failed {url}: {error}")