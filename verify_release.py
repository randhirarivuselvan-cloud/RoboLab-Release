from pathlib import Path
import ast

ROOT = Path(__file__).resolve().parent
required = [
    ROOT / "main.py", ROOT / "requirements.txt", ROOT / ".env.example",
    ROOT / "render.yaml", ROOT / "README.md", ROOT / "static" / "index.html",
    ROOT / "static" / "style.css", ROOT / "static" / "app.js",
]
for path in required:
    assert path.exists(), f"Missing: {path.relative_to(ROOT)}"

ast.parse((ROOT / "main.py").read_text(encoding="utf-8"))
import main

assert main.app.version == "2.1.0"
assert main.project_plan("line following robot under 3000", 3000)["within_budget"]
assert main.project_plan("line following robot under 3000", 3000)["items"][0]["id"] == "arduino-uno"
assert main.project_plan("quadruped robot")["items"]
print("RoboLab release verification: PASS")
