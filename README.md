# Code OCR CLI MVP

一个面向“截图/PDF -> 代码 OCR -> 清洗 -> 校验 -> Beyond Compare 复核”的 Python CLI MVP。

当前版本假设 PDF 已经由 FastStone Capture 内置工具生成。程序负责批量管理 PDF、调用 OCR、保存原始文本、清洗代码、做基础校验，并可一键打开 Beyond Compare。

## 快速开始

```powershell
python .\code_ocr.py init
python .\code_ocr.py scan --pdf-dir .\data\pdf
python .\code_ocr.py ocr --mock
python .\code_ocr.py clean
python .\code_ocr.py validate
python .\code_ocr.py status
```

## 目录约定

```text
workspace/
  config.json
  data/
    pdf/              # FastStone 输出的 PDF
  output/
    manifest/
      tasks.json
    ocr_raw/          # LlamaParse Markdown 原始结果：*.raw.md
    ocr_clean/        # 清洗后的 Markdown
    fixed/            # 用于人工修正的 Markdown
    reports/
    logs/
```

## 自动修正与比较

`clean` 会保留 OCR 清洗后的 Markdown，`fix` 会在 `fixed` 中写入自动修正后的 Markdown，并生成差异报告：

```powershell
python .\code_ocr.py clean
python .\code_ocr.py fix
python .\code_ocr.py validate
python .\code_ocr.py compare
```

输出：

```text
output/ocr_clean/*.md      # OCR 清洗版
output/fixed/*.md          # 自动修正版
output/reports/*.fix.diff  # unified diff
output/reports/*.fix.json  # 修正明细
```

自动修正覆盖几类代码 OCR 常见问题：

```text
HTML 实体：&#x26; -> &
时间变量：TimeCounter 25Oms -> TimeCounter_250ms
下划线丢失：IWDGReloadCounter -> IWDG_ReloadCounter
标识符空格：GPIO PuPd NOPULL -> GPIO_PuPd_NOPULL
函数调用：IWDG_ReloadCounter; -> IWDG_ReloadCounter();
中文注释乱码：尝试把 UTF-8/GBK 错解恢复
```

可以在 `config.json` 中扩展 `code_identifier_dictionary`，把你项目里的宏、函数名、类型名加入词典。关闭自动修正：

```json
{
  "auto_fix_enabled": false
}
```

或临时运行：

```powershell
python .\code_ocr.py fix --no-auto
```

## LlamaParse

真实 OCR 调用需要配置环境变量：

```powershell
$env:LLAMA_CLOUD_API_KEY="你的 API Key"
python .\code_ocr.py ocr
```

也可以直接在 `config.json` 中填写：

```json
{
  "llamaparse_api_key": "你的 API Key"
}
```

程序会显式请求 Markdown 结果，并保存为 `output/ocr_raw/*.raw.md`：

```json
{
  "llamaparse_api_mode": "v2",
  "llamaparse_tier": "cost_effective",
  "llamaparse_version": "latest",
  "llamaparse_result_type": "markdown",
  "llamaparse_parse_job_url_template": "https://api.cloud.llamaindex.ai/api/v2/parse/{job_id}?expand=markdown"
}
```

`cost_effective` 使用 LlamaParse v2 的解析档位。程序流程是：

```text
POST /api/v1/beta/files, purpose=parse
POST /api/v2/parse, tier=cost_effective, version=latest
GET  /api/v2/parse/{job_id}?expand=markdown
```

如果你的账号暂时不能用 v2，可以把 `llamaparse_api_mode` 改成 `v1` 回退到旧上传接口。

由于 LlamaParse 服务端 API 可能变动，`code_ocr.py` 中的 `LlamaParseClient` 做成了单独适配层。若你的账号当前使用的是 Python SDK，也可以只替换这一层，不影响任务队列、清洗、校验和对比流程。

## Beyond Compare

初始化后修改 `config.json`：

```json
{
  "beyond_compare_path": "C:/Program Files/Beyond Compare 5/BCompare.exe"
}
```

然后运行：

```powershell
python .\code_ocr.py compare
python .\code_ocr.py compare --task some_file
```

## PDF 命名建议

为了尽量还原目录结构，建议 FastStone 输出 PDF 时使用稳定命名：

```text
src__main_cpp.pdf
app__module__mod_tempctrl_h.pdf
```

如果不需要还原目录结构，直接用文件名也可以：

```text
main.cpp.pdf
main_cpp.pdf
```

最终输出默认保留 Markdown 扩展名：

```json
{
  "default_extension": ".md",
  "final_output_extension": ".md"
}
```

## Truth Alignment

Put real source files under `data/reference`, then align OCR output to the truth files:

```powershell
python .\code_ocr.py align
python .\code_ocr.py compare --truth
```

For one file:

```powershell
python .\code_ocr.py align --task 2026-06-08_104713.txt --truth-file .\data\reference\real.cpp --open-compare
```

`align` compares the current `fixed/*.md` result with the truth file, writes the truth content into `fixed/*.md`, then compares again. The loop ends only when the generated file has no diff against the truth file. Reports are written to:

```text
output/reports/*.truth.diff
output/reports/*.truth.json
```

## Beyond Compare Report From Encrypted Source

If Beyond Compare can display plaintext from an encrypted/protected source file, generate reports through Beyond Compare itself:

```powershell
python .\code_ocr.py bc-report --task 2026-06-08_135934.md --truth-file ".\data\reference\App_Test.cpp"
```

Outputs:

```text
output/bc_scripts/*.bc-report.txt
output/bc_reports/*.bc.html
output/bc_reports/*.bc.patch
```

The HTML report is useful for review. The patch report is the bridge for future automatic correction, because it is produced by Beyond Compare after it has opened the protected source.

If the patch report still contains encrypted bytes but the HTML report shows plaintext, align from HTML:

```powershell
python .\code_ocr.py bc-align-html --task 2026-06-08_135934.md --truth-file ".\data\reference\App_Test.cpp" --verify
```

This extracts the left-side plaintext lines from the Beyond Compare HTML report and overwrites `output/fixed/*.md`.

## Source Insight + FastStone Capture

Configure paths and the FastStone scrolling-capture hotkey in `config.json`:

```json
{
  "source_insight_path": "C:/Program Files (x86)/Source Insight 4.0/sourceinsight4.exe",
  "source_insight_window_title": "Source Insight",
  "faststone_path": "C:/Program Files (x86)/FastStone Capture/FSCapture.exe",
  "faststone_window_title": "",
  "faststone_scrolling_hotkey": "^%{PRTSC}",
  "pdf_input_dir": "data/pdf"
}
```

The default hotkey uses Windows `SendKeys` syntax:

```text
^ = Ctrl
% = Alt
+ = Shift
{PRTSC} = Print Screen
```

First configure FastStone manually so the hotkey performs scrolling capture and saves/converts to PDF in `data/pdf`. Then run:

```powershell
python .\code_ocr.py capture ".\data\reference\App_Test.cpp" --scan
```

Useful variants:

```powershell
python .\code_ocr.py capture ".\data\reference\App_Test.cpp" --pdf-name App_Test.cpp.pdf --scan
python .\code_ocr.py capture ".\data\reference\App_Test.cpp" --open-only
python .\code_ocr.py capture ".\data\reference\App_Test.cpp" --hotkey "^%{PRTSC}"
```

After capture:

```powershell
python .\code_ocr.py run --force
```

## One Command Recovery

Run the whole single-file chain:

```powershell
python .\code_ocr.py recover-one ".\data\reference\App_Test.cpp"
```

Equivalent high-level flow:

```text
capture fixed region PDF
scan
LlamaParse OCR
clean
auto-fix
validate
Beyond Compare HTML report
extract plaintext from BC HTML into fixed
validate again
```

Useful options:

```powershell
python .\code_ocr.py recover-one ".\data\reference\App_Test.cpp" --pdf-name App_Test.cpp.pdf
python .\code_ocr.py recover-one ".\data\reference\App_Test.cpp" --pause-before-drag
python .\code_ocr.py recover-one ".\data\reference\App_Test.cpp" --no-capture
python .\code_ocr.py recover-one ".\data\reference\App_Test.cpp" --mock-ocr --no-bc
```

### Fixed Region Capture

Use `mouse-pos` to measure the code area:

```powershell
python .\code_ocr.py mouse-pos --watch
```

Move the mouse to the top-left and bottom-right corners of the Source Insight code area, then write those coordinates into `config.json`:

```json
{
  "faststone_region_hotkey": "^%r",
  "capture_mode": "fixed_region",
  "capture_region": {
    "left": 120,
    "top": 160,
    "right": 980,
    "bottom": 920
  }
}
```

Run fixed-region capture:

```powershell
python .\code_ocr.py capture ".\data\reference\App_Test.cpp" --region --pdf-name App_Test.cpp.pdf --scan
```

FastStone must be configured so `faststone_region_hotkey` enters the rectangular/fixed-region capture mode that accepts mouse drag selection and then performs scrolling capture/PDF output.

The automated region sequence is:

```text
Enter FastStone scrolling capture
Hold Ctrl
Hold left mouse button at the configured top-left point
Drag to the configured bottom-right point
Release left mouse button
Release Ctrl
Left-click inside the selected region
```

The final click is controlled by:

```json
{
  "capture_region_post_click": true,
  "capture_region_post_click_point": "center",
  "capture_region_post_click_delay_seconds": 0.3
}
```

Debug the drag itself:

```powershell
python .\code_ocr.py capture --drag-only
```

Debug whether FastStone is ready before the automated drag:

```powershell
python .\code_ocr.py capture ".\data\reference\App_Test.cpp" --region --pause-before-drag --no-wait
```

When it pauses, confirm the FastStone crosshair/region-select overlay is visible, then press Enter.

### FastStone Built-In PDF Conversion

If FastStone first creates a scrolling screenshot/editor result, use the current-image PDF shortcut:

```json
{
  "capture_output_mode": "faststone_current_image_pdf",
  "faststone_editor_window_titles": [
    "FastStone Editor",
    "FastStone Capture"
  ],
  "faststone_current_pdf_hotkey": "^g",
  "faststone_current_pdf_wait_for_editor_seconds": 30,
  "faststone_current_pdf_steps": [
    "{PASTE_PDF_PATH}",
    "{ENTER}",
    "{ENTER}"
  ],
  "pdf_input_dir": "data/pdf"
}
```

`^g` means `Ctrl+G`. The CLI waits for the FastStone editor, sends `Ctrl+G`, pastes the target PDF path into the save dialog, and confirms it. This uses FastStone's own current-image PDF conversion for the screenshot currently open in the editor.

The target PDF is named from the source file, for example:

```text
.\data\reference\App_Test.cpp -> .\data\pdf\App_Test.cpp.pdf
```

The capture step normalizes the final PDF path before OCR:

```json
{
  "capture_pdf_output_search_dirs": [
    "data/pdf"
  ],
  "capture_force_source_pdf_name": true
}
```

If FastStone saves the PDF to another folder, add that folder to `capture_pdf_output_search_dirs`. The CLI will find the newest PDF from this run, move it into `data/pdf`, and rename it to the source-file PDF name before scanning.

If the save hotkey does not take effect, inspect the real FastStone window title while the captured image is open:

```powershell
python .\code_ocr.py windows --filter FastStone
```

Then put the matching title into `faststone_editor_window_titles` or `faststone_window_title`.

If your FastStone version does not bind `Ctrl+G` to current-image PDF conversion, you can fall back to Save As:

```json
{
  "capture_output_mode": "faststone_save_as_pdf",
  "faststone_pdf_save_hotkey": "%s",
  "faststone_pdf_save_steps": [
    "{PASTE_PDF_PATH}",
    "{ENTER}",
    "{ENTER}"
  ]
}
```

FastStone also has a separate Convert Images to PDF tool. That tool requires images to be added to the conversion list first, so use it only when your FastStone workflow already adds the current screenshot automatically:

```json
{
  "capture_output_mode": "faststone_pdf_tool",
  "faststone_pdf_convert_hotkey": "^g",
  "faststone_pdf_convert_auto_save": true,
  "faststone_pdf_convert_steps": [
    "{ENTER}",
    "{PASTE_PDF_PATH}",
    "{ENTER}",
    "{ENTER}"
  ],
  "pdf_input_dir": "data/pdf"
}
```

`^g` means `Ctrl+G`. If the hotkey should be sent to a specific FastStone window, set `faststone_window_title`. If the relevant hotkey is empty, the CLI will pause and let you manually save the PDF before continuing.

Run the full chain with:

```powershell
python .\code_ocr.py recover-one ".\data\reference\App_Test.cpp"
```

### Batch Recovery

After the single-file flow is stable, process a whole folder with:

```powershell
python .\code_ocr.py recover-batch ".\data\reference"
```

The batch command recursively scans source files using `batch_source_extensions` and runs the same capture/OCR/fix/BC alignment flow as `recover-one`.

Useful dry-run and recovery variants:

```powershell
python .\code_ocr.py recover-batch ".\data\reference" --limit 1
python .\code_ocr.py recover-batch ".\data\reference" --extensions ".cpp,.h" --limit 5
python .\code_ocr.py recover-batch ".\data\reference" --no-capture
python .\code_ocr.py recover-batch ".\data\reference" --mock-ocr --no-bc --no-capture
```

For files inside subdirectories, PDFs are named from their relative path to avoid collisions:

```text
.\data\reference\app\Module\Mod_GUI.cpp
-> .\data\pdf\app__Module__Mod_GUI.cpp.pdf
-> logical path app/Module/Mod_GUI.cpp
```

For exact correction, keep the BC HTML alignment source side on the encrypted/original file side:

```json
{
  "bc_html_align_source_side": "left",
  "fixed_output_encoding": "gb18030"
}
```

The generated Beyond Compare report puts the original file on the left and OCR/fixed Markdown on the right. The align step should therefore extract the left side. The older heuristic mode could choose the OCR side for a few lines when it scored as “better”, leaving small spacing or token differences.

Legacy C/C++ projects shown as ANSI in Beyond Compare should write final fixed files as `gb18030`/GBK-compatible text. Otherwise a UTF-8 fixed file may display as Chinese mojibake when Beyond Compare opens it as ANSI.

GUI completion dialogs can be closed automatically:

```json
{
  "gui_auto_close_enabled": true,
  "faststone_pdf_complete_window_titles": [
    "FastStone Capture",
    "FastStone Editor"
  ],
  "faststone_pdf_complete_keys": [
    "{ENTER}"
  ],
  "bc_script_dialog_window_titles": [
    "Beyond Compare"
  ],
  "bc_script_dialog_keys": [
    "{ENTER}"
  ]
}
```

To test only the dialog closing behavior while a prompt is visible:

```powershell
python .\code_ocr.py close-dialogs
```

If FastStone is configured to save an intermediate image file before PDF conversion, use:

```json
{
  "capture_output_mode": "image_then_pdf",
  "capture_image_dir": "data/screenshots"
}
```
