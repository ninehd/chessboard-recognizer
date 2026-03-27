import numpy as np
import PIL.Image

from constants import IMG_SIZE

BOARD_SIZE = IMG_SIZE * 8  # 768 for IMG_SIZE=96

def _get_resized_chessboard(chessboard_img_path):
    """ chessboard_img_path = path to a chessboard image
        Returns a BOARD_SIZExBOARD_SIZE image of a chessboard (IMG_SIZExIMG_SIZE per tile)
    """
    img_data = PIL.Image.open(chessboard_img_path).convert('RGB')
    return img_data.resize([BOARD_SIZE, BOARD_SIZE], PIL.Image.BILINEAR)

def get_chessboard_tiles(chessboard_img_path, use_grayscale=True):
    """ chessboard_img_path = path to a chessboard image
        use_grayscale = true/false for whether to return tiles in grayscale

        Returns a list (length 64) of IMG_SIZExIMG_SIZE image data
    """
    img_data = _get_resized_chessboard(chessboard_img_path)
    if use_grayscale:
        img_data = img_data.convert('L', (0.2989, 0.5870, 0.1140, 0))
    chessboard_img = np.asarray(img_data, dtype=np.uint8)
    # 64 tiles in order from top-left to bottom-right (A8, B8, ..., G1, H1)
    tiles = [None] * 64
    for rank in range(8): # rows/ranks (numbers)
        for file in range(8): # columns/files (letters)
            sq_i = rank * 8 + file
            y1 = rank * IMG_SIZE
            y2 = (rank + 1) * IMG_SIZE
            x1 = file * IMG_SIZE
            x2 = (file + 1) * IMG_SIZE
            if use_grayscale:
                tile = chessboard_img[y1:y2, x1:x2]
                tiles[sq_i] = PIL.Image.fromarray(tile)
            else:
                tile = chessboard_img[y1:y2, x1:x2, :]
                tiles[sq_i] = PIL.Image.fromarray(tile, 'RGB')
    return tiles
