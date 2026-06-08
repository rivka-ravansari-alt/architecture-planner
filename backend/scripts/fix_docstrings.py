"""Remove docstrings accidentally placed inside function signatures."""

from __future__ import annotations

import re
from pathlib import Path

SIGNATURE_DOCSTRING = re.compile(r"\n\s+\"\"\"[^\"]*\"\"\"\s*\n")


def fix_content(text: str) -> str:
    return SIGNATURE_DOCSTRING.sub("\n", text)


def main() -> None:
    root = Path(__file__).resolve().parents[1] / "app"
    for path in root.rglob("*.py"):
        original = path.read_text(encoding="utf-8")
        fixed = fix_content(original)
        if fixed == original:
            continue
        path.write_text(fixed, encoding="utf-8")
        print(f"fixed {path.relative_to(root.parent)}")


if __name__ == "__main__":
    main()
