"""GIF 分解模块：按百分比均匀采样 N 帧，输出为 PNG 图片列表"""

import os
from PIL import Image
from .gif_utils import is_gif, unfold_frames


def split_gif(input_path: str, output_dir: str, count: int) -> list[str]:
    """将 GIF 按百分比均匀采样分解为 N 张 PNG。

    采样算法：将帧序列 0%~100% 均分为 N 个点取帧。
    N=3, 30帧 → 取帧 0(0%), 15(50%), 29(100%)
    N=1 时直接取第 0 帧。

    Args:
        input_path: GIF 文件路径
        output_dir: 输出目录
        count: 分解张数

    Returns:
        PNG 文件路径列表（按时间顺序）

    Raises:
        ValueError: 非 GIF 或帧数不足
    """
    if not is_gif(input_path):
        raise ValueError("分解仅支持动图（GIF）")

    gif = Image.open(input_path)
    frames, _ = unfold_frames(gif)
    total = len(frames)

    if total <= 1:
        raise ValueError("该动图只有1帧，无法分解")

    # 钳制 count 到有效范围
    count = max(2, min(count, total))

    # 按百分比均匀采样
    indices = []
    if count == 1:
        indices = [0]
    else:
        for i in range(count):
            idx = round(i / (count - 1) * (total - 1))
            indices.append(idx)

    # 去重（帧数少于 count 时可能出现重复索引）
    seen = set()
    unique_indices = []
    for idx in indices:
        if idx not in seen:
            seen.add(idx)
            unique_indices.append(idx)

    os.makedirs(output_dir, exist_ok=True)
    paths = []
    for i, idx in enumerate(unique_indices):
        out_path = os.path.join(output_dir, f"split_{i:03d}.png")
        frames[idx].convert("RGBA").save(out_path, "PNG")
        paths.append(out_path)

    return paths
