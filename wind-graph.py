"""
Draws a wind graph for Thurmond (Clarks Hill) Lake from the USGS Water
Data API and saves it as a PNG.

Shows 15-minute wind speed for the last few days, with hourly arrows
along the top showing which way the wind is blowing.

Run:  python wind-graph.py [output.png]
"""
import math
import os
import sys
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import requests
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# ---- settings ---------------------------------------------------------
SITE = "USGS-02193900"          # Thurmond Lake near Plum Branch, SC
SPEED = "00035"                 # wind speed, mph
DIRECTION = "00036"             # wind direction, degrees (from)
DAYS = 3
ARROW_EVERY_HOURS = 2           # spacing of direction arrows
CALM_MPH = 1.0                  # no arrow below this speed
TITLE = "Clarks Hill Lake wind"
TZ = ZoneInfo("America/New_York")
OUT = sys.argv[1] if len(sys.argv) > 1 else "site/wind.png"

API = "https://api.waterdata.usgs.gov"
HEADERS = {"User-Agent": "lake-level-graph (Augusta Sailing Club)"}
if os.environ.get("USGS_API_KEY"):
    HEADERS["X-Api-Key"] = os.environ["USGS_API_KEY"]

COLOR = "#1f5fa8"
COMPASS = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
           "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]


def compass(deg):
    return COMPASS[int((deg % 360) / 22.5 + 0.5) % 16]


# ---- data -------------------------------------------------------------
def get_json(url, params=None):
    r = requests.get(url, params=params, headers=HEADERS, timeout=60)
    r.raise_for_status()
    return r.json()


def continuous(param, start, end):
    url = f"{API}/ogcapi/v1/collections/continuous/items"
    params = {
        "f": "json",
        "monitoring_location_id": SITE,
        "parameter_code": param,
        "time": f"{start:%Y-%m-%dT%H:%M:%SZ}/{end:%Y-%m-%dT%H:%M:%SZ}",
        "properties": "time,value",
        "skipGeometry": "true",
        "limit": 10000,
    }
    points = []
    while url:
        page = get_json(url, params)
        for f in page.get("features", []):
            p = f["properties"]
            if p.get("value") not in (None, ""):
                points.append((datetime.fromisoformat(p["time"]), float(p["value"])))
        nxt = [l["href"] for l in page.get("links", []) if l.get("rel") == "next"]
        url, params = (nxt[0], None) if nxt else (None, None)
    points.sort()
    return points


# ---- graph ------------------------------------------------------------
def main():
    end = datetime.now(timezone.utc).replace(second=0, microsecond=0)
    start = end - timedelta(days=DAYS)

    speed = continuous(SPEED, start, end)
    if not speed:
        sys.exit("No current wind data returned; keeping the previous image.")
    try:
        direction = dict(continuous(DIRECTION, start, end))
    except requests.RequestException as e:
        print("Direction data unavailable:", e)
        direction = {}

    fig, ax = plt.subplots(figsize=(8, 4.5), dpi=150)
    ax.plot(*zip(*speed), color=COLOR, lw=1.6, label="Wind speed (15-minute readings)")

    top = max(v for _, v in speed)
    ymax = max(10, math.ceil(top * 1.35 / 5) * 5)
    ax.set_ylim(0, ymax)
    ax.set_xlim(start, end)

    # Direction arrows along the top. Arrows point the way the wind is
    # blowing TO (a north wind's arrow points down).
    arrow_y = ymax * 0.9
    last_arrow = None
    for t, v in speed:
        if t not in direction or v < CALM_MPH:
            continue
        if last_arrow and t - last_arrow < timedelta(hours=ARROW_EVERY_HOURS):
            continue
        last_arrow = t
        to_rad = math.radians((direction[t] + 180) % 360)
        ax.quiver(mdates.date2num(t), arrow_y, math.sin(to_rad), math.cos(to_rad),
                  angles="uv", scale=40, width=0.003, color="#555", zorder=3)
    ax.text(0.005, 0.97, "Arrows show where the wind is blowing toward",
            transform=ax.transAxes, fontsize=7, color="#777", va="top")

    t_last, v_last = speed[-1]
    headline = f"{v_last:.1f} mph"
    if t_last in direction and v_last >= CALM_MPH:
        headline += f" from the {compass(direction[t_last])} ({direction[t_last]:.0f}°)"
    elif v_last < CALM_MPH:
        headline += " (calm)"
    day_ago = t_last - timedelta(hours=24)
    peak_t, peak_v = max(((t, v) for t, v in speed if t >= day_ago), key=lambda p: p[1])
    headline += (f"  ·  24-hr high {peak_v:.1f} mph at "
                 f"{peak_t.astimezone(TZ):%a %-I:%M %p}")

    fig.suptitle(TITLE, x=0.08, ha="left", fontsize=14, fontweight="bold")
    ax.set_title(f"Now: {headline}", loc="left", fontsize=10, color="#333")
    ax.set_ylabel("Wind speed, mph")

    ax.xaxis.set_major_locator(mdates.DayLocator(tz=TZ))
    ax.xaxis.set_minor_locator(mdates.HourLocator(byhour=[6, 12, 18], tz=TZ))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%a\n%b %-d", tz=TZ))
    ax.grid(True, which="major", color="#e5e5e5", lw=0.8)
    ax.grid(True, which="minor", axis="x", color="#f2f2f2", lw=0.6)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.legend(loc="upper left", bbox_to_anchor=(0, -0.16), frameon=False, fontsize=8)

    stamp = t_last.astimezone(TZ).strftime("%b %-d, %Y %-I:%M %p %Z")
    fig.text(0.99, 0.01,
             f"Last reading {stamp} · USGS {SITE.split('-')[1]} · provisional data",
             ha="right", va="bottom", fontsize=7, color="#777")

    fig.tight_layout(rect=(0, 0.03, 1, 1))
    os.makedirs(os.path.dirname(OUT) or ".", exist_ok=True)
    fig.savefig(OUT)
    print(f"Wrote {OUT}: {headline}")


if __name__ == "__main__":
    main()
