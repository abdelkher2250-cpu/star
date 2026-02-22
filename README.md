# USAF Folder Quicklook

This repository includes a lightweight script to inspect a downloaded folder that contains mixed artifacts (images, videos, logs) and produce a first-pass movement summary.

## Beginner step-by-step (copy/paste friendly)

If you have **0 experience**, follow this exactly.

### 1) Download the Google Drive folder

1. Open your Google Drive `USAF` folder link in your browser.
2. Click the folder name > **Download**.
3. Wait for Google to prepare a `.zip` file.
4. Save that zip file.

### 2) Put the zip into this project folder

Move/copy the downloaded zip into this location:

- `/workspace/star`

### 3) Unzip it

Open terminal in `/workspace/star`, then run:

```bash
unzip your_downloaded_file.zip
```

After unzip, you should have a folder like:

- `/workspace/star/USAF`

### 4) Verify the folder exists

Run:

```bash
cd /workspace/star
find . -maxdepth 2 -type d -name "USAF"
```

If you see `./USAF`, you're ready.

### 5) Run the analyzer

Run this exact command:

```bash
cd /workspace/star
python scripts/usaf_quicklook.py /workspace/star/USAF --out analysis
```

### 6) Open the results

After it finishes, you will get:

- `analysis/summary.json`
- `analysis/daily_counts.json`
- `analysis/trip_summary.json`

### 7) Share results (optional)

If you want help interpreting the data, send the contents of:

- `analysis/summary.json`
- first ~30 lines of `analysis/trip_summary.json`

---

## What the script does

Given a folder like your `USAF` export (images/videos/logs over many days), this script can:

- Count media and log artifacts by day.
- Parse common GPS log formats (`csv`, `json`, `ndjson`) when they contain timestamp + lat/lon fields.
- Split timeline into trips using a time-gap heuristic.
- Emit a trip table with basic direction hint (`going` / `returning` alternation).

## Expected log fields

The parser looks for common key names:

- Latitude: `lat` or `latitude`
- Longitude: `lon`, `lng`, or `longitude`
- Timestamp: `timestamp`, `time`, `datetime`, or `date`

## Usage (quick reference)

```bash
python scripts/usaf_quicklook.py /path/to/USAF --out analysis
```

Optional parameters:

- `--trip-gap-min 30` (default): gap threshold in minutes to split trips.

## Notes

- No third-party Python dependencies required.
- Timestamp extraction attempts filename parsing and file modification time fallback.
- Direction labels are heuristic placeholders and should be replaced with route-aware logic once sample logs are validated.
