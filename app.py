import io
import random
from pathlib import Path

import streamlit as st
from PIL import Image, ImageColor, ImageDraw, ImageEnhance, ImageFont

try:
    import arabic_reshaper
    from bidi.algorithm import get_display
except Exception:  # optional deps
    arabic_reshaper = None
    get_display = None


ASPECTS = {
    "Instagram Post (1:1)": (1080, 1080),
    "Instagram Portrait (4:5)": (1080, 1350),
    "Story/Reel (9:16)": (1080, 1920),
    "YouTube Thumb (16:9)": (1280, 720),
    "X/Twitter (16:9)": (1600, 900),
}


def has_arabic(text: str) -> bool:
    return any("\u0600" <= ch <= "\u06FF" for ch in text)


def shape_text(text: str) -> str:
    if has_arabic(text) and arabic_reshaper and get_display:
        return get_display(arabic_reshaper.reshape(text))
    return text


def pick_random_image(folder: Path, keyword: str) -> Path | None:
    if not folder.exists():
        return None
    images = [
        p
        for p in folder.rglob("*")
        if p.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"} and keyword.lower() in p.stem.lower()
    ]
    return random.choice(images) if images else None


def fit_with_zoom_pan(img: Image.Image, target_size: tuple[int, int], zoom: float, pan_x: float, pan_y: float) -> Image.Image:
    tw, th = target_size
    src_w, src_h = img.size

    base_scale = max(tw / src_w, th / src_h)
    scale = base_scale * zoom
    resized = img.resize((int(src_w * scale), int(src_h * scale)), Image.Resampling.LANCZOS)

    rw, rh = resized.size
    max_x = max(0, rw - tw)
    max_y = max(0, rh - th)

    left = int((max_x / 2) + pan_x * (max_x / 2))
    top = int((max_y / 2) + pan_y * (max_y / 2))
    left = max(0, min(left, max_x))
    top = max(0, min(top, max_y))

    return resized.crop((left, top, left + tw, top + th))


def build_gradient(size: tuple[int, int], top_color: str, bottom_color: str) -> Image.Image:
    w, h = size
    top_rgb = ImageColor.getrgb(top_color)
    bottom_rgb = ImageColor.getrgb(bottom_color)
    gradient = Image.new("RGB", size, top_rgb)
    draw = ImageDraw.Draw(gradient)

    for y in range(h):
        ratio = y / max(1, h - 1)
        color = tuple(int(top_rgb[i] * (1 - ratio) + bottom_rgb[i] * ratio) for i in range(3))
        draw.line([(0, y), (w, y)], fill=color)

    return gradient


def get_font(font_path: str | None, font_size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    if font_path:
        try:
            return ImageFont.truetype(font_path, font_size)
        except Exception:
            pass
    try:
        return ImageFont.truetype("DejaVuSans.ttf", font_size)
    except Exception:
        return ImageFont.load_default()


def draw_text_block(
    image: Image.Image,
    text: str,
    font: ImageFont.ImageFont,
    color: str,
    align: str,
    shadow: bool,
    shadow_color: str,
    shadow_offset: int,
    margin_x: int,
    margin_bottom: int,
):
    draw = ImageDraw.Draw(image)
    text = shape_text(text)

    bbox = draw.multiline_textbbox((0, 0), text, font=font, spacing=8, align=align)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]

    if align == "left":
        x = margin_x
    elif align == "right":
        x = image.width - margin_x - tw
    else:
        x = (image.width - tw) // 2

    y = image.height - margin_bottom - th

    if shadow:
        draw.multiline_text(
            (x + shadow_offset, y + shadow_offset),
            text,
            font=font,
            fill=shadow_color,
            spacing=8,
            align=align,
        )

    draw.multiline_text((x, y), text, font=font, fill=color, spacing=8, align=align)


def overlay_image(base: Image.Image, overlay: Image.Image, alpha: float) -> Image.Image:
    if overlay.mode != "RGBA":
        overlay = overlay.convert("RGBA")
    overlay = overlay.resize(base.size, Image.Resampling.LANCZOS)

    if alpha < 1.0:
        overlay = overlay.copy()
        overlay.putalpha(int(255 * alpha))

    out = base.convert("RGBA")
    out.alpha_composite(overlay)
    return out


def place_logo(image: Image.Image, logo: Image.Image, where: str, scale_pct: int, padding: int) -> Image.Image:
    logo = logo.convert("RGBA")
    max_w = int(image.width * (scale_pct / 100))
    ratio = max_w / logo.width
    logo = logo.resize((max_w, int(logo.height * ratio)), Image.Resampling.LANCZOS)

    x = padding if "left" in where else image.width - logo.width - padding
    y = padding if "top" in where else image.height - logo.height - padding

    out = image.convert("RGBA")
    out.alpha_composite(logo, (x, y))
    return out


st.set_page_config(page_title="News Thumbnail Studio", layout="wide")
st.title("📰 News Thumbnail Studio")
st.caption("Fast template-based image generator for Arabic + English headlines")

with st.sidebar:
    st.header("Source")
    mode = st.radio("Mode", ["Image + Text", "Breaking News (Text Only)"])

    library_folder = st.text_input("Images folder", value="./library")
    keyword = st.text_input("Keyword (e.g. trump, gaza, sport)", value="trump")

    if st.button("Pick Random Image by Keyword"):
        selected = pick_random_image(Path(library_folder), keyword)
        st.session_state["picked_path"] = str(selected) if selected else ""

    st.text_input("Picked image path", key="picked_path", disabled=True)
    uploaded_image = st.file_uploader("Or upload a specific image", type=["jpg", "jpeg", "png", "webp"])

    st.divider()
    aspect_name = st.selectbox("Aspect", list(ASPECTS.keys()), index=1)
    target_size = ASPECTS[aspect_name]

    zoom = st.slider("Zoom", 1.0, 2.5, 1.15, 0.01)
    pan_x = st.slider("Pan X", -1.0, 1.0, 0.0, 0.01)
    pan_y = st.slider("Pan Y", -1.0, 1.0, 0.0, 0.01)

    brightness = st.slider("Brightness", 0.4, 1.6, 1.0, 0.05)

    st.divider()
    st.header("Brand Defaults")
    logo_file = st.file_uploader("Logo PNG", type=["png"])
    logo_position = st.selectbox("Logo position", ["top-left", "top-right", "bottom-left", "bottom-right"], index=1)
    logo_scale = st.slider("Logo width %", 5, 35, 14)
    logo_padding = st.slider("Logo padding", 0, 80, 24)

    overlay_file = st.file_uploader("Overlay/filter PNG", type=["png"])
    overlay_alpha = st.slider("Overlay opacity", 0.0, 1.0, 0.35, 0.05)

    st.divider()
    st.header("Text")
    headline = st.text_area("Headline", value="Breaking: اكتب العنوان هنا / Write your headline")
    font_file = st.file_uploader("Font file (TTF/OTF)", type=["ttf", "otf"])
    font_size = st.slider("Font size", 24, 140, 72)
    text_color = st.color_picker("Font color", "#FFFFFF")
    align = st.selectbox("Alignment", ["center", "right", "left"], index=0)

    shadow_on = st.checkbox("Text shadow", value=True)
    shadow_color = st.color_picker("Shadow color", "#000000")
    shadow_offset = st.slider("Shadow offset", 0, 15, 4)
    margin_x = st.slider("Horizontal margin", 20, 260, 70)
    margin_bottom = st.slider("Bottom margin", 20, 400, 120)

    st.divider()
    st.header("Breaking News Background")
    bg_top = st.color_picker("Top gradient", "#0A0A23")
    bg_bottom = st.color_picker("Bottom gradient", "#CC0000")

# Compose
if mode == "Image + Text":
    if uploaded_image:
        base = Image.open(uploaded_image).convert("RGB")
    elif st.session_state.get("picked_path"):
        path = Path(st.session_state["picked_path"])
        base = Image.open(path).convert("RGB") if path.exists() else None
    else:
        base = None

    if base is not None:
        canvas = fit_with_zoom_pan(base, target_size, zoom, pan_x, pan_y)
    else:
        canvas = build_gradient(target_size, bg_top, bg_bottom)
        st.info("No source image selected yet. Showing gradient placeholder.")
else:
    canvas = build_gradient(target_size, bg_top, bg_bottom)

if brightness != 1.0:
    canvas = ImageEnhance.Brightness(canvas).enhance(brightness)

if overlay_file:
    ov = Image.open(overlay_file)
    canvas = overlay_image(canvas, ov, overlay_alpha).convert("RGB")

font_path = None
if font_file:
    font_bytes = font_file.getvalue()
    tmp = Path("/tmp/news_font.ttf")
    tmp.write_bytes(font_bytes)
    font_path = str(tmp)

font = get_font(font_path, font_size)
draw_text_block(canvas, headline, font, text_color, align, shadow_on, shadow_color, shadow_offset, margin_x, margin_bottom)

if logo_file:
    logo = Image.open(logo_file)
    canvas = place_logo(canvas, logo, logo_position, logo_scale, logo_padding).convert("RGB")

st.subheader("Preview")
st.image(canvas, use_column_width=True)

buf = io.BytesIO()
canvas.save(buf, format="PNG")
st.download_button("Export PNG", buf.getvalue(), file_name="news_card.png", mime="image/png")
