# 🖼️ 小K图片处理工具箱 (astrbot_plugin_kimage)

基于 AstrBot 框架的群聊图片 / 头像处理插件。支持静态图和 GIF 的**反色、翻转、对称、旋转、故障、万花筒、抖动、呼吸、包浆、波普、电子包浆、扭曲、裸眼3D、马赛克、调速、倒放、往返、分解**以及**摸头杀、发射、撅人、抽、砍头**等一系列趣味表情包生成。所有 GIF 处理统一使用增量帧展开管道，保留原图时长、透明度与循环信息

<p align="center">
  <img src="https://img.shields.io/badge/version-2.2.0-blue" alt="Version">
  <img src="https://img.shields.io/badge/Python-3.8%2B-blue" alt="Python">
  <img src="https://img.shields.io/badge/AstrBot-%E6%8F%92%E4%BB%B6%E6%A1%86%E6%9E%B6-brightgreen" alt="AstrBot">
  <img src="https://img.shields.io/badge/license-MIT-green" alt="License">
</p>

---

## ✨ 功能一览

### 🎨 基础变换

| 指令 | 说明 | 图片来源 |
| :--- | :--- | :--- |
| `反色` | 对图片 / GIF 执行反色处理 | 引用回复 / 直接发送 / `@用户` |
| `旋转 [角度步长]` | 圆形旋转 GIF，默认 6°/帧 | 同上 |
| `左右翻转` | 水平镜像翻转 | 同上 |
| `上下翻转` | 垂直颠倒翻转 | 同上 |

### 🪞 对称

| 指令 | 说明 | 图片来源 |
| :--- | :--- | :--- |
| `对称` / `对称1` / `对称左` / `左对称` | 保留左半边 → 镜像到右（默认） | 引用 / 直接 / `@用户` |
| `对称2` / `对称上` / `上对称` | 保留上半边 → 镜像到下 | 同上 |
| `对称3` / `对称左上` / `左上对称` | \\ 对角线对称（保留左上三角） | 同上 |
| `对称4` / `对称右上` / `右上对称` | / 对角线对称（保留右上三角） | 同上 |
| `对称5` / `对称右` / `右对称` | 保留右半边 → 镜像到左 | 同上 |
| `对称6` / `对称下` / `下对称` | 保留下半边 → 镜像到上 | 同上 |
| `真对称[1-4]` / `真对称右/左/上/下` / `右/左/上/下真对称` | 延展型对称，画布扩大 | 同上 |

> `真对称1` / `真对称右` / `右真对称` = 向右延展（宽度翻倍），`2`/`真对称左`/`左真对称`=向左，`3`/`真对称上`/`上真对称`=向上，`4`/`真对称下`/`下真对称`=向下

### 🖼️ 视觉特效

| 指令 | 说明 | 图片来源 |
| :--- | :--- | :--- |
| `故障 [强度]` | RGB 通道分离偏移，赛博故障风 GIF | 引用 / 直接 / `@用户` |
| `万花筒 [扇区]` | 扇区镜像对称旋转 GIF | 同上 |
| `抖动 [颜色数]` | 降色阶 + Floyd-Steinberg 抖动，复古 8-bit | 同上 |
| `呼吸 [帧延迟]` | 周期缩放呼吸动画 GIF | 同上 |
| `包浆 [强度]` | Sepia 染色 + 暗角 + 噪点 + 褪色，老照片感 | 同上 |
| `波普 [格数]` | Pop Art 波普艺术（默认 2 联画不同配色，支持动图联画） | 同上 |
| `电子包浆 [程度]` | JPEG 伪影 + 色彩断层 + 像素化，互联网蹂躏感 | 同上 |
| `扭曲 [类型] [强度]` | 6 种扭曲（凸/凹/横柱/竖柱/波浪/螺旋） | 同上 |
| `裸眼3d [强度]` | 帧差法前景提取，裸眼3D 效果 GIF | 同上 |
| `马赛克 [程度]` | 马赛克处理，默认块大小 8 | 同上 |

### 🎭 表情包 / 动效

| 指令 | 说明 | 类型 | 图片来源 |
| :--- | :--- | :--- | :--- |
| `摸头` | Petpet 摸头杀 GIF | 单人头 | 引用 / 直接 / `@用户` |
| `发射` | 射击表情包（含人脸检测定位） | 单人头 | 引用 / 直接 / `@用户` |
| `杀` | 砍头表情包 GIF | 单人头 | 必须 `@用户` |
| `撅` | 撅人表情包（双人互动） | 双人头 | 必须 `@用户` |
| `抽` | 鞭笞表情包（双人互动） | 双人头 | 必须 `@用户` |

### 🔄 GIF 动效

| 指令 | 说明 | 图片来源 |
| :--- | :--- | :--- |
| `加速 [倍率]` | GIF 加速，默认 2.5 倍速，范围 0.3~5.0 | 引用 / 直接 |
| `调速 <倍率>` | 精准 GIF 调速（必带参数） | 引用 / 直接 |
| `倒放` | 反转 GIF 帧顺序 | 引用 / 直接 / `@用户` |
| `往返` | GIF 正序+倒序 ping-pong 循环 | 同上 |
| `分解 [张数]` | 将 GIF 按百分比均匀采样分解为 N 张图片，合并转发发送（默认3，最大15） | 同上 |

### 通用特性

- **图片来源优先级**：①引用回复图片 ②当前消息内联图片 ③ `@用户` 的 QQ 头像（需开启 `enable_at_avatar`）
- **GIF 全支持**：所有变换和特效指令均正确处理 GIF 增量帧，保留时长、透明度与循环信息
- **紧凑语法**：`对称1` `扭曲1 0.5` `旋转90` `加速2.5` 等全部单参命令支持不带空格触发
- **带参触发**：多数指令支持参数覆盖配置默认值
- **精准匹配**：`match_mode` 开启后可直接发送词语触发，无需 `/` 前缀
- **自动清理**：启动时清理超过 1 小时的残留临时文件，处理后 10 秒自动删除输出文件

---

## 🛠️ 配置项

| 配置 | 类型 | 默认值 | 说明 |
| :--- | :--- | :--- | :--- |
| `enable_at_avatar` | bool | `true` | 允许 `@用户 + 指令` 获取对方头像处理 |
| `match_mode` | bool | `true` | 开启后直接发文字即可触发，无需 `/` 前缀 |
| `gif_speed_allow_frame_drop` | bool | `true` | 调速超 50 FPS 时允许均匀丢帧 |
| `default_speedup_factor` | float | `2.5` | 「加速」默认倍率 |
| `default_pixelate_block` | int | `8` | 「马赛克」默认块大小 |
| `spin_direction` / `spin_angle_step` | str/int | `clockwise` / `6` | 旋转方向与每帧角度 |
| `glitch_max_shift` / `glitch_num_frames` / `glitch_frame_delay` | int | `15` / `8` / `80` | 故障偏移/帧数/延迟 |
| `kal_sectors` / `kal_zoom` / `kal_angle_step` / `kal_frame_delay` | int/float/int/int | `8` / `0.5` / `3` / `40` | 万花筒参数 |
| `dither_num_colors` | int | `16` | 抖动颜色数 |
| `breath_min_scale` / `breath_max_scale` / `breath_frames` / `breath_frame_delay` | float/float/int/int | `0.92` / `1.08` / `30` / `40` | 呼吸缩放参数 |
| `patina_sepia_strength` / `patina_vignette_strength` / `patina_noise_amount` / `patina_fade_amount` | int | `60` / `40` / `20` / `30` | 包浆参数 |
| `popart_num_colors` / `popart_edge_width` / `popart_halftone_size` / `popart_panels` | int | `8` / `1` / `0` / `2` | 波普艺术参数 |
| `digital_patina_jpeg_quality` / `digital_patina_banding_level` / `digital_patina_pixelate_size` / `digital_patina_green_tint` | int | `15` / `5` / `0` / `40` | 电子包浆参数 |
| `funhouse_mirror_type` / `funhouse_mirror_strength` | str/float | `bulge` / `1.0` | 扭曲类型与强度 |
| `be3d_line_spacing` / `be3d_line_width` / `be3d_line_alpha` / `be3d_line_direction` / `be3d_mask_threshold` / `be3d_mask_blur` / `be3d_foreground_blur` / `be3d_max_frames` | int/int/int/str/int/int/int/int | `40` / `4` / `200` / `both` / `15` / `7` / `0` / `48` | 裸眼3D 参数 |
| `split_default_count` / `split_max_count` | int/int | `3` / `15` | 分解默认张数 / 最大张数 |

---

## ⚡ GIF 调速详解

`调速` 指令支持 0.3× ~ 5.0× 变速。GIF 调速遵循 **最高 50 FPS** 的硬上限（对应每帧最短 20ms），超出上限时有两种策略：

### 默认策略：自动取最接近上限倍率（推荐）

当请求倍率导致帧率超过 50 FPS 时，插件自动计算不超过 50 FPS 的最高合法倍率并回退。

### 丢帧模式：`gif_speed_allow_frame_drop`

开启后调速不再回退倍率，通过均匀丢帧保证每帧间隔不低于 20ms。

---

## 📦 安装与依赖

### 安装

将插件目录放入 AstrBot `addons/plugins/` 目录，或通过 AstrBot 管理面板上传安装。

### 依赖

```bash
pip install Pillow>=10.0.0 requests>=2.25.0
pip install opencv-python-headless  # 发射指令需要
```

> `opencv-python-headless` 仅 `发射`（人脸检测）需要，同时也会安装 numpy。

---

## 🖼️ 使用示例

```
用户：（发送一张图片）
用户：反色
Bot：  [返回反色后的图片]

用户：（引用一张 GIF）
用户：故障 30
Bot：  [返回 RGB 偏移故障风 GIF]

用户：@某人 对称
Bot：  [取对方头像 → 左对称拼接]

用户：@某人 撅
Bot：  [取发送者 + 被 @ 者头像 → 生成撅人 GIF]

用户：（引用一张 GIF）
用户：分解 5
Bot：  [合并转发：5 张按百分比采样的关键帧图片]
```

---

## 📁 项目结构

```
astrbot_plugin_kimage/
├── main.py              # 插件主体：指令路由与事件处理
├── metadata.yaml        # 插件元数据
├── _conf_schema.json    # 配置 Schema（24+ 配置项）
├── requirements.txt     # Python 依赖
├── logo.png             # 插件图标
├── meme/                # 图像处理模块
│   ├── gif_utils.py     # GIF 帧展开与保存公用函数
│   ├── invert.py        # 反色
│   ├── flip.py          # 水平 / 垂直翻转
│   ├── mirror.py        # 对称（含斜边/延展/统一入口）
│   ├── spin.py          # 旋转动画 GIF
│   ├── glitch.py        # RGB 故障风
│   ├── kaleidoscope.py  # 万花筒
│   ├── dither.py        # 抖动 / 降色
│   ├── breathing.py     # 呼吸缩放
│   ├── patina.py        # 包浆做旧
│   ├── popart.py        # 波普艺术
│   ├── digital_patina.py # 电子包浆
│   ├── funhouse_mirror.py # 扭曲
│   ├── bare_eye_3d.py   # 裸眼3D
│   ├── gif_speed.py     # GIF 调速
│   ├── pixelate.py      # 马赛克
│   ├── reverse.py       # GIF 倒放
│   ├── roundtrip.py     # GIF 往返
│   ├── split.py         # GIF 分解（按百分比采样为多张 PNG）
│   ├── petpet.py        # 摸头杀
│   ├── shoot.py         # 射击（含人脸检测）
│   ├── do.py            # 撅人（双人头）
│   ├── lash.py          # 鞭笞（双人头）
│   └── behead.py        # 砍头
└── resource/            # 资源素材
    ├── petpet_hand.png
    ├── lbpcascade_animeface.xml
    ├── do_frames/
    ├── shoot_frames/
    ├── lash_frames/
    └── behead_frames/
```

---

## 📝 许可证

[MIT License](LICENSE)

---

## 🙏 鸣谢

- [AstrBot](https://github.com/AstrBotDevs/AstrBot) — 机器人框架
- [Pillow](https://python-pillow.org/) — 图像处理核心库
- [OpenCV](https://opencv.org/) — 人脸检测
- [nagadomi/lbpcascade_animeface](https://github.com/nagadomi/lbpcascade_animeface) — 动漫人脸级联分类器
- [B1gM8c/Petpet](https://github.com/B1gM8c/Petpet) — 摸头杀原始算法
- [meme-generator](https://github.com/MeetWq/meme-generator) — 表情包灵感来源
- [lirundong093-glitch/astrbot_plugin_pic_toolbox](https://github.com/lirundong093-glitch/astrbot_plugin_pic_toolbox) — 本插件系其分支，感谢原作 Lucy

<p align="center">Maintained by <a href="https://github.com/konley">konley</a></p>
