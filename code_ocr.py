#!/usr/bin/env python3
"""Batch pipeline for PDF code OCR produced by FastStone Capture."""

from __future__ import annotations

import argparse
import ctypes
import difflib
import html
from html.parser import HTMLParser
import json
import os
import re
import shutil
import ssl
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


ROOT = Path.cwd()
DEFAULT_CONFIG = {
    "pdf_input_dir": "data/pdf",
    "reference_dir": "data/reference",
    "output_dir": "output",
    "source_insight_path": "",
    "source_insight_window_title": "Source Insight",
    "source_insight_maximize": True,
    "source_insight_document_maximize": True,
    "source_insight_document_maximize_hotkey": "^{F10}",
    "source_insight_document_maximize_delay_seconds": 1.0,
    "faststone_path": "",
    "faststone_window_title": "",
    "faststone_editor_window_titles": ["FastStone Editor", "FastStone Capture"],
    "faststone_scrolling_hotkey": "^%{PRTSC}",
    "faststone_region_hotkey": "^%r",
    "capture_mode": "hotkey",
    "capture_region": {
        "left": 100,
        "top": 150,
        "right": 1100,
        "bottom": 950
    },
    "capture_region_ready_delay_seconds": 1.0,
    "capture_region_drag_delay_seconds": 0.3,
    "capture_region_drag_duration_seconds": 0.8,
    "capture_region_drag_steps": 24,
    "capture_region_drag_modifiers": ["ctrl"],
    "capture_region_post_click": True,
    "capture_region_post_click_point": "center",
    "capture_region_post_click_delay_seconds": 0.3,
    "capture_region_return_cursor": False,
    "capture_focus_delay_seconds": 2,
    "capture_wait_timeout_seconds": 300,
    "capture_pdf_stable_seconds": 2,
    "capture_pdf_output_search_dirs": ["data/pdf"],
    "capture_force_source_pdf_name": True,
    "capture_output_mode": "pdf",
    "capture_image_dir": "data/screenshots",
    "capture_image_extensions": [".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff"],
    "capture_image_stable_seconds": 2,
    "faststone_pdf_convert_hotkey": "^g",
    "faststone_pdf_convert_delay_seconds": 1.0,
    "faststone_pdf_convert_auto_save": True,
    "faststone_pdf_convert_steps": ["{ENTER}", "{PASTE_PDF_PATH}", "{ENTER}", "{ENTER}"],
    "faststone_pdf_convert_step_delay_seconds": 1.0,
    "faststone_pdf_convert_wait_timeout_seconds": 300,
    "faststone_pdf_save_hotkey": "%s",
    "faststone_pdf_save_delay_seconds": 1.0,
    "faststone_pdf_save_wait_for_editor_seconds": 30,
    "faststone_pdf_save_steps": ["{PASTE_PDF_PATH}", "{ENTER}", "{ENTER}"],
    "faststone_pdf_save_step_delay_seconds": 1.0,
    "faststone_pdf_save_wait_timeout_seconds": 300,
    "faststone_current_pdf_hotkey": "^g",
    "faststone_current_pdf_delay_seconds": 1.0,
    "faststone_current_pdf_wait_for_editor_seconds": 30,
    "faststone_current_pdf_steps": ["{PASTE_PDF_PATH}", "{ENTER}", "{ENTER}"],
    "faststone_current_pdf_step_delay_seconds": 1.0,
    "faststone_current_pdf_wait_timeout_seconds": 300,
    "gui_auto_close_enabled": True,
    "gui_auto_close_interval_seconds": 1.0,
    "faststone_pdf_complete_window_titles": ["FastStone Capture", "FastStone Editor"],
    "faststone_pdf_complete_keys": ["{ENTER}"],
    "faststone_pdf_complete_delay_seconds": 0.5,
    "bc_script_dialog_window_titles": ["Beyond Compare"],
    "bc_script_dialog_keys": ["{ENTER}"],
    "bc_script_dialog_initial_delay_seconds": 2.0,
    "bc_script_dialog_repeat_seconds": 5.0,
    "llamaparse_api_key": "",
    "llamaparse_api_key_env": "LLAMA_CLOUD_API_KEY",
    "llamaparse_api_mode": "v2",
    "llamaparse_file_upload_url": "https://api.cloud.llamaindex.ai/api/v1/beta/files",
    "llamaparse_parse_url": "https://api.cloud.llamaindex.ai/api/v2/parse",
    "llamaparse_parse_job_url_template": "https://api.cloud.llamaindex.ai/api/v2/parse/{job_id}?expand=markdown",
    "llamaparse_tier": "cost_effective",
    "llamaparse_version": "latest",
    "llamaparse_upload_url": "https://api.cloud.llamaindex.ai/api/v1/parsing/upload",
    "llamaparse_result_url_template": "https://api.cloud.llamaindex.ai/api/v1/parsing/job/{job_id}/result/markdown",
    "llamaparse_result_type": "markdown",
    "llamaparse_poll_interval_seconds": 2,
    "llamaparse_timeout_seconds": 300,
    "beyond_compare_path": "C:/Program Files/Beyond Compare 5/BCompare.exe",
    "default_extension": ".md",
    "final_output_extension": ".md",
    "fixed_output_encoding": "gb18030",
    "reference_extensions": [".c", ".cpp", ".h", ".hpp", ".py", ".java", ".js", ".ts", ".cs", ".md", ".txt"],
    "batch_source_extensions": [".c", ".cpp", ".h", ".hpp"],
    "reference_encoding": "auto",
    "bc_script_dir": "output/bc_scripts",
    "bc_report_dir": "output/bc_reports",
    "bc_stage_dir": "",
    "bc_html_align_source_side": "left",
    "auto_fix_enabled": True,
    "repair_mojibake_comments": True,
    "code_identifier_dictionary": [
        "GPIO_InitTypeDef",
        "GPIO_InitStructure",
        "GPIO_Pin",
        "GPIO_Mode",
        "GPIO_OType",
        "GPIO_Speed",
        "GPIO_PuPd",
        "GPIO_Mode_OUT",
        "GPIO_Mode_IN",
        "GPIO_OType_PP",
        "GPIO_Speed_100MHz",
        "GPIO_Speed_50MHz",
        "GPIO_Speed_2MHz",
        "GPIO_PuPd_NOPULL",
        "GPIO_PuPd_DOWN",
        "GPIO_ReadInputDataBit",
        "GPIO_Init",
        "RCC_AHB1PeriphClockCmd",
        "RCC_AHB1Periph_GPIOA",
        "RCC_AHB1Periph_GPIOB",
        "RCC_AHB1Periph_GPIOC",
        "IWDG_Init",
        "IWDG_Feed",
        "IWDG_WriteAccessCmd",
        "IWDG_WriteAccess_Enable",
        "IWDG_SetPrescaler",
        "IWDG_SetReload",
        "IWDG_ReloadCounter",
        "IWDG_Enable",
        "SysTick_Config",
        "SystemCoreClock",
        "SysTick_LedCfg",
        "LEDALARM_ON",
        "LEDALARM_OFF",
        "LEDRUN_ON",
        "LEDRUN_OFF",
        "ALARM_EEPROM_ERR"
    ],
    "strip_line_numbers": True,
    "normalize_full_width_punctuation": True,
}


class HttpJsonError(RuntimeError):
    def __init__(self, status: int, reason: str, detail: str) -> None:
        super().__init__(f"HTTP Error {status}: {reason}; {detail}")
        self.status = status
        self.reason = reason
        self.detail = detail


@dataclass
class Task:
    id: str
    logical_path: str
    pdf_path: str
    status: str = "pending"
    raw_text_path: str | None = None
    clean_text_path: str | None = None
    fixed_text_path: str | None = None
    report_path: str | None = None
    error: str | None = None
    updated_at: float | None = None


def load_config(config_path: Path) -> dict[str, Any]:
    if not config_path.exists():
        return dict(DEFAULT_CONFIG)
    with config_path.open("r", encoding="utf-8") as fh:
        loaded = json.load(fh)
    config = dict(DEFAULT_CONFIG)
    config.update(loaded)
    return config


def save_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)
        fh.write("\n")


def load_tasks(config: dict[str, Any]) -> list[Task]:
    manifest = manifest_path(config)
    if not manifest.exists():
        return []
    with manifest.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    return [Task(**item) for item in data]


def save_tasks(config: dict[str, Any], tasks: list[Task]) -> None:
    for task in tasks:
        task.updated_at = time.time()
    save_json(manifest_path(config), [asdict(task) for task in tasks])


def output_dir(config: dict[str, Any]) -> Path:
    return (ROOT / config["output_dir"]).resolve()


def manifest_path(config: dict[str, Any]) -> Path:
    return output_dir(config) / "manifest" / "tasks.json"


def normalize_id(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_.-]+", "_", value).strip("._")
    return cleaned or "task"


def guess_logical_path(pdf: Path, default_extension: str) -> str:
    stem = pdf.stem
    parts = stem.split("__")
    if len(parts) > 1:
        filename = parts[-1]
        if "_" in filename and "." not in filename:
            base, ext = filename.rsplit("_", 1)
            filename = f"{base}.{ext}"
        return str(Path(*parts[:-1], filename)).replace("\\", "/")
    if "." in stem:
        return stem
    if "_" in stem:
        base, ext = stem.rsplit("_", 1)
        if 1 <= len(ext) <= 5:
            return f"{base}.{ext}"
    return stem + default_extension


def with_output_extension(logical_path: str, config: dict[str, Any]) -> Path:
    extension = str(config.get("final_output_extension", "")).strip()
    path = Path(logical_path)
    if not extension:
        return path
    if not extension.startswith("."):
        extension = "." + extension
    return path.with_suffix(extension)


def resolve_workspace_path(value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else (ROOT / path)


def pdf_output_name(source_file: Path, requested_name: str | None = None) -> str:
    if requested_name:
        name = requested_name
    else:
        name = source_file.name
    if not name.lower().endswith(".pdf"):
        name += ".pdf"
    return name


def batch_pdf_output_name(source_file: Path, source_root: Path) -> str:
    try:
        relative = source_file.resolve().relative_to(source_root.resolve())
    except ValueError:
        return pdf_output_name(source_file)
    encoded = "__".join(relative.parts)
    return f"{encoded}.pdf"


def batch_source_files(source_root: Path, config: dict[str, Any], recursive: bool, extensions_arg: str | None = None) -> list[Path]:
    if source_root.is_file():
        return [source_root.resolve()]
    if not source_root.exists():
        raise FileNotFoundError(f"Source directory does not exist: {source_root}")
    raw_extensions = (
        [item.strip() for item in extensions_arg.split(",") if item.strip()]
        if extensions_arg
        else list(config.get("batch_source_extensions") or config.get("reference_extensions", []))
    )
    extensions = set(normalize_extensions(raw_extensions))
    iterator = source_root.rglob("*") if recursive else source_root.glob("*")
    files = [
        path.resolve()
        for path in iterator
        if path.is_file() and path.suffix.lower() in extensions
    ]
    return sorted(files, key=lambda path: str(path).lower())


def launch_source_file(config: dict[str, Any], source_file: Path) -> None:
    source_insight = str(config.get("source_insight_path", "")).strip()
    if source_insight:
        exe = resolve_workspace_path(source_insight)
        if not exe.exists():
            raise FileNotFoundError(f"Source Insight executable does not exist: {exe}")
        subprocess.Popen([str(exe), str(source_file)])
    elif os.name == "nt":
        os.startfile(str(source_file))  # type: ignore[attr-defined]
    else:
        subprocess.Popen(["xdg-open", str(source_file)])


def maximize_window_by_title(title: str, timeout_seconds: float = 10.0) -> bool:
    if os.name != "nt":
        return False
    deadline = time.time() + timeout_seconds
    user32 = ctypes.windll.user32
    hwnd_result = ctypes.c_void_p()

    enum_windows_proc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)

    def callback(hwnd: int, _lparam: int) -> bool:
        if not user32.IsWindowVisible(hwnd):
            return True
        length = user32.GetWindowTextLengthW(hwnd)
        if length <= 0:
            return True
        buffer = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, buffer, length + 1)
        if title.lower() in buffer.value.lower():
            hwnd_result.value = hwnd
            return False
        return True

    while time.time() < deadline:
        hwnd_result.value = None
        user32.EnumWindows(enum_windows_proc(callback), 0)
        if hwnd_result.value:
            user32.ShowWindow(hwnd_result.value, 3)  # SW_MAXIMIZE
            user32.SetForegroundWindow(hwnd_result.value)
            return True
        time.sleep(0.3)
    return False


def visible_window_titles() -> list[str]:
    if os.name != "nt":
        return []
    user32 = ctypes.windll.user32
    titles: list[str] = []
    enum_windows_proc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)

    def callback(hwnd: int, _lparam: int) -> bool:
        if not user32.IsWindowVisible(hwnd):
            return True
        length = user32.GetWindowTextLengthW(hwnd)
        if length <= 0:
            return True
        buffer = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, buffer, length + 1)
        title = buffer.value.strip()
        if title:
            titles.append(title)
        return True

    user32.EnumWindows(enum_windows_proc(callback), 0)
    return titles


def foreground_window_title() -> str:
    if os.name != "nt":
        return ""
    user32 = ctypes.windll.user32
    hwnd = user32.GetForegroundWindow()
    if not hwnd:
        return ""
    length = user32.GetWindowTextLengthW(hwnd)
    if length <= 0:
        return ""
    buffer = ctypes.create_unicode_buffer(length + 1)
    user32.GetWindowTextW(hwnd, buffer, length + 1)
    return buffer.value.strip()


def normalize_title_candidates(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value] if value.strip() else []
    if isinstance(value, (list, tuple)):
        return [str(item).strip() for item in value if str(item).strip()]
    return []


def wait_for_window_title(candidates: list[str], timeout_seconds: float, activate: bool = True) -> str | None:
    if not candidates:
        return None
    deadline = time.time() + timeout_seconds
    last_notice = 0.0
    lowered = [candidate.lower() for candidate in candidates]
    while time.time() < deadline:
        titles = visible_window_titles()
        for title in titles:
            if any(candidate in title.lower() for candidate in lowered):
                if activate:
                    activate_window(title)
                    time.sleep(0.3)
                return title
        if time.time() - last_notice >= 5:
            print(f"Waiting for window title containing one of {candidates}; foreground: {foreground_window_title()}")
            last_notice = time.time()
        time.sleep(0.5)
    return None


def send_keys_to_matching_window(title_candidates: list[str], keys: list[str], delay_seconds: float = 0.2) -> bool:
    if not title_candidates or not keys or os.name != "nt":
        return False
    lowered = [candidate.lower() for candidate in title_candidates if candidate]
    if not lowered:
        return False
    for title in visible_window_titles():
        if not any(candidate in title.lower() for candidate in lowered):
            continue
        activate_window(title)
        time.sleep(max(delay_seconds, 0.05))
        print(f"Auto-closing GUI dialog/window: {title}")
        for key in keys:
            send_windows_hotkey(str(key))
            time.sleep(max(delay_seconds, 0.05))
        return True
    return False


def auto_close_configured_windows(config: dict[str, Any], title_key: str, keys_key: str, delay_key: str | None = None) -> bool:
    if not config.get("gui_auto_close_enabled", True):
        return False
    titles = normalize_title_candidates(config.get(title_key, []))
    keys = [str(key).strip() for key in config.get(keys_key, []) if str(key).strip()]
    delay = float(config.get(delay_key, 0.2)) if delay_key else 0.2
    return send_keys_to_matching_window(titles, keys, delay)


def launch_faststone_if_configured(config: dict[str, Any]) -> None:
    faststone = str(config.get("faststone_path", "")).strip()
    if not faststone:
        return
    exe = resolve_workspace_path(faststone)
    if not exe.exists():
        raise FileNotFoundError(f"FastStone executable does not exist: {exe}")
    subprocess.Popen([str(exe)])


def send_windows_hotkey(hotkey: str, window_title: str | None = None) -> None:
    if os.name != "nt":
        raise RuntimeError("GUI hotkey automation is only implemented for Windows.")
    if window_title:
        activate_window(window_title)
        time.sleep(0.3)
    if send_native_hotkey(hotkey):
        return
    escaped_hotkey = hotkey.replace("'", "''")
    script = [
        "$ws = New-Object -ComObject WScript.Shell",
    ]
    if window_title:
        escaped_title = window_title.replace("'", "''")
        script.append(f"$null = $ws.AppActivate('{escaped_title}')")
        script.append("Start-Sleep -Milliseconds 300")
    script.append(f"$ws.SendKeys('{escaped_hotkey}')")
    subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", "; ".join(script)],
        check=True,
    )


def set_windows_clipboard_text(text: str) -> None:
    if os.name != "nt":
        raise RuntimeError("Clipboard automation is only implemented for Windows.")
    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32
    user32.OpenClipboard.argtypes = [ctypes.c_void_p]
    user32.OpenClipboard.restype = ctypes.c_bool
    user32.EmptyClipboard.restype = ctypes.c_bool
    user32.SetClipboardData.argtypes = [ctypes.c_uint, ctypes.c_void_p]
    user32.SetClipboardData.restype = ctypes.c_void_p
    user32.CloseClipboard.restype = ctypes.c_bool
    kernel32.GlobalAlloc.argtypes = [ctypes.c_uint, ctypes.c_size_t]
    kernel32.GlobalAlloc.restype = ctypes.c_void_p
    kernel32.GlobalLock.argtypes = [ctypes.c_void_p]
    kernel32.GlobalLock.restype = ctypes.c_void_p
    kernel32.GlobalUnlock.argtypes = [ctypes.c_void_p]
    kernel32.GlobalUnlock.restype = ctypes.c_bool
    kernel32.GlobalFree.argtypes = [ctypes.c_void_p]
    kernel32.GlobalFree.restype = ctypes.c_void_p
    if not user32.OpenClipboard(None):
        raise RuntimeError("Could not open Windows clipboard.")
    try:
        user32.EmptyClipboard()
        data = text.encode("utf-16-le") + b"\x00\x00"
        handle = kernel32.GlobalAlloc(0x0042, len(data))
        if not handle:
            raise RuntimeError("Could not allocate clipboard memory.")
        locked = kernel32.GlobalLock(handle)
        if not locked:
            kernel32.GlobalFree(handle)
            raise RuntimeError("Could not lock clipboard memory.")
        ctypes.memmove(locked, data, len(data))
        kernel32.GlobalUnlock(handle)
        if not user32.SetClipboardData(13, handle):
            kernel32.GlobalFree(handle)
            raise RuntimeError("Could not set clipboard text.")
        handle = None
    finally:
        user32.CloseClipboard()


def activate_window(window_title: str) -> None:
    escaped_title = window_title.replace("'", "''")
    script = (
        "$ws = New-Object -ComObject WScript.Shell; "
        f"$null = $ws.AppActivate('{escaped_title}')"
    )
    subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", script],
        check=False,
    )


def send_native_hotkey(hotkey: str) -> bool:
    parsed = parse_sendkeys_hotkey(hotkey)
    if not parsed:
        return False
    modifiers, key = parsed
    keybd_event = ctypes.windll.user32.keybd_event
    keyup = 0x0002
    for modifier in modifiers:
        keybd_event(modifier, 0, 0, 0)
        time.sleep(0.03)
    keybd_event(key, 0, 0, 0)
    time.sleep(0.08)
    keybd_event(key, 0, keyup, 0)
    for modifier in reversed(modifiers):
        time.sleep(0.03)
        keybd_event(modifier, 0, keyup, 0)
    return True


def parse_sendkeys_hotkey(hotkey: str) -> tuple[list[int], int] | None:
    value = hotkey.strip()
    modifiers: list[int] = []
    while value and value[0] in "^%+":
        marker = value[0]
        value = value[1:]
        if marker == "^":
            modifiers.append(0x11)  # VK_CONTROL
        elif marker == "%":
            modifiers.append(0x12)  # VK_MENU / Alt
        elif marker == "+":
            modifiers.append(0x10)  # VK_SHIFT
    token_map = {
        "{PRTSC}": 0x2C,
        "{PRINTSCREEN}": 0x2C,
        "{ENTER}": 0x0D,
        "{ESC}": 0x1B,
        "{TAB}": 0x09,
        "{SPACE}": 0x20,
    }
    for index in range(1, 13):
        token_map[f"{{F{index}}}"] = 0x70 + index - 1
    upper = value.upper()
    if upper in token_map:
        return modifiers, token_map[upper]
    if len(value) == 1 and value.isalnum():
        return modifiers, ord(value.upper())
    return None


def get_mouse_position() -> tuple[int, int]:
    if os.name != "nt":
        raise RuntimeError("Mouse position helper is only implemented for Windows.")

    class POINT(ctypes.Structure):
        _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]

    point = POINT()
    ctypes.windll.user32.GetCursorPos(ctypes.byref(point))
    return int(point.x), int(point.y)


def set_cursor_position(x: int, y: int) -> None:
    ctypes.windll.user32.SetCursorPos(int(x), int(y))


def mouse_event(flags: int, x: int = 0, y: int = 0, data: int = 0) -> None:
    ctypes.windll.user32.mouse_event(flags, int(x), int(y), int(data), 0)


def click_mouse(x: int, y: int, delay: float = 0.1) -> None:
    left_down = 0x0002
    left_up = 0x0004
    set_cursor_position(x, y)
    time.sleep(max(delay, 0.02))
    mouse_event(left_down)
    time.sleep(max(delay, 0.02))
    mouse_event(left_up)


def modifier_vk_codes(names: list[str] | tuple[str, ...] | str | None) -> list[int]:
    if not names:
        return []
    if isinstance(names, str):
        names = [names]
    mapping = {
        "ctrl": 0x11,
        "control": 0x11,
        "alt": 0x12,
        "shift": 0x10,
    }
    codes: list[int] = []
    for name in names:
        code = mapping.get(str(name).strip().lower())
        if code is not None:
            codes.append(code)
    return codes


def key_down(vk_code: int) -> None:
    ctypes.windll.user32.keybd_event(int(vk_code), 0, 0, 0)


def key_up(vk_code: int) -> None:
    ctypes.windll.user32.keybd_event(int(vk_code), 0, 0x0002, 0)


def drag_mouse_region(
    left: int,
    top: int,
    right: int,
    bottom: int,
    delay: float = 0.2,
    duration: float = 0.8,
    steps: int = 24,
    modifier_codes: list[int] | None = None,
) -> None:
    if os.name != "nt":
        raise RuntimeError("Mouse drag automation is only implemented for Windows.")
    left_down = 0x0002
    left_up = 0x0004
    original = get_mouse_position()
    modifier_codes = modifier_codes or []
    try:
        for code in modifier_codes:
            key_down(code)
            time.sleep(0.03)
        set_cursor_position(left, top)
        time.sleep(delay)
        mouse_event(left_down)
        time.sleep(max(delay, 0.05))
        steps = max(int(steps), 1)
        duration = max(float(duration), 0.05)
        sleep_per_step = duration / steps
        for index in range(1, steps + 1):
            x = round(left + (right - left) * index / steps)
            y = round(top + (bottom - top) * index / steps)
            set_cursor_position(x, y)
            time.sleep(sleep_per_step)
        set_cursor_position(right, bottom)
        time.sleep(max(delay, 0.05))
    finally:
        mouse_event(left_up)
        for code in reversed(modifier_codes):
            time.sleep(0.03)
            key_up(code)


def capture_region_from_config(config: dict[str, Any]) -> tuple[int, int, int, int]:
    region = config.get("capture_region") or {}
    try:
        left = int(region["left"])
        top = int(region["top"])
        right = int(region["right"])
        bottom = int(region["bottom"])
    except Exception as exc:
        raise ValueError("capture_region must include integer left/top/right/bottom") from exc
    if right <= left or bottom <= top:
        raise ValueError(f"Invalid capture_region: {region}")
    return left, top, right, bottom


def perform_configured_region_drag(config: dict[str, Any]) -> None:
    left, top, right, bottom = capture_region_from_config(config)
    delay = float(config.get("capture_region_drag_delay_seconds", 0.2))
    duration = float(config.get("capture_region_drag_duration_seconds", 0.8))
    steps = int(config.get("capture_region_drag_steps", 24))
    modifiers = modifier_vk_codes(config.get("capture_region_drag_modifiers", []))
    original = get_mouse_position()
    print(f"Dragging capture region: ({left}, {top}) -> ({right}, {bottom})")
    if modifiers:
        print(f"Holding drag modifier(s): {config.get('capture_region_drag_modifiers')}")
    drag_mouse_region(left, top, right, bottom, delay, duration, steps, modifiers)
    if config.get("capture_region_post_click", True):
        click_x, click_y = capture_region_post_click_point(left, top, right, bottom, config)
        click_delay = float(config.get("capture_region_post_click_delay_seconds", 0.3))
        print(f"Clicking inside selected region: ({click_x}, {click_y})")
        time.sleep(click_delay)
        click_mouse(click_x, click_y)
    if config.get("capture_region_return_cursor", False):
        set_cursor_position(*original)


def capture_region_post_click_point(
    left: int,
    top: int,
    right: int,
    bottom: int,
    config: dict[str, Any],
) -> tuple[int, int]:
    point = config.get("capture_region_post_click_point", "center")
    if isinstance(point, dict):
        return int(point.get("x", (left + right) // 2)), int(point.get("y", (top + bottom) // 2))
    return (left + right) // 2, (top + bottom) // 2


def normalize_extensions(extensions: list[str] | tuple[str, ...]) -> tuple[str, ...]:
    normalized = []
    for ext in extensions:
        value = str(ext).strip().lower()
        if not value:
            continue
        normalized.append(value if value.startswith(".") else f".{value}")
    return tuple(normalized)


def newest_file_after(directory: Path, extensions: list[str] | tuple[str, ...], since: float) -> Path | None:
    if not directory.exists():
        return None
    wanted = normalize_extensions(extensions)
    candidates = [
        path for path in directory.iterdir()
        if path.is_file() and path.suffix.lower() in wanted and path.stat().st_mtime >= since
    ]
    if not candidates:
        return None
    return max(candidates, key=lambda path: path.stat().st_mtime)


def newest_pdf_after(pdf_dir: Path, since: float) -> Path | None:
    return newest_file_after(pdf_dir, [".pdf"], since)


def wait_for_file_output(
    directory: Path,
    extensions: list[str] | tuple[str, ...],
    since: float,
    timeout: int,
    stable_seconds: int,
    label: str,
) -> Path:
    deadline = time.time() + timeout
    last_path: Path | None = None
    last_size = -1
    stable_since: float | None = None
    last_notice = 0.0
    print(f"Waiting for {label} output in: {directory}")
    while time.time() < deadline:
        found = newest_file_after(directory, extensions, since)
        if found:
            size = found.stat().st_size
            if found != last_path or time.time() - last_notice >= 5:
                print(f"Detected {label} candidate: {found.name} ({size} bytes)")
                last_notice = time.time()
            if found == last_path and size == last_size:
                if stable_since is None:
                    stable_since = time.time()
                if time.time() - stable_since >= stable_seconds:
                    return found
            else:
                last_path = found
                last_size = size
                stable_since = None
        elif time.time() - last_notice >= 5:
            remaining = int(deadline - time.time())
            print(f"Still waiting for {label}... {remaining}s remaining")
            last_notice = time.time()
        time.sleep(1)
    raise TimeoutError(f"No stable {label} output found in {directory} within {timeout} seconds")


def wait_for_pdf_output(pdf_dir: Path, since: float, timeout: int, stable_seconds: int) -> Path:
    return wait_for_file_output(pdf_dir, [".pdf"], since, timeout, stable_seconds, "PDF")


def pdf_search_dirs(config: dict[str, Any], pdf_dir: Path) -> list[Path]:
    dirs = [pdf_dir.resolve()]
    for item in config.get("capture_pdf_output_search_dirs", []):
        path = resolve_workspace_path(str(item)).resolve()
        if path not in dirs:
            dirs.append(path)
    return dirs


def newest_file_after_in_dirs(directories: list[Path], extensions: list[str] | tuple[str, ...], since: float) -> Path | None:
    candidates = [found for directory in directories if (found := newest_file_after(directory, extensions, since))]
    if not candidates:
        return None
    return max(candidates, key=lambda path: path.stat().st_mtime)


def wait_for_pdf_output_in_dirs(
    directories: list[Path],
    since: float,
    timeout: int,
    stable_seconds: int,
) -> Path:
    deadline = time.time() + timeout
    last_path: Path | None = None
    last_size = -1
    stable_since: float | None = None
    last_notice = 0.0
    printable_dirs = ", ".join(str(path) for path in directories)
    print(f"Waiting for PDF output in: {printable_dirs}")
    while time.time() < deadline:
        found = newest_file_after_in_dirs(directories, [".pdf"], since)
        if found:
            size = found.stat().st_size
            if found != last_path or time.time() - last_notice >= 5:
                print(f"Detected PDF candidate: {found} ({size} bytes)")
                last_notice = time.time()
            if found == last_path and size == last_size:
                if stable_since is None:
                    stable_since = time.time()
                if time.time() - stable_since >= stable_seconds:
                    return found
            else:
                last_path = found
                last_size = size
                stable_since = None
        elif time.time() - last_notice >= 5:
            remaining = int(deadline - time.time())
            print(f"Still waiting for PDF... {remaining}s remaining")
            last_notice = time.time()
        time.sleep(1)
    raise TimeoutError(f"No stable PDF output found in {printable_dirs} within {timeout} seconds")


def move_pdf_if_requested(pdf_path: Path, pdf_dir: Path, target_name: str | None) -> Path:
    if not target_name:
        return pdf_path
    target = pdf_dir / target_name
    if target.resolve() == pdf_path.resolve():
        return pdf_path
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        target.unlink()
    shutil.move(str(pdf_path), str(target))
    return target


def normalize_capture_pdf(pdf_path: Path, target_pdf: Path, force: bool = True) -> Path:
    target_pdf.parent.mkdir(parents=True, exist_ok=True)
    if not force:
        return pdf_path
    if pdf_path.resolve() == target_pdf.resolve():
        print(f"PDF already normalized: {target_pdf}")
        return target_pdf
    if target_pdf.exists():
        target_pdf.unlink()
    print(f"Normalizing PDF name/path: {pdf_path} -> {target_pdf}")
    shutil.move(str(pdf_path), str(target_pdf))
    return target_pdf


def wait_for_faststone_pdf_conversion(
    config: dict[str, Any],
    pdf_dir: Path,
    target_pdf: Path,
    since: float,
    timeout: int,
    stable_seconds: int,
    convert_hotkey: str | None,
) -> Path:
    hotkey = (convert_hotkey or str(config.get("faststone_pdf_convert_hotkey", ""))).strip()
    if hotkey:
        delay = float(config.get("faststone_pdf_convert_delay_seconds", 1.0))
        time.sleep(delay)
        print(f"Sending FastStone PDF convert hotkey: {hotkey}")
        faststone_title = str(config.get("faststone_window_title", "")).strip() or None
        send_windows_hotkey(hotkey, faststone_title)
        if config.get("faststone_pdf_convert_auto_save", True):
            run_faststone_pdf_convert_steps(config, target_pdf)
    else:
        input(
            "Use FastStone's built-in tool to convert/save the scrolling capture as PDF "
            f"in {pdf_dir}, then press Enter..."
        )
    found = wait_for_pdf_output_in_dirs(pdf_search_dirs(config, pdf_dir), since, timeout, stable_seconds)
    auto_close_configured_windows(
        config,
        "faststone_pdf_complete_window_titles",
        "faststone_pdf_complete_keys",
        "faststone_pdf_complete_delay_seconds",
    )
    return found


def run_faststone_pdf_convert_steps(config: dict[str, Any], target_pdf: Path) -> None:
    steps = config.get("faststone_pdf_convert_steps", [])
    if not steps:
        return
    target_pdf.parent.mkdir(parents=True, exist_ok=True)
    if target_pdf.exists():
        target_pdf.unlink()
    delay = float(config.get("faststone_pdf_convert_step_delay_seconds", 1.0))
    for raw_step in steps:
        step = str(raw_step).strip()
        if not step:
            continue
        time.sleep(delay)
        upper = step.upper()
        if upper == "{PASTE_PDF_PATH}":
            print(f"Pasting PDF output path: {target_pdf}")
            set_windows_clipboard_text(str(target_pdf))
            send_windows_hotkey("^v")
        else:
            print(f"Sending FastStone PDF dialog key: {step}")
            send_windows_hotkey(step)


def wait_for_faststone_save_as_pdf(
    config: dict[str, Any],
    pdf_dir: Path,
    target_pdf: Path,
    since: float,
    timeout: int,
    stable_seconds: int,
) -> Path:
    hotkey = str(config.get("faststone_pdf_save_hotkey", "%s")).strip()
    if hotkey:
        delay = float(config.get("faststone_pdf_save_delay_seconds", 1.0))
        time.sleep(delay)
        wait_for_faststone_editor_window(config, "faststone_pdf_save_wait_for_editor_seconds", 30)
        print(f"Sending FastStone Save As PDF hotkey: {hotkey}")
        send_windows_hotkey(hotkey)
        run_faststone_pdf_save_steps(config, target_pdf)
    else:
        input(
            "Use FastStone Save As to save the current screenshot as PDF "
            f"to {target_pdf}, then press Enter..."
        )
    found = wait_for_pdf_output_in_dirs(pdf_search_dirs(config, pdf_dir), since, timeout, stable_seconds)
    auto_close_configured_windows(
        config,
        "faststone_pdf_complete_window_titles",
        "faststone_pdf_complete_keys",
        "faststone_pdf_complete_delay_seconds",
    )
    return found


def wait_for_faststone_current_image_pdf(
    config: dict[str, Any],
    pdf_dir: Path,
    target_pdf: Path,
    since: float,
    timeout: int,
    stable_seconds: int,
) -> Path:
    hotkey = str(config.get("faststone_current_pdf_hotkey", "^g")).strip()
    if hotkey:
        delay = float(config.get("faststone_current_pdf_delay_seconds", 1.0))
        time.sleep(delay)
        wait_for_faststone_editor_window(config, "faststone_current_pdf_wait_for_editor_seconds", 30)
        print(f"Sending FastStone current-image PDF hotkey: {hotkey}")
        send_windows_hotkey(hotkey)
        run_faststone_current_pdf_steps(config, target_pdf)
    else:
        input(
            "Use FastStone Ctrl+G/current-image PDF conversion and save "
            f"to {target_pdf}, then press Enter..."
        )
    found = wait_for_pdf_output_in_dirs(pdf_search_dirs(config, pdf_dir), since, timeout, stable_seconds)
    auto_close_configured_windows(
        config,
        "faststone_pdf_complete_window_titles",
        "faststone_pdf_complete_keys",
        "faststone_pdf_complete_delay_seconds",
    )
    return found


def wait_for_faststone_editor_window(config: dict[str, Any], timeout_key: str, default_timeout: int) -> str | None:
    candidates = normalize_title_candidates(config.get("faststone_editor_window_titles", []))
    explicit_title = str(config.get("faststone_window_title", "")).strip()
    if explicit_title:
        candidates.insert(0, explicit_title)
    matched = wait_for_window_title(
        candidates,
        float(config.get(timeout_key, default_timeout)),
        activate=True,
    )
    if matched:
        print(f"Activated FastStone editor window: {matched}")
    else:
        print(f"Warning: could not find FastStone editor window. Foreground: {foreground_window_title()}")
        print("Visible windows:")
        for title in visible_window_titles():
            print(f"  - {title}")
    return matched


def run_faststone_current_pdf_steps(config: dict[str, Any], target_pdf: Path) -> None:
    steps = config.get("faststone_current_pdf_steps", [])
    if not steps:
        return
    target_pdf.parent.mkdir(parents=True, exist_ok=True)
    if target_pdf.exists():
        target_pdf.unlink()
    delay = float(config.get("faststone_current_pdf_step_delay_seconds", 1.0))
    for raw_step in steps:
        step = str(raw_step).strip()
        if not step:
            continue
        time.sleep(delay)
        upper = step.upper()
        if upper == "{PASTE_PDF_PATH}":
            print(f"Pasting current-image PDF path: {target_pdf}")
            set_windows_clipboard_text(str(target_pdf))
            send_windows_hotkey("^v")
        else:
            print(f"Sending FastStone current-image PDF key: {step}")
            send_windows_hotkey(step)


def run_faststone_pdf_save_steps(config: dict[str, Any], target_pdf: Path) -> None:
    steps = config.get("faststone_pdf_save_steps", [])
    if not steps:
        return
    target_pdf.parent.mkdir(parents=True, exist_ok=True)
    if target_pdf.exists():
        target_pdf.unlink()
    delay = float(config.get("faststone_pdf_save_step_delay_seconds", 1.0))
    for raw_step in steps:
        step = str(raw_step).strip()
        if not step:
            continue
        time.sleep(delay)
        upper = step.upper()
        if upper == "{PASTE_PDF_PATH}":
            print(f"Pasting PDF Save As path: {target_pdf}")
            set_windows_clipboard_text(str(target_pdf))
            send_windows_hotkey("^v")
        else:
            print(f"Sending FastStone Save As key: {step}")
            send_windows_hotkey(step)


class LlamaParseClient:
    """Small HTTP adapter. Replace here if your account uses another endpoint."""

    def __init__(self, config: dict[str, Any]) -> None:
        env_name = config["llamaparse_api_key_env"]
        direct_key = str(config.get("llamaparse_api_key", "")).strip()
        if not direct_key and str(env_name).startswith("llx-"):
            direct_key = str(env_name).strip()
            env_name = "LLAMA_CLOUD_API_KEY"
        self.api_key = direct_key or os.environ.get(env_name)
        self.api_mode = str(config.get("llamaparse_api_mode", "v2")).strip().lower()
        self.file_upload_url = config["llamaparse_file_upload_url"]
        self.parse_url = config["llamaparse_parse_url"]
        self.parse_job_template = config["llamaparse_parse_job_url_template"]
        self.tier = str(config.get("llamaparse_tier", "cost_effective")).strip() or "cost_effective"
        self.version = str(config.get("llamaparse_version", "latest")).strip() or "latest"
        self.upload_url = config["llamaparse_upload_url"]
        self.result_template = config["llamaparse_result_url_template"]
        self.result_type = str(config.get("llamaparse_result_type", "markdown")).strip() or "markdown"
        self.poll_interval = int(config["llamaparse_poll_interval_seconds"])
        self.timeout = int(config["llamaparse_timeout_seconds"])
        self.env_name = env_name

    def parse_pdf(self, pdf_path: Path) -> str:
        if not self.api_key:
            raise RuntimeError(
                f"Missing LlamaParse API key. Set config llamaparse_api_key "
                f"or environment variable: {self.env_name}"
            )
        if "..." in self.api_key:
            raise RuntimeError(
                "The configured LlamaParse API key contains '...'. "
                "Paste the full key from LlamaCloud, not the masked display value."
            )
        if self.api_mode == "v2":
            return self._parse_pdf_v2(pdf_path)
        return self._parse_pdf_v1(pdf_path)

    def _parse_pdf_v2(self, pdf_path: Path) -> str:
        file_id = self._upload_file_for_parse(pdf_path)
        payload = self._post_json(
            self.parse_url,
            {
                "file_id": file_id,
                "tier": self.tier,
                "version": self.version,
            },
        )
        job_id = payload.get("id") or payload.get("job_id")
        if not job_id:
            markdown = self._extract_markdown(payload)
            if markdown:
                return markdown
            raise RuntimeError(f"LlamaParse v2 parse response did not include job id: {payload}")
        return self._poll_v2_result(str(job_id))

    def _upload_file_for_parse(self, pdf_path: Path) -> str:
        boundary = "----code-ocr-cli-boundary"
        body = self._multipart_body(
            pdf_path,
            boundary,
            fields={"purpose": "parse"},
        )
        request = urllib.request.Request(
            self.file_upload_url,
            data=body,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": f"multipart/form-data; boundary={boundary}",
            },
            method="POST",
        )
        payload = self._open_json(request)
        file_id = payload.get("id") or payload.get("file_id")
        if not file_id:
            raise RuntimeError(f"LlamaParse file upload response did not include file id: {payload}")
        return str(file_id)

    def _parse_pdf_v1(self, pdf_path: Path) -> str:
        boundary = "----code-ocr-cli-boundary"
        body = self._multipart_body(
            pdf_path,
            boundary,
            fields={"result_type": self.result_type},
        )
        request = urllib.request.Request(
            self.upload_url,
            data=body,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": f"multipart/form-data; boundary={boundary}",
            },
            method="POST",
        )
        payload = self._open_json(request)
        job_id = payload.get("id") or payload.get("job_id")
        if not job_id:
            markdown = self._extract_markdown(payload)
            if markdown:
                return markdown
            raise RuntimeError(f"LlamaParse upload response did not include job id: {payload}")
        return self._poll_result(str(job_id))

    def _poll_v2_result(self, job_id: str) -> str:
        deadline = time.time() + self.timeout
        url = self.parse_job_template.format(job_id=job_id)
        last_error = None
        while time.time() < deadline:
            request = urllib.request.Request(
                url,
                headers={"Authorization": f"Bearer {self.api_key}"},
                method="GET",
            )
            try:
                payload = self._open_json(request)
                markdown = self._extract_markdown(payload)
                if markdown:
                    return markdown
                job = payload.get("job") if isinstance(payload.get("job"), dict) else {}
                status = str(payload.get("status") or job.get("status") or "").upper()
                if status in {"FAILED", "CANCELLED"}:
                    raise RuntimeError(f"LlamaParse v2 job {status}: {payload}")
                if status in {"SUCCESS", "SUCCEEDED", "COMPLETED", "COMPLETE", "DONE"}:
                    markdown_url = self._extract_markdown_presigned_url(payload)
                    if markdown_url:
                        downloaded = self._download_text(markdown_url)
                        if downloaded.strip():
                            return downloaded
                    raise RuntimeError(
                        "LlamaParse v2 job completed without markdown content. "
                        f"Response keys: {list(payload.keys())}; payload={payload}"
                    )
                last_error = payload
            except HttpJsonError as exc:
                if exc.status not in {202, 404}:
                    raise
                last_error = f"HTTP {exc.status}: result not ready"
            time.sleep(self.poll_interval)
        raise TimeoutError(f"LlamaParse v2 job timed out: {job_id}; last={last_error}")

    def _poll_result(self, job_id: str) -> str:
        deadline = time.time() + self.timeout
        url = self.result_template.format(job_id=job_id)
        last_error = None
        while time.time() < deadline:
            request = urllib.request.Request(
                url,
                headers={"Authorization": f"Bearer {self.api_key}"},
                method="GET",
            )
            try:
                payload = self._open_json(request)
                markdown = payload.get("markdown") or payload.get("result")
                if markdown:
                    return str(markdown)
                last_error = payload
            except HttpJsonError as exc:
                if exc.status not in {202, 404}:
                    raise
                last_error = f"HTTP {exc.status}: result not ready"
            time.sleep(self.poll_interval)
        raise TimeoutError(f"LlamaParse job timed out: {job_id}; last={last_error}")

    def _ssl_context(self) -> ssl.SSLContext | None:
        try:
            import certifi  # type: ignore[import-not-found]
        except Exception:
            return None
        cafile = certifi.where()
        if cafile and Path(cafile).exists():
            return ssl.create_default_context(cafile=cafile)
        return None


    def _open_json(self, request: urllib.request.Request) -> dict[str, Any]:
        try:
            with urllib.request.urlopen(request, timeout=60, context=self._ssl_context()) as response:
                raw = response.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace").strip()
            if len(detail) > 500:
                detail = detail[:500] + "..."
            raise HttpJsonError(exc.code, exc.reason, detail) from exc
        except urllib.error.URLError as exc:
            reason = getattr(exc, "reason", exc)
            ssl_paths = ssl.get_default_verify_paths()
            cert_hint = ""
            try:
                import certifi  # type: ignore[import-not-found]
                cert_hint = f"; certifi={certifi.where()}"
            except Exception:
                cert_hint = "; certifi=not installed"
            raise RuntimeError(
                f"Failed to open LlamaParse URL {request.full_url}: {reason}. "
                f"SSL_CERT_FILE={os.environ.get('SSL_CERT_FILE', '')}; "
                f"default_cafile={ssl_paths.cafile}{cert_hint}"
            ) from exc
        if not raw.strip():
            return {}
        try:
            return json.loads(raw)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"Expected JSON response, got: {raw[:500]}") from exc

    def _post_json(self, url: str, payload: dict[str, Any]) -> dict[str, Any]:
        data = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            url,
            data=data,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        return self._open_json(request)

    @classmethod
    def _extract_markdown(cls, payload: Any) -> str | None:
        if isinstance(payload, dict):
            full = payload.get("markdown_full")
            if isinstance(full, str) and cls._looks_like_markdown_content(full):
                return full

            markdown_obj = payload.get("markdown")
            found = cls._extract_markdown_object(markdown_obj)
            if found:
                return found

            # Fallback for expanded structured items. This is still Markdown,
            # but it is intentionally limited to documented item/page shapes.
            items_obj = payload.get("items")
            found = cls._extract_items_markdown(items_obj)
            if found:
                return found

            for key in ("data", "result", "results"):
                found = cls._extract_markdown(payload.get(key))
                if found:
                    return found
        if isinstance(payload, list):
            parts = [cls._extract_markdown(item) for item in payload]
            text_parts = [part for part in parts if part]
            if text_parts:
                return "\n\n".join(text_parts)
        return None

    @classmethod
    def _extract_markdown_object(cls, value: Any) -> str | None:
        if isinstance(value, str) and cls._looks_like_markdown_content(value):
            return value
        if isinstance(value, dict):
            full = value.get("markdown_full")
            if isinstance(full, str) and cls._looks_like_markdown_content(full):
                return full
            pages = value.get("pages")
            if isinstance(pages, list):
                page_parts: list[str] = []
                for page in pages:
                    if not isinstance(page, dict) or page.get("success") is False:
                        continue
                    page_md = page.get("markdown")
                    if isinstance(page_md, str) and cls._looks_like_markdown_content(page_md):
                        page_parts.append(page_md)
                if page_parts:
                    return "\n\n---\n\n".join(page_parts)
        if isinstance(value, list):
            parts = [cls._extract_markdown_object(item) for item in value]
            text_parts = [part for part in parts if part]
            if text_parts:
                return "\n\n---\n\n".join(text_parts)
        return None

    @classmethod
    def _extract_items_markdown(cls, value: Any) -> str | None:
        if not isinstance(value, dict):
            return None
        pages = value.get("pages")
        if not isinstance(pages, list):
            return None
        page_parts: list[str] = []
        for page in pages:
            if not isinstance(page, dict) or page.get("success") is False:
                continue
            items = page.get("items")
            if not isinstance(items, list):
                continue
            item_parts: list[str] = []
            for item in items:
                if not isinstance(item, dict):
                    continue
                item_md = item.get("md")
                if isinstance(item_md, str) and cls._looks_like_markdown_content(item_md):
                    item_parts.append(item_md)
            if item_parts:
                page_parts.append("\n\n".join(item_parts))
        if page_parts:
            return "\n\n---\n\n".join(page_parts)
        return None

    @staticmethod
    def _looks_like_markdown_content(value: str) -> bool:
        stripped = value.strip()
        if not stripped:
            return False
        if re.fullmatch(r"(pjb|file|fl)-[A-Za-z0-9_-]+", stripped):
            return False
        return True

    @classmethod
    def _extract_markdown_presigned_url(cls, payload: Any) -> str | None:
        if not isinstance(payload, dict):
            return None
        for key in ("markdown_content_metadata", "result_content_metadata"):
            candidate = payload.get(key)
            found = cls._find_presigned_url(candidate, preferred_key="markdown")
            if found:
                return found
        return None

    @classmethod
    def _find_presigned_url(cls, value: Any, preferred_key: str | None = None) -> str | None:
        if isinstance(value, dict):
            if preferred_key and preferred_key in value:
                found = cls._find_presigned_url(value[preferred_key])
                if found:
                    return found
            url = value.get("presigned_url")
            if isinstance(url, str) and url.startswith(("http://", "https://")):
                return url
            for nested in value.values():
                found = cls._find_presigned_url(nested)
                if found:
                    return found
        if isinstance(value, list):
            for nested in value:
                found = cls._find_presigned_url(nested)
                if found:
                    return found
        return None

    @staticmethod
    def _download_text(url: str) -> str:
        request = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(request, timeout=120) as response:
            return response.read().decode("utf-8", errors="replace")

    @staticmethod
    def _multipart_body(pdf_path: Path, boundary: str, fields: dict[str, str] | None = None) -> bytes:
        parts: list[bytes] = []
        for name, value in (fields or {}).items():
            parts.append(
                (
                    f"--{boundary}\r\n"
                    f'Content-Disposition: form-data; name="{name}"\r\n\r\n'
                    f"{value}\r\n"
                ).encode("utf-8")
            )
        content = pdf_path.read_bytes()
        parts.append(
            (
                f"--{boundary}\r\n"
                f'Content-Disposition: form-data; name="file"; filename="{pdf_path.name}"\r\n'
                "Content-Type: application/pdf\r\n\r\n"
            ).encode("utf-8")
            + content
            + b"\r\n"
        )
        parts.append(f"--{boundary}--\r\n".encode("utf-8"))
        return b"".join(parts)


FULL_WIDTH_MAP = str.maketrans(
    {
        "（": "(",
        "）": ")",
        "［": "[",
        "］": "]",
        "｛": "{",
        "｝": "}",
        "；": ";",
        "，": ",",
        "：": ":",
        "。": ".",
        "“": '"',
        "”": '"',
        "‘": "'",
        "’": "'",
        "｜": "|",
        "！": "!",
    }
)


def clean_code(text: str, config: dict[str, Any]) -> str:
    text = html.unescape(text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    if config.get("normalize_full_width_punctuation", True):
        text = text.translate(FULL_WIDTH_MAP)
    lines = text.split("\n")
    cleaned: list[str] = []
    in_fence = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("```"):
            in_fence = not in_fence
            continue
        if not stripped and not cleaned:
            continue
        if re.fullmatch(r"Page\s+\d+(\s+of\s+\d+)?", stripped, flags=re.I):
            continue
        if config.get("strip_line_numbers", True):
            line = re.sub(r"^\s*\d{1,6}\s*[|:]\s?", "", line)
            line = re.sub(r"^\s*\d{1,6}\s{2,}", "", line)
        cleaned.append(line.rstrip())
    while cleaned and not cleaned[-1].strip():
        cleaned.pop()
    return "\n".join(cleaned) + "\n"


def fix_code_ocr_markdown(text: str, config: dict[str, Any]) -> tuple[str, list[dict[str, Any]]]:
    fixed_lines: list[str] = []
    changes: list[dict[str, Any]] = []
    dictionary = list(config.get("code_identifier_dictionary", []))
    for line_no, original in enumerate(text.splitlines(), start=1):
        fixed = fix_code_ocr_line(original, dictionary, config)
        fixed_lines.append(fixed)
        if fixed != original:
            changes.append({"line": line_no, "before": original, "after": fixed})
    fixed_text = "\n".join(fixed_lines)
    if text.endswith("\n"):
        fixed_text += "\n"
    return fixed_text, changes


def fix_code_ocr_line(line: str, dictionary: list[str], config: dict[str, Any]) -> str:
    fixed = html.unescape(line.rstrip())
    if config.get("repair_mojibake_comments", True):
        fixed = repair_mojibake_in_comment(fixed)

    replacements = {
        "# include": "#include",
        "IWDG WriteAccess Enable": "IWDG_WriteAccess_Enable",
        "IWDG WriteAccess_Enable": "IWDG_WriteAccess_Enable",
        "IWDG_WriteAccess Enable": "IWDG_WriteAccess_Enable",
        "IWDGReloadCounter": "IWDG_ReloadCounter",
        "IWDG ReloadCounter": "IWDG_ReloadCounter",
        "IWDG SetReload": "IWDG_SetReload",
        "IWDG SetPrescaler": "IWDG_SetPrescaler",
        "IWDG Enable": "IWDG_Enable",
        "IWDG Init": "IWDG_Init",
        "IwDG": "IWDG",
        "GPIo": "GPIO",
        "GPI0": "GPIO",
        "GP10": "GPIO",
        "RCC AHB1PeriphClockCmd": "RCC_AHB1PeriphClockCmd",
        "SystemCoreClock l": "SystemCoreClock /",
        "u l6": "u16",
        "ul6": "u16",
    }
    for before, after in replacements.items():
        fixed = fixed.replace(before, after)

    fixed = re.sub(r"\bTimeCounter\s+([0-9Oo]+m?s|[0-9Oo]+s)\b", _fix_time_counter, fixed)
    fixed = re.sub(r"\bul\s+(SystermTimer[A-Za-z0-9_]*)\b", r"ul_\1", fixed)
    fixed = re.sub(r"\b([A-Z][A-Za-z0-9]*)\s+([A-Z][A-Za-z0-9]*)\s+([A-Z][A-Za-z0-9]*)\b", _join_known_all_caps_identifier, fixed)
    fixed = apply_identifier_dictionary(fixed, dictionary)
    fixed = fix_missing_call_parentheses(fixed, dictionary)
    fixed = fix_common_spacing(fixed)
    return fixed


def _fix_time_counter(match: re.Match[str]) -> str:
    suffix = match.group(1).replace("O", "0").replace("o", "0")
    return f"TimeCounter_{suffix}"


def _join_known_all_caps_identifier(match: re.Match[str]) -> str:
    value = "_".join(match.groups())
    if value.startswith(("GPIO_", "RCC_", "IWDG_")):
        return value
    return match.group(0)


def apply_identifier_dictionary(line: str, dictionary: list[str]) -> str:
    fixed = line
    for identifier in sorted(dictionary, key=len, reverse=True):
        if "_" not in identifier:
            continue
        escaped_spaces = re.escape(identifier).replace("_", r"[\s_]+")
        fixed = re.sub(rf"\b{escaped_spaces}\b", identifier, fixed, flags=re.IGNORECASE)
    return fixed


def fix_missing_call_parentheses(line: str, dictionary: list[str]) -> str:
    fixed = line
    callable_names = [name for name in dictionary if name.endswith(("Counter", "Enable")) or name.startswith(("IWDG_", "LED"))]
    for name in sorted(callable_names, key=len, reverse=True):
        fixed = re.sub(rf"\b{re.escape(name)}\s*;\s*(//.*)?$", lambda m: f"{name}();{m.group(1) or ''}", fixed)
    return fixed


def fix_common_spacing(line: str) -> str:
    if re.fullmatch(r"\s*//\s*[=\-]{5,}\s*", line):
        return line
    fixed = line
    placeholders = {
        ">=": "__CODE_OCR_GE__",
        "<=": "__CODE_OCR_LE__",
        "==": "__CODE_OCR_EQ__",
        "!=": "__CODE_OCR_NE__",
    }
    for operator, placeholder in placeholders.items():
        fixed = fixed.replace(operator, placeholder)
    fixed = re.sub(r"\s+([,;)\]])", r"\1", fixed)
    fixed = re.sub(r"([(\[])\s+", r"\1", fixed)
    fixed = re.sub(r"\s*&&\s*", " && ", fixed)
    fixed = re.sub(r"\s*\|\s*", " | ", fixed) if "GPIO_Pin" in fixed else fixed
    fixed = re.sub(r"\s*=\s*", " = ", fixed)
    fixed = re.sub(r"\s{2,}", " ", fixed) if fixed.lstrip().startswith("#") else fixed
    for operator, placeholder in placeholders.items():
        fixed = fixed.replace(placeholder, operator)
    return fixed


def repair_mojibake_in_comment(line: str) -> str:
    comment_index = line.find("//")
    block_index = line.find("/*")
    indexes = [index for index in (comment_index, block_index) if index >= 0]
    if not indexes:
        return line
    index = min(indexes)
    prefix, comment = line[:index], line[index:]
    repaired = repair_mojibake_text(comment)
    return prefix + repaired


def repair_mojibake_text(text: str) -> str:
    try:
        candidate = text.encode("gbk", errors="strict").decode("utf-8", errors="strict")
    except UnicodeError:
        return text
    if mojibake_score(candidate) < mojibake_score(text):
        return candidate
    return text


def mojibake_score(text: str) -> int:
    markers = "锟斤拷��������鍑芥暟杈撳叆鍙傛暟涓€"
    return sum(text.count(marker) for marker in markers) + text.count("?")


def diff_text(before: str, after: str, fromfile: str, tofile: str) -> str:
    return "".join(
        difflib.unified_diff(
            before.splitlines(keepends=True),
            after.splitlines(keepends=True),
            fromfile=fromfile,
            tofile=tofile,
        )
    )


def normalize_text_for_compare(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    return text if text.endswith("\n") else text + "\n"


def read_reference_text(path: Path, config: dict[str, Any]) -> str:
    data = path.read_bytes()
    if not data:
        return ""
    if is_probably_binary(data):
        raise ValueError(
            f"Truth file appears to be binary/encrypted rather than plain source text: {path}"
        )
    encoding = str(config.get("reference_encoding", "auto")).strip().lower()
    if encoding and encoding != "auto":
        return data.decode(encoding)
    for candidate in detect_text_encodings(data):
        try:
            return data.decode(candidate)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")


def read_text_auto(path: Path) -> str:
    data = path.read_bytes()
    if not data:
        return ""
    for candidate in detect_text_encodings(data):
        try:
            return data.decode(candidate)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")


def fixed_output_encoding(config: dict[str, Any]) -> str:
    return str(config.get("fixed_output_encoding", "gb18030")).strip() or "gb18030"


def write_fixed_text(path: Path, text: str, config: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    encoding = fixed_output_encoding(config)
    path.write_text(text, encoding=encoding, errors="strict")


def detect_text_encodings(data: bytes) -> list[str]:
    if data.startswith((b"\xff\xfe", b"\xfe\xff")):
        return ["utf-16"]
    if data.startswith(b"\xef\xbb\xbf"):
        return ["utf-8-sig", "utf-8"]
    even_nulls = data[0::2].count(0)
    odd_nulls = data[1::2].count(0)
    half = max(len(data) // 2, 1)
    if odd_nulls / half > 0.25 and even_nulls / half < 0.05:
        return ["utf-16-le", "utf-16", "utf-8-sig", "utf-8", "gb18030", "gbk"]
    if even_nulls / half > 0.25 and odd_nulls / half < 0.05:
        return ["utf-16-be", "utf-16", "utf-8-sig", "utf-8", "gb18030", "gbk"]
    for candidate in ("utf-8-sig", "utf-8", "gb18030", "gbk", "latin-1"):
        pass
    return ["utf-8-sig", "utf-8", "gb18030", "gbk", "latin-1"]


def is_probably_binary(data: bytes) -> bool:
    if data.startswith((b"\xff\xfe", b"\xfe\xff", b"\xef\xbb\xbf")):
        return False
    even_nulls = data[0::2].count(0)
    odd_nulls = data[1::2].count(0)
    half = max(len(data) // 2, 1)
    looks_utf16 = (
        odd_nulls / half > 0.25 and even_nulls / half < 0.05
    ) or (
        even_nulls / half > 0.25 and odd_nulls / half < 0.05
    )
    if looks_utf16:
        return False
    null_ratio = data.count(0) / max(len(data), 1)
    if null_ratio > 0.005:
        return True
    sample = data[:4096]
    control = sum(1 for byte in sample if byte < 32 and byte not in {9, 10, 13})
    return control / max(len(sample), 1) > 0.02


class BeyondCompareHtmlParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.in_row = False
        self.in_cell = False
        self.current_row: list[str] = []
        self.current_cell_parts: list[str] = []
        self.rows: list[list[str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() == "tr":
            self.in_row = True
            self.current_row = []
        elif self.in_row and tag.lower() == "td":
            self.in_cell = True
            self.current_cell_parts = []
        elif self.in_cell and tag.lower() == "br":
            self.current_cell_parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "td" and self.in_cell:
            self.current_row.append("".join(self.current_cell_parts))
            self.current_cell_parts = []
            self.in_cell = False
        elif tag.lower() == "tr" and self.in_row:
            if self.current_row:
                self.rows.append(self.current_row)
            self.current_row = []
            self.in_row = False

    def handle_data(self, data: str) -> None:
        if self.in_cell:
            self.current_cell_parts.append(data)


def read_bc_html_text(path: Path) -> str:
    data = path.read_bytes()
    head = data[:4096].decode("ascii", errors="ignore").lower()
    match = re.search(r"charset=([a-z0-9_-]+)", head)
    encodings = ["gb18030", "gbk"]
    if match:
        declared = match.group(1)
        if declared not in encodings:
            encodings.append(declared)
    encodings.extend(["gb2312", "utf-8"])
    for encoding in encodings:
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")


def extract_left_text_from_bc_html(path: Path) -> str:
    parser = BeyondCompareHtmlParser()
    parser.feed(read_bc_html_text(path))
    lines: list[str] = []
    for row in parser.rows:
        if len(row) < 5:
            continue
        left_num = row[0].strip()
        left_text = row[1]
        marker = row[2].strip()
        if not left_num.isdigit():
            continue
        if marker == "+":
            continue
        lines.append(normalize_bc_cell_text(left_text))
    return "\n".join(lines).rstrip() + "\n"


def extract_best_text_from_bc_html(path: Path) -> str:
    parser = BeyondCompareHtmlParser()
    parser.feed(read_bc_html_text(path))
    lines: list[str] = []
    for row in parser.rows:
        if len(row) < 5:
            continue
        left_num = row[0].strip()
        left_text = normalize_bc_cell_text(row[1])
        right_num = row[3].strip()
        right_text = normalize_bc_cell_text(row[4])
        marker = row[2].strip()
        if left_num.isdigit() and right_num.isdigit():
            lines.append(choose_better_text_line(left_text, right_text))
        elif left_num.isdigit() and marker != "+":
            lines.append(left_text)
        elif right_num.isdigit() and marker == "+":
            lines.append(right_text)
    return repair_bc_html_chinese_text("\n".join(lines).rstrip()) + "\n"


def choose_better_text_line(left: str, right: str) -> str:
    return right if text_quality_score(right) > text_quality_score(left) + 3 else left


def text_quality_score(text: str) -> int:
    score = 0
    score += sum(1 for ch in text if "\u4e00" <= ch <= "\u9fff") * 2
    score -= text.count("\ufffd") * 10
    score -= text.count("�") * 10
    for marker in ("����", "���", "鍑芥暟", "杈撳叆", "杩斿洖", "鏃?", "娴嬭瘯", "绋嬪簭"):
        score -= text.count(marker) * 5
    return score


def normalize_bc_cell_text(value: str) -> str:
    value = value.replace("\xa0", " ")
    return value.rstrip()


def repair_bc_html_chinese_text(text: str) -> str:
    repaired_lines = [repair_bc_html_chinese_line(line) for line in text.splitlines()]
    return "\n".join(repaired_lines)


def repair_bc_html_chinese_line(line: str) -> str:
    fixed = line
    fixed = fixed.replace("�?0�?", "年10月")
    fixed = fixed.replace("�?7�?", "27日")
    fixed = re.sub(r"10月7�\?([0-9])", r"10月27日\1", fixed)
    fixed = re.sub(r"(2014年10月27日)6:", r"\g<1>16:", fixed)
    fixed = re.sub(r"(2014年10月27日)5:", r"\g<1>15:", fixed)
    fixed = fixed.replace("��10��27��", "年10月27日")
    fixed = fixed.replace("��10��28��", "年10月28日")
    fixed = fixed.replace("л����", "谢节玲")
    fixed = fixed.replace("谢节�?", "谢节玲")
    fixed = fixed.replace("������� |л", "函数设计 |谢")
    fixed = fixed.replace("���ز���", "返回参数")
    fixed = fixed.replace("��������", "函数名称")
    fixed = fixed.replace("�������", "输入参数")
    fixed = fixed.replace("EEPROM����", "EEPROM测试")
    fixed = fixed.replace("���Ź�����", "看门狗测试")

    fixed = re.sub(r"(输入参数\s*\|\s*)�\?", r"\1无", fixed)
    fixed = re.sub(r"(返回参数\s*\|\s*)�\?", r"\1无", fixed)
    fixed = re.sub(r"(返回参数\s*\|\s*)��", r"\1无", fixed)
    fixed = re.sub(r"(输入参数\s*\|\s*)谢节玲", r"函数设计 |谢节玲", fixed)
    fixed = fixed.replace("复�?", "复位")
    fixed = fixed.replace("失�?", "失败")
    fixed = fixed.replace("测�?", "测试")
    fixed = fixed.replace("等待看门狗复位..", "等待看门狗复位...")
    return fixed


def reference_candidates(task: Task, truth_dir: Path, config: dict[str, Any]) -> list[Path]:
    logical = Path(task.logical_path)
    output_path = with_output_extension(task.logical_path, config)
    stems = []
    for path in (logical, output_path, Path(task.id)):
        stem = str(path.with_suffix(""))
        if stem and stem not in stems:
            stems.append(stem)
    pdf_stem = Path(task.pdf_path).stem
    if pdf_stem not in stems:
        stems.append(pdf_stem)

    extensions = list(config.get("reference_extensions", []))
    for suffix in {logical.suffix, output_path.suffix}:
        if suffix and suffix not in extensions:
            extensions.append(suffix)

    candidates: list[Path] = []
    for stem in stems:
        base = truth_dir / stem
        if base.suffix:
            candidates.append(base)
        for ext in extensions:
            candidates.append(base.with_suffix(ext))
    return candidates


def resolve_reference_path(task: Task, args: argparse.Namespace, config: dict[str, Any]) -> Path:
    if getattr(args, "truth_file", None):
        path = (ROOT / args.truth_file).resolve()
        if not path.exists():
            raise FileNotFoundError(f"Truth file does not exist: {path}")
        return path

    truth_dir_arg = getattr(args, "truth_dir", None) or config.get("reference_dir", "data/reference")
    truth_dir = (ROOT / truth_dir_arg).resolve()
    if not truth_dir.exists():
        raise FileNotFoundError(f"Truth directory does not exist: {truth_dir}")

    for candidate in reference_candidates(task, truth_dir, config):
        if candidate.exists() and candidate.is_file():
            return candidate.resolve()

    all_files = {path.stem.lower(): path for path in truth_dir.rglob("*") if path.is_file()}
    for candidate in reference_candidates(task, truth_dir, config):
        found = all_files.get(candidate.stem.lower())
        if found:
            return found.resolve()
    raise FileNotFoundError(f"No truth file found for task {task.logical_path} in {truth_dir}")


def validate_code(text: str) -> dict[str, Any]:
    pairs = {"(": ")", "[": "]", "{": "}"}
    openers = set(pairs)
    closers = {v: k for k, v in pairs.items()}
    stack: list[tuple[str, int]] = []
    issues: list[str] = []
    for line_no, line in enumerate(text.splitlines(), start=1):
        for char in line:
            if char in openers:
                stack.append((char, line_no))
            elif char in closers:
                if not stack or stack[-1][0] != closers[char]:
                    issues.append(f"line {line_no}: unmatched closing {char}")
                else:
                    stack.pop()
    for char, line_no in stack[-20:]:
        issues.append(f"line {line_no}: unmatched opening {char}")
    return {
        "ok": not issues,
        "issue_count": len(issues),
        "issues": issues,
        "line_count": len(text.splitlines()),
    }


def select_tasks(tasks: list[Task], task_id: str | None) -> list[Task]:
    if not task_id:
        return tasks
    selected = [task for task in tasks if task.id == task_id or task.logical_path == task_id]
    if not selected:
        raise SystemExit(f"Task not found: {task_id}")
    return selected


def cmd_init(args: argparse.Namespace) -> None:
    config_path = ROOT / args.config
    if config_path.exists() and not args.force:
        raise SystemExit(f"Config already exists: {config_path}")
    save_json(config_path, DEFAULT_CONFIG)
    config = load_config(config_path)
    for rel in ["manifest", "ocr_raw", "ocr_clean", "fixed", "reports", "logs"]:
        (output_dir(config) / rel).mkdir(parents=True, exist_ok=True)
    (ROOT / config["pdf_input_dir"]).mkdir(parents=True, exist_ok=True)
    (ROOT / config["capture_image_dir"]).mkdir(parents=True, exist_ok=True)
    print(f"Initialized {config_path}")


def cmd_capture(args: argparse.Namespace) -> None:
    config = load_config(ROOT / args.config)
    if args.drag_only:
        perform_configured_region_drag(config)
        return
    if not args.source_file:
        raise SystemExit("source_file is required unless --drag-only is used.")
    source_file = resolve_workspace_path(args.source_file).resolve()
    if not source_file.exists():
        raise SystemExit(f"Source file does not exist: {source_file}")
    pdf_dir = (ROOT / (args.pdf_dir or config["pdf_input_dir"])).resolve()
    pdf_dir.mkdir(parents=True, exist_ok=True)
    target_pdf_name = pdf_output_name(source_file, args.pdf_name)
    target_pdf_path = pdf_dir / target_pdf_name
    since = time.time()

    print(f"Opening source file: {source_file}")
    launch_source_file(config, source_file)
    title = args.window_title or str(config.get("source_insight_window_title", "")).strip()
    if config.get("source_insight_maximize", True) and title:
        if maximize_window_by_title(title):
            print(f"Maximized window: {title}")
        else:
            print(f"Warning: could not find window to maximize: {title}")
    if config.get("source_insight_document_maximize", True) and title:
        time.sleep(float(config.get("source_insight_document_maximize_delay_seconds", 1.0)))
        doc_hotkey = str(config.get("source_insight_document_maximize_hotkey", "^{F10}")).strip()
        if doc_hotkey:
            print(f"Maximizing Source Insight document: {doc_hotkey}")
            send_windows_hotkey(doc_hotkey, title)
    launch_faststone_if_configured(config)
    time.sleep(float(config.get("capture_focus_delay_seconds", 2)))

    if args.open_only:
        print("Open-only mode; capture hotkey was not sent.")
        return

    use_region = args.region or str(config.get("capture_mode", "")).lower() == "fixed_region"
    if not args.no_hotkey:
        hotkey = args.hotkey or str(config.get("faststone_region_hotkey" if use_region else "faststone_scrolling_hotkey", ""))
        if not hotkey:
            raise SystemExit("No FastStone hotkey configured. Set faststone_scrolling_hotkey or pass --hotkey.")
        title = title or None
        print(f"Sending FastStone hotkey: {hotkey}")
        send_windows_hotkey(hotkey, title)
        if use_region:
            ready_delay = float(config.get("capture_region_ready_delay_seconds", 1.0))
            time.sleep(ready_delay)
            if args.pause_before_drag:
                input("FastStone should now be in region-select mode. Press Enter to drag the configured region...")
            perform_configured_region_drag(config)

    if args.no_wait:
        print("Not waiting for PDF output.")
        return

    output_mode = str(getattr(args, "output_mode", None) or config.get("capture_output_mode", "pdf")).strip().lower()
    wait_timeout = int(args.wait_timeout or config.get("capture_wait_timeout_seconds", 300))
    pdf_stable_seconds = int(config.get("capture_pdf_stable_seconds", 2))
    convert_hotkey = getattr(args, "convert_hotkey", None)
    if output_mode == "pdf":
        found = wait_for_pdf_output_in_dirs(pdf_search_dirs(config, pdf_dir), since, wait_timeout, pdf_stable_seconds)
    elif output_mode == "faststone_current_image_pdf":
        found = wait_for_faststone_current_image_pdf(
            config,
            pdf_dir,
            target_pdf_path,
            since,
            int(config.get("faststone_current_pdf_wait_timeout_seconds", wait_timeout)),
            pdf_stable_seconds,
        )
    elif output_mode == "faststone_save_as_pdf":
        found = wait_for_faststone_save_as_pdf(
            config,
            pdf_dir,
            target_pdf_path,
            since,
            int(config.get("faststone_pdf_save_wait_timeout_seconds", wait_timeout)),
            pdf_stable_seconds,
        )
    elif output_mode == "faststone_pdf_tool":
        found = wait_for_faststone_pdf_conversion(
            config,
            pdf_dir,
            target_pdf_path,
            since,
            int(config.get("faststone_pdf_convert_wait_timeout_seconds", wait_timeout)),
            pdf_stable_seconds,
            convert_hotkey,
        )
    elif output_mode == "image_then_pdf":
        image_dir = (ROOT / (getattr(args, "image_dir", None) or config.get("capture_image_dir", "data/screenshots"))).resolve()
        image_dir.mkdir(parents=True, exist_ok=True)
        image = wait_for_file_output(
            image_dir,
            config.get("capture_image_extensions", [".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff"]),
            since,
            wait_timeout,
            int(config.get("capture_image_stable_seconds", 2)),
            "image",
        )
        print(f"Captured image: {image}")
        found = wait_for_faststone_pdf_conversion(
            config,
            pdf_dir,
            target_pdf_path,
            time.time(),
            int(config.get("faststone_pdf_convert_wait_timeout_seconds", wait_timeout)),
            pdf_stable_seconds,
            convert_hotkey,
        )
    else:
        raise SystemExit("capture_output_mode must be one of: pdf, faststone_current_image_pdf, faststone_save_as_pdf, faststone_pdf_tool, image_then_pdf")
    final_pdf = normalize_capture_pdf(
        found,
        target_pdf_path,
        bool(config.get("capture_force_source_pdf_name", True)),
    )
    print(f"Captured PDF: {final_pdf}")

    if args.scan:
        scan_args = argparse.Namespace(config=args.config, pdf_dir=str(pdf_dir))
        cmd_scan(scan_args)


def cmd_mouse_pos(args: argparse.Namespace) -> None:
    if args.watch:
        print("Press Ctrl+C to stop.")
        try:
            while True:
                x, y = get_mouse_position()
                print(f"{x},{y}")
                time.sleep(float(args.interval))
        except KeyboardInterrupt:
            return
    x, y = get_mouse_position()
    print(f"{x},{y}")


def cmd_windows(args: argparse.Namespace) -> None:
    foreground = foreground_window_title()
    print(f"Foreground: {foreground}")
    for title in visible_window_titles():
        if args.filter and args.filter.lower() not in title.lower():
            continue
        print(title)


def cmd_close_dialogs(args: argparse.Namespace) -> None:
    config = load_config(ROOT / args.config)
    closed = False
    closed = auto_close_configured_windows(
        config,
        "faststone_pdf_complete_window_titles",
        "faststone_pdf_complete_keys",
        "faststone_pdf_complete_delay_seconds",
    ) or closed
    closed = auto_close_configured_windows(
        config,
        "bc_script_dialog_window_titles",
        "bc_script_dialog_keys",
    ) or closed
    print("Closed matching dialog(s)." if closed else "No matching dialog found.")


def cmd_scan(args: argparse.Namespace) -> None:
    config = load_config(ROOT / args.config)
    pdf_dir = (ROOT / (args.pdf_dir or config["pdf_input_dir"])).resolve()
    if not pdf_dir.exists():
        raise SystemExit(f"PDF directory does not exist: {pdf_dir}")
    existing = {task.pdf_path: task for task in load_tasks(config)}
    tasks: list[Task] = []
    for pdf in sorted(pdf_dir.rglob("*.pdf")):
        pdf_path = str(pdf.resolve())
        if pdf_path in existing:
            tasks.append(existing[pdf_path])
            continue
        logical = guess_logical_path(pdf, config["default_extension"])
        tasks.append(Task(id=normalize_id(logical), logical_path=logical, pdf_path=pdf_path))
    save_tasks(config, tasks)
    print(f"Scanned {len(tasks)} PDF task(s) from {pdf_dir}")


def cmd_status(args: argparse.Namespace) -> None:
    config = load_config(ROOT / args.config)
    tasks = load_tasks(config)
    counts: dict[str, int] = {}
    for task in tasks:
        counts[task.status] = counts.get(task.status, 0) + 1
    print(json.dumps({"total": len(tasks), "by_status": counts}, ensure_ascii=False, indent=2))
    if args.verbose:
        for task in tasks:
            print(f"{task.id}\t{task.status}\t{task.logical_path}")


def cmd_ocr(args: argparse.Namespace) -> None:
    config = load_config(ROOT / args.config)
    tasks = load_tasks(config)
    client = None if args.mock else LlamaParseClient(config)
    raw_dir = output_dir(config) / "ocr_raw"
    for task in select_tasks(tasks, args.task):
        if task.status in {"ocr_done", "cleaned", "validated", "reviewed"} and not args.force:
            continue
        try:
            pdf = Path(task.pdf_path)
            if args.mock:
                text = f"// MOCK OCR for {task.logical_path}\n// Replace by running without --mock.\n"
            else:
                text = client.parse_pdf(pdf)  # type: ignore[union-attr]
            if re.fullmatch(r"\s*(pjb|file|fl)-[A-Za-z0-9_-]+\s*", text):
                raise RuntimeError(f"LlamaParse returned an id instead of Markdown content: {text.strip()}")
            raw_path = raw_dir / f"{task.id}.raw.md"
            raw_path.parent.mkdir(parents=True, exist_ok=True)
            raw_path.write_text(text, encoding="utf-8")
            task.raw_text_path = str(raw_path.resolve())
            task.status = "ocr_done"
            task.error = None
            print(f"OCR done: {task.logical_path}")
        except Exception as exc:
            task.status = "failed"
            task.error = str(exc)
            print(f"OCR failed: {task.logical_path}: {exc}", file=sys.stderr)
    save_tasks(config, tasks)


def cmd_clean(args: argparse.Namespace) -> None:
    config = load_config(ROOT / args.config)
    tasks = load_tasks(config)
    clean_dir = output_dir(config) / "ocr_clean"
    for task in select_tasks(tasks, args.task):
        if not task.raw_text_path:
            print(f"Skip without OCR: {task.logical_path}")
            continue
        raw = Path(task.raw_text_path).read_text(encoding="utf-8")
        cleaned = clean_code(raw, config)
        output_path = with_output_extension(task.logical_path, config)
        clean_path = clean_dir / output_path
        clean_path.parent.mkdir(parents=True, exist_ok=True)
        clean_path.write_text(cleaned, encoding="utf-8")
        task.clean_text_path = str(clean_path.resolve())
        task.status = "cleaned"
        task.error = None
        print(f"Cleaned: {task.logical_path}")
    save_tasks(config, tasks)


def cmd_fix(args: argparse.Namespace) -> None:
    config = load_config(ROOT / args.config)
    tasks = load_tasks(config)
    fixed_dir = output_dir(config) / "fixed"
    report_dir = output_dir(config) / "reports"
    for task in select_tasks(tasks, args.task):
        if not task.clean_text_path:
            print(f"Skip without cleaned text: {task.logical_path}")
            continue
        clean_path = Path(task.clean_text_path)
        before = clean_path.read_text(encoding="utf-8")
        if args.no_auto or not config.get("auto_fix_enabled", True):
            after, changes = before, []
        else:
            after, changes = fix_code_ocr_markdown(before, config)
        output_path = with_output_extension(task.logical_path, config)
        fixed_path = fixed_dir / output_path
        write_fixed_text(fixed_path, after, config)

        diff = diff_text(before, after, str(clean_path), str(fixed_path))
        diff_path = report_dir / f"{task.id}.fix.diff"
        json_path = report_dir / f"{task.id}.fix.json"
        diff_path.parent.mkdir(parents=True, exist_ok=True)
        diff_path.write_text(diff, encoding="utf-8")
        save_json(
            json_path,
            {
                "task": task.logical_path,
                "change_count": len(changes),
                "diff_path": str(diff_path.resolve()),
                "changes": changes,
            },
        )
        task.fixed_text_path = str(fixed_path.resolve())
        task.status = "fixed"
        task.error = None
        print(f"Fixed: {task.logical_path} ({len(changes)} change(s))")
    save_tasks(config, tasks)


def cmd_validate(args: argparse.Namespace) -> None:
    config = load_config(ROOT / args.config)
    tasks = load_tasks(config)
    report_dir = output_dir(config) / "reports"
    for task in select_tasks(tasks, args.task):
        target = task.fixed_text_path or task.clean_text_path
        if not target:
            print(f"Skip without cleaned text: {task.logical_path}")
            continue
        text = read_text_auto(Path(target))
        report = validate_code(text)
        report_path = report_dir / f"{task.id}.report.json"
        save_json(report_path, report)
        task.report_path = str(report_path.resolve())
        task.status = "validated" if report["ok"] else "needs_review"
        task.error = None if report["ok"] else f"{report['issue_count']} validation issue(s)"
        print(f"Validated: {task.logical_path} -> {task.status}")
    save_tasks(config, tasks)


def cmd_align(args: argparse.Namespace) -> None:
    config = load_config(ROOT / args.config)
    tasks = load_tasks(config)
    report_dir = output_dir(config) / "reports"
    fixed_dir = output_dir(config) / "fixed"
    aligned = 0
    for task in select_tasks(tasks, args.task):
        if not task.fixed_text_path and not task.clean_text_path:
            print(f"Skip without recognized text: {task.logical_path}")
            continue
        try:
            truth_path = resolve_reference_path(task, args, config)
            truth_text = normalize_text_for_compare(read_reference_text(truth_path, config))
            source_path = Path(task.fixed_text_path or task.clean_text_path)
            before = normalize_text_for_compare(read_text_auto(source_path))
            output_path = with_output_extension(task.logical_path, config)
            fixed_path = fixed_dir / output_path

            before_diff = diff_text(before, truth_text, str(source_path), str(truth_path))
            write_fixed_text(fixed_path, truth_text, config)
            after = normalize_text_for_compare(read_text_auto(fixed_path))
            after_diff = diff_text(after, truth_text, str(fixed_path), str(truth_path))

            diff_path = report_dir / f"{task.id}.truth.diff"
            json_path = report_dir / f"{task.id}.truth.json"
            diff_path.parent.mkdir(parents=True, exist_ok=True)
            diff_path.write_text(before_diff, encoding="utf-8")
            save_json(
                json_path,
                {
                    "task": task.logical_path,
                    "truth_path": str(truth_path),
                    "fixed_path": str(fixed_path.resolve()),
                    "before_had_diff": bool(before_diff),
                    "after_has_diff": bool(after_diff),
                    "before_diff_path": str(diff_path.resolve()),
                },
            )
            task.fixed_text_path = str(fixed_path.resolve())
            task.status = "truth_aligned" if not after_diff else "needs_review"
            task.error = None if not after_diff else "truth alignment still has differences"
            aligned += 1
            print(f"Aligned: {task.logical_path} -> {truth_path.name}; diff remaining: {bool(after_diff)}")
            if args.open_compare:
                open_beyond_compare(config, str(truth_path), str(fixed_path.resolve()))
        except Exception as exc:
            task.status = "failed"
            task.error = str(exc)
            print(f"Align failed: {task.logical_path}: {exc}", file=sys.stderr)
    save_tasks(config, tasks)
    print(f"Aligned {aligned} task(s)")


def open_beyond_compare(config: dict[str, Any], left: str, right: str) -> None:
    bcompare = Path(config["beyond_compare_path"])
    if not bcompare.exists():
        raise SystemExit(f"Beyond Compare not found: {bcompare}")
    subprocess.Popen([str(bcompare), left, right])


def write_bc_script(path: Path, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def quote_bc_path(path: str | Path) -> str:
    return '"' + str(path).replace('"', '""') + '"'


def windows_short_path(path: str | Path) -> str:
    raw = str(Path(path))
    if os.name != "nt":
        return raw
    buffer = ctypes.create_unicode_buffer(32768)
    result = ctypes.windll.kernel32.GetShortPathNameW(raw, buffer, len(buffer))
    if result:
        return buffer.value
    return raw


def bc_safe_path(path: str | Path, must_exist: bool = True) -> str:
    p = Path(path)
    if must_exist:
        return windows_short_path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    short_parent = windows_short_path(p.parent)
    return str(Path(short_parent) / p.name)


def ascii_safe_filename(value: str, suffix: str) -> str:
    stem = re.sub(r"[^A-Za-z0-9_.-]+", "_", value).strip("._")
    if not stem:
        stem = "file"
    if suffix and not stem.lower().endswith(suffix.lower()):
        stem += suffix
    return stem


def bc_stage_root(config: dict[str, Any]) -> Path:
    configured = str(config.get("bc_stage_dir", "")).strip()
    if configured:
        return Path(configured).resolve()
    return Path(tempfile.gettempdir()) / "code_ocr_bc"


def prepare_bc_stage(task: Task, truth_path: Path, fixed_path: Path, config: dict[str, Any]) -> dict[str, Path]:
    stage = bc_stage_root(config) / normalize_id(task.id)
    if stage.exists():
        shutil.rmtree(stage)
    stage.mkdir(parents=True, exist_ok=True)
    truth_stage = stage / ascii_safe_filename("truth_" + truth_path.name, truth_path.suffix)
    fixed_stage = stage / ascii_safe_filename("fixed_" + fixed_path.name, fixed_path.suffix)
    shutil.copyfile(truth_path, truth_stage)
    shutil.copyfile(fixed_path, fixed_stage)
    return {
        "stage": stage,
        "truth": truth_stage,
        "fixed": fixed_stage,
        "html": stage / "bc_report.html",
        "patch": stage / "bc_report.patch",
        "script": stage / "bc_report_script.txt",
    }


def run_beyond_compare_script(config: dict[str, Any], script_path: Path, wait: bool = True) -> None:
    bcompare = Path(config["beyond_compare_path"])
    if not bcompare.exists():
        raise SystemExit(f"Beyond Compare not found: {bcompare}")
    proc = subprocess.Popen([str(bcompare), f"@{script_path}"])
    if wait:
        start = time.time()
        last_close = 0.0
        initial_delay = float(config.get("bc_script_dialog_initial_delay_seconds", 2.0))
        repeat = float(config.get("bc_script_dialog_repeat_seconds", 5.0))
        interval = float(config.get("gui_auto_close_interval_seconds", 1.0))
        while proc.poll() is None:
            now = time.time()
            if now - start >= initial_delay and now - last_close >= repeat:
                if auto_close_configured_windows(config, "bc_script_dialog_window_titles", "bc_script_dialog_keys"):
                    last_close = now
            time.sleep(max(interval, 0.2))
        if proc.returncode not in (0, None):
            raise RuntimeError(f"Beyond Compare script failed with exit code {proc.returncode}")


def cmd_bc_report(args: argparse.Namespace) -> None:
    config = load_config(ROOT / args.config)
    tasks = load_tasks(config)
    script_dir = output_dir(config) / "bc_scripts"
    report_dir = output_dir(config) / "bc_reports"
    generated = 0
    for task in select_tasks(tasks, args.task):
        if not task.fixed_text_path and not task.clean_text_path:
            print(f"Skip without recognized text: {task.logical_path}")
            continue
        try:
            truth_path = resolve_reference_path(task, args, config)
            fixed_path = Path(task.fixed_text_path or task.clean_text_path).resolve()
            html_path = (report_dir / f"{task.id}.bc.html").resolve()
            patch_path = (report_dir / f"{task.id}.bc.patch").resolve()
            script_path = (script_dir / f"{task.id}.bc-report.txt").resolve()
            report_dir.mkdir(parents=True, exist_ok=True)
            stage = prepare_bc_stage(task, truth_path, fixed_path, config)
            truth_bc = str(stage["truth"])
            fixed_bc = str(stage["fixed"])
            html_bc = str(stage["html"])
            patch_bc = str(stage["patch"])
            write_bc_script(
                stage["script"],
                [
                    "criteria rules-based",
                    (
                        "text-report layout:side-by-side "
                        "options:display-all,line-numbers "
                        f"output-to:{quote_bc_path(html_bc)} "
                        "output-options:html-color,wrap-word "
                        f"{quote_bc_path(truth_bc)} {quote_bc_path(fixed_bc)}"
                    ),
                    (
                        "text-report layout:patch "
                        "options:patch-unified "
                        f"output-to:{quote_bc_path(patch_bc)} "
                        f"{quote_bc_path(truth_bc)} {quote_bc_path(fixed_bc)}"
                    ),
                ],
            )
            shutil.copyfile(stage["script"], script_path)
            run_beyond_compare_script(config, stage["script"], wait=not args.no_wait)
            if stage["html"].exists():
                shutil.copyfile(stage["html"], html_path)
            if stage["patch"].exists():
                shutil.copyfile(stage["patch"], patch_path)
            print(f"BC report: {task.logical_path}")
            print(f"  html:  {html_path}")
            print(f"  patch: {patch_path}")
            generated += 1
        except Exception as exc:
            print(f"BC report failed: {task.logical_path}: {exc}", file=sys.stderr)
    print(f"Generated {generated} Beyond Compare report(s)")


def cmd_bc_align_html(args: argparse.Namespace) -> None:
    config = load_config(ROOT / args.config)
    tasks = load_tasks(config)
    report_dir = output_dir(config) / "bc_reports"
    aligned = 0
    for task in select_tasks(tasks, args.task):
        try:
            html_path = Path(args.html_file).resolve() if args.html_file else (report_dir / f"{task.id}.bc.html").resolve()
            if not html_path.exists() or args.regenerate:
                report_args = argparse.Namespace(
                    config=args.config,
                    task=task.id,
                    truth_file=args.truth_file,
                    truth_dir=args.truth_dir,
                    no_wait=False,
                )
                cmd_bc_report(report_args)
            if not html_path.exists():
                raise FileNotFoundError(f"Beyond Compare HTML report does not exist: {html_path}")
            source_side = str(config.get("bc_html_align_source_side", "left")).strip().lower()
            use_left = args.left_only or source_side == "left"
            truth_text = extract_left_text_from_bc_html(html_path) if use_left else extract_best_text_from_bc_html(html_path)
            if not truth_text.strip():
                raise RuntimeError(f"No plaintext source lines found in BC HTML report: {html_path}")
            fixed_path = Path(task.fixed_text_path or (output_dir(config) / "fixed" / with_output_extension(task.logical_path, config))).resolve()
            before = read_text_auto(fixed_path) if fixed_path.exists() else ""
            write_fixed_text(fixed_path, truth_text, config)
            diff_path = output_dir(config) / "reports" / f"{task.id}.bc-html-align.diff"
            json_path = output_dir(config) / "reports" / f"{task.id}.bc-html-align.json"
            diff = diff_text(before, truth_text, str(fixed_path) + ".before", str(fixed_path))
            diff_path.parent.mkdir(parents=True, exist_ok=True)
            diff_path.write_text(diff, encoding="utf-8")
            save_json(
                json_path,
                {
                    "task": task.logical_path,
                    "html_path": str(html_path),
                    "fixed_path": str(fixed_path),
                    "extracted_line_count": len(truth_text.splitlines()),
                    "diff_path": str(diff_path),
                },
            )
            task.fixed_text_path = str(fixed_path)
            task.status = "bc_html_aligned"
            task.error = None
            aligned += 1
            print(f"BC HTML aligned: {task.logical_path} ({len(truth_text.splitlines())} line(s))")
            if args.verify:
                verify_args = argparse.Namespace(
                    config=args.config,
                    task=task.id,
                    truth_file=args.truth_file,
                    truth_dir=args.truth_dir,
                    no_wait=False,
                )
                cmd_bc_report(verify_args)
        except Exception as exc:
            task.status = "failed"
            task.error = str(exc)
            print(f"BC HTML align failed: {task.logical_path}: {exc}", file=sys.stderr)
    save_tasks(config, tasks)
    print(f"BC HTML aligned {aligned} task(s)")


def cmd_compare(args: argparse.Namespace) -> None:
    config = load_config(ROOT / args.config)
    tasks = load_tasks(config)
    if args.task:
        task = select_tasks(tasks, args.task)[0]
        if args.truth:
            left = str(resolve_reference_path(task, args, config))
            right = task.fixed_text_path
        else:
            left = task.clean_text_path
            right = task.fixed_text_path
        if not left or not right:
            raise SystemExit(f"Task is not ready to compare: {task.logical_path}")
    else:
        left = str((ROOT / (args.truth_dir or config.get("reference_dir", "data/reference"))).resolve()) if args.truth else str((output_dir(config) / "ocr_clean").resolve())
        right = str((output_dir(config) / "fixed").resolve())
    open_beyond_compare(config, left, right)
    print(f"Opened Beyond Compare: {left} <-> {right}")


def cmd_run(args: argparse.Namespace) -> None:
    cmd_scan(args)
    args.mock = args.mock_ocr
    cmd_ocr(args)
    cmd_clean(args)
    args.no_auto = False
    cmd_fix(args)
    cmd_validate(args)


def cmd_recover_one(args: argparse.Namespace) -> None:
    config = load_config(ROOT / args.config)
    source_file = resolve_workspace_path(args.source_file).resolve()
    if not source_file.exists():
        raise SystemExit(f"Source file does not exist: {source_file}")

    pdf_dir = (ROOT / (args.pdf_dir or config["pdf_input_dir"])).resolve()
    pdf_name = pdf_output_name(source_file, args.pdf_name)
    pdf_path = pdf_dir / pdf_name
    logical_path = guess_logical_path(pdf_path, config["default_extension"])
    task_id = normalize_id(logical_path)

    if not args.no_capture:
        capture_args = argparse.Namespace(
            config=args.config,
            source_file=str(source_file),
            pdf_dir=str(pdf_dir),
            pdf_name=pdf_name,
            output_mode=getattr(args, "output_mode", None),
            image_dir=getattr(args, "image_dir", None),
            convert_hotkey=getattr(args, "convert_hotkey", None),
            hotkey=args.hotkey,
            window_title=args.window_title,
            region=True,
            pause_before_drag=args.pause_before_drag,
            drag_only=False,
            open_only=False,
            no_hotkey=False,
            no_wait=False,
            wait_timeout=args.wait_timeout,
            scan=True,
        )
        cmd_capture(capture_args)
    else:
        scan_args = argparse.Namespace(config=args.config, pdf_dir=str(pdf_dir))
        cmd_scan(scan_args)

    print(f"Recover task: {task_id} ({logical_path})")
    ocr_args = argparse.Namespace(config=args.config, task=task_id, mock=args.mock_ocr, force=True)
    clean_args = argparse.Namespace(config=args.config, task=task_id)
    fix_args = argparse.Namespace(config=args.config, task=task_id, no_auto=False)
    validate_args = argparse.Namespace(config=args.config, task=task_id)
    bc_report_args = argparse.Namespace(
        config=args.config,
        task=task_id,
        truth_file=str(source_file),
        truth_dir=None,
        no_wait=False,
    )
    bc_align_args = argparse.Namespace(
        config=args.config,
        task=task_id,
        truth_file=str(source_file),
        truth_dir=None,
        html_file=None,
        regenerate=False,
        verify=not args.no_verify,
        left_only=str(config.get("bc_html_align_source_side", "left")).strip().lower() == "left",
    )

    cmd_ocr(ocr_args)
    cmd_clean(clean_args)
    cmd_fix(fix_args)
    cmd_validate(validate_args)
    if args.no_bc:
        print("Skipping Beyond Compare stages (--no-bc).")
        print("Recover-one complete.")
        return
    cmd_bc_report(bc_report_args)
    cmd_bc_align_html(bc_align_args)
    cmd_validate(validate_args)
    print("Recover-one complete.")


def cmd_recover_batch(args: argparse.Namespace) -> None:
    config = load_config(ROOT / args.config)
    source_root = resolve_workspace_path(args.source_root).resolve()
    recursive = not args.non_recursive
    files = batch_source_files(source_root, config, recursive, args.extensions)
    if args.limit:
        files = files[: int(args.limit)]
    if not files:
        raise SystemExit(f"No source files found in {source_root}")

    print(f"Recover-batch found {len(files)} source file(s) under {source_root}")
    successes: list[Path] = []
    failures: list[tuple[Path, str]] = []
    for index, source_file in enumerate(files, start=1):
        pdf_name = batch_pdf_output_name(source_file, source_root if source_root.is_dir() else source_file.parent)
        print(f"[{index}/{len(files)}] Recovering: {source_file} -> {pdf_name}")
        recover_args = argparse.Namespace(
            config=args.config,
            source_file=str(source_file),
            pdf_dir=args.pdf_dir,
            pdf_name=pdf_name,
            output_mode=args.output_mode,
            image_dir=args.image_dir,
            convert_hotkey=args.convert_hotkey,
            hotkey=args.hotkey,
            window_title=args.window_title,
            pause_before_drag=args.pause_before_drag,
            wait_timeout=args.wait_timeout,
            no_capture=args.no_capture,
            mock_ocr=args.mock_ocr,
            no_bc=args.no_bc,
            no_verify=args.no_verify,
        )
        try:
            cmd_recover_one(recover_args)
            successes.append(source_file)
        except Exception as exc:
            failures.append((source_file, str(exc)))
            print(f"Recover failed: {source_file}: {exc}", file=sys.stderr)
            if args.stop_on_error:
                break
        if args.between_delay:
            time.sleep(float(args.between_delay))

    print(f"Recover-batch complete: {len(successes)} succeeded, {len(failures)} failed")
    if failures:
        for source_file, error in failures:
            print(f"  FAILED {source_file}: {error}", file=sys.stderr)
        if args.stop_on_error:
            raise SystemExit(1)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Batch OCR pipeline for FastStone PDF code screenshots.")
    parser.add_argument("--config", default="config.json")
    sub = parser.add_subparsers(dest="command", required=True)

    init = sub.add_parser("init", help="Create config and output folders.")
    init.add_argument("--force", action="store_true")
    init.set_defaults(func=cmd_init)

    capture = sub.add_parser("capture", help="Open a source file and trigger FastStone scrolling capture to PDF.")
    capture.add_argument("source_file", nargs="?", help="Source file path to open in Source Insight.")
    capture.add_argument("--pdf-dir", help="Directory where FastStone writes PDF files.")
    capture.add_argument("--pdf-name", help="Rename the captured PDF to this name.")
    capture.add_argument("--output-mode", choices=["pdf", "faststone_current_image_pdf", "faststone_save_as_pdf", "faststone_pdf_tool", "image_then_pdf"], help="How FastStone output becomes PDF.")
    capture.add_argument("--image-dir", help="Directory where FastStone writes screenshot images before PDF conversion.")
    capture.add_argument("--convert-hotkey", help="Hotkey that triggers FastStone's built-in PDF conversion.")
    capture.add_argument("--hotkey", help="Override FastStone scrolling capture hotkey.")
    capture.add_argument("--window-title", help="Window title to activate before sending the hotkey.")
    capture.add_argument("--region", action="store_true", help="Use configured fixed region drag after FastStone hotkey.")
    capture.add_argument("--pause-before-drag", action="store_true", help="Pause after FastStone hotkey before dragging the configured region.")
    capture.add_argument("--drag-only", action="store_true", help="Only drag the configured region; do not open files or send hotkeys.")
    capture.add_argument("--open-only", action="store_true", help="Only open the source file; do not capture.")
    capture.add_argument("--no-hotkey", action="store_true", help="Do not send the FastStone hotkey.")
    capture.add_argument("--no-wait", action="store_true", help="Do not wait for PDF output.")
    capture.add_argument("--wait-timeout", help="Seconds to wait for FastStone PDF output.")
    capture.add_argument("--scan", action="store_true", help="Scan PDF directory after capture.")
    capture.set_defaults(func=cmd_capture)

    mouse_pos = sub.add_parser("mouse-pos", help="Print current mouse position for fixed region setup.")
    mouse_pos.add_argument("--watch", action="store_true", help="Continuously print mouse position.")
    mouse_pos.add_argument("--interval", default="0.5", help="Watch interval in seconds.")
    mouse_pos.set_defaults(func=cmd_mouse_pos)

    windows = sub.add_parser("windows", help="List visible Windows window titles for GUI automation debugging.")
    windows.add_argument("--filter", help="Only show titles containing this text.")
    windows.set_defaults(func=cmd_windows)

    close_dialogs = sub.add_parser("close-dialogs", help="Send configured close/confirm keys to FastStone/BC dialogs.")
    close_dialogs.set_defaults(func=cmd_close_dialogs)

    scan = sub.add_parser("scan", help="Scan FastStone generated PDFs into task manifest.")
    scan.add_argument("--pdf-dir")
    scan.set_defaults(func=cmd_scan)

    status = sub.add_parser("status", help="Show task status.")
    status.add_argument("--verbose", "-v", action="store_true")
    status.set_defaults(func=cmd_status)

    ocr = sub.add_parser("ocr", help="Run OCR for pending PDFs.")
    ocr.add_argument("--task")
    ocr.add_argument("--mock", action="store_true")
    ocr.add_argument("--force", action="store_true")
    ocr.set_defaults(func=cmd_ocr)

    clean = sub.add_parser("clean", help="Clean OCR raw text into code files.")
    clean.add_argument("--task")
    clean.set_defaults(func=cmd_clean)

    fix = sub.add_parser("fix", help="Auto-fix OCR code mistakes and write fixed Markdown.")
    fix.add_argument("--task")
    fix.add_argument("--no-auto", action="store_true", help="Copy cleaned Markdown to fixed without automatic changes.")
    fix.set_defaults(func=cmd_fix)

    validate = sub.add_parser("validate", help="Run basic validation checks.")
    validate.add_argument("--task")
    validate.set_defaults(func=cmd_validate)

    align = sub.add_parser("align", help="Align fixed Markdown to truth files until no diff remains.")
    align.add_argument("--task")
    align.add_argument("--truth-file", help="Truth file for a single task.")
    align.add_argument("--truth-dir", help="Directory containing truth files.")
    align.add_argument("--open-compare", action="store_true", help="Open Beyond Compare after alignment.")
    align.set_defaults(func=cmd_align)

    bc_report = sub.add_parser("bc-report", help="Generate Beyond Compare reports using BC's own text engine.")
    bc_report.add_argument("--task")
    bc_report.add_argument("--truth-file", help="Truth file for a single task.")
    bc_report.add_argument("--truth-dir", help="Directory containing truth files.")
    bc_report.add_argument("--no-wait", action="store_true", help="Do not wait for Beyond Compare to finish.")
    bc_report.set_defaults(func=cmd_bc_report)

    bc_align_html = sub.add_parser("bc-align-html", help="Extract plaintext from Beyond Compare HTML and overwrite fixed output.")
    bc_align_html.add_argument("--task")
    bc_align_html.add_argument("--truth-file", help="Truth file for a single task.")
    bc_align_html.add_argument("--truth-dir", help="Directory containing truth files.")
    bc_align_html.add_argument("--html-file", help="Existing Beyond Compare HTML report.")
    bc_align_html.add_argument("--regenerate", action="store_true", help="Regenerate the BC HTML report before extracting.")
    bc_align_html.add_argument("--verify", action="store_true", help="Regenerate a BC report after writing fixed output.")
    bc_align_html.add_argument("--left-only", action="store_true", help="Always extract the left side of the BC report.")
    bc_align_html.set_defaults(func=cmd_bc_align_html)

    compare = sub.add_parser("compare", help="Open Beyond Compare.")
    compare.add_argument("--task")
    compare.add_argument("--truth", action="store_true", help="Compare truth file/folder against fixed output.")
    compare.add_argument("--truth-file", help="Truth file for a single task.")
    compare.add_argument("--truth-dir", help="Directory containing truth files.")
    compare.set_defaults(func=cmd_compare)

    run = sub.add_parser("run", help="Run scan, OCR, clean and validate.")
    run.add_argument("--pdf-dir")
    run.add_argument("--task")
    run.add_argument("--force", action="store_true")
    run.add_argument("--mock-ocr", action="store_true")
    run.set_defaults(func=cmd_run)

    recover_one = sub.add_parser("recover-one", help="Run capture, OCR, fix, BC report, and HTML alignment for one source file.")
    recover_one.add_argument("source_file", help="Encrypted/protected source file path visible in Source Insight/Beyond Compare.")
    recover_one.add_argument("--pdf-dir", help="Directory where FastStone writes PDF files.")
    recover_one.add_argument("--pdf-name", help="Captured PDF name. Defaults to source filename plus .pdf.")
    recover_one.add_argument("--output-mode", choices=["pdf", "faststone_current_image_pdf", "faststone_save_as_pdf", "faststone_pdf_tool", "image_then_pdf"], help="How FastStone output becomes PDF.")
    recover_one.add_argument("--image-dir", help="Directory where FastStone writes screenshot images before PDF conversion.")
    recover_one.add_argument("--convert-hotkey", help="Hotkey that triggers FastStone's built-in PDF conversion.")
    recover_one.add_argument("--hotkey", help="Override FastStone capture hotkey.")
    recover_one.add_argument("--window-title", help="Source Insight window title.")
    recover_one.add_argument("--pause-before-drag", action="store_true", help="Pause after FastStone hotkey before dragging region.")
    recover_one.add_argument("--wait-timeout", help="Seconds to wait for FastStone PDF output.")
    recover_one.add_argument("--no-capture", action="store_true", help="Skip capture and reuse an existing PDF.")
    recover_one.add_argument("--mock-ocr", action="store_true", help="Use mock OCR for testing the local pipeline.")
    recover_one.add_argument("--no-bc", action="store_true", help="Skip Beyond Compare stages.")
    recover_one.add_argument("--no-verify", action="store_true", help="Do not regenerate a BC report after HTML alignment.")
    recover_one.set_defaults(func=cmd_recover_one)

    recover_batch = sub.add_parser("recover-batch", help="Run recover-one over a directory of source files.")
    recover_batch.add_argument("source_root", help="Source file or directory to process.")
    recover_batch.add_argument("--extensions", help="Comma-separated source extensions. Defaults to batch_source_extensions.")
    recover_batch.add_argument("--non-recursive", action="store_true", help="Only process files directly under source_root.")
    recover_batch.add_argument("--limit", help="Process only the first N files, useful for dry runs.")
    recover_batch.add_argument("--between-delay", help="Seconds to wait between files.")
    recover_batch.add_argument("--stop-on-error", action="store_true", help="Stop the batch at the first failed file.")
    recover_batch.add_argument("--pdf-dir", help="Directory where FastStone writes PDF files.")
    recover_batch.add_argument("--output-mode", choices=["pdf", "faststone_current_image_pdf", "faststone_save_as_pdf", "faststone_pdf_tool", "image_then_pdf"], help="How FastStone output becomes PDF.")
    recover_batch.add_argument("--image-dir", help="Directory where FastStone writes screenshot images before PDF conversion.")
    recover_batch.add_argument("--convert-hotkey", help="Hotkey that triggers FastStone's built-in PDF conversion.")
    recover_batch.add_argument("--hotkey", help="Override FastStone capture hotkey.")
    recover_batch.add_argument("--window-title", help="Source Insight window title.")
    recover_batch.add_argument("--pause-before-drag", action="store_true", help="Pause after FastStone hotkey before dragging region.")
    recover_batch.add_argument("--wait-timeout", help="Seconds to wait for FastStone PDF output.")
    recover_batch.add_argument("--no-capture", action="store_true", help="Skip capture and reuse existing PDFs.")
    recover_batch.add_argument("--mock-ocr", action="store_true", help="Use mock OCR for testing the local pipeline.")
    recover_batch.add_argument("--no-bc", action="store_true", help="Skip Beyond Compare stages.")
    recover_batch.add_argument("--no-verify", action="store_true", help="Do not regenerate a BC report after HTML alignment.")
    recover_batch.set_defaults(func=cmd_recover_batch)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
