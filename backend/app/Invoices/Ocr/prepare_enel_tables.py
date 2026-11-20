"""Separate non-overlapping ENEL panels; never recognize or modify numeric text."""
import json
import math
import os
import sys
from pathlib import Path

from PIL import Image


def bands(counts, width, threshold):
    runs = []
    for y, count in enumerate(counts):
        if count > width * threshold:
            if not runs or y > runs[-1][1] + 1:
                runs.append([y, y])
            else:
                runs[-1][1] = y
    return [run for run in runs if run[1] - run[0] >= 3]


def is_blue(pixel):
    r, g, b = pixel
    return b > r * 1.3 and g > r * 1.15 and b > 80


def panels(pixels, width, band):
    counts = [sum(is_blue(pixels[y * width + x]) for y in range(band[0], band[1] + 1)) for x in range(width)]
    filled = [x for x, count in enumerate(counts) if count > (band[1] - band[0]) * 0.5]
    if not filled:
        return []
    runs = []
    for x in range(min(filled), max(filled) + 1):
        if counts[x] > 0:
            if not runs or x > runs[-1][1] + 1:
                runs.append([x, x])
            else:
                runs[-1][1] = x
    return [run for run in runs if run[1] - run[0] > width * 0.12]


def prepare(source, directory, max_pixels):
    with Image.open(source) as opened:
        if opened.width * opened.height > max_pixels:
            raise ValueError("Image exceeds the pixel budget")
        image = opened.convert("RGB")
    thumb = image.copy()
    thumb.thumbnail((850, 1400))
    width, height = thumb.size
    pixels = list(thumb.getdata())
    counts = [sum(is_blue(pixel) for pixel in pixels[y * width:(y + 1) * width]) for y in range(height)]
    wide = [band for band in bands(counts, width, 0.60) if height * 0.20 < band[0] < height * 0.65]
    if len(wide) < 2:
        return []
    table, footer = wide[:2]
    table_panels = panels(pixels, width, table)
    footer_panels = panels(pixels, width, footer)
    following = [band[0] for band in bands(counts, width, 0.25) if band[0] > footer[1] + 10]
    if len(table_panels) != 2 or len(footer_panels) < 2 or not following:
        return []
    scale = image.width / width
    rectangles = [(left + 1, table[1] + 1, right, footer[0] - 1) for left, right in table_panels]
    rectangles.extend((left + 1, footer[0], right, following[0] - 1) for left, right in footer_panels)
    files = []
    for index, rectangle in enumerate(rectangles):
        box = tuple(round(value * scale) for value in rectangle)
        crop = image.crop(box)
        factor = min(4.0, math.sqrt(max_pixels / (crop.width * crop.height)), 10000 / max(crop.size))
        size = (max(1, int(crop.width * factor)), max(1, int(crop.height * factor)))
        crop = crop.resize(size, Image.Resampling.LANCZOS)
        name = f"panel-{index}.png"
        crop.save(Path(directory) / name)
        files.append(name)
    return files


if __name__ == "__main__":
    os.umask(0o077)
    print(json.dumps(prepare(sys.argv[1], sys.argv[2], int(sys.argv[3]))))
