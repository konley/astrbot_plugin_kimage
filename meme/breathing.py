"""呼吸模块：图片周期缩放，像在呼吸"""

import math
from PIL import Image
from .gif_utils import is_gif, unfold_frames, save_rgba_gif


def breathing_image(input_path, output_path,
                    min_scale=0.92, max_scale=1.08,
                    frames=30, frame_delay=40):
    """生成呼吸缩放 GIF，支持动图输入。

    动图输入时，逐帧呼吸缩放，原始动画与呼吸叠加。
    """
    src = Image.open(input_path)
    if getattr(src, "is_animated", False):
        src_frames, src_durations = unfold_frames(src)
        n_src = len(src_frames)
        processed = []
        for i, f in enumerate(src_frames):
            rgba = f.convert("RGBA")
            w, h = rgba.size
            t = 2 * math.pi * i / n_src
            if t < math.pi:
                p = t / math.pi
                scale = 1.0 - (1.0 - min_scale) * math.sin(p * math.pi / 2)
            else:
                p = (t - math.pi) / math.pi
                scale = 1.0 + (max_scale - 1.0) * math.sin(p * math.pi / 2)
            nw = max(1, int(w * scale))
            nh = max(1, int(h * scale))
            scaled = rgba.resize((nw, nh), Image.LANCZOS)
            canvas = Image.new("RGBA", (w, h), (0, 0, 0, 0))
            canvas.paste(scaled, ((w - nw) // 2, (h - nh) // 2))
            processed.append(canvas)
        save_rgba_gif(processed, src_durations, output_path, loop=0)
        return

    rgba = src.convert("RGBA")
    w, h = rgba.size
    out_frames = []
    for i in range(frames):
        t = 2 * math.pi * i / frames
        if t < math.pi:
            p = t / math.pi
            scale = 1.0 - (1.0 - min_scale) * math.sin(p * math.pi / 2)
        else:
            p = (t - math.pi) / math.pi
            scale = 1.0 + (max_scale - 1.0) * math.sin(p * math.pi / 2)
        nw = max(1, int(w * scale))
        nh = max(1, int(h * scale))
        scaled = rgba.resize((nw, nh), Image.LANCZOS)
        canvas = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        canvas.paste(scaled, ((w - nw) // 2, (h - nh) // 2))
        out_frames.append(canvas)
    save_rgba_gif(out_frames, [frame_delay] * frames, output_path, loop=0)
