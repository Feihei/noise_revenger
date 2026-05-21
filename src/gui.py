"""GUI module for Noise Revenger - Tkinter-based graphical interface."""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import logging
from datetime import datetime
from typing import Optional

from .config import load_config, save_config, AppConfig
from .audio_capture import AudioCapture
from .noise_detector.engine import NoiseDetector
from .feedback_player import FeedbackPlayer
from .logger import EventLogger
from .paths import get_logs_dir

logger = logging.getLogger(__name__)


class CollapsibleFrame(ttk.Frame):
    """A collapsible/expandable frame widget."""

    def __init__(self, parent, title, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)

        self._collapsed = False
        self._content_frame = ttk.Frame(self)

        self._header = ttk.Frame(self)
        self._header.pack(fill=tk.X, padx=0, pady=0)

        self._toggle_btn = ttk.Button(
            self._header,
            text=f"▶ {title}",
            command=self._toggle,
            width=12,
        )
        self._toggle_btn.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self._content_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def _toggle(self):
        if self._collapsed:
            self._content_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            self._toggle_btn.config(text=self._toggle_btn.cget("text").replace("▶", "▼"))
        else:
            self._content_frame.pack_forget()
            self._toggle_btn.config(text=self._toggle_btn.cget("text").replace("▼", "▶"))
        self._collapsed = not self._collapsed

    def content(self):
        return self._content_frame


class NoiseRevengerGUI:
    """Main GUI application for Noise Revenger."""

    def __init__(self, config: Optional[AppConfig] = None):
        self.config = config or load_config()
        self._running = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

        self.capture: Optional[AudioCapture] = None
        self.detector: Optional[NoiseDetector] = None
        self.player: Optional[FeedbackPlayer] = None
        self.event_logger: Optional[EventLogger] = None

        self._setup_root()
        self._build_ui()
        self._load_devices()

    def _setup_root(self):
        self.root = tk.Tk()
        self.root.title("Noise Revenger - 噪音实时反馈系统")
        self.root.geometry("600x750")
        self.root.minsize(500, 600)
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)

        style = ttk.Style()
        style.theme_use("clam")

        style.configure("Title.TLabel", font=("Microsoft YaHei UI", 16, "bold"))
        style.configure("Status.TLabel", font=("Microsoft YaHei UI", 10))
        style.configure("Running.TLabel", foreground="#22c55e", font=("Microsoft YaHei UI", 10, "bold"))
        style.configure("Stopped.TLabel", foreground="#ef4444", font=("Microsoft YaHei UI", 10, "bold"))
        style.configure("Section.TLabelframe", font=("Microsoft YaHei UI", 10, "bold"))
        style.configure("Section.TLabelframe.Label", font=("Microsoft YaHei UI", 10, "bold"))
        style.configure("Action.TButton", font=("Microsoft YaHei UI", 11, "bold"))
        style.configure("Log.TText", font=("Consolas", 9))

    def _build_ui(self):
        main_frame = ttk.Frame(self.root, padding=15)
        main_frame.pack(fill=tk.BOTH, expand=True)

        self._build_title(main_frame)
        self._build_device_section(main_frame)
        self._build_threshold_section(main_frame)
        self._build_control_section(main_frame)
        self._build_log_section(main_frame)
        self._build_status_bar(main_frame)

    def _build_title(self, parent):
        title_frame = ttk.Frame(parent)
        title_frame.pack(fill=tk.X, pady=(0, 15))

        title_label = ttk.Label(
            title_frame,
            text="Noise Revenger",
            style="Title.TLabel",
        )
        title_label.pack(side=tk.LEFT)

        subtitle_label = ttk.Label(
            title_frame,
            text="噪音实时反馈系统",
            font=("Microsoft YaHei UI", 10),
            foreground="#6b7280",
        )
        subtitle_label.pack(side=tk.LEFT, padx=(10, 0), pady=4)

    def _build_device_section(self, parent):
        section = ttk.LabelFrame(parent, text=" 音频设备 ", padding=10, style="Section.TLabelframe")
        section.pack(fill=tk.X, pady=(0, 10))

        input_frame = ttk.Frame(section)
        input_frame.pack(fill=tk.X, pady=(0, 8))

        ttk.Label(input_frame, text="输入设备:", width=10, anchor=tk.W).pack(side=tk.LEFT)
        self.input_device_var = tk.StringVar()
        self.input_device_combo = ttk.Combobox(
            input_frame,
            textvariable=self.input_device_var,
            state="readonly",
            width=40,
        )
        self.input_device_combo.pack(side=tk.LEFT, padx=(5, 0), fill=tk.X, expand=True)
        self.input_device_combo.bind("<<ComboboxSelected>>", self._on_input_device_change)

        output_frame = ttk.Frame(section)
        output_frame.pack(fill=tk.X)

        ttk.Label(output_frame, text="输出设备:", width=10, anchor=tk.W).pack(side=tk.LEFT)
        self.output_device_var = tk.StringVar()
        self.output_device_combo = ttk.Combobox(
            output_frame,
            textvariable=self.output_device_var,
            state="readonly",
            width=40,
        )
        self.output_device_combo.pack(side=tk.LEFT, padx=(5, 0), fill=tk.X, expand=True)
        self.output_device_combo.bind("<<ComboboxSelected>>", self._on_output_device_change)

    def _build_threshold_section(self, parent):
        section = ttk.LabelFrame(parent, text=" 检测参数 ", padding=10, style="Section.TLabelframe")
        section.pack(fill=tk.X, pady=(0, 10))

        low_frame = ttk.Frame(section)
        low_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(low_frame, text="低频阈值:", width=10, anchor=tk.W).pack(side=tk.LEFT)
        self.low_threshold_var = tk.DoubleVar(value=self.config.detection.low_freq.energy_threshold)
        self.low_threshold_slider = ttk.Scale(
            low_frame,
            from_=1.0,
            to=8.0,
            variable=self.low_threshold_var,
            orient=tk.HORIZONTAL,
            command=self._on_low_threshold_change,
        )
        self.low_threshold_slider.pack(side=tk.LEFT, padx=(5, 5), fill=tk.X, expand=True)

        self.low_threshold_label = ttk.Label(
            low_frame,
            text=f"{self.low_threshold_var.get():.1f}",
            width=5,
            anchor=tk.E,
            font=("Microsoft YaHei UI", 9, "bold"),
        )
        self.low_threshold_label.pack(side=tk.LEFT)

        high_frame = ttk.Frame(section)
        high_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(high_frame, text="高频阈值:", width=10, anchor=tk.W).pack(side=tk.LEFT)
        self.high_threshold_var = tk.DoubleVar(value=self.config.detection.high_freq.energy_threshold)
        self.high_threshold_slider = ttk.Scale(
            high_frame,
            from_=1.0,
            to=8.0,
            variable=self.high_threshold_var,
            orient=tk.HORIZONTAL,
            command=self._on_high_threshold_change,
        )
        self.high_threshold_slider.pack(side=tk.LEFT, padx=(5, 5), fill=tk.X, expand=True)

        self.high_threshold_label = ttk.Label(
            high_frame,
            text=f"{self.high_threshold_var.get():.1f}",
            width=5,
            anchor=tk.E,
            font=("Microsoft YaHei UI", 9, "bold"),
        )
        self.high_threshold_label.pack(side=tk.LEFT)

        delay_frame = ttk.Frame(section)
        delay_frame.pack(fill=tk.X)

        ttk.Label(delay_frame, text="警报延迟时间:", width=12, anchor=tk.W).pack(side=tk.LEFT)
        self.delay_var = tk.IntVar(value=self.config.feedback.delay)
        self.delay_slider = ttk.Scale(
            delay_frame,
            from_=0,
            to=5000,
            variable=self.delay_var,
            orient=tk.HORIZONTAL,
            command=self._on_delay_change,
        )
        self.delay_slider.pack(side=tk.LEFT, padx=(5, 5), fill=tk.X, expand=True)

        self.delay_label = ttk.Label(
            delay_frame,
            text=f"{self.delay_var.get()} ms",
            width=8,
            anchor=tk.E,
            font=("Microsoft YaHei UI", 9, "bold"),
        )
        self.delay_label.pack(side=tk.LEFT)

    def _build_control_section(self, parent):
        control_frame = ttk.Frame(parent)
        control_frame.pack(fill=tk.X, pady=(0, 10))

        self.control_btn = ttk.Button(
            control_frame,
            text="开始监听",
            command=self._toggle_monitoring,
            style="Action.TButton",
            width=15,
        )
        self.control_btn.pack(side=tk.LEFT)

        self.status_var = tk.StringVar(value="已停止")
        self.status_label = ttk.Label(
            control_frame,
            textvariable=self.status_var,
            style="Stopped.TLabel",
        )
        self.status_label.pack(side=tk.LEFT, padx=(15, 0))

        self.progress_label = ttk.Label(
            control_frame,
            text="",
            font=("Microsoft YaHei UI", 9),
            foreground="#6b7280",
        )
        self.progress_label.pack(side=tk.LEFT, padx=(15, 0))

    def _build_log_section(self, parent):
        self.log_collapsible = CollapsibleFrame(parent, "事件日志")
        self.log_collapsible.pack(fill=tk.BOTH, expand=True)

        content = self.log_collapsible.content()

        log_header_frame = ttk.Frame(content)
        log_header_frame.pack(fill=tk.X, pady=(0, 5))

        self.log_count_label = ttk.Label(
            log_header_frame,
            text="今日事件: 0",
            font=("Microsoft YaHei UI", 9),
            foreground="#6b7280",
        )
        self.log_count_label.pack(side=tk.LEFT)

        clear_btn = ttk.Button(
            log_header_frame,
            text="清空",
            command=self._clear_log,
            width=8,
        )
        clear_btn.pack(side=tk.RIGHT)

        columns = ("time", "type", "intensity", "confidence")
        self.log_tree = ttk.Treeview(
            content,
            columns=columns,
            show="headings",
            height=8,
        )

        self.log_tree.heading("time", text="时间")
        self.log_tree.heading("type", text="类型")
        self.log_tree.heading("intensity", text="强度")
        self.log_tree.heading("confidence", text="置信度")

        self.log_tree.column("time", width=140, minwidth=100)
        self.log_tree.column("type", width=120, minwidth=80)
        self.log_tree.column("intensity", width=80, minwidth=60)
        self.log_tree.column("confidence", width=80, minwidth=60)

        scrollbar = ttk.Scrollbar(content, orient=tk.VERTICAL, command=self.log_tree.yview)
        self.log_tree.configure(yscrollcommand=scrollbar.set)

        self.log_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def _build_status_bar(self, parent):
        status_bar = ttk.Frame(parent)
        status_bar.pack(fill=tk.X, pady=(10, 0))

        ttk.Separator(status_bar, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=(0, 5))

        self.bar_status = ttk.Label(
            status_bar,
            text="就绪",
            font=("Microsoft YaHei UI", 8),
            foreground="#6b7280",
        )
        self.bar_status.pack(side=tk.LEFT)

    def _load_devices(self):
        try:
            devices = AudioCapture.list_devices()
            input_devices = []
            output_devices = []

            for i, dev in enumerate(devices):
                dev_str = f"[{i}] {dev['name']}"
                if dev['max_input_channels'] > 0:
                    input_devices.append(dev_str)
                if dev['max_output_channels'] > 0:
                    output_devices.append(dev_str)

            self.input_device_combo["values"] = input_devices
            self.output_device_combo["values"] = output_devices

            if input_devices:
                default_input = self.config.input_device_index
                if default_input is not None and default_input < len(input_devices):
                    self.input_device_var.set(input_devices[default_input])
                else:
                    self.input_device_var.set(input_devices[0])

            if output_devices:
                default_output = self.config.feedback.output_device_index
                if default_output is not None and default_output < len(output_devices):
                    self.output_device_var.set(output_devices[default_output])
                else:
                    self.output_device_var.set(output_devices[0])

        except Exception as e:
            logger.error(f"Failed to load audio devices: {e}")
            messagebox.showerror("设备错误", f"无法加载音频设备:\n{e}")

    def _parse_device_index(self, device_str: str) -> Optional[int]:
        if not device_str:
            return None
        try:
            return int(device_str.split("]")[0].replace("[", ""))
        except (ValueError, IndexError):
            return None

    def _on_input_device_change(self, event=None):
        if self._running:
            messagebox.showwarning("警告", "请先停止监听再切换设备")
            self._restore_input_device_selection()
            return
        device_idx = self._parse_device_index(self.input_device_var.get())
        self.config.input_device_index = device_idx
        self._set_bar_status(f"输入设备已切换: {self.input_device_var.get()}")

    def _on_output_device_change(self, event=None):
        if self._running:
            messagebox.showwarning("警告", "请先停止监听再切换设备")
            self._restore_output_device_selection()
            return
        device_idx = self._parse_device_index(self.output_device_var.get())
        self.config.feedback.output_device_index = device_idx
        self._set_bar_status(f"输出设备已切换: {self.output_device_var.get()}")

    def _restore_input_device_selection(self):
        idx = self.config.input_device_index
        devices = self.input_device_combo["values"]
        if idx is not None and idx < len(devices):
            self.input_device_var.set(devices[idx])
        elif devices:
            self.input_device_var.set(devices[0])

    def _restore_output_device_selection(self):
        idx = self.config.feedback.output_device_index
        devices = self.output_device_combo["values"]
        if idx is not None and idx < len(devices):
            self.output_device_var.set(devices[idx])
        elif devices:
            self.output_device_var.set(devices[0])

    def _on_low_threshold_change(self, value=None):
        val = self.low_threshold_var.get()
        self.low_threshold_label.config(text=f"{val:.1f}")
        if self.detector:
            self.detector.low_detector.energy_threshold = val
        self.config.detection.low_freq.energy_threshold = val
        self._set_bar_status(f"低频阈值已更新: {val:.1f}")

    def _on_high_threshold_change(self, value=None):
        val = self.high_threshold_var.get()
        self.high_threshold_label.config(text=f"{val:.1f}")
        if self.detector:
            self.detector.high_detector.energy_threshold = val
        self.config.detection.high_freq.energy_threshold = val
        self._set_bar_status(f"高频阈值已更新: {val:.1f}")

    def _on_delay_change(self, value=None):
        val = int(self.delay_var.get())
        self.delay_label.config(text=f"{val} ms")
        self.config.feedback.delay = val
        self._set_bar_status(f"警报延迟时间已更新: {val} ms")

    def _toggle_monitoring(self):
        if self._running:
            self._stop_monitoring()
        else:
            self._start_monitoring()

    def _start_monitoring(self):
        try:
            input_idx = self._parse_device_index(self.input_device_var.get())
            output_idx = self._parse_device_index(self.output_device_var.get())

            self.capture = AudioCapture(
                sample_rate=self.config.sample_rate,
                chunk_size=self.config.chunk_size,
                channels=self.config.channels,
                device_index=input_idx,
            )

            self.detector = NoiseDetector(
                sample_rate=self.config.sample_rate,
                low_freq_config={
                    "enabled": self.config.detection.low_freq.enabled,
                    "freq_range": self.config.detection.low_freq.freq_range,
                    "energy_threshold": self.config.detection.low_freq.energy_threshold,
                    "spectral_centroid_max": self.config.detection.low_freq.spectral_centroid_max,
                },
                high_freq_config={
                    "enabled": self.config.detection.high_freq.enabled,
                    "freq_range": self.config.detection.high_freq.freq_range,
                    "energy_threshold": self.config.detection.high_freq.energy_threshold,
                    "zero_crossing_min": self.config.detection.high_freq.zero_crossing_min,
                },
                cooldown_seconds=self.config.detection.cooldown_seconds,
            )

            sounds = {
                "mild": self.config.feedback.sounds.mild,
                "medium": self.config.feedback.sounds.medium,
                "strong": self.config.feedback.sounds.strong,
            }
            self.player = FeedbackPlayer(
                sounds=sounds,
                volume=self.config.feedback.volume,
            )

            self.event_logger = EventLogger(log_dir=str(get_logs_dir()))

            self._stop_event.clear()
            self._monitor_thread = threading.Thread(
                target=self._monitor_loop,
                daemon=True,
                name="NoiseMonitor",
            )
            self._monitor_thread.start()

            self._running = True
            self.control_btn.config(text="停止监听")
            self.status_var.set("监听中")
            self.status_label.config(style="Running.TLabel")
            self._set_bar_status("正在学习背景噪声...")
            self._set_device_state(tk.DISABLED)
            self._set_bar_status("监听已启动")

            logger.info("Monitoring started via GUI")

        except Exception as e:
            logger.error(f"Failed to start monitoring: {e}")
            messagebox.showerror("启动失败", f"无法启动监听:\n{e}")
            self._cleanup_resources()

    def _stop_monitoring(self):
        self._running = False
        self._stop_event.set()

        if self._monitor_thread and self._monitor_thread.is_alive():
            self._monitor_thread.join(timeout=3.0)

        self._cleanup_resources()

        self.control_btn.config(text="开始监听")
        self.status_var.set("已停止")
        self.status_label.config(style="Stopped.TLabel")
        self.progress_label.config(text="")
        self._set_device_state(tk.NORMAL)
        self._set_bar_status("监听已停止")

        logger.info("Monitoring stopped via GUI")

    def _cleanup_resources(self):
        try:
            if self.capture:
                self.capture.stop()
        except Exception as e:
            logger.error(f"Error stopping capture: {e}")

        try:
            if self.player:
                self.player.quit()
        except Exception as e:
            logger.error(f"Error stopping player: {e}")

    def _monitor_loop(self):
        try:
            self.capture.start()

            self.root.after(0, lambda: self._set_bar_status("正在学习背景噪声..."))

            learn_start = datetime.now()
            learn_duration = self.config.detection.background_learning_seconds
            chunks_collected = 0

            while not self._stop_event.is_set():
                elapsed = (datetime.now() - learn_start).total_seconds()
                if elapsed < learn_duration:
                    remaining = int(learn_duration - elapsed)
                    self.root.after(0, lambda r=remaining: self.progress_label.config(
                        text=f"背景学习: {r}s"
                    ))
                    chunk = self.capture.read_chunk(timeout=0.5)
                    if chunk is not None:
                        self.detector.learn_background(chunk.flatten())
                        chunks_collected += 1
                else:
                    self.root.after(0, lambda: self.progress_label.config(text=""))
                    self.root.after(0, lambda: self._set_bar_status("监听中"))
                    break

            while not self._stop_event.is_set():
                chunk = self.capture.read_chunk(timeout=1.0)
                if chunk is None:
                    continue

                audio_data = chunk.flatten()
                event = self.detector.analyze(audio_data)
                if event is not None:
                    self.event_logger.log_event(event)
                    if self.config.feedback.enabled:
                        delay_ms = self.config.feedback.delay
                        if delay_ms > 0:
                            self.root.after(delay_ms, lambda i=event.intensity.value: self.player.play(i))
                        else:
                            self.player.play(event.intensity.value)
                    self.root.after(0, lambda e=event: self._add_log_entry(e))

        except Exception as e:
            logger.error(f"Monitor loop error: {e}")
            self.root.after(0, lambda: messagebox.showerror("监听错误", f"监听过程中发生错误:\n{e}"))
            self.root.after(0, self._stop_monitoring)

    def _add_log_entry(self, event):
        timestamp = datetime.fromtimestamp(event.timestamp).strftime("%Y-%m-%d %H:%M:%S")
        type_map = {
            "low_freq_impact": "低频冲击",
            "high_freq_friction": "高频摩擦",
        }
        intensity_map = {
            "mild": "轻度",
            "medium": "中度",
            "strong": "重度",
        }

        noise_type = type_map.get(event.noise_type.value, event.noise_type.value)
        intensity = intensity_map.get(event.intensity.value, event.intensity.value)

        self.log_tree.insert(
            "",
            tk.END,
            values=(timestamp, noise_type, intensity, f"{event.confidence:.2f}"),
        )

        events = self.event_logger.get_today_events() if self.event_logger else []
        self.log_count_label.config(text=f"今日事件: {len(events)}")

        self.log_tree.see(self.log_tree.get_children()[-1])

    def _clear_log(self):
        for item in self.log_tree.get_children():
            self.log_tree.delete(item)
        self.log_count_label.config(text="今日事件: 0")
        self._set_bar_status("日志已清空")

    def _set_device_state(self, state):
        self.input_device_combo.config(state="readonly" if state == tk.NORMAL else tk.DISABLED)
        self.output_device_combo.config(state="readonly" if state == tk.NORMAL else tk.DISABLED)

    def _set_bar_status(self, text: str):
        self.bar_status.config(text=text)

    def _on_closing(self):
        if self._running:
            if messagebox.askokcancel("退出确认", "监听正在运行，确定要退出吗？"):
                self._stop_monitoring()
                self.root.destroy()
        else:
            self.root.destroy()

    def run(self):
        self.root.mainloop()
