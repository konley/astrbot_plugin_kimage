"""万花筒模块：扇区镜像对称万花筒效果"""

import math
from PIL import Image, ImageDraw
from .gif_utils import is_gif, unfold_frames, save_rgba_gif


def _circular_mask(size):
    mask = Image.new("L", (size, size), 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0, size - 1, size - 1), fill=255)
    return mask


def _kaleidoscope_frame(img, sectors, rotation_deg):
    """对单帧图像应用万花筒效果。"""
    side = min(img.size)
    cx, cy = img.size[0] // 2, img.size[1] // 2
    square = img.crop((cx - side // 2, cy - side // 2,
                       cx + side // 2, cy + side // 2))
    square = square.resize((side, side))

    circle_mask = _circular_mask(side)
    circular = Image.composite(square, Image.new("RGBA", (side, side), (0, 0, 0, 0)), circle_mask)

    out = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    angle_per = 360.0 / sectors

    for i in range(sectors):
        sector = circular.rotate(-i * angle_per - rotation_deg, expand=False, resample=Image.BICUBIC)
        if i % 2 == 1:
            sector = sector.transpose(Image.FLIP_LEFT_RIGHT)

        wedge = Image.new("L", (side, side), 0)
        dw = ImageDraw.Draw(wedge)
        dw.pieslice((0, 0, side - 1, side - 1), 0, angle_per, fill=255)

        masked = Image.composite(sector, Image.new("RGBA", (side, side), (0, 0, 0, 0)), wedge)
        placed = masked.rotate(i * angle_per, expand=False, resample=Image.BICUBIC)
        out = Image.alpha_composite(out, placed)

    return out


def kaleidoscope_image(input_path, output_path,
                       sectors=8, zoom=0.5,
                       angle_step=3, frame_delay=40):
    """生成旋转万花筒 GIF，支持动图输入。"""
    src = Image.open(input_path)
    w, h = src.size
    side = min(w, h)
    cx, cy = w // 2, h // 2
    zoom_side = max(4, int(side * zoom))

    def _prep_zoomed(rgba):
        square = rgba.crop((cx - side // 2, cy - side // 2,
                            cx + side // 2, cy + side // 2))
        return square.resize((zoom_side, zoom_side)).resize((side, side), Image.LANCZOS)

    if getattr(src, "is_animated", False):
        frames, durations = unfold_frames(src)
        n = len(frames)
        processed = []
        for i, f in enumerate(frames):
            zoomed = _prep_zoomed(f.convert("RGBA"))
            angle = (360.0 / n) * i
            processed.append(_kaleidoscope_frame(zoomed, sectors, angle))
        save_rgba_gif(processed, durations, output_path, loop=0)
        return

    rgba = src.convert("RGBA")
    zoomed = _prep_zoomed(rgba)
    n_frames = max(1, int(360 / abs(angle_step)))
    actual_step = 360.0 / n_frames
    frames = [_kaleidoscope_frame(zoomed, sectors, i * actual_step) for i in range(n_frames)]
    save_rgba_gif(frames, [frame_delay] * n_frames, output_path, loop=0)
