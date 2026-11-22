"""
Draws a 7-day water-temperature graph for Thurmond (Clarks Hill) Lake
from the USGS Water Data API and saves it as a PNG.

Lines:  this week (15-min data), same week last year, and the median
daily temperature for the period of record.

Run:  python water-temp-graph.py [output.png]
"""
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
PARAM = "00010"                 # water temperature, deg C
DAYS = 7
FAHRENHEIT = True               # False to show deg C
TITLE = "Clarks Hill Lake water temperature"
TZ = ZoneInfo("America/New_York")
OUT = sys.argv[1] if len(sys.argv) > 1 else "site/temp.png"

API = "https://api.waterdata.usgs.gov"
HEADERS = {"User-Agent": "lake-level-graph (Augusta Sailing Club)"}
if os.environ.get("USGS_API_KEY"):
    HEADERS["X-Api-Key"] = os.environ["USGS_API_KEY"]

COLORS = {"now": "#c0392b", "last": "#8a8f98", "median": "#1f5fa8"}
UNIT = "°F" if FAHRENHEIT else "°C"


def conv(c):
    return c * 9 / 5 + 32 if FAHRENHEIT else c


# ---- data -------------------------------------------------------------
def get_json(url, params=None):
    r = requests.get(url, params=params, headers=HEADERS, timeout=60)
    r.raise_for_status()
    return r.json()


def continuous(start, end):
    url = f"{API}/ogcapi/v1/collections/continuous/items"
    params = {
        "f": "json",
        "monitoring_location_id": SITE,
        "parameter_code": PARAM,
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
                points.append((datetime.fromisoformat(p["time"]), conv(float(p["value"]))))
        nxt = [l["href"] for l in page.get("links", []) if l.get("rel") == "next"]
        url, params = (nxt[0], None) if nxt else (None, None)
    points.sort()
    return points


def daily_medians():
    data = get_json(f"{API}/statistics/v0/observationNormals", {
        "monitoring_location_id": SITE,
        "parameter_code": PARAM,
        "computation_type": "median",
        "normal_type": "DOY",
    })
    out = {}
    for feat in data.get("features", []):
        for series in feat["properties"].get("data", []):
            if series.get("parent_statistic_id") != "00003":   # daily mean
                continue
            for v in series.get("values", []):
                out[v["time_of_year"]] = conv(float(v["value"]))
    return out


# ---- graph ------------------------------------------------------------
def main():
    end = datetime.now(timezone.utc).replace(second=0, microsecond=0)
    start = end - timedelta(days=DAYS)

    now_pts = continuous(start, end)
    if not now_pts:
        sys.exit("No current data returned; keeping the previous image.")

    shift = timedelta(days=365)
    try:
        last_pts = [(t + shift, v) for t, v in continuous(start - shift, end - shift)]
    except requests.RequestException as e:
        print("Last-year data unavailable:", e)
        last_pts = []

    try:
        medians = daily_medians()
    except requests.RequestException as e:
        print("Median data unavailable:", e)
        medians = {}

    med_pts = []
    day = start.astimezone(TZ).date()
    while day <= end.astimezone(TZ).date():
        key = day.strftime("%m-%d")
        if key in medians:
            med_pts.append((datetime(day.year, day.month, day.day, 12, tzinfo=TZ), medians[key]))
        day += timedelta(days=1)

    fig, ax = plt.subplots(figsize=(8, 4.5), dpi=150)

    ax.plot(*zip(*now_pts), color=COLORS["now"], lw=2.2, label="This week")
    if last_pts:
        ax.plot(*zip(*last_pts), color=COLORS["last"], lw=1.4, ls="--",
                label=f"Same week {end.astimezone(TZ).year - 1}")
    if med_pts:
        ax.plot(*zip(*med_pts), color=COLORS["median"], lw=1.4, marker="o", ms=3.5,
                label="Median daily temperature (period of record)")

    vals = [v for _, v in now_pts + last_pts + med_pts]
    lo, hi = min(vals), max(vals)
    pad = max(0.5, (hi - lo) * 0.12)
    ax.set_ylim(lo - pad, hi + pad)
    ax.set_xlim(start, end)

    t_last, v_last = now_pts[-1]
    headline = f"{v_last:.1f} {UNIT}"
    if med_pts:
        nearest = min(med_pts, key=lambda p: abs(p[0] - t_last))[1]
        d = v_last - nearest
        headline += f"  ·  {abs(d):.1f} {UNIT} {'above' if d > 0 else 'below'} median"

    fig.suptitle(TITLE, x=0.08, ha="left", fontsize=14, fontweight="bold")
    ax.set_title(f"Now: {headline}", loc="left", fontsize=10, color="#333")
    ax.set_ylabel(f"Water temperature, {UNIT}")

    ax.xaxis.set_major_locator(mdates.DayLocator(tz=TZ))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%a\n%b %-d", tz=TZ))
    ax.grid(True, color="#e5e5e5", lw=0.8)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.legend(loc="upper left", bbox_to_anchor=(0, -0.16), ncol=3, frameon=False, fontsize=8)

    stamp = t_last.astimezone(TZ).strftime("%b %-d, %Y %-I:%M %p %Z")
    fig.text(0.99, 0.01,
             f"Last reading {stamp} · USGS {SITE.split('-')[1]} · provisional data",
             ha="right", va="bottom", fontsize=7, color="#777")

    fig.tight_layout(rect=(0, 0.03, 1, 1))
    os.makedirs(os.path.dirname(OUT) or ".", exist_ok=True)
    fig.savefig(OUT)
    print(f"Wrote {OUT}: {v_last:.1f} {UNIT} at {stamp}")


if __name__ == "__main__":
    main()
