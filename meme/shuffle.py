"""GIF 重组模块：打乱所有帧顺序后重新合成 GIF"""

import random
from PIL import Image
from .gif_utils import is_gif, unfold_frames, save_rgba_gif


def shuffle_gif(input_path: str, output_path: str, seed: int | None = None) -> str:
    """打乱 GIF 帧顺序并重新合成。

    静态图无动画帧，原样返回。

    Args:
        input_path: 输入文件路径
        output_path: 输出文件路径
        seed: 随机种子（可选，用于可复现结果）

    Returns:
        输出文件路径
    """
    gif = Image.open(input_path)

    if not is_gif(input_path):
        img = gif.convert("RGBA")
        img.save(output_path, "PNG")
        return output_path

    src_palette = gif.getpalette()
    src_trans = gif.info.get("transparency")
    frames, durations = unfold_frames(gif)

    if len(frames) <= 1:
        frames[0].convert("RGBA").save(output_path, "PNG")
        return output_path

    rng = random.Random(seed)
    indices = list(range(len(frames)))
    rng.shuffle(indices)

    shuffled_frames = [frames[i] for i in indices]
    shuffled_durations = [durations[i] for i in indices]

    save_rgba_gif(shuffled_frames, shuffled_durations, output_path,
                  loop=gif.info.get("loop", 0),
                  source_palette=src_palette,
                  source_trans_idx=src_trans)
    return output_path
