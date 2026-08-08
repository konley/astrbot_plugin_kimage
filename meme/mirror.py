"""镜像对称模块：左/右/上/下半边对称 + 斜边对称，支持静态图和 GIF"""

import numpy as np
from PIL import Image
from .gif_utils import is_gif, unfold_frames, save_rgba_gif


def _mirror_static(img: Image.Image, keep: str) -> Image.Image:
    """对单帧执行半边对称"""
    w, h = img.size
    if keep == "left":
        half = img.crop((0, 0, w // 2, h))
        flipped = half.transpose(Image.FLIP_LEFT_RIGHT)
        result = Image.new("RGBA", (w, h))
        result.paste(half, (0, 0))
        result.paste(flipped, (w // 2, 0))
    elif keep == "right":
        half = img.crop((w // 2, 0, w, h))
        flipped = half.transpose(Image.FLIP_LEFT_RIGHT)
        result = Image.new("RGBA", (w, h))
        result.paste(flipped, (0, 0))
        result.paste(half, (w // 2, 0))
    elif keep == "top":
        half = img.crop((0, 0, w, h // 2))
        flipped = half.transpose(Image.FLIP_TOP_BOTTOM)
        result = Image.new("RGBA", (w, h))
        result.paste(half, (0, 0))
        result.paste(flipped, (0, h // 2))
    else:  # bottom
        half = img.crop((0, h // 2, w, h))
        flipped = half.transpose(Image.FLIP_TOP_BOTTOM)
        result = Image.new("RGBA", (w, h))
        result.paste(flipped, (0, 0))
        result.paste(half, (0, h // 2))
    return result


def _mirror_diagonal_static(img: Image.Image, keep: str) -> Image.Image:
    """斜边对称单帧（\\ 或 / 对角线），支持任意宽高比。

    在归一化坐标 [0,1]^2 上做对角线反射，再映射回像素，
    避免旧实现直接交换 x/y（仅对正方形合法）导致长方形越界。
    """
    arr = np.array(img)
    h, w = arr.shape[:2]
    if h <= 1 or w <= 1:
        return img.copy() if hasattr(img, "copy") else Image.fromarray(arr.copy())

    y_idx, x_idx = np.mgrid[0:h, 0:w].astype(np.float64)
    # 归一化到单位正方形，使矩形真实对角线对应 u=v 或 u+v=1
    u = x_idx / (w - 1)
    v = y_idx / (h - 1)

    if keep == "diag_tl":
        # \ 对角线：单位坐标反射 (u,v)->(v,u)；覆盖 v>=u 一侧（与旧正方形行为一致）
        mask = v >= u
        src_u, src_v = v, u
    else:  # diag_tr
        # / 对角线：单位坐标反射 (u,v)->(1-v, 1-u)
        mask = (u + v) >= 1.0
        src_u = 1.0 - v
        src_v = 1.0 - u

    src_x = np.clip(np.rint(src_u * (w - 1)), 0, w - 1).astype(np.intp)
    src_y = np.clip(np.rint(src_v * (h - 1)), 0, h - 1).astype(np.intp)

    result = arr.copy()
    result[mask] = arr[src_y[mask], src_x[mask]]
    return Image.fromarray(result)


def _mirror_gif(input_path: str, output_path: str, keep: str) -> str:
    gif = Image.open(input_path)
    src_palette = gif.getpalette()
    src_trans = gif.info.get("transparency")
    frames, durations = unfold_frames(gif)
    if keep in ("diag_tl", "diag_tr"):
        mirrored = [_mirror_diagonal_static(f, keep) for f in frames]
    else:
        mirrored = [_mirror_static(f, keep) for f in frames]
    save_rgba_gif(mirrored, durations, output_path, loop=gif.info.get("loop", 0),
                  source_palette=src_palette, source_trans_idx=src_trans)
    return output_path


def mirror_by_type(input_path: str, output_path: str, mirror_type: int = 1):
    """统一对称入口。

    mirror_type:
        1 = 左对称（保留左半部镜像到右半部）[默认]
        2 = 上对称（保留上半部镜像到下半部）
        3 = \\ 对角线对称（保留左上三角形）
        4 = / 对角线对称（保留右上三角形）
        5 = 右对称（保留右半部镜像到左半部）
        6 = 下对称（保留下半部镜像到上半部）
    """
    mapping = {1: "left", 2: "top", 3: "diag_tl", 4: "diag_tr", 5: "right", 6: "bottom"}
    keep = mapping.get(mirror_type, "left")

    if not is_gif(input_path):
        img = Image.open(input_path).convert("RGBA")
        if keep in ("diag_tl", "diag_tr"):
            _mirror_diagonal_static(img, keep).save(output_path, "PNG")
        else:
            _mirror_static(img, keep).save(output_path, "PNG")
        return

    _mirror_gif(input_path, output_path, keep)


def mirror_left(input_path: str, output_path: str) -> str:
    if is_gif(input_path):
        return _mirror_gif(input_path, output_path, "left")
    img = Image.open(input_path).convert("RGBA")
    _mirror_static(img, "left").save(output_path, "PNG")
    return output_path


def mirror_right(input_path: str, output_path: str) -> str:
    if is_gif(input_path):
        return _mirror_gif(input_path, output_path, "right")
    img = Image.open(input_path).convert("RGBA")
    _mirror_static(img, "right").save(output_path, "PNG")
    return output_path


def mirror_top(input_path: str, output_path: str) -> str:
    if is_gif(input_path):
        return _mirror_gif(input_path, output_path, "top")
    img = Image.open(input_path).convert("RGBA")
    _mirror_static(img, "top").save(output_path, "PNG")
    return output_path


def _extend_frame(frame, direction):
    """对单帧执行延展对称。"""
    w, h = frame.size
    if direction == 1:
        canvas = Image.new("RGBA", (w * 2, h))
        flipped = frame.transpose(Image.FLIP_LEFT_RIGHT)
        canvas.paste(frame, (0, 0))
        canvas.paste(flipped, (w, 0))
    elif direction == 2:
        canvas = Image.new("RGBA", (w * 2, h))
        flipped = frame.transpose(Image.FLIP_LEFT_RIGHT)
        canvas.paste(flipped, (0, 0))
        canvas.paste(frame, (w, 0))
    elif direction == 3:
        canvas = Image.new("RGBA", (w, h * 2))
        flipped = frame.transpose(Image.FLIP_TOP_BOTTOM)
        canvas.paste(flipped, (0, 0))
        canvas.paste(frame, (0, h))
    else:
        canvas = Image.new("RGBA", (w, h * 2))
        flipped = frame.transpose(Image.FLIP_TOP_BOTTOM)
        canvas.paste(frame, (0, 0))
        canvas.paste(flipped, (0, h))
    return canvas


def extend_symmetry(input_path: str, output_path: str, direction: int = 1):
    """延展对称：放大画布，翻转镜像拼接到外侧。支持 GIF。

    direction:
        1 = 向右延展（原图在左，翻转拼到右）
        2 = 向左延展（原图在右，翻转拼到左）
        3 = 向上延展（原图在下，翻转拼到上）
        4 = 向下延展（原图在上，翻转拼到下）
    """
    src = Image.open(input_path)
    if not is_gif(input_path):
        _extend_frame(src.convert("RGBA"), direction).save(output_path, "PNG")
        return

    frames, durations = unfold_frames(src)
    processed = [_extend_frame(f, direction) for f in frames]
    save_rgba_gif(processed, durations, output_path, loop=src.info.get("loop", 0))


def mirror_bottom(input_path: str, output_path: str) -> str:
    if is_gif(input_path):
        return _mirror_gif(input_path, output_path, "bottom")
    img = Image.open(input_path).convert("RGBA")
    _mirror_static(img, "bottom").save(output_path, "PNG")
    return output_path
