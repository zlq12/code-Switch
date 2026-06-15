#!/usr/bin/env python3
"""Tkinter UI for the Beyond Compare source recovery CLI."""

from __future__ import annotations

import queue
import shutil
import subprocess
import sys
import threading
from pathlib import Path
from tkinter import BOTH, END, LEFT, RIGHT, Button, Checkbutton, Entry, Frame, Label, Listbox, StringVar, Text, Tk, filedialog, messagebox
from tkinter import ttk

import code_ocr


ROOT = Path(__file__).resolve().parent
SOURCE_EXTENSIONS = {".c", ".cpp", ".h", ".hpp"}


class CodeOcrUi:
    def __init__(self, root: Tk) -> None:
        self.root = root
        self.root.title("Code Source Recovery")
        self.root.geometry("980x680")
        self.root.minsize(820, 560)

        self.files: list[Path] = []
        self.export_dir = StringVar()
        self.no_bc = StringVar(value="0")
        self.status_text = StringVar(value="Ready")
        self.message_queue: queue.Queue[tuple[str, object]] = queue.Queue()
        self.worker: threading.Thread | None = None
        self.current_process: subprocess.Popen[str] | None = None

        self._build_ui()
        self.root.after(100, self._drain_queue)

    def _build_ui(self) -> None:
        outer = Frame(self.root, padx=14, pady=12)
        outer.pack(fill=BOTH, expand=True)

        header = Frame(outer)
        header.pack(fill="x")
        Label(header, text="待恢复文件（.c / .cpp / .h / .hpp）").pack(side=LEFT)
        Button(header, text="导入文件", command=self.add_files).pack(side=RIGHT, padx=(6, 0))
        Button(header, text="移除选中", command=self.remove_selected).pack(side=RIGHT, padx=(6, 0))
        Button(header, text="清空", command=self.clear_files).pack(side=RIGHT, padx=(6, 0))

        list_frame = Frame(outer)
        list_frame.pack(fill=BOTH, expand=False, pady=(8, 12))
        self.file_list = Listbox(list_frame, height=8, selectmode="extended")
        self.file_list.pack(side=LEFT, fill=BOTH, expand=True)
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.file_list.yview)
        scrollbar.pack(side=RIGHT, fill="y")
        self.file_list.configure(yscrollcommand=scrollbar.set)

        export_frame = Frame(outer)
        export_frame.pack(fill="x", pady=(0, 10))
        Label(export_frame, text="导出路径").pack(side=LEFT)
        Entry(export_frame, textvariable=self.export_dir).pack(side=LEFT, fill="x", expand=True, padx=8)
        Button(export_frame, text="选择目录", command=self.choose_export_dir).pack(side=RIGHT)

        options = Frame(outer)
        options.pack(fill="x", pady=(0, 10))
        Checkbutton(options, text="跳过 Beyond Compare", variable=self.no_bc, onvalue="1", offvalue="0").pack(side=LEFT)

        action = Frame(outer)
        action.pack(fill="x", pady=(0, 8))
        self.start_button = Button(action, text="开始恢复", command=self.start_conversion, height=2)
        self.start_button.pack(side=LEFT)
        self.progress = ttk.Progressbar(action, mode="determinate")
        self.progress.pack(side=LEFT, fill="x", expand=True, padx=12)
        Label(action, textvariable=self.status_text, width=28, anchor="w").pack(side=RIGHT)

        Label(outer, text="恢复进度").pack(anchor="w")
        log_frame = Frame(outer)
        log_frame.pack(fill=BOTH, expand=True, pady=(6, 0))
        self.log = Text(log_frame, height=18, wrap="word")
        self.log.pack(side=LEFT, fill=BOTH, expand=True)
        log_scroll = ttk.Scrollbar(log_frame, orient="vertical", command=self.log.yview)
        log_scroll.pack(side=RIGHT, fill="y")
        self.log.configure(yscrollcommand=log_scroll.set)

    def add_files(self) -> None:
        selected = filedialog.askopenfilenames(
            title="选择要恢复的 C/C++ 文件",
            filetypes=[
                ("C/C++ source/header", "*.c *.cpp *.h *.hpp"),
                ("C source", "*.c"),
                ("C++ source", "*.cpp"),
                ("Header", "*.h *.hpp"),
                ("All files", "*.*"),
            ],
        )
        for raw in selected:
            path = Path(raw).resolve()
            if path.suffix.lower() not in SOURCE_EXTENSIONS:
                self._log(f"Skip unsupported file: {path}")
                continue
            if path not in self.files:
                self.files.append(path)
                self.file_list.insert(END, str(path))

    def remove_selected(self) -> None:
        indices = list(self.file_list.curselection())
        for index in reversed(indices):
            self.file_list.delete(index)
            del self.files[index]

    def clear_files(self) -> None:
        self.files.clear()
        self.file_list.delete(0, END)

    def choose_export_dir(self) -> None:
        selected = filedialog.askdirectory(title="选择恢复后文件的导出目录")
        if selected:
            self.export_dir.set(str(Path(selected).resolve()))

    def start_conversion(self) -> None:
        if self.worker and self.worker.is_alive():
            messagebox.showinfo("正在恢复", "当前恢复任务仍在运行。")
            return
        if not self.files:
            messagebox.showwarning("缺少文件", "请先导入要恢复的 .c/.cpp/.h/.hpp 文件。")
            return
        export = Path(self.export_dir.get()).expanduser()
        if not str(export).strip():
            messagebox.showwarning("缺少导出路径", "请选择导出路径。")
            return
        export.mkdir(parents=True, exist_ok=True)

        self.start_button.configure(state="disabled")
        self.progress.configure(maximum=len(self.files), value=0)
        self.status_text.set("Starting")
        self._log("=" * 80)
        self._log(f"Export directory: {export.resolve()}")
        self.worker = threading.Thread(target=self._run_batch, args=(list(self.files), export.resolve()), daemon=True)
        self.worker.start()

    def _run_batch(self, files: list[Path], export_dir: Path) -> None:
        successes = 0
        failures: list[tuple[Path, str]] = []
        for index, source in enumerate(files, start=1):
            self.message_queue.put(("status", f"{index}/{len(files)}"))
            self.message_queue.put(("log", f"\n[{index}/{len(files)}] Recovering: {source}"))
            try:
                self._run_one(source)
                exported = self._export_fixed_file(source, export_dir)
                successes += 1
                self.message_queue.put(("log", f"Exported: {exported}"))
            except Exception as exc:
                failures.append((source, str(exc)))
                self.message_queue.put(("log", f"FAILED: {source}: {exc}"))
            self.message_queue.put(("progress", index))

        summary = f"Done: {successes} succeeded, {len(failures)} failed"
        self.message_queue.put(("status", summary))
        self.message_queue.put(("log", "\n" + summary))
        self.message_queue.put(("done", None))

    def _run_one(self, source: Path) -> None:
        cmd = [sys.executable, "-u", str(ROOT / "code_ocr.py"), "recover-one", str(source)]
        if self.no_bc.get() == "1":
            cmd.append("--no-bc")

        self.message_queue.put(("log", "Command: " + " ".join(f'"{item}"' if " " in item else item for item in cmd)))
        self.current_process = subprocess.Popen(
            cmd,
            cwd=str(ROOT),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        assert self.current_process.stdout is not None
        for line in self.current_process.stdout:
            self.message_queue.put(("log", line.rstrip()))
        code = self.current_process.wait()
        self.current_process = None
        if code != 0:
            raise RuntimeError(f"recover-one exited with code {code}")
        self._assert_task_completed(source)

    def _assert_task_completed(self, source: Path) -> None:
        config = code_ocr.load_config(ROOT / "config.json")
        logical_path = code_ocr.logical_path_for_source(source, config)
        task_id = code_ocr.normalize_id(logical_path)
        task = code_ocr.find_task_by_id(config, task_id)
        if not task:
            raise RuntimeError(f"Task not found after recovery: {logical_path}")
        if task.status == "failed":
            raise RuntimeError(f"Task failed: {task.error}")
        if not task.fixed_text_path or not Path(task.fixed_text_path).exists():
            raise RuntimeError(f"Fixed output not found for task: {logical_path}")

    def _export_fixed_file(self, source: Path, export_dir: Path) -> Path:
        config = code_ocr.load_config(ROOT / "config.json")
        logical_path = code_ocr.logical_path_for_source(source, config)
        output_path = code_ocr.with_output_extension(logical_path, config)
        fixed_path = code_ocr.output_dir(config) / "fixed" / output_path
        if not fixed_path.exists():
            raise FileNotFoundError(f"Fixed output not found: {fixed_path}")

        target = unique_export_path(export_dir / Path(output_path).name)
        shutil.copy2(fixed_path, target)
        return target

    def _drain_queue(self) -> None:
        try:
            while True:
                kind, payload = self.message_queue.get_nowait()
                if kind == "log":
                    self._log(str(payload))
                elif kind == "status":
                    self.status_text.set(str(payload))
                elif kind == "progress":
                    self.progress.configure(value=int(payload))
                elif kind == "done":
                    self.start_button.configure(state="normal")
        except queue.Empty:
            pass
        self.root.after(100, self._drain_queue)

    def _log(self, message: str) -> None:
        self.log.insert(END, message + "\n")
        self.log.see(END)


def unique_export_path(path: Path) -> Path:
    if not path.exists():
        return path
    stem = path.stem
    suffix = path.suffix
    parent = path.parent
    index = 1
    while True:
        candidate = parent / f"{stem}_{index}{suffix}"
        if not candidate.exists():
            return candidate
        index += 1


def main() -> int:
    root = Tk()
    CodeOcrUi(root)
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
