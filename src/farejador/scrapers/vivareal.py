"""VivaReal scraper: opens each search in a headless Chromium and turns the cards into listings."""

import asyncio
import json
import logging
import random
import re

from playwright.async_api import async_playwright
from playwright_stealth import Stealth

from farejador.config import EXCLUDED_NEIGHBORHOODS, HEADLESS, MAX_PAGES, USER_AGENT

log = logging.getLogger(__name__)

# URL pattern: /imovel/apartamento-N-quartos-...-Xm2-aluguel-RSPRICE-id-ID/
_URL_RE = re.compile(
    r"/imovel/(?P<slug>[^/]+)-id-(?P<id>\d+)/",
    re.IGNORECASE,
)
_ROOMS_RE = re.compile(r"-(\d+)-quartos?-", re.IGNORECASE)
_AREA_RE = re.compile(r"-(\d+)m2-", re.IGNORECASE)
_PRICE_URL = re.compile(r"-RS(\d+)-id-", re.IGNORECASE)
# Matches rental price in card text: "R$ 5.800/mês" or "R$5800/mês"
_PRICE_TXT = re.compile(r"R\$\s*([\d.,]+)\s*/\s*m[eê]s", re.IGNORECASE)
_CONDO_RE = re.compile(r"Cond\.\s*R\$\s*([\d.,]+)", re.IGNORECASE)
_IPTU_RE = re.compile(r"IPTU\s+R\$\s*([\d.,]+)", re.IGNORECASE)


def _parse_brl(raw: str) -> int:
    raw = raw.replace(".", "").replace(",", "")
    return int(raw) if raw.isdigit() else 0


def _price_from_text(title: str) -> int:
    m = _PRICE_TXT.search(title)
    return _parse_brl(m.group(1)) if m else 0


def _extract_card_fields(text: str) -> dict:
    """Extract neighborhood, street, condo fee, and IPTU from card inner text."""
    neighborhood = ""
    street = ""

    # Neighborhood appears after "em\n" and before ", City"
    m = re.search(r"em\n([^\n,]+),", text, re.IGNORECASE)
    if m:
        neighborhood = m.group(1).strip()
        # Street is the first line after "Neighborhood, City\n\n"
        m2 = re.search(re.escape(neighborhood) + r"[^\n]*\n\n([^\n]+)", text, re.IGNORECASE)
        if m2:
            street = m2.group(1).strip()

    mc = _CONDO_RE.search(text)
    mi = _IPTU_RE.search(text)
    condo = _parse_brl(mc.group(1)) if mc else 0
    iptu = _parse_brl(mi.group(1)) if mi else 0

    return {"neighborhood": neighborhood, "street": street, "condo": condo, "iptu": iptu}


def _parse_link(href: str, title: str):
    """Extract listing fields from a VivaReal imovel URL + card text."""
    m = _URL_RE.search(href)
    if not m:
        return None

    listing_id = m.group("id")
    slug = m.group("slug")

    rooms_m = _ROOMS_RE.search(slug)
    area_m = _AREA_RE.search(slug)

    bedrooms = int(rooms_m.group(1)) if rooms_m else 0
    area = float(area_m.group(1)) if area_m else 0.0

    # Prefer price from card text (shows rental price even for dual-listed properties)
    price = _price_from_text(title)
    if not price:
        pm = _PRICE_URL.search(href)
        price = int(pm.group(1)) if pm else 0

    card_fields = _extract_card_fields(title)

    return {
        "id": listing_id,
        "url": href.split("?")[0],
        "title": title.strip(),
        "street": card_fields["street"],
        "neighborhood": card_fields["neighborhood"],
        "price": price,
        "condo": card_fields["condo"],
        "iptu": card_fields["iptu"],
        "area": area,
        "bedrooms": bedrooms,
    }


async def _scroll_to_bottom(page):
    """Scroll incrementally to trigger lazy-load; stop after 5 consecutive stable steps."""
    prev_count = 0
    stable_steps = 0
    for _ in range(60):
        await page.evaluate("window.scrollBy(0, 400)")
        await asyncio.sleep(0.5)
        count = await page.locator('a[href*="/imovel/"]').count()
        if count == prev_count:
            stable_steps += 1
            if stable_steps >= 5:
                break
        else:
            stable_steps = 0
        prev_count = count
    await asyncio.sleep(1.0)
    await page.evaluate("window.scrollTo(0, 0)")
    await asyncio.sleep(0.3)


async def _get_card_images(card) -> list:
    """Return all real image URLs found in a card element."""
    imgs = await card.locator("img").all()
    urls = []
    for img in imgs:
        src = await img.get_attribute("src") or await img.get_attribute("data-src") or ""
        if src.startswith("http") and not src.endswith(".svg"):
            urls.append(src)
    return urls


async def _extract_listings(page) -> list:
    """Scroll page, extract card-based listings with images."""
    await _scroll_to_bottom(page)

    seen_ids: set = set()
    results: list = []

    # 1. Card-based extraction — gets link, text, and all images per card
    cards = await page.locator('li[data-cy="rp-property-cd"]:has(a[href*="/imovel/"])').all()
    for card in cards:
        try:
            link = card.locator('a[href*="/imovel/"]').first
            href = await link.get_attribute("href") or ""
            title = (await card.inner_text()).strip()
            listing = _parse_link(href, title)
            if listing and listing["id"] not in seen_ids:
                image_urls = await _get_card_images(card)
                listing["images"] = json.dumps(image_urls) if image_urls else None
                seen_ids.add(listing["id"])
                results.append(listing)
        except Exception:
            continue

    # 2. Button-based multi-unit cards (open a modal — count as ONE listing each)
    btn_only = page.locator('li[data-cy="rp-property-cd"]:not(:has(a[href*="/imovel/"])) a[role="button"]')
    btn_count = await btn_only.count()
    for i in range(btn_count):
        try:
            card = btn_only.nth(i)
            card_text = (await card.inner_text()).strip()
            image_urls = await _get_card_images(card)
            await card.click()
            modal = page.locator('div.olx-modal-content a[href*="/imovel/"]')
            await modal.first.wait_for(timeout=8_000)
            modal_links = await page.locator('div.olx-modal-content a[href*="/imovel/"]').all()
            chosen = None
            for link in modal_links:
                href = await link.get_attribute("href") or ""
                if "aluguel" in href.lower():
                    chosen = href
                    break
            if not chosen and modal_links:
                chosen = await modal_links[0].get_attribute("href") or ""
            if chosen:
                listing = _parse_link(chosen, card_text)
                if listing and listing["id"] not in seen_ids:
                    listing["images"] = json.dumps(image_urls) if image_urls else None
                    seen_ids.add(listing["id"])
                    results.append(listing)
            await page.keyboard.press("Escape")
            await asyncio.sleep(0.5)
        except Exception:
            await page.keyboard.press("Escape")
            await asyncio.sleep(0.5)

    return results


async def fetch_listings(urls: list) -> list:
    from farejador.db import is_new as _is_new

    all_listings: list = []
    seen_ids: set = set()

    async with async_playwright() as p:
        stealth = Stealth()
        stealth.hook_playwright_context(p)
        browser = await p.chromium.launch(
            headless=HEADLESS,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
            ],
        )
        try:
            context = await browser.new_context(
                user_agent=USER_AGENT,
                viewport={"width": 1366, "height": 768},
            )
            page = await context.new_page()

            for search_idx, start_url in enumerate(urls, 1):
                log.info("search %d/%d: %s", search_idx, len(urls), start_url[:80])
                url = start_url
                for page_num in range(1, MAX_PAGES + 1):
                    log.info("page %d: %s", page_num, url[:100])
                    # VivaReal never reaches "networkidle" (ads/trackers keep polling),
                    # so wait for the DOM and then for the listing cards themselves.
                    try:
                        await page.goto(url, wait_until="domcontentloaded", timeout=60_000)
                        await page.locator('li[data-cy="rp-property-cd"]').first.wait_for(timeout=30_000)
                    except Exception as exc:
                        # Keep what earlier pages gave us instead of failing the whole run.
                        log.warning("page %d failed, stopping pagination: %s", page_num, str(exc).splitlines()[0][:120])
                        break
                    await asyncio.sleep(random.uniform(1.5, 3))

                    page_listings = await _extract_listings(page)
                    log.info("found %d listings on page %d", len(page_listings), page_num)

                    # Deduplicate, filter excluded neighborhoods, split into known vs new
                    fresh = []
                    for lst in page_listings:
                        url_lower = lst["url"].lower()
                        neighborhood_lower = lst.get("neighborhood", "").lower()
                        if any(n in url_lower or n in neighborhood_lower for n in EXCLUDED_NEIGHBORHOODS):
                            continue
                        if lst["id"] not in seen_ids:
                            seen_ids.add(lst["id"])
                            all_listings.append(lst)
                            if _is_new(lst["id"]):
                                fresh.append(lst)

                    new_on_page = len(fresh)
                    log.info("%d new listings on page %d", new_on_page, page_num)

                    # Follow the "próxima página" link if present
                    next_link = page.locator('a[aria-label="próxima página"]:not([aria-disabled="true"])')
                    if await next_link.count() == 0:
                        log.info("no next page button, done.")
                        break
                    next_href = await next_link.get_attribute("href")
                    if not next_href:
                        break
                    url = "https://www.vivareal.com.br" + next_href if next_href.startswith("/") else next_href
        finally:
            await browser.close()

    return all_listings
