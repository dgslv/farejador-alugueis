"""macOS menu bar status icon for the apartment scraper."""

import re
import webbrowser
from collections import deque
from pathlib import Path

import rumps

LOG_PATH = Path(__file__).parent / "scraper.log"
DASHBOARD_URL = "http://127.0.0.1:8080"
POLL_SECONDS = 30
LOG_LINES = 50

# Matches: [2026-03-06 12:30:09] Checked 68 listings, 0 new.
RE_CHECKED = re.compile(
    r"\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\] Checked (\d+) listings, (\d+) new\."
)
# Matches: [2026-03-06 12:28:44] Fetching listings...
RE_FETCHING = re.compile(r"\[.*?\] Fetching listings\.\.\.")
# Matches: ERROR fetching listings: ...
RE_ERROR = re.compile(r"ERROR fetching listings: (.+)")

ICON_IDLE = "🏠"
ICON_FETCHING = "🔄"
ICON_ERROR = "⚠️"


class ScraperMenuBar(rumps.App):
    def __init__(self):
        super().__init__(ICON_IDLE, quit_button=None)
        self.status_item = rumps.MenuItem("Status: idle")
        self.last_update_item = rumps.MenuItem("Last: —")
        self.menu = [
            self.status_item,
            self.last_update_item,
            None,  # separator
            rumps.MenuItem("Open Dashboard", callback=self.open_dashboard),
            None,
            rumps.MenuItem("Quit", callback=rumps.quit_application),
        ]
        self.poll_log(None)

    @rumps.timer(POLL_SECONDS)
    def poll_log(self, _):
        if not LOG_PATH.exists():
            self._set_status("idle", "No log file")
            return

        lines = deque(LOG_PATH.open(), maxlen=LOG_LINES)
        last_checked = None
        is_fetching = False
        error_after_last_check = None

        for line in lines:
            m = RE_CHECKED.search(line)
            if m:
                last_checked = m.groups()
                is_fetching = False
                error_after_last_check = None  # reset: successful run clears error

            if RE_FETCHING.search(line):
                is_fetching = True
                error_after_last_check = None  # new run started

            m = RE_ERROR.search(line)
            if m:
                error_after_last_check = m.group(1)
                is_fetching = False

        # Only show error if the last run failed AND there was no prior success
        if error_after_last_check and not last_checked:
            self._set_status("error", error_after_last_check)
        elif is_fetching:
            self._set_status("fetching")
        else:
            self._set_status("idle")

        if last_checked:
            ts, total, new = last_checked
            time_part = ts.split(" ")[1][:5]  # HH:MM
            self.last_update_item.title = f"Last: {time_part} — {total} listings, {new} new"

    def _set_status(self, status, detail=None):
        if status == "fetching":
            self.title = ICON_FETCHING
            self.status_item.title = "Status: fetching..."
        elif status == "error":
            self.title = ICON_ERROR
            self.status_item.title = f"Status: error — {detail}"
        else:
            self.title = ICON_IDLE
            self.status_item.title = "Status: idle"

    def open_dashboard(self, _):
        webbrowser.open(DASHBOARD_URL)


if __name__ == "__main__":
    ScraperMenuBar().run()
