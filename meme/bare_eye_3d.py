"""裸眼3D模块：分层假象裸眼3D效果"""

from PIL import Image, ImageChops, ImageDraw, ImageFilter
from .gif_utils import is_gif, unfold_frames, save_rgba_gif


def _compute_background(frames):
    """从多帧计算静态背景（中位数合成）。"""
    import numpy as np
    w, h = frames[0].size
    arr = np.stack([np.array(f.convert("RGBA")) for f in frames], axis=0)
    bg = np.median(arr, axis=0).astype(np.uint8)
    return Image.fromarray(bg, "RGBA")


def _draw_dividing_lines(img, spacing=80, line_width=3, line_alpha=200, direction="both"):
    """在图像上画分割白线。"""
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    w, h = img.size
    color = (255, 255, 255, line_alpha)

    step_y = spacing if spacing > 0 else max(1, h // 4)
    step_x = spacing if spacing > 0 else max(1, w // 4)
    if direction in ("horizontal", "both"):
        y = step_y
        while y < h:
            draw.line([(0, y), (w, y)], fill=color, width=line_width)
            y += step_y
    if direction in ("vertical", "both"):
        x = step_x
        while x < w:
            draw.line([(x, 0), (x, h)], fill=color, width=line_width)
            x += step_x
    return Image.alpha_composite(img, overlay)


def _extract_foreground_mask(frame, background, threshold=25, blur_radius=7):
    """通过帧差法提取前景蒙版。"""
    frame_gray = frame.convert("L")
    bg_gray = background.convert("L")
    diff = ImageChops.difference(frame_gray, bg_gray)
    mask = diff.point(lambda p: 255 if p > threshold else 0)
    if blur_radius > 0:
        mask = mask.filter(ImageFilter.GaussianBlur(radius=blur_radius))
    mask = mask.point(lambda p: 255 if p > 50 else 0)
    mask = mask.filter(ImageFilter.MinFilter(3))
    mask = mask.filter(ImageFilter.MaxFilter(3))
    return mask


def _create_3d_frame(frame, background, line_spacing=80, line_width=3,
                     line_alpha=200, line_direction="both",
                     mask_threshold=25, mask_blur=7, foreground_blur=0):
    """创建单帧裸眼3D效果。"""
    frame_rgba = frame.convert("RGBA")
    bg_rgba = background.convert("RGBA")

    bg_with_lines = _draw_dividing_lines(
        bg_rgba, spacing=line_spacing, line_width=line_width,
        line_alpha=line_alpha, direction=line_direction,
    )

    mask = _extract_foreground_mask(
        frame_rgba, bg_rgba, threshold=mask_threshold, blur_radius=mask_blur,
    )

    foreground = frame_rgba
    if foreground_blur > 0:
        foreground = foreground.filter(ImageFilter.GaussianBlur(radius=foreground_blur))

    return Image.composite(foreground, bg_with_lines, mask)


def bare_eye_3d(input_path, output_path,
                line_spacing=80, line_width=3, line_alpha=200,
                line_direction="both", mask_threshold=25,
                mask_blur=7, foreground_blur=0, max_frames=48):
    """将图片/GIF 转换为裸眼3D效果。

    参数详见 _conf_schema.json 配置说明。
    """
    img = Image.open(input_path)

    if not is_gif(input_path):
        result = _draw_dividing_lines(
            img.convert("RGBA"), spacing=line_spacing,
            line_width=line_width, line_alpha=line_alpha,
            direction=line_direction,
        )
        result.save(output_path, "PNG")
        return

    frames, durations, = unfold_frames(img)

    if len(frames) == 1:
        result = _draw_dividing_lines(
            frames[0], spacing=line_spacing, line_width=line_width,
            line_alpha=line_alpha, direction=line_direction,
        )
        result.save(output_path, "PNG")
        return

    n = len(frames)
    if max_frames > 0 and n > max_frames:
        indices = [int(i * n / max_frames) for i in range(max_frames)]
        frames = [frames[i] for i in indices]
        durations = [durations[i] for i in indices]

    background = _compute_background(frames)
    result_frames = []
    for frame in frames:
        syn = _create_3d_frame(
            frame, background,
            line_spacing=line_spacing, line_width=line_width,
            line_alpha=line_alpha, line_direction=line_direction,
            mask_threshold=mask_threshold, mask_blur=mask_blur,
            foreground_blur=foreground_blur,
        )
        result_frames.append(syn)

    save_rgba_gif(result_frames, durations, output_path,
                  loop=img.info.get("loop", 0))
