#!/usr/bin/env python3
"""Generate chessboard images from multiple sources with diverse styles."""

import os
import time
from urllib import request
from io import BytesIO

import numpy as np
import PIL.Image

from constants import CHESSBOARDS_DIR, FEN_CHARS

OUTPUT_DIR = os.path.join(CHESSBOARDS_DIR, "generated")
os.makedirs(OUTPUT_DIR, exist_ok=True)


def random_fen_array():
    """Generate random 64-char array of FEN characters."""
    chars = list(FEN_CHARS)
    return np.random.choice(chars, 64)


def fen_array_to_compressed(arr):
    """Convert 64-char array to proper compressed FEN string."""
    rows = []
    for rank in range(8):
        row = "".join(arr[rank * 8 : (rank + 1) * 8])
        # Compress consecutive 1s
        for length in reversed(range(2, 9)):
            row = row.replace("1" * length, str(length))
        rows.append(row)
    return "/".join(rows)


def fen_array_to_filename(arr):
    """Convert 64-char array to filename format."""
    rows = []
    for rank in range(8):
        row = "".join(arr[rank * 8 : (rank + 1) * 8])
        rows.append(row)
    return "-".join(rows)


def generate_backscattering(n, pieces=None):
    """Generate from backscattering.de (different piece/board styles)."""
    # Available piece styles
    piece_sets = ["california", "cardinal", "cburnett", "chess7",
                  "chessnut", "companion", "dubrovny", "fantasy",
                  "gioco", "governor", "horsey", "kosal",
                  "leipzig", "letter", "merida", "mono",
                  "pirouetti", "pixel", "staunty", "tatiana"]

    count = 0
    for i in range(n):
        arr = random_fen_array()
        fen = fen_array_to_compressed(arr)
        filename = fen_array_to_filename(arr)
        filepath = os.path.join(OUTPUT_DIR, filename + ".png")
        if os.path.exists(filepath):
            continue

        piece_set = np.random.choice(piece_sets)
        url = f"https://backscattering.de/web-boardimage/board.png?fen={fen}&size=256&piece={piece_set}"

        try:
            img = PIL.Image.open(BytesIO(request.urlopen(url).read()))
            img.save(filepath)
            count += 1
            if count % 10 == 0:
                print(f"  Generated {count}/{n} (backscattering)")
            time.sleep(0.2)  # Be nice to the server
        except Exception as e:
            print(f"  Error: {e}")
            time.sleep(1)

    print(f"Done: {count} images from backscattering.de")
    return count


def generate_fentoimage(n):
    """Generate from fen-to-image.com."""
    count = 0
    for i in range(n):
        arr = random_fen_array()
        fen_param = "/".join("".join(arr[r * 8 : (r + 1) * 8]) for r in range(8))
        filename = fen_array_to_filename(arr)
        filepath = os.path.join(OUTPUT_DIR, filename + ".png")
        if os.path.exists(filepath):
            continue

        url = f"http://www.fen-to-image.com/image/32/{fen_param}"

        try:
            img = PIL.Image.open(BytesIO(request.urlopen(url).read()))
            img.save(filepath)
            count += 1
            if count % 10 == 0:
                print(f"  Generated {count}/{n} (fen-to-image)")
            time.sleep(0.2)
        except Exception as e:
            print(f"  Error: {e}")
            time.sleep(1)

    print(f"Done: {count} images from fen-to-image.com")
    return count


if __name__ == "__main__":
    np.random.seed(42)
    print("Generating training images...")
    print("\n--- backscattering.de (diverse piece sets) ---")
    generate_backscattering(200)
    print("\n--- fen-to-image.com ---")
    generate_fentoimage(100)
    print("\nDone!")
