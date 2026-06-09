from pathlib import Path
from tempfile import TemporaryDirectory

import code_ocr


def test_guess_logical_path() -> None:
    assert code_ocr.guess_logical_path(Path("src__main_cpp.pdf"), ".txt") == "src/main.cpp"
    assert code_ocr.guess_logical_path(Path("main.py.pdf"), ".txt") == "main.py"
    assert code_ocr.guess_logical_path(Path("main_py.pdf"), ".txt") == "main.py"
    assert code_ocr.pdf_output_name(Path("App_Test.cpp")) == "App_Test.cpp.pdf"
    assert code_ocr.pdf_output_name(Path("App_Test.cpp"), "App_Test.pdf") == "App_Test.pdf"
    assert code_ocr.parse_sendkeys_hotkey("^%{PRTSC}") == ([0x11, 0x12], 0x2C)
    assert code_ocr.parse_sendkeys_hotkey("^%r") == ([0x11, 0x12], ord("R"))
    assert code_ocr.parse_sendkeys_hotkey("^{F10}") == ([0x11], 0x79)
    assert code_ocr.modifier_vk_codes(["ctrl"]) == [0x11]


def test_clean_code() -> None:
    config = dict(code_ocr.DEFAULT_CONFIG)
    raw = "```python\n001 | def f（x）：\n002 |     return x\n```\nPage 1\n"
    assert code_ocr.clean_code(raw, config) == "def f(x):\n    return x\n"


def test_fix_code_ocr_markdown() -> None:
    config = dict(code_ocr.DEFAULT_CONFIG)
    raw = "\n".join(
        [
            "volatile int TimeCounter 25Oms = 0;",
            "IWDGReloadCounter;//comment",
            "GPIO InitStructure.GPIO PuPd = GPIO PuPd NOPULL;",
            "m_Alarm.Del( ALARM EEPROM_ERR );",
        ]
    )
    fixed, changes = code_ocr.fix_code_ocr_markdown(raw, config)
    assert "TimeCounter_250ms" in fixed
    assert "IWDG_ReloadCounter();" in fixed
    assert "GPIO_InitStructure.GPIO_PuPd = GPIO_PuPd_NOPULL;" in fixed
    assert "m_Alarm.Del(ALARM_EEPROM_ERR);" in fixed
    assert len(changes) == 4

    stable, stable_changes = code_ocr.fix_code_ocr_markdown("//====\nif(x >= y)\n", config)
    assert stable == "//====\nif(x >= y)\n"
    assert stable_changes == []


def test_extract_markdown_ignores_ids() -> None:
    payload = {
        "id": "pjb-not-markdown",
        "status": "PENDING",
        "file_id": "file-not-markdown",
    }
    assert code_ocr.LlamaParseClient._extract_markdown(payload) is None

    payload = {
        "job": {"id": "pjb-not-markdown", "status": "COMPLETED"},
        "markdown": {
            "pages": [
                {"page_number": 1, "success": True, "markdown": "# Parsed"},
                {"page_number": 2, "success": True, "markdown": "```c\nint main(void) {}\n```"},
            ]
        },
    }
    assert code_ocr.LlamaParseClient._extract_markdown(payload).startswith("# Parsed")


def test_reference_binary_detection() -> None:
    assert code_ocr.is_probably_binary(b"E-SafeNet\x00\x00LOCK\x00\x00\x00\x00")
    assert not code_ocr.is_probably_binary("int main(void) {}\n".encode("utf-16-le"))


def test_cli_mock_pipeline() -> None:
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        old_root = code_ocr.ROOT
        code_ocr.ROOT = root
        try:
            code_ocr.main(["init"])
            pdf_dir = root / "data" / "pdf"
            pdf_dir.mkdir(parents=True, exist_ok=True)
            (pdf_dir / "src__main_py.pdf").write_bytes(b"%PDF-1.4\n")
            code_ocr.main(["run", "--mock-ocr"])
            assert (root / "output" / "fixed" / "src" / "main.md").exists()
            assert (root / "output" / "reports" / "src_main.py.fix.json").exists()
            truth_dir = root / "data" / "reference" / "src"
            truth_dir.mkdir(parents=True, exist_ok=True)
            truth = truth_dir / "main.py"
            truth.write_text("def real():\n    return 42\n", encoding="utf-8")
            code_ocr.main(["align", "--task", "src/main.py"])
            fixed = (root / "output" / "fixed" / "src" / "main.md").read_text(encoding="utf-8")
            assert fixed == "def real():\n    return 42\n"
            report = root / "output" / "reports" / "src_main.py.truth.json"
            assert report.exists()
        finally:
            code_ocr.ROOT = old_root


def test_recover_one_mock_without_gui() -> None:
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        old_root = code_ocr.ROOT
        code_ocr.ROOT = root
        try:
            code_ocr.main(["init"])
            source_dir = root / "data" / "reference"
            source_dir.mkdir(parents=True, exist_ok=True)
            source = source_dir / "demo.c"
            source.write_text("int demo(void) { return 1; }\n", encoding="utf-8")
            pdf_dir = root / "data" / "pdf"
            pdf_dir.mkdir(parents=True, exist_ok=True)
            (pdf_dir / "demo.c.pdf").write_bytes(b"%PDF-1.4\n")
            code_ocr.main(["recover-one", str(source), "--no-capture", "--mock-ocr", "--no-bc"])
            assert (root / "output" / "fixed" / "demo.md").exists()
        finally:
            code_ocr.ROOT = old_root


if __name__ == "__main__":
    test_guess_logical_path()
    test_clean_code()
    test_fix_code_ocr_markdown()
    test_extract_markdown_ignores_ids()
    test_reference_binary_detection()
    test_cli_mock_pipeline()
    test_recover_one_mock_without_gui()
    print("smoke tests passed")
