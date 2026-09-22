"""The scheduler: one round = fetch every active source, save, notify about what is new."""

import asyncio
import logging
import time

from farejador.db import (
    count_listings,
    get_setting,
    get_sources,
    get_tracked_ids,
    init_db,
    is_new,
    save_listing,
)
from farejador.notify import log_listing, notify
from farejador.scrapers.vivareal import fetch_listings

log = logging.getLogger(__name__)


def run_once() -> None:
    log.info("Fetching listings...")
    try:
        urls = [s["url"] for s in get_sources() if s["active"]]
        listings = asyncio.run(fetch_listings(urls))
    except Exception as exc:
        log.error("ERROR fetching listings: %s", exc)
        return

    max_total_price = get_setting("max_total_price")
    # Empty database = first run: everything is "new"; do not fire dozens of notifications.
    first_run = count_listings() == 0
    if first_run:
        log.info("first run: saving listings silently")
    new_found = 0
    for lst in listings:
        total = lst["price"] + (lst.get("condo") or 0) + (lst.get("iptu") or 0)
        if total > max_total_price:
            continue
        if is_new(lst["id"]):
            save_listing(lst)
            if not first_run:
                notify(
                    "Novo Apartamento!",
                    f"{lst['bedrooms']}q · {lst['area']}m² · R${lst['price']:,} — {lst['title']}",
                )
            log_listing(lst)
            new_found += 1
            log.info("NEW: %sq %sm² R$%s — %s", lst["bedrooms"], lst["area"], f"{lst['price']:,}", lst["url"])
        else:
            save_listing(lst)  # only refreshes last_seen_at

    scraped_ids = {lst["id"] for lst in listings}
    for tid in get_tracked_ids():
        if tid not in scraped_ids:
            log.info("TRACKED LISTING NOT FOUND: %s", tid)

    log.info(
        "Checked %d listings, %d new (max total R$%s, next run in %ss)",
        len(listings),
        new_found,
        f"{max_total_price:,}",
        get_setting("interval_seconds"),
    )


def run_forever() -> None:
    """Re-run every N seconds; N is re-read from the database on each tick, so a
    change made in the dashboard applies without a restart."""
    last_run = time.time()
    while True:
        time.sleep(1)
        if time.time() - last_run >= get_setting("interval_seconds"):
            run_once()
            last_run = time.time()


def main() -> None:
    """Headless mode: only the scraper, in the terminal (`farejador --headless`)."""
    init_db()
    run_once()
    run_forever()
