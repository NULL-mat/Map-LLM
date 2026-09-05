"""Utility helpers for unified mapping tools."""

import platform
import re
from pathlib import Path
from typing import Tuple

import matplotlib.pyplot as plt
from matplotlib import font_manager


def setup_chinese_font():
    """Configure a Chinese-capable matplotlib font."""
    try:
        custom_font_paths = [
            Path("/usr/share/fonts/truetype/custom/msyh.ttc"),
            Path(__file__).resolve().parents[3] / "assets" / "fonts" / "msyh.ttc",
        ]
        for font_path in custom_font_paths:
            if font_path.exists():
                try:
                    font_manager.fontManager.addfont(str(font_path))
                    font_name = font_manager.FontProperties(fname=str(font_path)).get_name()
                    plt.rcParams["font.sans-serif"] = [font_name] + plt.rcParams["font.sans-serif"]
                    plt.rcParams["axes.unicode_minus"] = False
                    return font_name
                except Exception:
                    continue

        system = platform.system()
        if system == "Windows":
            font_candidates = ["Microsoft YaHei", "SimHei", "SimSun", "DejaVu Sans"]
        elif system == "Darwin":
            font_candidates = ["PingFang SC", "Heiti SC", "STHeiti", "Arial Unicode MS", "DejaVu Sans"]
        else:
            font_candidates = ["Noto Sans CJK SC", "WenQuanYi Micro Hei", "DejaVu Sans"]

        plt.rcParams["font.sans-serif"] = font_candidates
        plt.rcParams["axes.unicode_minus"] = False
        return font_candidates[0]
    except Exception as e:
        print(f"字体设置失败: {e}")
        return None


def wrap_text(text: str, max_chars_per_line: int = 30) -> str:
    """Wrap long text using punctuation-aware line breaks."""
    if not text or len(text) <= max_chars_per_line:
        return text

    punctuation = r"[，。！？；：、]"
    parts = re.split(f"({punctuation})", text)

    lines = []
    current_line = ""

    for part in parts:
        if len(current_line) + len(part) <= max_chars_per_line:
            current_line += part
        else:
            if current_line:
                lines.append(current_line)
            current_line = part

    if current_line:
        lines.append(current_line)

    return "\n".join(lines)


def parse_coordinates(coord_str: str) -> Tuple[float, float]:
    """Parse a coordinate string into longitude and latitude."""
    coord_str = (coord_str or "").strip()
    if "," in coord_str:
        lon_str, lat_str = coord_str.split(",", 1)
    else:
        parts = coord_str.split()
        if len(parts) != 2:
            raise ValueError(f"无法解析坐标: {coord_str}")
        lon_str, lat_str = parts
    return float(lon_str.strip()), float(lat_str.strip())
