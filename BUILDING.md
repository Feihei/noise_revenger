# 打包说明文档

## 概述

本项目使用 PyInstaller 将 Python 应用程序打包为 Windows 可执行文件。打包后的程序无需安装 Python 环境即可直接运行。

---

## 打包后的目录结构

```
NoiseRevenger/                          # 分发根目录（整体打包给朋友）
├── NoiseRevenger.exe                   # 主程序（双击运行）
├── _internal/                          # 运行时依赖（自动生成，勿手动修改）
├── config/                             # 配置目录（可编辑）
│   └── settings.yaml                   # 主配置文件
├── sounds/                             # 音效目录（可替换）
│   ├── alert_mild.wav                  # 轻度提醒音效
│   ├── alert_medium.wav                # 中度提醒音效
│   └── alert_strong.wav                # 重度提醒音效
└── logs/                               # 日志目录（运行时自动生成）
    ├── noise_revenger.log              # 程序运行日志
    ├── noise_events.jsonl              # 噪音事件记录（JSON 格式）
    ├── noise_events_YYYY-MM-DD.csv     # 每日噪音事件（CSV 格式）
    └── clips/                          # 音频片段目录（可选）
```

---

## 独立文件说明

### 1. 配置文件 `config/settings.yaml`

**位置：** `NoiseRevenger/config/settings.yaml`

**可编辑性：** 用户可使用任意文本编辑器（如记事本）直接编辑。

**修改后生效方式：** 修改配置文件后，**重启程序**即可生效。

**常用可调整参数：**

```yaml
# 低频检测阈值（默认 3.0，调高降低灵敏度，调低提高灵敏度）
detection:
  low_freq:
    energy_threshold: 3.0

# 高频检测阈值（默认 2.5）
  high_freq:
    energy_threshold: 2.5

# 冷却时间（默认 5 秒，两次提醒之间的最小间隔）
  cooldown_seconds: 5.0

# 音量（0.0 - 1.0）
feedback:
  volume: 1.0
```

### 2. 音效文件 `sounds/`

**位置：** `NoiseRevenger/sounds/`

**可替换性：** 用户可将 `alert_mild.wav`、`alert_medium.wav`、`alert_strong.wav` 替换为任意 `.wav` 格式音频文件。

**要求：**
- 文件格式必须为 `.wav`
- 文件名必须与配置文件中一致（默认：`alert_mild.wav`、`alert_medium.wav`、`alert_strong.wav`）
- 替换后无需重启程序，下次触发时自动使用新音效

**自定义音效示例：**

如果你想使用自己的提醒声音：
1. 准备一个 `.wav` 格式的音频文件
2. 将其复制到 `sounds/` 目录
3. 命名为 `alert_mild.wav`（或对应强度等级）
4. 覆盖原有文件即可

---

## 打包方法（开发者）

### 前置条件

确保已安装 uv 和项目依赖：

```bash
uv sync --group dev
```

PyInstaller 已包含在开发依赖中（`pyproject.toml` 的 `dev` 组）。

### 方式一：使用构建脚本（推荐）

```bash
# Windows 下直接运行批处理脚本
build.bat
```

该脚本会自动：
1. 清理旧的构建文件
2. 运行 PyInstaller 打包
3. 复制 `config/`、`sounds/` 到分发目录
4. 创建 `logs/` 目录结构

### 方式二：手动打包

```bash
# 1. 运行 PyInstaller
uv run pyinstaller noise_revenger.spec

# 2. 复制配置文件
mkdir dist\NoiseRevenger\config
copy config\settings.yaml dist\NoiseRevenger\config\

# 3. 复制音效文件
mkdir dist\NoiseRevenger\sounds
copy sounds\*.wav dist\NoiseRevenger\sounds\

# 4. 创建日志目录
mkdir dist\NoiseRevenger\logs
mkdir dist\NoiseRevenger\logs\clips
```

### 分发

打包完成后，将 `dist/NoiseRevenger/` 整个文件夹压缩为 ZIP 文件，发送给朋友即可：

```bash
# 压缩为 ZIP（PowerShell）
Compress-Archive -Path dist\NoiseRevenger -DestinationPath NoiseRevenger.zip
```

朋友收到后只需：
1. 解压 ZIP 文件到任意位置
2. 双击 `NoiseRevenger.exe` 运行

---

## 路径机制说明

程序使用动态路径解析，确保在开发环境和打包后都能正确定位文件：

| 资源 | 开发环境路径 | 打包后路径 |
|------|-------------|-----------|
| 配置文件 | `项目根目录/config/settings.yaml` | `exe所在目录/config/settings.yaml` |
| 音效文件 | `项目根目录/sounds/*.wav` | `exe所在目录/sounds/*.wav` |
| 日志目录 | `项目根目录/logs/` | `exe所在目录/logs/` |

核心实现位于 `src/paths.py`，通过检测 `sys.frozen` 标志判断运行环境，自动选择正确的基目录。

---

## 常见问题

### Q: 打包后修改配置文件不生效？

**A:** 修改配置文件后需要**重启程序**才能生效。程序仅在启动时读取一次配置。

### Q: 可以打包成单个 exe 文件吗？

**A:** 可以，但不推荐。单文件模式（`--onefile`）会将所有资源嵌入 exe，导致：
- 配置文件和音效无法独立编辑
- 首次启动需要解压到临时目录，启动较慢
- 杀毒软件更容易误报

当前使用的目录模式（`--onedir`）是最适合本项目的方案。

### Q: 打包体积较大（约 150MB）？

**A:** 主要因为包含了 Python 解释器和 numpy/scipy 等大型库。这是正常现象。如需减小体积：
- 移除不需要的模块（如 matplotlib）
- 使用 UPX 压缩（已启用）

### Q: 朋友电脑上运行时被杀毒软件拦截？

**A:** PyInstaller 打包的程序可能被误报。解决方法：
1. 将 `NoiseRevenger.exe` 添加到杀毒软件白名单
2. 使用代码签名证书（如有条件）
3. 向杀毒软件厂商提交误报申诉

### Q: 如何添加程序图标？

**A:** 准备一个 `.ico` 文件，在 `noise_revenger.spec` 中修改：

```python
exe = EXE(
    ...
    icon='icon.ico',  # 添加图标路径
)
```

然后重新运行打包命令。
