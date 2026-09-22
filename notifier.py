import sys
from datetime import datetime

from config import APP_NAME, LOG_PATH


def notify(title: str, message: str):
    try:
        from plyer import notification
        notification.notify(title=title, message=message, app_name=APP_NAME, timeout=8)
    except Exception:
        # Fallback: macOS osascript
        if sys.platform == "darwin":
            import subprocess
            script = f'display notification "{message}" with title "{title}"'
            subprocess.run(["osascript", "-e", script], check=False)


def log_listing(listing: dict):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = (
        f"[{timestamp}] "
        f"{listing.get('bedrooms')}q · "
        f"{listing.get('area')}m² · "
        f"R${listing.get('price'):,} · "
        f"{listing.get('title', '')} · "
        f"{listing.get('url')}\n"
    )
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(line)
