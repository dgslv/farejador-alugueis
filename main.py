import asyncio
import time
from datetime import datetime

import schedule

from scraper import fetch_listings
from storage import init_db, is_new, save_listing, get_tracked_ids, get_sources
from notifier import notify, log_listing
from config import INTERVAL_MINUTES


def run_once():
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Fetching listings...")
    try:
        urls = [s["url"] for s in get_sources() if s["active"]]
        listings = asyncio.run(fetch_listings(urls))
    except Exception as exc:
        print(f"  ERROR fetching listings: {exc}")
        return

    new_found = 0
    for lst in listings:
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
        f"Checked {len(listings)} listings, {new_found} new.\n"
    )


if __name__ == "__main__":
    init_db()

    run_once()  # immediate first run

    schedule.every(INTERVAL_MINUTES).minutes.do(run_once)

    while True:
        schedule.run_pending()
        time.sleep(30)
