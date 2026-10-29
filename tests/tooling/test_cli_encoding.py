"""The public CLI emits readable UTF-8 even under a legacy Windows locale."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def test_cli_preserves_unicode_when_inherited_output_encoding_is_cp1252(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("# Урок\n", encoding="utf-8")
    (tmp_path / "test_unit.py").write_text("", encoding="utf-8")
    (tmp_path / "curriculum.toml").write_text(
        '[[items]]\nid="unicode"\ntitle="Урок: оценка модели"\nkind="lesson"\n'
        'readme="README.md"\ntests=["test_unit.py"]\n',
        encoding="utf-8",
    )
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "from pathlib import Path; from roadmap_tools.cli import main; "
            "import sys; raise SystemExit(main(['list'], Path(sys.argv[1])))",
            str(tmp_path),
        ],
        env={**os.environ, "PYTHONIOENCODING": "cp1252", "PYTHONUTF8": "0"},
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr.decode("utf-8", errors="replace")
    assert result.stdout.decode("utf-8").strip() == "unicode [lesson] Урок: оценка модели"
