#!/usr/bin/env python3
"""Generate diverse chessboard training images locally using python-chess.

Supports both Lichess SVG piece sets and chess.com PNG piece sets.
Varies: square colors + piece sets + random positions.
"""
import io
import os
import re

import cairosvg
import chess
import chess.svg
import numpy as np
import PIL.Image

from constants import CHESSBOARDS_DIR, FEN_CHARS, IMG_SIZE

OUTPUT_DIR = os.path.join(CHESSBOARDS_DIR, "generated")
os.makedirs(OUTPUT_DIR, exist_ok=True)

BOARD_PX = IMG_SIZE * 8  # 768 for IMG_SIZE=96

LICHESS_DIR = "piece_sets"
CHESSCOM_DIR = "piece_sets_chesscom"

SVG_TO_KEY = {
    "wK": "K", "wQ": "Q", "wR": "R", "wB": "B", "wN": "N", "wP": "P",
    "bK": "k", "bQ": "q", "bR": "r", "bB": "b", "bN": "n", "bP": "p",
}

PIECE_IDS = {
    "K": ("white-king", "white king"),
    "Q": ("white-queen", "white queen"),
    "R": ("white-rook", "white rook"),
    "B": ("white-bishop", "white bishop"),
    "N": ("white-knight", "white knight"),
    "P": ("white-pawn", "white pawn"),
    "k": ("black-king", "black king"),
    "q": ("black-queen", "black queen"),
    "r": ("black-rook", "black rook"),
    "b": ("black-bishop", "black bishop"),
    "n": ("black-knight", "black knight"),
    "p": ("black-pawn", "black pawn"),
}

# FEN key to chess.com filename (without extension)
FEN_TO_CHESSCOM = {
    "K": "wK", "Q": "wQ", "R": "wR", "B": "wB", "N": "wN", "P": "wP",
    "k": "bK", "q": "bQ", "r": "bR", "b": "bB", "n": "bN", "p": "bP",
}

COLOR_SCHEMES = [
    ("#f0d9b5", "#b58863"),
    ("#ffffdd", "#86a666"),
    ("#ebecd0", "#779556"),
    ("#dee3e6", "#8ca2ad"),
    ("#e8ceab", "#a67d5d"),
    ("#e8e0f0", "#9070a0"),
    ("#d0d0d0", "#808080"),
    ("#ffffff", "#000000"),
    ("#e8e0a0", "#a0a030"),
    ("#f0e0d0", "#c08060"),
    ("#e0f0f8", "#6090b0"),
    ("#f5deb3", "#8b7355"),
    ("#d8e8d0", "#6b8e5a"),
    ("#c8d0d8", "#5a6a7a"),
    ("#ffffff", "#d0d0d0"),
]


# --- Lichess SVG piece sets ---

def load_svg_piece_set(name):
    """Load a Lichess SVG piece set for chess.svg injection."""
    pieces = {}
    ps_dir = os.path.join(LICHESS_DIR, name)
    for svg_name, key in SVG_TO_KEY.items():
        path = os.path.join(ps_dir, f"{svg_name}.svg")
        if not os.path.exists(path):
            return None
        with open(path) as f:
            svg_content = f.read()
        match = re.search(r"<svg[^>]*>(.*)</svg>", svg_content, re.DOTALL)
        vb_match = re.search(r'viewBox="([^"]*)"', svg_content)
        if match:
            inner = match.group(1).strip()
            viewbox = vb_match.group(1) if vb_match else "0 0 45 45"
            parts = viewbox.split()
            vb_w = float(parts[2]) - float(parts[0])
            piece_id, piece_class = PIECE_IDS[key]
            if vb_w != 45 and vb_w > 0:
                scale = 45.0 / vb_w
                pieces[key] = f'<g id="{piece_id}" class="{piece_class}" transform="scale({scale})">{inner}</g>'
            else:
                pieces[key] = f'<g id="{piece_id}" class="{piece_class}">{inner}</g>'
    return pieces if len(pieces) == 12 else None


def get_lichess_sets():
    """List available Lichess SVG piece sets."""
    sets = []
    if not os.path.exists(LICHESS_DIR):
        return sets
    for name in sorted(os.listdir(LICHESS_DIR)):
        if load_svg_piece_set(name) is not None:
            sets.append(("lichess", name))
    return sets


def generate_svg_board(arr, colors_dict, piece_set_name):
    """Render a board using chess.svg with Lichess SVG pieces."""
    pieces_svg = load_svg_piece_set(piece_set_name)
    original_pieces = dict(chess.svg.PIECES)
    chess.svg.PIECES.update(pieces_svg)
    try:
        board = fen_array_to_board(arr)
        svg_data = chess.svg.board(board, size=BOARD_PX, coordinates=False, colors=colors_dict)
        png_data = cairosvg.svg2png(
            bytestring=svg_data.encode(), output_width=BOARD_PX, output_height=BOARD_PX
        )
        return PIL.Image.open(io.BytesIO(png_data))
    finally:
        chess.svg.PIECES.update(original_pieces)


# --- Chess.com PNG piece sets ---

def load_png_piece_set(name):
    """Load a chess.com PNG piece set as PIL Images."""
    pieces = {}
    ps_dir = os.path.join(CHESSCOM_DIR, name)
    for fen_key, filename in FEN_TO_CHESSCOM.items():
        path = os.path.join(ps_dir, f"{filename}.png")
        if not os.path.exists(path):
            return None
        pieces[fen_key] = PIL.Image.open(path).convert("RGBA").resize(
            (IMG_SIZE, IMG_SIZE), PIL.Image.LANCZOS
        )
    return pieces if len(pieces) == 12 else None


def get_chesscom_sets():
    """List available chess.com PNG piece sets."""
    sets = []
    if not os.path.exists(CHESSCOM_DIR):
        return sets
    for name in sorted(os.listdir(CHESSCOM_DIR)):
        if load_png_piece_set(name) is not None:
            sets.append(("chesscom", name))
    return sets


def hex_to_rgb(hex_color):
    h = hex_color.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def generate_png_board(arr, colors_dict, piece_set_name):
    """Render a board by compositing PNG pieces onto a colored grid."""
    light = hex_to_rgb(colors_dict["square light"])
    dark = hex_to_rgb(colors_dict["square dark"])
    pieces = load_png_piece_set(piece_set_name)

    board_img = PIL.Image.new("RGB", (BOARD_PX, BOARD_PX))

    for rank in range(8):
        for file in range(8):
            x = file * IMG_SIZE
            y = rank * IMG_SIZE
            is_light = (rank + file) % 2 == 0
            color = light if is_light else dark

            # Draw square
            square = PIL.Image.new("RGB", (IMG_SIZE, IMG_SIZE), color)
            board_img.paste(square, (x, y))

            # Draw piece if any
            fen_char = arr[rank * 8 + file]
            if fen_char != "1" and fen_char in pieces:
                piece_img = pieces[fen_char]
                board_img.paste(piece_img, (x, y), piece_img)  # use alpha mask

    return board_img


# --- Common ---

def random_fen_array():
    chars = list(FEN_CHARS)
    return np.random.choice(chars, 64)


def fen_array_to_board(arr):
    rows = []
    for rank in range(8):
        row = "".join(arr[rank * 8 : (rank + 1) * 8])
        for length in reversed(range(2, 9)):
            row = row.replace("1" * length, str(length))
        rows.append(row)
    fen = "/".join(rows) + " w - - 0 1"
    board = chess.Board()
    board.set_fen(fen)
    return board


def fen_array_to_filename(arr):
    rows = []
    for rank in range(8):
        row = "".join(arr[rank * 8 : (rank + 1) * 8])
        rows.append(row)
    return "-".join(rows)


def generate(n_per_combo=30):
    """Generate boards for all piece sets × color schemes."""
    np.random.seed(456)
    total = 0

    all_sets = get_lichess_sets() + get_chesscom_sets()
    print(f"Found {len(all_sets)} piece sets ({len(get_lichess_sets())} Lichess + {len(get_chesscom_sets())} chess.com)")
    print(f"Color schemes: {len(COLOR_SCHEMES)}")
    print(f"Target: {n_per_combo} boards per piece set")
    print(f"Expected: ~{len(all_sets) * n_per_combo} boards\n")

    for idx, (source, ps_name) in enumerate(all_sets):
        count = 0
        for i in range(n_per_combo):
            arr = random_fen_array()
            filename = f"{ps_name}_{fen_array_to_filename(arr)}"
            filepath = os.path.join(OUTPUT_DIR, filename + ".png")

            light, dark = COLOR_SCHEMES[i % len(COLOR_SCHEMES)]
            colors = {"square light": light, "square dark": dark}

            try:
                if source == "lichess":
                    img = generate_svg_board(arr, colors, ps_name)
                else:
                    img = generate_png_board(arr, colors, ps_name)
                img.save(filepath)
                count += 1
            except Exception as e:
                print(f"  Error ({ps_name}): {e}")

        total += count
        print(f"[{idx+1}/{len(all_sets)}] {ps_name} ({source}): {count} boards")

    print(f"\nTotal: {total} boards generated")


if __name__ == "__main__":
    generate()
