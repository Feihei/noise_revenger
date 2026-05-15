# Noise Revenger - 噪音实时反馈系统

运行在 Windows 电脑上的实时噪音检测与反馈系统。通过麦克风采集环境音频，自动识别楼上噪音（低频冲击、高频摩擦），并即时播放提醒声音。

---

## 环境配置

### 系统要求

| 项目 | 要求 |
|------|------|
| 操作系统 | Windows 10/11（64 位） |
| Python | 3.12 或更高版本 |
| 包管理器 | [uv](https://docs.astral.sh/uv/)（推荐）或 pip |
| 内存 | 建议 4GB 以上 |
| 磁盘空间 | 约 500MB（含依赖） |

### 硬件需求

| 设备 | 说明 |
|------|------|
| 麦克风 | USB 麦克风或 3.5mm 接口麦克风，用于环境音频采集 |
| 音箱 | 蓝牙音箱或有线音箱，用于播放提醒声音 |

### 安装步骤

#### 1. 获取项目代码

```bash
# 方式一：克隆 Git 仓库
git clone <repository-url>
cd noise_revenger

# 方式二：直接解压项目压缩包
# 解压后进入项目目录
cd noise_revenger
```

#### 2. 安装 uv 包管理器（如未安装）

```powershell
# 使用官方安装脚本
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# 安装完成后重启终端，验证安装
uv --version
```

#### 3. 安装项目依赖

```bash
# 使用 uv 创建虚拟环境并安装所有依赖（推荐）
uv sync

# 如果只需要生产依赖（不含开发工具）
uv sync --no-dev
```

#### 4. 验证安装

```bash
# 运行测试套件，确认所有组件正常工作
uv run pytest tests/ -v

# 预期输出：42 passed
```

#### 5. 生成提醒音效（首次使用）

```bash
# 运行音效生成脚本，创建默认提醒音频
uv run python generate_sounds.py

# 预期输出：在 sounds/ 目录下生成 alert_mild.wav、alert_medium.wav、alert_strong.wav
```

---

## 操作步骤

### 启动方式

项目提供两种运行模式：图形界面（GUI）模式和命令行（CLI）模式。

#### GUI 模式（推荐）

```bash
uv run python main.py --gui
```

启动后界面包含以下区域：

| 区域 | 功能 |
|------|------|
| 音频设备 | 选择麦克风输入设备和音箱输出设备 |
| 检测参数 | 调整低频/高频噪音检测阈值 |
| 控制按钮 | 开始/停止监听，实时显示运行状态 |
| 事件日志 | 折叠面板，记录每次检测到的噪音事件 |

#### CLI 模式

```bash
uv run python main.py
```

命令行模式无界面，适合后台运行或调试。

### 基本使用流程

#### 第一步：连接硬件

1. 将麦克风连接至电脑（USB 或 3.5mm）
2. 将蓝牙音箱配对并连接（或使用有线音箱）
3. 确认 Windows 声音设置中设备正常工作

#### 第二步：启动程序

```bash
uv run python main.py --gui
```

#### 第三步：选择音频设备

在界面"音频设备"区域：
- **输入设备**：选择你的麦克风
- **输出设备**：选择你的音箱

> 如果不确定哪个设备，可以在 Windows 声音设置中查看设备名称进行匹配。

#### 第四步：调整检测参数（可选）

在"检测参数"区域拖动滑块：
- **低频阈值**：控制对砸楼板、重物落地等低频噪音的灵敏度
  - 值越小 → 越灵敏，可能误报
  - 值越大 → 越保守，可能漏报
- **高频阈值**：控制对拉拽椅子、拖动家具等高频噪音的灵敏度

> 建议首次使用时保持默认值，运行一段时间后根据实际效果微调。

#### 第五步：开始监听

1. 点击 **"开始监听"** 按钮
2. 系统进入 **背景学习阶段**（默认 10 秒），期间请保持环境安静
3. 学习完成后，状态变为 **"监听中"**，系统开始实时检测

#### 第六步：查看事件日志

检测到噪音时：
- 自动播放对应强度的提醒声音
- 事件日志面板自动记录：时间、类型、强度、置信度
- 点击 **"事件日志"** 标题栏可折叠/展开日志区

#### 第七步：停止监听

点击 **"停止监听"** 按钮即可。关闭窗口时如正在监听，会弹出确认提示。

---

## 参数说明

### 命令行参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `--gui` | 布尔标志 | `false` | 启动图形用户界面。不带此参数则以命令行模式运行 |

**示例：**

```bash
# 命令行模式
python main.py

# GUI 模式
python main.py --gui
```

### 配置文件参数

配置文件位于 `config/settings.yaml`，所有参数均可编辑。

#### 音频配置（audio）

| 参数 | 类型 | 默认值 | 取值范围 | 说明 |
|------|------|--------|----------|------|
| `sample_rate` | int | `44100` | 8000 - 192000 | 音频采样率（Hz），越高音质越好但占用更多资源 |
| `chunk_size` | int | `1024` | 256 - 4096 | 音频缓冲区大小，影响处理延迟。值越小延迟越低，但 CPU 占用越高 |
| `channels` | int | `1` | 1 - 2 | 音频通道数，1 为单声道，2 为立体声 |
| `input_device_index` | int/null | `null` | 0 - 设备总数-1 | 麦克风设备索引，`null` 表示使用系统默认输入设备 |

**示例：**

```yaml
audio:
  sample_rate: 44100
  chunk_size: 1024
  channels: 1
  input_device_index: 2    # 使用索引为 2 的麦克风
```

#### 低频检测配置（detection.low_freq）

| 参数 | 类型 | 默认值 | 取值范围 | 说明 |
|------|------|--------|----------|------|
| `enabled` | bool | `true` | `true` / `false` | 是否启用低频噪音检测 |
| `freq_range` | list | `[20, 250]` | [10, 500] | 监测频率范围（Hz），覆盖脚步声、重物落地等低频噪音 |
| `energy_threshold` | float | `3.0` | 1.0 - 10.0 | 能量阈值（相对于背景噪声的倍数）。值越小越灵敏 |
| `spectral_centroid_max` | float | `500.0` | 200 - 1000 | 频谱质心上限（Hz），用于判断能量是否集中在低频 |
| `window_size` | float | `0.1` | 0.05 - 0.5 | 分析窗口大小（秒） |

**示例：**

```yaml
detection:
  low_freq:
    enabled: true
    freq_range: [20, 250]
    energy_threshold: 2.5      # 提高灵敏度（从 3.0 降低到 2.5）
    spectral_centroid_max: 500
    window_size: 0.1
```

#### 高频检测配置（detection.high_freq）

| 参数 | 类型 | 默认值 | 取值范围 | 说明 |
|------|------|--------|----------|------|
| `enabled` | bool | `true` | `true` / `false` | 是否启用高频噪音检测 |
| `freq_range` | list | `[2000, 8000]` | [1000, 16000] | 监测频率范围（Hz），覆盖椅子拖动、家具摩擦等高频噪音 |
| `energy_threshold` | float | `2.5` | 1.0 - 10.0 | 能量阈值（相对于背景噪声的倍数）。值越小越灵敏 |
| `zero_crossing_min` | float | `0.3` | 0.1 - 0.8 | 过零率下限，用于识别尖锐摩擦声特征 |
| `window_size` | float | `0.05` | 0.02 - 0.2 | 分析窗口大小（秒） |

**示例：**

```yaml
detection:
  high_freq:
    enabled: true
    freq_range: [2000, 8000]
    energy_threshold: 2.0      # 提高灵敏度
    zero_crossing_min: 0.3
    window_size: 0.05
```

#### 通用检测配置（detection）

| 参数 | 类型 | 默认值 | 取值范围 | 说明 |
|------|------|--------|----------|------|
| `cooldown_seconds` | float | `5.0` | 1.0 - 60.0 | 冷却时间（秒），两次触发之间的最小间隔，防止重复报警 |
| `background_learning_seconds` | float | `10.0` | 5.0 - 60.0 | 背景噪声学习时间（秒），启动时采集环境底噪 |

#### 反馈配置（feedback）

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `enabled` | bool | `true` | 是否启用声音反馈 |
| `output_device_index` | int/null | `null` | 音箱设备索引，`null` 表示使用系统默认输出设备 |
| `volume` | float | `1.0` | 音量（0.0 - 1.0） |
| `sounds.mild` | string | `"sounds/alert_mild.wav"` | 轻度噪音提醒音效路径 |
| `sounds.medium` | string | `"sounds/alert_medium.wav"` | 中度噪音提醒音效路径 |
| `sounds.strong` | string | `"sounds/alert_strong.wav"` | 重度噪音提醒音效路径 |

#### 日志配置（logging）

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `level` | string | `"INFO"` | 日志级别：`DEBUG`、`INFO`、`WARNING`、`ERROR` |
| `save_audio_clips` | bool | `false` | 是否保存检测到的噪音音频片段 |
| `clips_dir` | string | `"logs/clips"` | 音频片段保存目录 |

---

## 故障排除

### 音频设备相关

#### 问题：无法找到音频设备 / 设备列表为空

**现象：** 启动后设备下拉菜单为空，或报错 "无法加载音频设备"

**可能原因：**
- 麦克风未正确连接
- 设备驱动未安装
- Windows 隐私设置禁止麦克风访问

**解决步骤：**

1. 检查硬件连接，确认麦克风已插入且指示灯亮起
2. 打开 Windows 设置 → 隐私 → 麦克风，确保"允许应用访问麦克风"已开启
3. 在 Windows 声音设置中确认设备已被识别
4. 运行以下命令查看系统可用设备：

```bash
uv run python -c "import sounddevice as sd; print(sd.query_devices())"
```

#### 问题：听不到提醒声音

**现象：** 检测到噪音但音箱无声音输出

**可能原因：**
- 音箱未连接或音量过低
- 输出设备选择错误
- 音效文件不存在

**解决步骤：**

1. 确认音箱已连接且音量已调高
2. 在界面中检查"输出设备"是否选择了正确的音箱
3. 确认 `sounds/` 目录下存在 `.wav` 音效文件，如缺失请运行：

```bash
uv run python generate_sounds.py
```

4. 测试音箱是否正常：

```bash
uv run python -c "import pygame; pygame.mixer.init(); s = pygame.mixer.Sound('sounds/alert_mild.wav'); s.play(); import time; time.sleep(2)"
```

### 依赖安装相关

#### 问题：uv sync 失败 / 依赖安装超时

**现象：** 执行 `uv sync` 时出现网络错误或超时

**可能原因：**
- 网络环境无法访问 PyPI
- 镜像源配置问题

**解决步骤：**

1. 项目已配置清华镜像源，如仍失败可手动指定：

```bash
uv sync --index-url https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple
```

2. 如果使用 pip，可设置镜像：

```bash
pip install -e . --index-url https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple
```

#### 问题：sounddevice 安装失败

**现象：** 安装 sounddevice 时出现编译错误或 "PortAudio not found"

**可能原因：**
- 缺少 PortAudio 库（Windows 通常预装）
- 缺少编译工具链

**解决步骤：**

1. 尝试安装预编译 wheel：

```bash
uv pip install sounddevice --only-binary :all:
```

2. 如仍失败，手动安装 PortAudio：
   - 下载：http://www.portaudio.com/download.html
   - 将 `portaudio.dll` 放入系统 PATH 或项目根目录

### 运行时异常

#### 问题：启动后立即崩溃 / 报错

**现象：** 程序启动后闪退或打印错误堆栈

**可能原因：**
- Python 版本不兼容（需要 3.12+）
- 配置文件格式错误
- 缺少必要目录

**解决步骤：**

1. 检查 Python 版本：

```bash
python --version
# 应输出 Python 3.12.x 或更高
```

2. 检查配置文件语法：

```bash
uv run python -c "import yaml; yaml.safe_load(open('config/settings.yaml')); print('配置文件格式正确')"
```

3. 确保必要目录存在：

```bash
mkdir -p sounds logs logs/clips
```

4. 以 DEBUG 级别运行查看详细日志：

```bash
# 编辑 config/settings.yaml，将 logging.level 改为 "DEBUG"
# 然后重新启动程序
```

#### 问题：误报频繁（安静环境也触发）

**现象：** 环境安静时仍频繁触发提醒

**可能原因：**
- 阈值设置过低
- 背景噪声学习期间环境不够安静
- 麦克风灵敏度过高

**解决步骤：**

1. 调高检测阈值（在界面滑块或配置文件中）：
   - 低频阈值：从 3.0 提高到 4.0 或更高
   - 高频阈值：从 2.5 提高到 3.5 或更高

2. 重启程序，确保背景学习期间环境安静

3. 降低 Windows 麦克风增益：
   - 右键音量图标 → 声音设置 → 输入 → 设备属性 → 降低音量

#### 问题：漏报（有噪音但未检测到）

**现象：** 明显有噪音但程序未触发提醒

**可能原因：**
- 阈值设置过高
- 频率范围不匹配实际噪音特征
- 冷却时间过长

**解决步骤：**

1. 降低检测阈值：
   - 低频阈值：从 3.0 降低到 2.0
   - 高频阈值：从 2.5 降低到 1.5

2. 调整频率范围（如噪音特征不在默认范围内）

3. 缩短冷却时间（如需要更频繁触发）：

```yaml
detection:
  cooldown_seconds: 2.0    # 从 5.0 降低到 2.0
```

#### 问题：GUI 界面无法启动

**现象：** 运行 `python main.py --gui` 后无界面弹出或报错

**可能原因：**
- tkinter 未安装（Windows Python 通常自带）
- 显示环境问题

**解决步骤：**

1. 验证 tkinter 可用性：

```bash
uv run python -c "import tkinter; print('tkinter 可用')"
```

2. 如 tkinter 不可用，重新安装 Python 并确保勾选 "tcl/tk and IDLE" 组件

3. 尝试命令行模式作为替代：

```bash
uv run python main.py
```

### 日志查看

程序运行日志保存在 `logs/noise_revenger.log`，噪音事件记录在 `logs/noise_events.jsonl` 和 `logs/noise_events_YYYY-MM-DD.csv`。

```bash
# 查看最新日志
type logs\noise_revenger.log

# 查看今日噪音事件统计
uv run python -c "from src.logger import EventLogger; e = EventLogger(); print(e.get_stats())"
```

---

## 项目结构

```
noise_revenger/
├── src/                          # 源代码
│   ├── __init__.py
│   ├── audio_capture.py          # 音频采集模块
│   ├── noise_detector/
│   │   ├── __init__.py
│   │   ├── low_freq.py           # 低频冲击检测
│   │   ├── high_freq.py          # 高频摩擦检测
│   │   └── engine.py             # 检测引擎
│   ├── feedback_player.py        # 音频播放模块
│   ├── config.py                 # 配置管理
│   ├── logger.py                 # 日志模块
│   └── gui.py                    # 图形界面
├── sounds/                       # 提醒音效
├── config/
│   └── settings.yaml             # 配置文件
├── logs/                         # 日志目录
├── tests/                        # 测试用例
├── generate_sounds.py            # 音效生成脚本
├── main.py                       # 程序入口
└── pyproject.toml                # 项目配置
```

---

## 注意事项

- 首次使用需在安静环境下运行，让系统准确学习背景噪声
- 阈值参数需根据实际环境微调，建议从小幅度调整开始
- 蓝牙音箱可能存在延迟，建议使用有线音箱或低延迟蓝牙音箱
- 请合理使用，避免激化邻里矛盾
