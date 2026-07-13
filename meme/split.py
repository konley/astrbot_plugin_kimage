"""GIF 分解模块：按百分比均匀采样 / 智能关键帧采样，输出为 PNG 图片列表"""

import os
import numpy as np
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


def _frame_diff(a: np.ndarray, b: np.ndarray) -> float:
    """计算两帧缩略图之间的归一化 MSE 差异（0~1）。"""
    return float(np.mean((a.astype(np.float32) - b.astype(np.float32)) ** 2)) / 255.0 / 3.0


def _compute_thumb(frame: Image.Image, size: int = 64) -> np.ndarray:
    """将帧缩放为灰度缩略图用于快速差异比较。"""
    return np.asarray(frame.convert("L").resize((size, size)), dtype=np.uint8)


def split_gif_smart(input_path: str, output_dir: str, count: int) -> list[str]:
    """智能分解 GIF：基于帧间差异 + 动态规划选取差异最大的 N 个关键帧。

    算法：
    1. 展开所有帧，每帧缩放为 64x64 灰度图
    2. 计算任意两帧之间的差异矩阵
    3. 动态规划：从 total 帧中选 N 帧，使得相邻选中帧之间的累计差异最大化
       dp[j][k] = 选了 j 帧、最后一帧是第 k 帧时的最大累计差异
    4. 回溯得到选中的帧索引

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

    count = max(2, min(count, total))

    # 如果帧数恰好等于 count，直接全取
    if total == count:
        indices = list(range(total))
    else:
        # 计算缩略图
        thumbs = [_compute_thumb(f) for f in frames]

        # 计算差异矩阵 diff[i][j] = 帧 i 和帧 j 的差异
        diff = np.zeros((total, total), dtype=np.float32)
        for i in range(total):
            for j in range(i + 1, total):
                d = _frame_diff(thumbs[i], thumbs[j])
                diff[i][j] = d
                diff[j][i] = d

        # 动态规划：选 N 帧使相邻选中帧差异之和最大
        # dp[k][i] = 已选 k 帧、最后一帧为 i 时的最大累计差异
        # 转移: dp[k][i] = max(dp[k-1][j] + diff[j][i]) for j < i
        # 第 1 帧固定取第 0 帧（保证起点）
        NEG = -1e9
        dp = [[NEG] * total for _ in range(count)]
        prev = [[-1] * total for _ in range(count)]

        # 初始化：选第 1 帧 = 第 0 帧
        dp[0][0] = 0.0

        for k in range(1, count):
            for i in range(k, total):
                best = NEG
                best_j = -1
                for j in range(k - 1, i):
                    if dp[k - 1][j] == NEG:
                        continue
                    val = dp[k - 1][j] + diff[j][i]
                    if val > best:
                        best = val
                        best_j = j
                dp[k][i] = best
                prev[k][i] = best_j

        # 找最后一帧：在 dp[count-1] 中取最大值
        best_last = count - 1
        best_val = NEG
        for i in range(count - 1, total):
            if dp[count - 1][i] > best_val:
                best_val = dp[count - 1][i]
                best_last = i

        # 回溯
        indices = []
        k = count - 1
        i = best_last
        while k >= 0 and i >= 0:
            indices.append(i)
            i = prev[k][i]
            k -= 1
        indices.reverse()

    os.makedirs(output_dir, exist_ok=True)
    paths = []
    for i, idx in enumerate(indices):
        out_path = os.path.join(output_dir, f"split_{i:03d}.png")
        frames[idx].convert("RGBA").save(out_path, "PNG")
        paths.append(out_path)

    return paths
