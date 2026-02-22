#!/usr/bin/env python3
"""Quickly profile USAF-style movement data (logs + images/videos) from a local folder.

The script is intentionally dependency-light (stdlib only).
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tif", ".tiff", ".webp"}
VIDEO_EXTS = {".mp4", ".mov", ".avi", ".mkv", ".webm", ".m4v"}
LOG_EXTS = {".csv", ".json", ".txt", ".log", ".ndjson"}

TS_PATTERNS = [
    re.compile(r"(20\d{2})[-_]?([01]\d)[-_]?([0-3]\d)[T_ -]?([0-2]\d)[-_:]?([0-5]\d)[-_:]?([0-5]\d)"),
    re.compile(r"(20\d{2})[-_/]([01]?\d)[-_/]([0-3]?\d)"),
]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="USAF folder quicklook and route summary")
    p.add_argument("dataset", type=Path, help="Path to the downloaded dataset folder")
    p.add_argument("--out", type=Path, default=Path("analysis"), help="Output directory")
    p.add_argument("--trip-gap-min", type=float, default=30.0, help="New trip split gap in minutes")
    return p.parse_args()


def parse_timestamp_from_text(text: str) -> dt.datetime | None:
    for pat in TS_PATTERNS:
        m = pat.search(text)
        if not m:
            continue
        parts = [int(x) for x in m.groups()]
        if len(parts) == 6:
            y, mo, d, hh, mm, ss = parts
            try:
                return dt.datetime(y, mo, d, hh, mm, ss)
            except ValueError:
                continue
        if len(parts) == 3:
            y, mo, d = parts
            try:
                return dt.datetime(y, mo, d)
            except ValueError:
                continue
    return None


def infer_timestamp(path: Path) -> dt.datetime | None:
    ts = parse_timestamp_from_text(path.name)
    if ts:
        return ts
    ts = parse_timestamp_from_text(str(path.parent))
    if ts:
        return ts
    try:
        return dt.datetime.fromtimestamp(path.stat().st_mtime)
    except OSError:
        return None


def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = p2 - p1
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def maybe_float(v: object) -> float | None:
    if v is None:
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def parse_point(record: dict[str, object]) -> tuple[dt.datetime, float, float] | None:
    keys = {k.lower(): k for k in record.keys()}
    lat = maybe_float(record.get(keys.get("lat")) or record.get(keys.get("latitude")))
    lon = maybe_float(record.get(keys.get("lon")) or record.get(keys.get("lng")) or record.get(keys.get("longitude")))
    ts_raw = record.get(keys.get("timestamp") or keys.get("time") or keys.get("datetime") or keys.get("date"))

    ts = None
    if isinstance(ts_raw, (int, float)):
        try:
            ts = dt.datetime.fromtimestamp(float(ts_raw))
        except (OverflowError, OSError, ValueError):
            ts = None
    elif isinstance(ts_raw, str):
        try:
            ts = dt.datetime.fromisoformat(ts_raw.replace("Z", "+00:00")).replace(tzinfo=None)
        except ValueError:
            ts = parse_timestamp_from_text(ts_raw)

    if ts and lat is not None and lon is not None:
        return ts, lat, lon
    return None


def read_points(log_file: Path) -> list[tuple[dt.datetime, float, float]]:
    points: list[tuple[dt.datetime, float, float]] = []
    suffix = log_file.suffix.lower()

    if suffix == ".csv":
        with log_file.open("r", encoding="utf-8", errors="ignore", newline="") as f:
            for row in csv.DictReader(f):
                pt = parse_point(dict(row))
                if pt:
                    points.append(pt)
    elif suffix in {".json", ".ndjson"}:
        with log_file.open("r", encoding="utf-8", errors="ignore") as f:
            content = f.read().strip()
            if not content:
                return points
            if suffix == ".ndjson":
                for line in content.splitlines():
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        obj = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if isinstance(obj, dict):
                        pt = parse_point(obj)
                        if pt:
                            points.append(pt)
            else:
                try:
                    obj = json.loads(content)
                except json.JSONDecodeError:
                    return points
                iterable: Iterable[object]
                if isinstance(obj, list):
                    iterable = obj
                elif isinstance(obj, dict):
                    iterable = obj.get("points", []) if isinstance(obj.get("points"), list) else [obj]
                else:
                    iterable = []
                for item in iterable:
                    if isinstance(item, dict):
                        pt = parse_point(item)
                        if pt:
                            points.append(pt)

    points.sort(key=lambda x: x[0])
    return points


def summarize_trips(points: list[tuple[dt.datetime, float, float]], gap_minutes: float) -> list[dict[str, object]]:
    if not points:
        return []

    trips: list[list[tuple[dt.datetime, float, float]]] = [[points[0]]]
    gap = dt.timedelta(minutes=gap_minutes)

    for pt in points[1:]:
        if pt[0] - trips[-1][-1][0] > gap:
            trips.append([pt])
        else:
            trips[-1].append(pt)

    out: list[dict[str, object]] = []
    for idx, trip in enumerate(trips, start=1):
        dist_m = 0.0
        for a, b in zip(trip, trip[1:]):
            dist_m += haversine_m(a[1], a[2], b[1], b[2])
        duration_s = (trip[-1][0] - trip[0][0]).total_seconds()
        out.append(
            {
                "trip_id": idx,
                "start": trip[0][0].isoformat(sep=" "),
                "end": trip[-1][0].isoformat(sep=" "),
                "points": len(trip),
                "distance_km": round(dist_m / 1000.0, 3),
                "duration_min": round(duration_s / 60.0, 2),
                "direction_hint": "going" if idx % 2 else "returning",
            }
        )
    return out


def main() -> int:
    args = parse_args()
    root = args.dataset
    out_dir = args.out
    out_dir.mkdir(parents=True, exist_ok=True)

    if not root.exists():
        raise SystemExit(f"Dataset path does not exist: {root}")

    all_files = [p for p in root.rglob("*") if p.is_file()]
    exts = Counter(p.suffix.lower() or "<none>" for p in all_files)

    images = [p for p in all_files if p.suffix.lower() in IMAGE_EXTS]
    videos = [p for p in all_files if p.suffix.lower() in VIDEO_EXTS]
    logs = [p for p in all_files if p.suffix.lower() in LOG_EXTS]

    by_day = defaultdict(lambda: {"images": 0, "videos": 0, "logs": 0})
    for group, key in [(images, "images"), (videos, "videos"), (logs, "logs")]:
        for p in group:
            ts = infer_timestamp(p)
            if ts:
                by_day[ts.date().isoformat()][key] += 1

    all_points: list[tuple[dt.datetime, float, float]] = []
    parsed_log_count = 0
    for lf in logs:
        pts = read_points(lf)
        if pts:
            parsed_log_count += 1
            all_points.extend(pts)
    all_points.sort(key=lambda x: x[0])

    trips = summarize_trips(all_points, args.trip_gap_min)

    summary = {
        "dataset": str(root),
        "files_total": len(all_files),
        "images_total": len(images),
        "videos_total": len(videos),
        "logs_total": len(logs),
        "logs_with_gps_points": parsed_log_count,
        "gps_points_total": len(all_points),
        "trips_total": len(trips),
        "days_detected": sorted(by_day.keys()),
        "extensions_top": exts.most_common(20),
    }

    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    (out_dir / "daily_counts.json").write_text(json.dumps(by_day, indent=2), encoding="utf-8")
    (out_dir / "trip_summary.json").write_text(json.dumps(trips, indent=2), encoding="utf-8")

    print("Wrote:")
    print(f"- {out_dir / 'summary.json'}")
    print(f"- {out_dir / 'daily_counts.json'}")
    print(f"- {out_dir / 'trip_summary.json'}")
    print("\nQuick summary:")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
