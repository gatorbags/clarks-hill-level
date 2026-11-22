# Clarks Hill Lake level graph

Hourly-updated graph of Thurmond (Clarks Hill) Lake elevation for the
Augusta Sailing Club website.

**Image:** https://YOUR-ACCOUNT.github.io/lake-level/thurmond.png

## How it works
- `.github/workflows/lake-graph.yml` runs every hour on GitHub Actions.
- It runs `make_graph.py`, which pulls data from the USGS Water Data API
  (site USGS-02193900, lake elevation) and draws the PNG.
- The image is published to GitHub Pages at the address above.

## Lines on the graph
- This week (15-minute readings)
- Same week last year
- Median daily level for the period of record
- Full pool (330 ft), shown only when the lake is near it

## Maintenance
- Settings (title, days, full pool, colors) are at the top of `make_graph.py`.
- The optional `USGS_API_KEY` secret raises the USGS rate limit.
  Get a free key at https://api.waterdata.usgs.gov/signup/
- If the image stops updating, check the **Actions** tab for a failed run.
- A small `keepalive.txt` commit on the 1st of each month stops GitHub
  from pausing the hourly schedule.

Data are provisional and subject to revision by USGS.
