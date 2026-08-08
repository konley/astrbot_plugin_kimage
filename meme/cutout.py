"""本地抠图：rembg + onnxruntime，输出透明 GIF（QQ 更易保留透明）。"""

from __future__ import annotations

import io
import os
import threading
from pathlib import Path

from PIL import Image

from .gif_utils import is_gif, unfold_frames, save_rgba_gif

_ALLOWED_MODELS = frozenset(
    {
        "u2netp",
        "u2net",
        "silueta",
        "u2net_human_seg",
        "isnet-general-use",
        "isnet-anime",
    }
)

_session = None
_session_model: str | None = None
_session_lock = threading.Lock()
_infer_lock = threading.Lock()


class CutoutDependencyError(RuntimeError):
    """rembg / onnxruntime 未安装。"""


def _ensure_rembg():
    try:
        from rembg import new_session, remove  # noqa: F401
    except ImportError as exc:
        raise CutoutDependencyError(
            "未安装抠图依赖或进程需重启以加载新包。"
            f"详情: {type(exc).__name__}: {exc}。"
            "请在 AstrBot 环境执行 pip install rembg onnxruntime 后重启 AstrBot。"
        ) from exc
    except Exception as exc:
        # 长驻进程中途装包后，常见为旧 numpy 与新扩展不兼容
        raise CutoutDependencyError(
            f"抠图依赖加载失败: {type(exc).__name__}: {exc}。"
            "若刚安装 rembg，请重启 AstrBot 后再试。"
        ) from exc
    return True


def _model_home() -> Path:
    from astrbot.core.utils.astrbot_path import get_astrbot_data_path

    home = Path(get_astrbot_data_path()) / "plugin_data" / "kimage" / "u2net"
    home.mkdir(parents=True, exist_ok=True)
    return home


def _get_session(model: str):
    global _session, _session_model
    model = (model or "u2netp").strip()
    if model not in _ALLOWED_MODELS:
        model = "u2netp"
    with _session_lock:
        if _session is not None and _session_model == model:
            return _session
        _ensure_rembg()
        from rembg import new_session

        os.environ.setdefault("U2NET_HOME", str(_model_home()))
        _session = new_session(model)
        _session_model = model
        return _session


def _resize_max_side(img: Image.Image, max_side: int) -> Image.Image:
    max_side = max(64, min(2048, int(max_side or 512)))
    w, h = img.size
    longest = max(w, h)
    if longest <= max_side:
        return img
    scale = max_side / float(longest)
    nw = max(1, int(round(w * scale)))
    nh = max(1, int(round(h * scale)))
    return img.resize((nw, nh), Image.Resampling.LANCZOS)


def _sample_indices(n: int, max_frames: int) -> list[int]:
    max_frames = max(1, min(48, int(max_frames or 24)))
    if n <= max_frames:
        return list(range(n))
    if max_frames == 1:
        return [0]
    return [int(round(i * (n - 1) / (max_frames - 1))) for i in range(max_frames)]


def _remove_bg_rgba(
    rgba: Image.Image,
    session,
    alpha_matting: bool = False,
) -> Image.Image:
    from rembg import remove

    buf = io.BytesIO()
    rgba.convert("RGBA").save(buf, format="PNG")
    raw = buf.getvalue()
    kwargs = {"session": session}
    if alpha_matting:
        kwargs["alpha_matting"] = True
        kwargs["alpha_matting_foreground_threshold"] = 240
        kwargs["alpha_matting_background_threshold"] = 10
        kwargs["alpha_matting_erode_size"] = 10
    out = remove(raw, **kwargs)
    return Image.open(io.BytesIO(out)).convert("RGBA")


def cutout_image(
    input_path: str,
    output_path: str,
    model: str = "u2netp",
    max_side: int = 512,
    gif_max_frames: int = 24,
    alpha_matting: bool = False,
) -> str:
    """抠图并保存为透明 GIF。

    静图：单帧透明 GIF；动图：均匀抽帧后逐帧抠图再合成。
    返回可选提示文案（空串表示无提示）。
    """
    _ensure_rembg()
    session = _get_session(model)
    note = ""

    with _infer_lock:
        src = Image.open(input_path)
        if is_gif(input_path) or getattr(src, "is_animated", False):
            frames, durations = unfold_frames(src)
            n = len(frames)
            idxs = _sample_indices(n, gif_max_frames)
            if len(idxs) < n:
                note = f"动图已抽帧 {n}→{len(idxs)}，最长边≤{max_side}"
            out_frames = []
            out_durs = []
            for i in idxs:
                rgba = _resize_max_side(frames[i].convert("RGBA"), max_side)
                out_frames.append(
                    _remove_bg_rgba(rgba, session, alpha_matting=alpha_matting)
                )
                d = durations[i] if i < len(durations) else 100
                out_durs.append(max(20, int(d)))
            if len(out_frames) == 1:
                out_durs = [500]
            save_rgba_gif(out_frames, out_durs, output_path, loop=0)
        else:
            rgba = _resize_max_side(src.convert("RGBA"), max_side)
            cut = _remove_bg_rgba(rgba, session, alpha_matting=alpha_matting)
            # 单帧透明 GIF：QQ 比 PNG alpha 更稳
            save_rgba_gif([cut], [500], output_path, loop=0)

    return note
