import math
import random
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter, ImageOps
import scipy.optimize

# --- PALETTE & CANVAS CONFIG ---
CANVAS_W, CANVAS_H = 1180, 610
PORTRAIT_W, PORTRAIT_H = 300, 340
PORTRAIT_X, PORTRAIT_Y = 45, 135

# Color Definitions
C_BG_DARK = "#0A101F"
C_UI_CHROME = "#10B981"
C_ACCENT_DARK = "#A78BFA"  # Portrait dark mode
C_ACCENT_LIGHT = "#7C3AED" # Portrait light mode
C_TRAVELLER = "#22D3EE"

def generate_dither(image_path, is_dark_mode=True):
    """Processes image, applies 1-bit dither, and handles dark-mode background segmentation."""
    img = Image.open(image_path).convert("L")
    
    # 1. Crop Head & Shoulders (300x340)
    w, h = img.size
    crop_box = (int(w * 0.15), int(h * 0.05), int(w * 0.85), int(h * 0.85))
    img = img.crop(crop_box).resize((PORTRAIT_W, PORTRAIT_H), Image.Resampling.LANCZOS)
    
    # 2. Contrast & Unsharp Mask
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(1.3)
    img = img.filter(ImageFilter.UnsharpMask(radius=3, percent=140))
    
    arr = np.array(img, dtype=float)
    
    # 3. Segmentation for Dark Mode
    if is_dark_mode:
        # Simple thresholding/masking to keep subject only
        mask = arr > 45
        arr[~mask] = 255.0  # Clear background
    
    # 4. Floyd-Steinberg Dither (Serpentine Order)
    h_len, w_len = arr.shape
    dots = []
    
    for y in range(h_len):
        x_range = range(w_len) if y % 2 == 0 else range(w_len - 1, -1, -1)
        for x in x_range:
            old_val = arr[y, x]
            new_val = 0 if old_val < 128 else 255
            arr[y, x] = new_val
            error = old_val - new_val
            
            # Draw dot on dark pixels
            if new_val == 0:
                dots.append((x, y))
                
            # Distribute error
            if y % 2 == 0:
                if x + 1 < w_len: arr[y, x + 1] += error * 7 / 16
                if y + 1 < h_len:
                    if x > 0: arr[y + 1, x - 1] += error * 3 / 16
                    arr[y + 1, x] += error * 5 / 16
                    if x + 1 < w_len: arr[y + 1, x + 1] += error * 1 / 16
            else:
                if x - 1 >= 0: arr[y, x - 1] += error * 7 / 16
                if y + 1 < h_len:
                    if x + 1 < w_len: arr[y + 1, x + 1] += error * 3 / 16
                    arr[y + 1, x] += error * 5 / 16
                    if x - 1 >= 0: arr[y + 1, x - 1] += error * 1 / 16
                    
    return dots

def build_svg(is_dark=True):
    accent_color = C_ACCENT_DARK if is_dark else C_ACCENT_LIGHT
    bg_color = C_BG_DARK if is_dark else "#F8FAFC"
    text_main = "#F3F4F6" if is_dark else "#0F172A"
    
    dots = generate_dither("photo.png", is_dark_mode=is_dark)
    
    # Pre-grouping Noise (sigma ~4) to prevent blocky linear grid artifacts
    grouped_bands = [[] for _ in range(94)]
    for x, y in dots:
        noisy_y = y + random.gauss(0, 4)
        band_idx = int(np.clip((noisy_y / PORTRAIT_H) * 94, 0, 93))
        grouped_bands[band_idx].append((x, y))
        
    svg_lines = []
    svg_lines.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {CANVAS_W} {CANVAS_H}" width="{CANVAS_W}" height="{CANVAS_H}">')
    svg_lines.append(f'<rect width="100%" height="100%" fill="{bg_color}"/>')
    
    # Terminal UI Chrome
    svg_lines.append(f'<rect x="20" y="20" width="1140" height="570" rx="10" fill="none" stroke="{C_UI_CHROME}" stroke-width="2"/>')
    svg_lines.append(f'<text x="40" y="50" font-family="monospace" font-size="14" fill="{C_UI_CHROME}">VISUAL.MAP — profile.sh --live</text>')
    svg_lines.append(f'<line x1="20" y1="65" x2="1160" y2="65" stroke="{C_UI_CHROME}" stroke-width="1"/>')
    
    # Left Frame: Dithered Portrait
    svg_lines.append(f'<g transform="translate({PORTRAIT_X}, {PORTRAIT_Y})">')
    for b_idx, band in enumerate(grouped_bands):
        path_data = " ".join([f"M{x},{y}h1v1h-1z" for x, y in band])
        svg_lines.append(f'  <path d="{path_data}" fill="{accent_color}" shape-rendering="crispEdges">')
        # SMIL Drift animation loop
        svg_lines.append(f'    <animateTransform attributeName="transform" type="translate" values="0,0; 20,0; 0,0" keyTimes="0;0.5;1" dur="14.2s" repeatCount="indefinite"/>')
        svg_lines.append(f'  </path>')
    svg_lines.append('</g>')
    
    # Right Frame: Locked Layout System Info
    info_rows = [
        ("Subject", "Subhadip Patra"),
        ("Role", "AI/ML & Full-Stack Developer"),
        ("Origin", "Kolkata, India"),
        ("Education", "B.Tech Student"),
        ("Status", "Building + Learning + Shipping"),
        ("Core.Lang", "Python, JS, C, C++, HTML, CSS"),
        ("Core.Frontend", "React, Tailwind CSS"),
        ("Core.Backend", "Node.js, Express.js"),
        ("Core.Database", "MySQL, MongoDB"),
        ("Core.Infra", "Git, Firebase, GCP, Vercel"),
        ("Grid.Mail", "subhadippatra789@gmail.com"),
        ("Grid.LinkedIn", "subhadip-patra-004532325"),
        ("Grid.GitHub", "Subhadip6666")
    ]
    
    start_x, start_y = 520, 120
    row_height = 23
    
    # Pulse LIVE badge
    svg_lines.append(f'<circle cx="{start_x}" cy="{start_y - 20}" r="5" fill="#EF4444"><animate attributeName="opacity" values="1;0.2;1" dur="1.5s" repeatCount="indefinite"/></circle>')
    svg_lines.append(f'<text x="{start_x + 15}" y="{start_y - 16}" font-family="monospace" font-size="12" fill="#EF4444">LIVE</text>')
    
    # Pill Tag
    svg_lines.append(f'<rect x="{start_x + 60}" y="{start_y - 30}" width="140" height="20" rx="10" fill="{C_UI_CHROME}" opacity="0.2"/>')
    svg_lines.append(f'<text x="{start_x + 70}" y="{start_y - 16}" font-family="monospace" font-size="14" fill="{C_UI_CHROME}">@Subhadip6666</text>')
    
    for i, (label, val) in enumerate(info_rows):
        cy = start_y + (i * row_height)
        dots_count = max(2, 45 - len(label) - len(val))
        leader = "." * dots_count
        
        svg_lines.append(
            f'<text x="{start_x}" y="{cy}" font-family="monospace" font-size="14" fill="{C_UI_CHROME}" textLength="160" lengthAdjust="spacingAndGlyphs">{label}</text>'
        )
        svg_lines.append(
            f'<text x="{start_x + 170}" y="{cy}" font-family="monospace" font-size="14" fill="#4B5563">{leader}</text>'
        )
        svg_lines.append(
            f'<text x="{start_x + 350}" y="{cy}" font-family="monospace" font-size="14" fill="{text_main}" textLength="250" lengthAdjust="spacingAndGlyphs">{val}</text>'
        )

    svg_lines.append('</svg>')
    
    out_filename = "dark.svg" if is_dark else "light.svg"
    with open(out_filename, "w") as f:
        f.write("\n".join(svg_lines))

# Build both SVGs
build_svg(is_dark=True)
build_svg(is_dark=False)