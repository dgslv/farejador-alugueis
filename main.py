import asyncio
import time
from datetime import datetime

from scraper import fetch_listings
from storage import init_db, is_new, save_listing, get_tracked_ids, get_sources, get_setting
from notifier import notify, log_listing


def run_once():
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Fetching listings...")
    try:
        urls = [s["url"] for s in get_sources() if s["active"]]
        listings = asyncio.run(fetch_listings(urls))
    except Exception as exc:
        print(f"  ERROR fetching listings: {exc}")
        return

    max_total_price = get_setting("max_total_price")
    new_found = 0
    for lst in listings:
        total = lst["price"] + (lst.get("condo") or 0) + (lst.get("iptu") or 0)
        if total > max_total_price:
            continue
        if is_new(lst["id"]):
            save_listing(lst)
            notify(
                "Novo Apartamento!",
                f"{lst['bedrooms']}q · {lst['area']}m² · R${lst['price']:,} — {lst['title']}",
            )
            log_listing(lst)
            new_found += 1
            print(
                f"  NEW: {lst['bedrooms']}q {lst['area']}m² R${lst['price']:,} — {lst['url']}"
            )
        else:
            save_listing(lst)  # update last_seen_at for existing listings

    scraped_ids = {lst["id"] for lst in listings}
    for tid in get_tracked_ids():
        if tid not in scraped_ids:
            print(f"  TRACKED LISTING NOT FOUND: {tid}")

    print(
        f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] "
        f"Checked {len(listings)} listings, {new_found} new "
        f"(max total R${max_total_price:,}, next run in {get_setting('interval_seconds')}s).\n"
    )


def run_forever():
    """Re-run the scraper every N seconds; N is re-read from settings each tick
    so changes made in the dashboard apply without a restart."""
    last_run = time.time()
    while True:
        time.sleep(1)
        if time.time() - last_run >= get_setting("interval_seconds"):
            run_once()
            last_run = time.time()


if __name__ == "__main__":
    init_db()

    run_once()  # immediate first run

    run_forever()
