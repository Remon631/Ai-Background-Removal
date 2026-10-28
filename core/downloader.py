"""Image downloader module supporting direct image URLs and web pages with embedded images."""

import io
import urllib.parse
from typing import Optional, Tuple
from PIL import Image
from PySide6.QtCore import QThread, Signal

# Realistic User-Agent to avoid scraping blocks from CDNs and image hosts
DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


def extract_image_url_from_html(html_text: str, base_url: str) -> Optional[str]:
    """Parse HTML and extract candidate image URLs (OpenGraph, Twitter card, or large img)."""
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html_text, "html.parser")

    # 1. OpenGraph image
    og_img = soup.find("meta", property="og:image")
    if og_img and og_img.get("content"):
        return urllib.parse.urljoin(base_url, og_img["content"])

    # 2. Twitter card image
    tw_img = soup.find("meta", attrs={"name": "twitter:image"}) or soup.find(
        "meta", property="twitter:image"
    )
    if tw_img and tw_img.get("content"):
        return urllib.parse.urljoin(base_url, tw_img["content"])

    # 3. link rel=image_src
    link_img = soup.find("link", rel=lambda r: r and "image_src" in r.lower())
    if link_img and link_img.get("href"):
        return urllib.parse.urljoin(base_url, link_img["href"])

    # 4. Search <img> tags, filtering out icons and 1x1 tracking pixels
    for img in soup.find_all("img"):
        src = (
            img.get("src")
            or img.get("data-src")
            or img.get("data-original")
            or img.get("data-lazy-src")
        )
        if not src:
            srcset = img.get("srcset") or img.get("data-srcset")
            if srcset:
                src = srcset.split(",")[0].strip().split(" ")[0]

        if src and not src.startswith("data:image/svg") and not src.endswith(".svg"):
            # Skip tiny tracker icons
            width = img.get("width")
            height = img.get("height")
            if width and width.isdigit() and int(width) < 60:
                continue
            if height and height.isdigit() and int(height) < 60:
                continue
            return urllib.parse.urljoin(base_url, src)

    return None


def fetch_image_from_url(url: str, timeout: int = 15) -> Tuple[Image.Image, str]:
    """Download and return PIL.Image along with resolved image URL."""
    import requests

    url = url.strip()
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "https://" + url

    session = requests.Session()
    session.headers.update(DEFAULT_HEADERS)

    response = session.get(url, timeout=timeout, allow_redirects=True)
    response.raise_for_status()

    content_type = response.headers.get("Content-Type", "").lower()
    target_url = response.url

    # Check if this is an HTML page rather than direct image
    if "text/html" in content_type:
        extracted = extract_image_url_from_html(response.text, target_url)
        if not extracted:
            raise ValueError(
                "Could not find any suitable image on this web page. "
                "Try copying the direct image link (ending in .png, .jpg, etc.)."
            )
        # Fetch the discovered image URL
        target_url = extracted
        img_resp = session.get(target_url, timeout=timeout, allow_redirects=True)
        img_resp.raise_for_status()
        raw_bytes = img_resp.content
    else:
        raw_bytes = response.content

    # Load into PIL
    img = Image.open(io.BytesIO(raw_bytes))

    # Convert modes (palette / animated frames)
    if img.mode in ("P", "1"):
        img = img.convert("RGBA")
    elif img.mode not in ("RGB", "RGBA"):
        img = img.convert("RGBA")

    # In case of multi-frame animated GIFs, grab the primary frame
    img.load()
    return img, target_url


class DownloadWorker(QThread):
    """Background worker thread for non-blocking URL downloads."""

    finished_success = Signal(object, str)  # (PIL.Image, resolved_url)
    failed = Signal(str)  # error_message

    def __init__(self, url: str, parent=None):
        super().__init__(parent)
        self.url = url

    def run(self):
        try:
            image, resolved_url = fetch_image_from_url(self.url)
            self.finished_success.emit(image, resolved_url)
        except requests.exceptions.RequestException as e:
            self.failed.emit(f"Network error downloading image: {str(e)}")
        except Exception as e:
            self.failed.emit(f"Failed to process image: {str(e)}")
