"""Website scraper using requests + BeautifulSoup."""

import re
import time
from urllib.parse import urljoin, urlparse

import requests
import urllib3
from bs4 import BeautifulSoup

# Disable SSL warnings for sites with cert issues (common on macOS)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from config import SCRAPE_TIMEOUT, USER_AGENT, MAX_CONTENT_LENGTH, ADDITIONAL_PAGES
from models import ScrapedWebsite


def normalize_url(url: str) -> str:
    url = url.strip()
    if not url:
        return ""
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    return url


def _fetch_page(url: str) -> tuple[str, bool]:
    """Fetch a single page. Returns (html, success)."""
    try:
        resp = requests.get(
            url,
            timeout=SCRAPE_TIMEOUT,
            headers={"User-Agent": USER_AGENT},
            allow_redirects=True,
            verify=False,  # Handle SSL cert issues gracefully
        )
        resp.raise_for_status()
        return resp.text, True
    except requests.exceptions.RequestException:
        return "", False


def _extract_content(html: str) -> dict:
    """Extract meaningful content from HTML."""
    soup = BeautifulSoup(html, "html.parser")

    # Remove noise elements
    for tag in soup(["script", "style", "nav", "footer", "header", "noscript", "iframe"]):
        tag.decompose()

    # Title
    title = ""
    if soup.title and soup.title.string:
        title = soup.title.string.strip()

    # Meta description
    meta_desc = ""
    meta_tag = soup.find("meta", attrs={"name": "description"})
    if meta_tag and meta_tag.get("content"):
        meta_desc = meta_tag["content"].strip()

    # Headings
    headings = []
    for tag in soup.find_all(["h1", "h2", "h3"]):
        text = tag.get_text(strip=True)
        if text and len(text) > 2:
            headings.append(text)

    # Body text
    body = soup.get_text(separator=" ", strip=True)
    # Clean up excessive whitespace
    body = re.sub(r"\s+", " ", body).strip()

    # Detect tech hints
    tech_hints = []
    full_html = str(soup)
    tech_patterns = {
        "Shopify": r"shopify|cdn\.shopify",
        "WordPress": r"wp-content|wordpress",
        "HubSpot": r"hubspot|hs-scripts",
        "Salesforce": r"salesforce|pardot",
        "Intercom": r"intercom",
        "Zendesk": r"zendesk",
        "Google Analytics": r"google-analytics|gtag|googletagmanager",
        "Mailchimp": r"mailchimp",
        "Wix": r"wix\.com|wixsite",
        "Squarespace": r"squarespace",
    }
    for tech, pattern in tech_patterns.items():
        if re.search(pattern, full_html, re.IGNORECASE):
            tech_hints.append(tech)

    return {
        "title": title,
        "meta_description": meta_desc,
        "headings": headings[:20],
        "body": body,
        "tech_hints": tech_hints,
    }


def scrape_website(url: str) -> ScrapedWebsite:
    """Scrape a website and return structured content."""
    url = normalize_url(url)
    if not url:
        return ScrapedWebsite(url="", success=False, error="Empty URL")

    # Fetch homepage
    html, success = _fetch_page(url)
    if not success:
        return ScrapedWebsite(url=url, success=False, error=f"Failed to fetch {url}")

    content = _extract_content(html)
    pages_scraped = 1
    all_text = content["body"]

    # Try additional pages
    base_url = f"{urlparse(url).scheme}://{urlparse(url).netloc}"
    for page_path in ADDITIONAL_PAGES:
        page_url = urljoin(base_url, page_path)
        page_html, page_ok = _fetch_page(page_url)
        if page_ok and len(page_html) > 500:
            page_content = _extract_content(page_html)
            if page_content["body"] and len(page_content["body"]) > 100:
                all_text += "\n\n" + page_content["body"]
                content["headings"].extend(page_content["headings"])
                pages_scraped += 1
        time.sleep(0.3)  # Small delay between pages on same site

    # Truncate
    if len(all_text) > MAX_CONTENT_LENGTH:
        all_text = all_text[:MAX_CONTENT_LENGTH]

    return ScrapedWebsite(
        url=url,
        title=content["title"],
        meta_description=content["meta_description"],
        headings=content["headings"][:30],
        main_text=all_text,
        tech_hints=content["tech_hints"],
        pages_scraped=pages_scraped,
        success=True,
    )


def scrape_all(urls: list[str], delay: float = 1.0, progress_callback=None) -> list[ScrapedWebsite]:
    """Scrape multiple websites with delay between requests."""
    results = []
    for i, url in enumerate(urls):
        result = scrape_website(url)
        results.append(result)
        if progress_callback:
            progress_callback(i + 1, len(urls), url)
        if i < len(urls) - 1:
            time.sleep(delay)
    return results
