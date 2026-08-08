"""图片处理工具箱：反色、调速、@用户反色（参照 pic_mirror 的指令解析模式）"""

import asyncio
import os
import re
import time
import uuid
from PIL import Image

import astrbot.api.message_components as Comp
from astrbot.api import logger
from astrbot.api.event import filter, AstrMessageEvent, MessageChain
from astrbot.api.event.filter import EventMessageType
from astrbot.api.star import Context, Star
from pathlib import Path
from astrbot.core.utils.astrbot_path import get_astrbot_data_path

from .meme import gif_speed, invert, flip, petpet, mirror, shoot, do, lash, behead, pixelate, reverse, roundtrip, bare_eye_3d, spin, glitch, kaleidoscope, dither, breathing, patina, popart, digital_patina, funhouse_mirror, split, shuffle, cutout

QQ_AVATAR_URL = "http://q1.qlogo.cn/g?b=qq&nk={qq}&s=640"
TMP_DIR = Path(get_astrbot_data_path()) / "plugin_data" / "pic_toolbox"
os.makedirs(TMP_DIR, exist_ok=True)

# ── 工具函数 ────────────────────────────────────

def _download_sync(url: str, path: str) -> bool:
    """下载图片到本地。支持 HTTP URL 和本地文件路径。"""
    import requests
    import shutil
    try:
        if os.path.isfile(url):
            shutil.copy2(url, path)
            return True
        r = requests.get(url, timeout=30, headers={"User-Agent": "AstrBot/pic_toolbox"})
        r.raise_for_status()
        with open(path, "wb") as f:
            f.write(r.content)
        return True
    except Exception as e:
        logger.error(f"[pic_toolbox] 下载失败: {e}")
        return False

def _is_gif(path: str) -> bool:
    try:
        with Image.open(path) as im:
            return getattr(im, "is_animated", False)
    except Exception:
        return path.lower().endswith(".gif")


# ── 插件主体 ─────────────────────────────────────

class PicToolboxPlugin(Star):
    def __init__(self, context: Context, config: dict = None):
        super().__init__(context)
        if config is None:
            config = {}
        self._enable_at_avatar = config.get("enable_at_avatar", True)
        self._match_mode = config.get("match_mode", True)
        self._gif_speed_allow_frame_drop = config.get("gif_speed_allow_frame_drop", True)
        self._default_speedup_factor = config.get("default_speedup_factor", 2.5)
        self._default_pixelate_block = config.get("default_pixelate_block", 8)
        # 裸眼3D 参数
        self._be3d_line_spacing = config.get("be3d_line_spacing", 40)
        self._be3d_line_width = config.get("be3d_line_width", 4)
        self._be3d_line_alpha = config.get("be3d_line_alpha", 200)
        self._be3d_line_direction = config.get("be3d_line_direction", "both")
        self._be3d_mask_threshold = config.get("be3d_mask_threshold", 15)
        self._be3d_mask_blur = config.get("be3d_mask_blur", 7)
        self._be3d_foreground_blur = config.get("be3d_foreground_blur", 0)
        self._be3d_max_frames = config.get("be3d_max_frames", 48)
        # 旋转参数
        self._spin_direction = config.get("spin_direction", "clockwise")
        self._spin_angle_step = config.get("spin_angle_step", 6)
        # 故障参数
        self._glitch_max_shift = config.get("glitch_max_shift", 15)
        self._glitch_num_frames = config.get("glitch_num_frames", 8)
        self._glitch_frame_delay = config.get("glitch_frame_delay", 80)
        # 万花筒参数
        self._kal_sectors = config.get("kal_sectors", 8)
        self._kal_zoom = config.get("kal_zoom", 0.5)
        self._kal_angle_step = config.get("kal_angle_step", 3)
        self._kal_frame_delay = config.get("kal_frame_delay", 40)
        # 抖动参数
        self._dither_num_colors = config.get("dither_num_colors", 16)
        # 呼吸参数
        self._breath_min_scale = config.get("breath_min_scale", 0.92)
        self._breath_max_scale = config.get("breath_max_scale", 1.08)
        self._breath_frames = config.get("breath_frames", 30)
        self._breath_frame_delay = config.get("breath_frame_delay", 40)
        # 包浆参数
        self._patina_sepia = config.get("patina_sepia_strength", 60)
        self._patina_vignette = config.get("patina_vignette_strength", 40)
        self._patina_noise = config.get("patina_noise_amount", 20)
        self._patina_fade = config.get("patina_fade_amount", 30)
        # 波普参数
        self._pop_colors = config.get("popart_num_colors", 8)
        self._pop_edge = config.get("popart_edge_width", 1)
        self._pop_halftone = config.get("popart_halftone_size", 0)
        self._pop_panels = config.get("popart_panels", 2)
        # 电子包浆参数
        self._dp_jpeg = config.get("digital_patina_jpeg_quality", 15)
        self._dp_banding = config.get("digital_patina_banding_level", 5)
        self._dp_pixelate = config.get("digital_patina_pixelate_size", 0)
        self._dp_green = config.get("digital_patina_green_tint", 40)
        # 扭曲参数
        self._fm_type = config.get("funhouse_mirror_type", "bulge")
        self._fm_strength = config.get("funhouse_mirror_strength", 1.0)
        # 分解参数
        self._split_default_count = config.get("split_default_count", 3)
        self._split_max_count = config.get("split_max_count", 15)
        self._split_smart_max_count = config.get("split_smart_max_count", 10)
        # 抠图参数
        self._cutout_model = config.get("cutout_model", "u2netp")
        self._cutout_max_side = config.get("cutout_max_side", 512)
        self._cutout_gif_max_frames = config.get("cutout_gif_max_frames", 24)
        self._cutout_timeout_sec = config.get("cutout_timeout_sec", 120)
        self._cutout_alpha_matting = config.get("cutout_alpha_matting", False)
        self._cutout_busy = False
        # 启动时清理旧临时文件（进程崩溃残留）
        self._cleanup_stale_tempfiles()

    # ── 参照 pic_mirror 的指令解析 ─────────────
    @filter.event_message_type(EventMessageType.ALL)
    async def handle_all_commands(self, event: AstrMessageEvent):
        """手动解析 @用户 指令 或 指令 @用户，避免 / 前缀和 @ 标记冲突。"""
        msg = event.message_str.strip()

        # 解析指令和 @ 目标（参照 pic_mirror 两阶段解析）
        actual_cmd = msg
        at_qq = self._extract_at_qq(event)

        if " @" in msg:
            parts = msg.split("@", 1)
            actual_cmd = parts[0].strip()
        elif msg.startswith("@"):
            parts = msg.split(None, 2)
            if len(parts) >= 2:
                actual_cmd = parts[1].strip()

        # 去掉可能的前导 /
        cmd_text = actual_cmd.lstrip("/").strip()

        # ── 帮助 ────────────────────────────
        if cmd_text in ("帮助", "图帮助", "图help", "img_help"):
            event.stop_event()
            yield event.plain_result(
                "━━━ 小K图片处理工具箱 ━━━\n"
                "发送或引用一张图片，附带以下指令：\n"
                "🎨 基础\n"
                "  反色 | 抠图/去背景 [边长] | 旋转 [角度步长] | 左右翻转 | 上下翻转\n"
                "🪞 对称\n"
                "  对称[1-6/左/右/上/下/左上/右上]（1=左 2=上 3=\\ 4=/ 5=右 6=下，默认左）\n"
                "  左对称 | 右对称 | 上对称 | 下对称 | 左上对称 | 右上对称\n"
                "  真对称[1-4/右/左/上/下]（1=右 2=左 3=上 4=下，默认右）\n"
                "  右真对称 | 左真对称 | 上真对称 | 下真对称\n"
                "🖼️ 特效\n"
                "  故障 [强度] | 万花筒 [扇区] | 抖动 [颜色数]\n"
                "  呼吸 [帧延迟] | 包浆 [强度] | 电子包浆 [程度]\n"
                "  扭曲 [类型] [强度] | 波普 [格数] | 马赛克 [程度] | 裸眼3d [强度]\n"
                "🔄 GIF\n"
                "  加速 [倍率] | 调速 <倍率> | 倒放 | 往返\n"
                "  分解 [张数] | 智能分解 [张数] | 将动图分解为N张图片\n"
                "  重组/打乱 | 打乱动图所有帧重新合成GIF\n"
                "🎭 表情（@用户使用）\n"
                "  摸头 | 发射 | 撅 | 抽 | 杀\n"
                "💡 /帮助 /图帮助 /图help 显示本帮助\n"
                "⚙️ 更多参数可前往 WebUI 设置页面进行调整"
            )
            return

        # ── 旋转（转圈 GIF）─────────────────
        _sx_m = re.match(r"^旋转(\d+)$", cmd_text)
        if _sx_m or cmd_text == "旋转" or (cmd_text.startswith("旋转 ") and cmd_text.split(None, 1)[1].isdigit()):
            if not self._match_mode and not actual_cmd.startswith("/"):
                return
            image_url = self._resolve_image_url(event, at_qq)
            if not image_url:
                return
            event.stop_event()
            spin_kwargs = dict(
                direction=self._spin_direction,
                angle_step=self._spin_angle_step,
            )
            if _sx_m:
                spin_kwargs["angle_step"] = max(1, min(360, int(_sx_m.group(1))))
            else:
                parts = cmd_text.split(None, 1)
                if len(parts) > 1:
                    spin_kwargs["angle_step"] = max(1, min(360, int(parts[1])))
            def _spin_proc(inp, out):
                spin.spin_image(inp, out, **spin_kwargs)
            async for r in self._download_and_process(event, image_url, _spin_proc, "旋转"):
                yield r
            return

        # ── 故障（RGB 通道偏移 GIF）──────────
        _gz_m = re.match(r"^故障(\d+)$", cmd_text)
        if _gz_m or cmd_text == "故障" or (cmd_text.startswith("故障 ") and cmd_text.split(None, 1)[1].isdigit()):
            if not self._match_mode and not actual_cmd.startswith("/"):
                return
            image_url = self._resolve_image_url(event, at_qq)
            if not image_url:
                return
            event.stop_event()
            gk = dict(max_shift=self._glitch_max_shift,
                      num_frames=self._glitch_num_frames,
                      frame_delay=self._glitch_frame_delay)
            if _gz_m:
                gk["max_shift"] = max(1, min(100, int(_gz_m.group(1))))
            else:
                parts = cmd_text.split(None, 1)
                if len(parts) > 1:
                    gk["max_shift"] = max(1, min(100, int(parts[1])))
            def _gproc(inp, out): glitch.glitch_image(inp, out, **gk)
            async for r in self._download_and_process(event, image_url, _gproc, "故障"):
                yield r
            return

        # ── 万花筒 ─────────────────────────
        _wht_m = re.match(r"^万花筒(\d+)$", cmd_text)
        if _wht_m or cmd_text == "万花筒" or (cmd_text.startswith("万花筒 ") and cmd_text.split(None, 1)[1].isdigit()):
            if not self._match_mode and not actual_cmd.startswith("/"):
                return
            image_url = self._resolve_image_url(event, at_qq)
            if not image_url:
                return
            event.stop_event()
            kk = dict(sectors=self._kal_sectors, zoom=self._kal_zoom,
                      angle_step=self._kal_angle_step,
                      frame_delay=self._kal_frame_delay)
            if _wht_m:
                kk["sectors"] = max(2, min(24, int(_wht_m.group(1))))
            else:
                parts = cmd_text.split(None, 1)
                if len(parts) > 1:
                    kk["sectors"] = max(2, min(24, int(parts[1])))
            def _kproc(inp, out): kaleidoscope.kaleidoscope_image(inp, out, **kk)
            async for r in self._download_and_process(event, image_url, _kproc, "万花筒"):
                yield r
            return

        # ── 抖动（降色阶 8-bit 风）──────────
        _dd_m = re.match(r"^抖动(\d+)$", cmd_text)
        if _dd_m or cmd_text == "抖动" or (cmd_text.startswith("抖动 ") and cmd_text.split(None, 1)[1].isdigit()):
            if not self._match_mode and not actual_cmd.startswith("/"):
                return
            image_url = self._resolve_image_url(event, at_qq)
            if not image_url:
                return
            event.stop_event()
            nc = self._dither_num_colors
            if _dd_m:
                nc = max(2, min(256, int(_dd_m.group(1))))
            else:
                parts = cmd_text.split(None, 1)
                if len(parts) > 1:
                    nc = max(2, min(256, int(parts[1])))
            def _dproc(inp, out): dither.dither_image(inp, out, num_colors=nc)
            async for r in self._download_and_process(event, image_url, _dproc, "抖动"):
                yield r
            return

        # ── 呼吸（周期缩放 GIF）─────────────
        _hx_m = re.match(r"^呼吸(\d+)$", cmd_text)
        if _hx_m or cmd_text == "呼吸" or (cmd_text.startswith("呼吸 ") and cmd_text.split(None, 1)[1].isdigit()):
            if not self._match_mode and not actual_cmd.startswith("/"):
                return
            image_url = self._resolve_image_url(event, at_qq)
            if not image_url:
                return
            event.stop_event()
            bk = dict(min_scale=self._breath_min_scale,
                      max_scale=self._breath_max_scale,
                      frames=self._breath_frames,
                      frame_delay=self._breath_frame_delay)
            if _hx_m:
                bk["frame_delay"] = max(10, min(1000, int(_hx_m.group(1))))
            else:
                parts = cmd_text.split(None, 1)
                if len(parts) > 1:
                    bk["frame_delay"] = max(10, min(1000, int(parts[1])))
            def _bproc(inp, out): breathing.breathing_image(inp, out, **bk)
            async for r in self._download_and_process(event, image_url, _bproc, "呼吸"):
                yield r
            return

        # ── 包浆（复古做旧）──────────────────
        _bj_m = re.match(r"^包浆(\d+)$", cmd_text)
        if _bj_m or cmd_text == "包浆" or (cmd_text.startswith("包浆 ") and cmd_text.split(None, 1)[1].isdigit()):
            if not self._match_mode and not actual_cmd.startswith("/"):
                return
            image_url = self._resolve_image_url(event, at_qq)
            if not image_url:
                return
            event.stop_event()
            pk = dict(sepia_strength=self._patina_sepia,
                      vignette_strength=self._patina_vignette,
                      noise_amount=self._patina_noise,
                      fade_amount=self._patina_fade)
            if _bj_m:
                s = max(0, min(100, int(_bj_m.group(1)))) / 100.0
            else:
                parts = cmd_text.split(None, 1)
                if len(parts) > 1:
                    s = max(0, min(100, float(parts[1]))) / 100.0
                pk["sepia_strength"] = int(pk["sepia_strength"] * s)
                pk["vignette_strength"] = int(pk["vignette_strength"] * s)
                pk["noise_amount"] = int(pk["noise_amount"] * s)
                pk["fade_amount"] = int(pk["fade_amount"] * s)
            def _pproc(inp, out): patina.patina_image(inp, out, **pk)
            async for r in self._download_and_process(event, image_url, _pproc, "包浆"):
                yield r
            return

        # ── 波普（Pop Art）───────────────────
        _pp_match = False
        _pp_panels = None
        m = re.match(r"^波普(\d+)$", cmd_text)
        if m:
            _pp_match = True
            _pp_panels = int(m.group(1))
        elif cmd_text == "波普":
            _pp_match = True
        elif cmd_text.startswith("波普 ") and cmd_text.split(None, 1)[1].isdigit():
            _pp_match = True
            _pp_panels = int(cmd_text.split(None, 1)[1])
        if _pp_match:
            if not self._match_mode and not actual_cmd.startswith("/"):
                return
            image_url = self._resolve_image_url(event, at_qq)
            if not image_url:
                return
            event.stop_event()
            pok = dict(num_colors=self._pop_colors, edge_width=self._pop_edge,
                       halftone_size=self._pop_halftone, panels=self._pop_panels)
            if _pp_panels is not None:
                pok["panels"] = max(1, min(9, _pp_panels))
            def _poproc(inp, out): popart.popart_image(inp, out, **pok)
            async for r in self._download_and_process(event, image_url, _poproc, "波普"):
                yield r
            return

        # ── 电子包浆 ───────────────────────
        _dz_m = re.match(r"^电子包浆(\d+)$", cmd_text)
        if _dz_m or cmd_text == "电子包浆" or (cmd_text.startswith("电子包浆 ") and cmd_text.split(None, 1)[1].isdigit()):
            if not self._match_mode and not actual_cmd.startswith("/"):
                return
            image_url = self._resolve_image_url(event, at_qq)
            if not image_url:
                return
            event.stop_event()
            dk = dict(jpeg_quality=self._dp_jpeg,
                      banding_level=self._dp_banding,
                      pixelate_size=self._dp_pixelate,
                      green_tint=self._dp_green)
            if _dz_m:
                intensity = int(_dz_m.group(1))
            else:
                parts = cmd_text.split(None, 1)
                intensity = int(parts[1]) if len(parts) > 1 else None
            if intensity is not None:
                dk["jpeg_quality"] = max(5, min(80, int(85 - intensity * 8)))
                dk["banding_level"] = max(2, min(128, int(14 - intensity)))
                dk["pixelate_size"] = max(0, min(20, intensity - 1))
                dk["green_tint"] = min(100, intensity * 10)
            def _dproc(inp, out): digital_patina.digital_patina_image(inp, out, **dk)
            async for r in self._download_and_process(event, image_url, _dproc, "电子包浆"):
                yield r
            return

        # ── 扭曲 ─────────────────────────
        _fm_num_map = {"1": "bulge", "2": "concave", "3": "cylinder_h",
                       "4": "cylinder_v", "5": "wave", "6": "spiral"}
        _fm_alias = {"凸": "bulge", "凹": "concave", "横柱": "cylinder_h",
                     "竖柱": "cylinder_v", "波浪": "wave", "螺旋": "spiral"}
        _fm_match = cmd_text == "扭曲"
        _fm_type = None
        _fm_strength = None
        if not _fm_match and cmd_text.startswith("扭曲"):
            rest = cmd_text[len("扭曲"):].strip()
            if rest:
                parts = rest.split(None, 1)
                first = parts[0]
                if first.isdigit():
                    _fm_type = _fm_num_map.get(first, "bulge")
                    if len(parts) > 1:
                        try:
                            _fm_strength = max(0.1, min(5.0, float(parts[1])))
                        except ValueError:
                            pass
                    _fm_match = True
                elif first in _fm_alias:
                    _fm_type = _fm_alias[first]
                    if len(parts) > 1:
                        try:
                            _fm_strength = max(0.1, min(5.0, float(parts[1])))
                        except ValueError:
                            pass
                    _fm_match = True
        if _fm_match:
            if not self._match_mode and not actual_cmd.startswith("/"):
                return
            image_url = self._resolve_image_url(event, at_qq)
            if not image_url:
                return
            event.stop_event()
            fk = dict(mirror_type=self._fm_type, strength=self._fm_strength)
            if _fm_type:
                fk["mirror_type"] = _fm_type
            if _fm_strength is not None:
                fk["strength"] = _fm_strength
            def _fproc(inp, out): funhouse_mirror.funhouse_mirror_image(inp, out, **fk)
            async for r in self._download_and_process(event, image_url, _fproc, "扭曲"):
                yield r
            return

        # ── 反色 ────────────────────────────
        if cmd_text == "反色":
            image_url = self._resolve_image_url(event, at_qq)
            if not image_url:
                return
            event.stop_event()
            async for r in self._download_and_process(event, image_url, invert.invert_image, "反色"):
                yield r
            return

        # ── 抠图 / 去背景（本地 rembg，输出透明 GIF）──
        _co_m = re.match(r"^(?:抠图|去背景|去背|cutout)(\d+)$", cmd_text, re.I)
        _co_aliases = {"抠图", "去背景", "去背", "cutout"}
        _co_prefix = (
            cmd_text.startswith("抠图 ")
            or cmd_text.startswith("去背景 ")
            or cmd_text.startswith("去背 ")
            or cmd_text.lower().startswith("cutout ")
        )
        if _co_m or cmd_text in _co_aliases or cmd_text.lower() in _co_aliases or _co_prefix:
            if not self._match_mode and not actual_cmd.startswith("/"):
                return
            image_url = self._resolve_image_url(event, at_qq)
            if not image_url:
                return
            if self._cutout_busy:
                yield event.plain_result("抠图忙碌中，请稍后再试")
                return
            max_side = self._cutout_max_side
            if _co_m:
                max_side = max(64, min(2048, int(_co_m.group(1))))
            elif _co_prefix:
                parts = cmd_text.split(None, 1)
                if len(parts) > 1:
                    try:
                        max_side = max(64, min(2048, int(parts[1].strip())))
                    except ValueError:
                        yield event.plain_result("边长请用数字，如「抠图 512」")
                        return
            event.stop_event()
            async for r in self._run_cutout(event, image_url, max_side):
                yield r
            return

        # ── 左右翻转 ─────────────────────────
        if cmd_text == "左右翻转":
            if not self._match_mode and not actual_cmd.startswith("/"):
                return

            image_url = self._resolve_image_url(event, at_qq)
            if not image_url:
                return
            event.stop_event()
            async for r in self._download_and_process(event, image_url, flip.flip_horizontal, "左右翻转"):
                yield r
            return

        # ── 上下翻转 ─────────────────────────
        if cmd_text == "上下翻转":
            if not self._match_mode and not actual_cmd.startswith("/"):
                return

            image_url = self._resolve_image_url(event, at_qq)
            if not image_url:
                return
            event.stop_event()
            async for r in self._download_and_process(event, image_url, flip.flip_vertical, "上下翻转"):
                yield r
            return

        # ── 左对称 ───────────────────────────
        if cmd_text == "左对称":
            if not self._match_mode and not actual_cmd.startswith("/"):
                return
            image_url = self._resolve_image_url(event, at_qq)
            if not image_url:
                return
            event.stop_event()
            async for r in self._download_and_process(event, image_url, mirror.mirror_left, "左对称"):
                yield r
            return

        # ── 右对称 ───────────────────────────
        if cmd_text == "右对称":
            if not self._match_mode and not actual_cmd.startswith("/"):
                return
            image_url = self._resolve_image_url(event, at_qq)
            if not image_url:
                return
            event.stop_event()
            async for r in self._download_and_process(event, image_url, mirror.mirror_right, "右对称"):
                yield r
            return

        # ── 上对称 ───────────────────────────
        if cmd_text == "上对称":
            if not self._match_mode and not actual_cmd.startswith("/"):
                return
            image_url = self._resolve_image_url(event, at_qq)
            if not image_url:
                return
            event.stop_event()
            async for r in self._download_and_process(event, image_url, mirror.mirror_top, "上对称"):
                yield r
            return

        # ── 下对称 ───────────────────────────
        if cmd_text == "下对称":
            if not self._match_mode and not actual_cmd.startswith("/"):
                return
            image_url = self._resolve_image_url(event, at_qq)
            if not image_url:
                return
            event.stop_event()
            async for r in self._download_and_process(event, image_url, mirror.mirror_bottom, "下对称"):
                yield r
            return

        # ── 左上对称（\ 对角线）────────────
        if cmd_text == "左上对称":
            if not self._match_mode and not actual_cmd.startswith("/"):
                return
            image_url = self._resolve_image_url(event, at_qq)
            if not image_url:
                return
            event.stop_event()
            def _zsym_proc(inp, out): mirror.mirror_by_type(inp, out, mirror_type=3)
            async for r in self._download_and_process(event, image_url, _zsym_proc, "左上对称"):
                yield r
            return

        # ── 右上对称（/ 对角线）────────────
        if cmd_text == "右上对称":
            if not self._match_mode and not actual_cmd.startswith("/"):
                return
            image_url = self._resolve_image_url(event, at_qq)
            if not image_url:
                return
            event.stop_event()
            def _ysym_proc(inp, out): mirror.mirror_by_type(inp, out, mirror_type=4)
            async for r in self._download_and_process(event, image_url, _ysym_proc, "右上对称"):
                yield r
            return

        # ── 对称（统一：1=左 2=上 3=\ 4=/）─
        _sym_dir = {"左": 1, "上": 2, "左上": 3, "右上": 4, "右": 5, "下": 6}
        _sym_m = re.match(r"^对称(\d)$", cmd_text)
        _sym_n = None
        if _sym_m:
            _sym_n = int(_sym_m.group(1))
        elif cmd_text == "对称":
            _sym_n = 1
        else:
            m2 = re.match(r"^对称\s+(\d)$", cmd_text)
            if m2:
                _sym_n = int(m2.group(1))
            else:
                for word, n in _sym_dir.items():
                    if cmd_text in (f"对称{word}", f"对称 {word}"):
                        _sym_n = n
                        break
        if _sym_n is not None:
            if not self._match_mode and not actual_cmd.startswith("/"):
                return
            image_url = self._resolve_image_url(event, at_qq)
            if not image_url:
                return
            event.stop_event()
            _sn = max(1, min(6, _sym_n))
            def _sym_proc(inp, out): mirror.mirror_by_type(inp, out, mirror_type=_sn)
            async for r in self._download_and_process(event, image_url, _sym_proc, f"对称{_sn}"):
                yield r
            return

        # ── 真对称（延展型，画布扩大）────────
        _zs_dir = {"右": 1, "左": 2, "上": 3, "下": 4}
        _zs_m = re.match(r"^真对称(\d)$", cmd_text)
        _zs_n = None
        if _zs_m:
            _zs_n = int(_zs_m.group(1))
        elif cmd_text == "真对称":
            _zs_n = 1
        else:
            m2 = re.match(r"^真对称\s+(\d)$", cmd_text)
            if m2:
                _zs_n = int(m2.group(1))
            else:
                for word, n in _zs_dir.items():
                    if cmd_text in (f"真对称{word}", f"真对称 {word}"):
                        _zs_n = n
                        break
        if _zs_n is None:
            # 左真对称 / 右真对称 / 上真对称 / 下真对称
            m3 = re.match(r"^(左|右|上|下)真对称$", cmd_text)
            if m3:
                _zs_n = _zs_dir.get(m3.group(1))
        if _zs_n is not None and 1 <= _zs_n <= 4:
            if not self._match_mode and not actual_cmd.startswith("/"):
                return
            image_url = self._resolve_image_url(event, at_qq)
            if not image_url:
                return
            event.stop_event()
            _zn = _zs_n
            def _zs_proc(inp, out): mirror.extend_symmetry(inp, out, direction=_zn)
            async for r in self._download_and_process(event, image_url, _zs_proc, f"真对称{_zn}"):
                yield r
            return

        # ── 摸头 ────────────────────────────
        if cmd_text == "摸头":
            if not self._match_mode and not actual_cmd.startswith("/"):
                return

            image_url = self._resolve_image_url(event, at_qq)
            if not image_url:
                return
            event.stop_event()
            async for r in self._download_and_process(event, image_url, petpet.generate_petpet, "摸头"):
                yield r
            return

        # ── 发射 ────────────────────────────
        if cmd_text == "发射":
            if not self._match_mode and not actual_cmd.startswith("/"):
                return
            image_url = self._resolve_image_url(event, at_qq)
            if not image_url:
                return
            event.stop_event()
            async for r in self._download_and_process(event, image_url, shoot.generate_shoot, "发射"):
                yield r
            return

        # ── 撅（双头像，原"操你"）────────────────
        if cmd_text == "撅":
            if not self._match_mode and not actual_cmd.startswith("/"):
                return
            if not at_qq:
                yield event.plain_result("请 @ 一个目标！")
                return
            event.stop_event()
            async for r in self._dual_avatar(event, at_qq, do.generate_do):
                yield r
            return

        # ── 抽（双头像，原"抽你"）────────────────
        if cmd_text == "抽":
            if not self._match_mode and not actual_cmd.startswith("/"):
                return
            if not at_qq:
                yield event.plain_result("请 @ 一个目标！")
                return
            event.stop_event()
            async for r in self._dual_avatar(event, at_qq, lash.generate_lash):
                yield r
            return

        # ── 杀（单头像）─────────────────────
        if cmd_text == "杀":
            if not self._match_mode and not actual_cmd.startswith("/"):
                return
            if not at_qq or not self._enable_at_avatar:
                return
            event.stop_event()
            image_url = QQ_AVATAR_URL.format(qq=at_qq)
            async for r in self._download_and_process(event, image_url, behead.generate_behead, "杀"):
                yield r
            return

        # ── 马赛克（可带程度参数）────────────────
        _msk_m = re.match(r"^马赛克(\d+)$", cmd_text)
        if _msk_m or cmd_text == "马赛克" or cmd_text.startswith("马赛克 "):
            if not self._match_mode and not actual_cmd.startswith("/"):
                return
            image_url = self._resolve_image_url(event, at_qq)
            if not image_url:
                return

            block_size = self._default_pixelate_block
            if _msk_m:
                level = int(_msk_m.group(1))
                block_size = max(2, min(50, 2 + (level - 1) * 5))
            elif cmd_text.startswith("马赛克 "):
                parts = cmd_text.split(None, 1)
                if len(parts) > 1:
                    try:
                        level = int(parts[1].strip())
                        block_size = max(2, min(50, 2 + (level - 1) * 5))
                    except ValueError:
                        yield event.plain_result("马赛克程度请用数字，如「马赛克 5」")
                        return

            event.stop_event()
            def _pix_proc(inp, out, _bs=block_size):
                return pixelate.pixelate_image(inp, out, block_size=_bs)
            async for r in self._download_and_process(event, image_url, _pix_proc, "马赛克"):
                yield r
            return

        # ── 加速（默认 2 倍，可带倍数参数）──────
        _js_m = re.match(r"^加速([\d.]+)$", cmd_text)
        if _js_m or cmd_text == "加速" or cmd_text.startswith("加速 "):
            if not self._match_mode and not actual_cmd.startswith("/"):
                return
            image_url = self._resolve_image_url(event, at_qq)
            if not image_url:
                return

            speed = self._default_speedup_factor
            if _js_m:
                try:
                    speed = gif_speed.parse_speed(_js_m.group(1))
                except ValueError as e:
                    yield event.plain_result(str(e))
                    return
            elif cmd_text.startswith("加速 "):
                parts = cmd_text.split(None, 1)
                if len(parts) > 1:
                    try:
                        speed = gif_speed.parse_speed(parts[1].strip())
                    except ValueError as e:
                        yield event.plain_result(str(e))
                        return

            event.stop_event()
            speed_result = {"warning": None}
            allow_drop = self._gif_speed_allow_frame_drop
            def _speedup_proc(inp, out, _sp=speed):
                _, _, warning = gif_speed.adjust_gif_speed(
                    inp, out, _sp, allow_frame_drop=allow_drop
                )
                speed_result["warning"] = warning
            async for r in self._download_and_process(
                event, image_url, _speedup_proc, "加速",
                get_prefix=lambda: speed_result["warning"],
            ):
                yield r
            return

        # ── 倒放（反转 GIF 帧顺序）──────────────
        if cmd_text == "倒放":
            if not self._match_mode and not actual_cmd.startswith("/"):
                return
            image_url = self._resolve_image_url(event, at_qq)
            if not image_url:
                return
            event.stop_event()
            async for r in self._download_and_process(event, image_url, reverse.reverse_gif, "倒放"):
                yield r
            return

        # ── 往返（GIF 正序+倒序 ping-pong）───
        if cmd_text == "往返":
            if not self._match_mode and not actual_cmd.startswith("/"):
                return
            image_url = self._resolve_image_url(event, at_qq)
            if not image_url:
                return
            event.stop_event()
            async for r in self._download_and_process(event, image_url, roundtrip.roundtrip_gif, "往返"):
                yield r
            return

        # ── 分解（GIF 按百分比采样为多张 PNG，合并转发）──
        _fen_m = re.match(r"^分解(\d+)$", cmd_text)
        if _fen_m or cmd_text == "分解" or (cmd_text.startswith("分解 ") and cmd_text.split(None, 1)[1].isdigit()):
            if not self._match_mode and not actual_cmd.startswith("/"):
                return
            image_url = self._resolve_image_url(event, at_qq)
            if not image_url:
                return
            event.stop_event()

            count = self._split_default_count
            if _fen_m:
                count = int(_fen_m.group(1))
            else:
                parts = cmd_text.split(None, 1)
                if len(parts) > 1:
                    count = int(parts[1])
            count = max(2, min(count, self._split_max_count))

            async for r in self._split_and_send(event, image_url, count):
                yield r
            return

        # ── 智能分解（帧间差异+动态规划选关键帧，合并转发）──
        _znfen_m = re.match(r"^智能分解(\d+)$", cmd_text)
        if _znfen_m or cmd_text == "智能分解" or (cmd_text.startswith("智能分解 ") and cmd_text.split(None, 1)[1].isdigit()):
            if not self._match_mode and not actual_cmd.startswith("/"):
                return
            image_url = self._resolve_image_url(event, at_qq)
            if not image_url:
                return
            event.stop_event()

            count = self._split_default_count
            if _znfen_m:
                count = int(_znfen_m.group(1))
            else:
                parts = cmd_text.split(None, 1)
                if len(parts) > 1:
                    count = int(parts[1])
            count = max(2, min(count, self._split_smart_max_count))

            async for r in self._split_and_send(event, image_url, count, smart=True):
                yield r
            return

        # ── 重组/打乱（打乱 GIF 帧顺序重新合成）──
        if cmd_text in ("重组", "打乱"):
            if not self._match_mode and not actual_cmd.startswith("/"):
                return
            image_url = self._resolve_image_url(event, at_qq)
            if not image_url:
                return
            event.stop_event()
            label = "重组" if cmd_text == "重组" else "打乱"
            async for r in self._download_and_process(event, image_url, shuffle.shuffle_gif, label):
                yield r
            return

        # ── 裸眼3D ─────────────────────────
        _be3d_match = cmd_text in ("裸眼3d", "裸眼3D")
        _be3d_intensity = None
        if not _be3d_match:
            m = re.match(r"^裸眼3[dD](\d+)$", cmd_text)
            if m:
                _be3d_match = True
                _be3d_intensity = int(m.group(1))
        if not _be3d_match:
            m = re.match(r"^裸眼3[dD]\s+(\d+)$", cmd_text)
            if m:
                _be3d_match = True
                _be3d_intensity = int(m.group(1))
        if _be3d_match:
            if not self._match_mode and not actual_cmd.startswith("/"):
                return
            image_url = self._resolve_image_url(event, at_qq)
            if not image_url:
                return
            event.stop_event()

            be3d_kwargs = dict(
                line_spacing=self._be3d_line_spacing,
                line_width=self._be3d_line_width,
                line_alpha=self._be3d_line_alpha,
                line_direction=self._be3d_line_direction,
                mask_threshold=self._be3d_mask_threshold,
                mask_blur=self._be3d_mask_blur,
                foreground_blur=self._be3d_foreground_blur,
                max_frames=self._be3d_max_frames,
            )
            if _be3d_intensity is not None:
                i = max(1, min(10, _be3d_intensity))
                be3d_kwargs["line_spacing"] = max(30, 120 - i * 8)
                be3d_kwargs["line_width"] = max(1, min(6, i // 2 + 1))
                be3d_kwargs["mask_threshold"] = max(5, 45 - i * 4)
            def _be3d_proc(inp, out):
                bare_eye_3d.bare_eye_3d(inp, out, **be3d_kwargs)

            async for r in self._download_and_process(event, image_url, _be3d_proc, "裸眼3d"):
                yield r
            return

        # ── 调速（需精准匹配模式 或 显式 /）──
        speed_match = re.match(r"^调速\s+([\d.]+)$", actual_cmd) or re.match(r"^调速([\d.]+)$", actual_cmd)
        if speed_match:
            if not self._match_mode and not actual_cmd.startswith("/"):
                return
            image_url = self._extract_image_url(event)
            if not image_url:
                return
            try:
                speed = gif_speed.parse_speed(speed_match.group(1))
            except ValueError as e:
                yield event.plain_result(str(e))
                return
            event.stop_event()
            allow_drop = self._gif_speed_allow_frame_drop
            speed_result = {"warning": None}
            def proc(inp, out):
                _, actual_speed, warning = gif_speed.adjust_gif_speed(
                    inp, out, speed, allow_frame_drop=allow_drop
                )
                speed_result["warning"] = warning
            async for r in self._download_and_process(
                event, image_url, proc, "调速",
                get_prefix=lambda: speed_result["warning"],
            ):
                yield r

    # ── 从组件提取 ────────────────────────────
    @staticmethod
    def _extract_at_qq(event: AstrMessageEvent) -> str | None:
        for comp in event.get_messages():
            if isinstance(comp, Comp.At):
                for attr in ("qq", "target", "user_id", "id"):
                    qq = getattr(comp, attr, None)
                    if qq:
                        return str(qq)
        return None

    @staticmethod
    def _extract_image_url(event: AstrMessageEvent) -> str | None:
        """提取当前消息中的图片（不含引用链）。"""
        for comp in event.get_messages():
            if isinstance(comp, Comp.Image):
                url = getattr(comp, "url", None) or getattr(comp, "file", None)
                if url:
                    return url
        return None

    @staticmethod
    def _get_reply_image(event: AstrMessageEvent) -> str | None:
        """仅从引用（回复）链中提取图片。"""
        for comp in event.get_messages():
            if isinstance(comp, Comp.Reply):
                chain = getattr(comp, "chain", None) or []
                for rc in chain:
                    if isinstance(rc, Comp.Image):
                        url = getattr(rc, "url", None) or getattr(rc, "file", None)
                        if url:
                            return url
        return None

    def _resolve_image_url(self, event: AstrMessageEvent, at_qq: str | None) -> str | None:
        """按优先级获取图片源：引用图 > 当前消息内联图 > @用户头像"""
        url = self._get_reply_image(event)
        if url:
            return url
        url = self._extract_image_url(event)
        if url:
            return url
        if at_qq and self._enable_at_avatar:
            return QQ_AVATAR_URL.format(qq=at_qq)
        return None

    async def _run_cutout(self, event: AstrMessageEvent, image_url: str, max_side: int):
        """下载图片 → 本地 rembg 抠图 → 发送透明 GIF。

        注意：进度提示必须用 event.send 直发，不能中间 yield。
        管道洋葱模型在 yield 后会跑 decorate/respond；其它插件 stop_event
        会截断生成器，导致后续抠图逻辑永不执行。
        """
        self._cutout_busy = True
        uid = uuid.uuid4().hex[:8]
        input_path = os.path.join(TMP_DIR, f"pt_in_{os.getpid()}_{uid}.tmp")
        output_path = os.path.join(TMP_DIR, f"pt_cutout_{os.getpid()}_{uid}.gif")
        loop = asyncio.get_event_loop()
        try:
            try:
                await event.send(MessageChain([Comp.Plain("抠图中，请稍候…")]))
            except Exception as e:
                logger.warning("[kimage] 抠图进度提示发送失败: %s", e)

            logger.info(
                "[kimage] 抠图开始: url=%s max_side=%s model=%s",
                (image_url or "")[:120],
                max_side,
                self._cutout_model,
            )
            ok = await loop.run_in_executor(None, _download_sync, image_url, input_path)
            if not ok:
                yield event.plain_result("图片下载失败，请稍后重试。")
                return
            logger.info(
                "[kimage] 抠图下载完成: path=%s size=%s",
                input_path,
                os.path.getsize(input_path) if os.path.isfile(input_path) else 0,
            )

            def _proc():
                return cutout.cutout_image(
                    input_path,
                    output_path,
                    model=self._cutout_model,
                    max_side=max_side,
                    gif_max_frames=self._cutout_gif_max_frames,
                    alpha_matting=bool(self._cutout_alpha_matting),
                )

            timeout = max(30, min(600, int(self._cutout_timeout_sec or 120)))
            try:
                note = await asyncio.wait_for(
                    loop.run_in_executor(None, _proc),
                    timeout=timeout,
                )
            except asyncio.TimeoutError:
                logger.error("[kimage] 抠图超时: timeout=%ss", timeout)
                yield event.plain_result(f"抠图超时（>{timeout}s），可缩小边长或减少动图帧数")
                return
            except cutout.CutoutDependencyError as e:
                yield event.plain_result(str(e))
                return
            except Exception as e:
                logger.exception("[kimage] 抠图失败: %s", e)
                yield event.plain_result(f"抠图失败: {e}")
                return

            if not os.path.isfile(output_path):
                yield event.plain_result("抠图失败：未生成输出文件")
                return

            logger.info(
                "[kimage] 抠图完成: out=%s size=%s note=%s",
                output_path,
                os.path.getsize(output_path),
                note or "",
            )
            chain = []
            if note:
                chain.append(Comp.Plain(note + "\n"))
            chain.append(Comp.Image(file=str(output_path)))
            yield event.chain_result(chain)

            out = output_path
            async def _cleanup():
                await asyncio.sleep(10)
                try:
                    os.remove(out)
                except OSError:
                    pass
            asyncio.ensure_future(_cleanup())
        finally:
            self._cutout_busy = False
            try:
                os.remove(input_path)
            except OSError:
                pass

    async def _download_and_process(self, event: AstrMessageEvent,
                                     image_url: str, processor, label: str,
                                     get_prefix=None):
        uid = uuid.uuid4().hex[:8]  # 每次请求唯一标识，避免并发冲突
        input_path = os.path.join(TMP_DIR, f"pt_in_{os.getpid()}_{uid}.tmp")
        output_path = None
        loop = asyncio.get_event_loop()
        ok = await loop.run_in_executor(None, _download_sync, image_url, input_path)
        if not ok:
            try:
                os.remove(input_path)
            except OSError:
                pass
            yield event.plain_result("图片下载失败，请稍后重试。")
            return

        ext = ".gif" if _is_gif(input_path) else ".png"
        output_path = os.path.join(TMP_DIR, f"pt_out_{os.getpid()}_{uid}{ext}")

        try:
            await loop.run_in_executor(None, processor, input_path, output_path)
        except Exception as e:
            logger.error(f"[pic_toolbox] {label} 失败: {e}")
            try:
                os.remove(output_path)
            except OSError:
                pass
            yield event.plain_result(f"处理失败: {e}")
            return
        finally:
            try:
                os.remove(input_path)
            except OSError:
                pass

        if get_prefix:
            prefix_text = get_prefix()
        else:
            prefix_text = None
        if prefix_text:
            yield event.chain_result([
                Comp.Plain(prefix_text + "\n"),
                Comp.Image(file=str(output_path)),
            ])
        else:
            yield event.chain_result([Comp.Image(file=str(output_path))])
        # 延迟 10s 后清理输出文件（给 QQ 足够时间上传）
        out = output_path
        async def _cleanup():
            await asyncio.sleep(10)
            try:
                os.remove(out)
                logger.debug(f"[pic_toolbox] 清理临时文件: {os.path.basename(out)}")
            except OSError:
                pass
        asyncio.ensure_future(_cleanup())

    async def _split_and_send(self, event: AstrMessageEvent,
                              image_url: str, count: int, smart: bool = False):
        """下载 GIF → 分解为 N 张 PNG → 合并转发发送。

        Args:
            smart: True 时使用智能关键帧采样，False 时使用百分比均匀采样
        """
        uid = uuid.uuid4().hex[:8]
        input_path = os.path.join(TMP_DIR, f"pt_in_{os.getpid()}_{uid}.tmp")
        output_dir = os.path.join(TMP_DIR, f"pt_split_{os.getpid()}_{uid}")
        loop = asyncio.get_event_loop()

        ok = await loop.run_in_executor(None, _download_sync, image_url, input_path)
        if not ok:
            try:
                os.remove(input_path)
            except OSError:
                pass
            yield event.plain_result("图片下载失败，请稍后重试。")
            return

        if not _is_gif(input_path):
            try:
                os.remove(input_path)
            except OSError:
                pass
            yield event.plain_result("分解仅支持动图（GIF）")
            return

        try:
            split_fn = split.split_gif_smart if smart else split.split_gif
            paths = await loop.run_in_executor(
                None, split_fn, input_path, output_dir, count
            )
        except ValueError as e:
            yield event.plain_result(str(e))
            return
        except Exception as e:
            label = "智能分解" if smart else "分解"
            logger.error(f"[pic_toolbox] {label}失败: {e}")
            yield event.plain_result(f"{label}失败: {e}")
            return
        finally:
            try:
                os.remove(input_path)
            except OSError:
                pass

        if not paths:
            label = "智能分解" if smart else "分解"
            yield event.plain_result(f"{label}失败：未生成任何图片")
            return

        actual_count = len(paths)
        self_id = event.get_self_id()
        self_uin = int(self_id) if str(self_id).isdigit() else 0
        label = "智能分解" if smart else "分解"

        # 构造合并转发节点
        node_list = []
        for i, p in enumerate(paths):
            node_list.append(Comp.Node(
                uin=self_uin,
                name=f"{label}结果 {i + 1}/{actual_count}",
                content=[Comp.Image(file=str(p))],
            ))

        try:
            nodes = Comp.Nodes(node_list)
            yield event.chain_result([nodes])
        except Exception as e:
            logger.warning(f"[pic_toolbox] 合并转发构造失败，降级逐张发送: {e}")
            for i, p in enumerate(paths):
                yield event.chain_result([Comp.Image(file=str(p))])

        # 延迟 10s 后清理输出文件
        _paths = paths
        _dir = output_dir
        async def _cleanup():
            await asyncio.sleep(10)
            for p in _paths:
                try:
                    os.remove(p)
                except OSError:
                    pass
            try:
                os.rmdir(_dir)
            except OSError:
                pass
            logger.debug(f"[pic_toolbox] 清理分解临时文件: {len(_paths)} 张")
        asyncio.ensure_future(_cleanup())

    async def _dual_avatar(self, event: AstrMessageEvent, at_qq: str, processor):
        """双头像处理：指令者 + 被 @ 者。"""
        sender_qq = event.get_sender_id()
        loop = asyncio.get_event_loop()
        uid = uuid.uuid4().hex[:8]
        c_path = os.path.join(TMP_DIR, f"pt_da_c_{os.getpid()}_{uid}.png")
        t_path = os.path.join(TMP_DIR, f"pt_da_t_{os.getpid()}_{uid}.png")
        o_path = os.path.join(TMP_DIR, f"pt_da_o_{os.getpid()}_{uid}.gif")

        def _clean_inputs():
            for p in (c_path, t_path):
                try:
                    os.remove(p)
                except OSError:
                    pass

        ok1 = await loop.run_in_executor(None, _download_sync, QQ_AVATAR_URL.format(qq=sender_qq), c_path)
        ok2 = await loop.run_in_executor(None, _download_sync, QQ_AVATAR_URL.format(qq=at_qq), t_path)
        if ok1 and ok2:
            try:
                processor(c_path, t_path, o_path)
                yield event.chain_result([Comp.Image(file=str(o_path))])
            except Exception as e:
                yield event.plain_result(f"失败: {e}")
                try:
                    os.remove(o_path)
                except OSError:
                    pass
            _clean_inputs()
            out = o_path
            async def _cleanup():
                await asyncio.sleep(10)
                try:
                    os.remove(out)
                    logger.debug(f"[pic_toolbox] 清理临时文件: {os.path.basename(out)}")
                except OSError:
                    pass
            asyncio.ensure_future(_cleanup())
        else:
            _clean_inputs()
            yield event.plain_result("下载失败")

    @staticmethod
    def _cleanup_stale_tempfiles():
        """清除进程崩溃后残留的旧临时文件（超过 1 小时的）。"""
        import time
        now = time.time()
        cutoff = now - 3600
        try:
            for fname in os.listdir(TMP_DIR):
                if fname.startswith("pt_") and not fname.endswith((".py", ".pyc")):
                    fpath = os.path.join(TMP_DIR, fname)
                    try:
                        if os.path.getmtime(fpath) < cutoff:
                            os.remove(fpath)
                            logger.info(f"[pic_toolbox] 清理残留: {fname}")
                    except OSError:
                        pass
        except OSError:
            pass

    async def terminate(self):
        pass
