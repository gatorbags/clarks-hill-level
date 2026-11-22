# Clarks Hill Lake graphs

Hourly-updated graphs of Thurmond (Clarks Hill) Lake conditions for the
Augusta Sailing Club website, drawn from USGS gauge 02193900
(Thurmond Lake near Plum Branch, SC).

## Images
| Graph | Address |
|---|---|
| Lake level | https://gatorbags.github.io/clarks-hill-level/ch.png |
| Water temperature | https://gatorbags.github.io/clarks-hill-level/temp.png |
| Wind | https://gatorbags.github.io/clarks-hill-level/wind.png |

Embed on a web page with:

    <img src="https://gatorbags.github.io/clarks-hill-level/ch.png" alt="Clarks Hill Lake level">

## How it works
- `.github/workflows/lake-graph.yml` runs every hour on GitHub Actions.
- It runs the three scripts below, which pull data from the USGS Water
  Data API and draw the PNGs.
- The images are published to GitHub Pages at the addresses above.

| Script | Graph | What it shows |
|---|---|---|
| `level-graph.py` | Lake level, last 7 days | This week, same week last year, median daily level, full pool (330 ft) when the lake is near it |
| `water-temp-graph.py` | Water temperature, last 7 days | This week, same week last year, median daily temperature (°F) |
| `wind-graph.py` | Wind, last 3 days | 15-minute wind speed, arrows every 2 hours showing where the wind is blowing toward, 24-hour high |

## Maintenance
- Settings (title, number of days, colors, units) are at the top of each script.
- The optional `USGS_API_KEY` secret raises the USGS rate limit.
  Get a free key at https://api.waterdata.usgs.gov/signup/
- If an image stops updating, check the **Actions** tab for a failed run.
  The timestamp in the corner of each image shows the last reading.
- If USGS is down, the previous images stay up until the next good run.
- A small `keepalive.txt` commit on the 1st of each month stops GitHub
  from pausing the hourly schedule.

Data are provisional and subject to revision by USGS.
