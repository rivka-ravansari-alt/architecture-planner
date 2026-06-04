from pathlib import Path

css_path = Path(__file__).resolve().parent.parent / "src" / "styles.css"
css = css_path.read_text(encoding="utf-8")
out = css_path.parent / "styles"
out.mkdir(exist_ok=True)

sections = {
    "base.css": (0, css.find("/* App shell")),
    "login.css": (css.find("/* App shell"), css.find(".app-shell {")),
    "layout.css": (css.find(".app-shell {"), css.find("/* Architecture document workspace")),
    "document.css": (
        css.find("/* Architecture document workspace"),
        css.find("/* Notice shown when inputs"),
    ),
    "wizard.css": (css.find("/* Notice shown when inputs"), css.find("/* Cards")),
    "forms.css": (css.find("/* Cards"), css.find("/* Mermaid architecture diagram")),
    "diagrams.css": (
        css.find("/* Mermaid architecture diagram"),
        css.find("/* Tables (AWS pricing style)"),
    ),
    "tables.css": (css.find("/* Tables (AWS pricing style)"), css.find("/* Misc")),
    "misc.css": (css.find("/* Misc"), len(css)),
}

for name, (start, end) in sections.items():
    chunk = css[start:end].strip()
    if chunk:
        (out / name).write_text(chunk + "\n", encoding="utf-8")

imports = "\n".join(f'@import "./{name}";' for name in sections)
(out / "index.css").write_text(imports + "\n", encoding="utf-8")
print("CSS split complete")
