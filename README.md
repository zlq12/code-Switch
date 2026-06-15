# Code Recovery CLI

This tool recovers protected source files through Beyond Compare. The current main workflow no longer uses screenshots, PDF conversion, LlamaParse, OCR cleanup, or OCR auto-fix.

## Workflow

```text
protected/original source file
-> blank output file under output/fixed
-> Beyond Compare side-by-side HTML report
-> extract left-side plaintext from the HTML report
-> write recovered source into output/fixed
-> optional verification report
```

Beyond Compare must be able to show the protected/original file as plaintext on the left side.

## Setup

Create the config file:

```powershell
python .\code_ocr.py init
```

Then edit `config.json`:

```json
{
  "reference_dir": "data/reference",
  "output_dir": "output",
  "beyond_compare_path": "C:/Program Files/Beyond Compare 5/BCompare.exe",
  "bc_html_align_source_side": "left",
  "final_output_extension": "",
  "fixed_output_encoding": "gb18030"
}
```

Use `fixed_output_encoding: "gb18030"` when Beyond Compare treats legacy C/C++ files as ANSI and Chinese comments must display correctly.

## Single File

Recover one file:

```powershell
python .\code_ocr.py recover-one ".\data\reference\App_Test.cpp"
```

The output keeps the source extension:

```text
output/fixed/App_Test.cpp
```

Useful options:

```powershell
python .\code_ocr.py recover-one ".\data\reference\App_Test.cpp" --no-verify
python .\code_ocr.py recover-one ".\data\reference\App_Test.cpp" --no-bc
```

`--no-bc` only creates the blank output task and is mainly useful for debugging.

## Batch Recovery

Recover all supported source files in a folder:

```powershell
python .\code_ocr.py recover-batch ".\data\reference"
```

Supported extensions default to:

```json
{
  "batch_source_extensions": [".c", ".cpp", ".h", ".hpp"]
}
```

Batch mode is sequential. The next file starts only after the current task has reached a final state and the fixed output file exists:

```json
{
  "batch_wait_for_completion": true,
  "batch_completion_timeout_seconds": 600,
  "batch_completion_poll_seconds": 2,
  "batch_gui_settle_seconds": 3,
  "batch_close_dialogs_between_files": true
}
```

Useful variants:

```powershell
python .\code_ocr.py recover-batch ".\data\reference" --limit 1
python .\code_ocr.py recover-batch ".\data\reference" --extensions ".cpp,.h" --limit 5
python .\code_ocr.py recover-batch ".\data\reference" --completion-timeout 900
```

Nested files keep their relative path:

```text
data/reference/app/Module/Mod_GUI.cpp
-> output/fixed/app/Module/Mod_GUI.cpp
```

## Desktop UI

Start the UI:

```powershell
python .\code_ocr_ui.py
```

The UI imports `.c`, `.cpp`, `.h`, and `.hpp` files, runs the same `recover-one` flow for each file, shows live logs, and copies recovered files from `output/fixed` to the selected export directory.

## Reports

Generated files:

```text
output/manifest/tasks.json
output/fixed/
output/bc_reports/*.bc.html
output/bc_reports/*.bc.patch
output/reports/*.bc-html-align.diff
output/reports/*.bc-html-align.json
output/reports/*.report.json
```

If the patch report contains encrypted bytes but the HTML report shows plaintext, this is expected for protected files. The recovery step uses the HTML report.

## Dialog Automation

Beyond Compare completion dialogs can be closed automatically:

```json
{
  "gui_auto_close_enabled": true,
  "bc_script_dialog_window_titles": ["Beyond Compare"],
  "bc_script_dialog_keys": ["{ENTER}"],
  "bc_script_dialog_initial_delay_seconds": 2.0,
  "bc_script_dialog_repeat_seconds": 5.0
}
```

Test dialog closing:

```powershell
python .\code_ocr.py close-dialogs
```

## Legacy Tools

The CLI still contains low-level `capture`, `scan`, `ocr`, `clean`, `fix`, and `run` commands for old experiments. They are no longer part of the recommended recovery workflow.
