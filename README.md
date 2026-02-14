# News Thumbnail Studio (Arabic + English)

A small Streamlit app to mass-produce news images with consistent branding.

## Why this solves your workflow
- Randomly pick images by keyword from a large local library (e.g., `trump`, `gaza`, `sport`).
- Keep the same logo position, font style, shadow, and colors every time.
- Add optional overlay/filter PNG on all exports.
- Crop/zoom/pan to fit multiple aspect ratios cleanly.
- Support bilingual headlines (Arabic RTL + English).
- Switch to **Breaking News** mode for text-only cards with your gradient background.

## Features
1. **Image source options**
   - Pick random image from your database folder by keyword.
   - Or upload a specific custom image manually.
2. **Composition controls**
   - Aspect presets: 1:1, 4:5, 9:16, 16:9.
   - Zoom + pan crop controls.
   - Brightness adjustment.
3. **Brand settings**
   - Logo PNG (auto-place top/bottom + left/right).
   - Overlay/filter PNG with opacity.
4. **Headline styling**
   - Font upload (`.ttf` / `.otf`).
   - Font size, color, alignment (left/center/right).
   - Shadow enable/disable with color + offset.
   - Arabic shaping + RTL rendering using `arabic-reshaper` + `python-bidi`.
5. **Export**
   - One-click PNG export.

## Quick start
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Suggested folder structure for 2000+ images
```text
library/
  politics/
    trump_001.jpg
    trump_002.jpg
    biden_001.jpg
  war/
    gaza_001.jpg
  sports/
    messi_001.jpg
```

The random picker currently searches by filename stem. So `trump_123.jpg` is found when keyword is `trump`.

## Android options
### Option A (fastest): Use it as a web app on Android
- Host Streamlit app on a server/VPS.
- Open URL on Android browser.
- "Add to Home Screen" for app-like usage.

### Option B: Real APK wrapper
- Wrap the hosted web app URL using **Trusted Web Activity (TWA)** or **WebView** shell.
- Good for publishing quickly with minimal app rewrite.

### Option C: Native rewrite (best long-term)
- Rebuild UI in Flutter.
- Reuse same image pipeline logic (Python backend API or Dart image libs).
- Export proper APK/AAB for Play Store.

## Next upgrades I recommend
- Save/load presets (per channel style).
- Auto text fit (dynamic font size to avoid overflow).
- Multi-line title/subtitle template sets.
- Bulk mode: generate 20 cards at once from a CSV of headlines.
- Optional AI image generation input.
