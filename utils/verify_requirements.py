import ast
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def gather_imports(file_path: Path):
    with file_path.open("r") as f:
        tree = ast.parse(f.read(), filename=str(file_path))
    packages = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                packages.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.level == 0 and node.module:
                packages.add(node.module.split(".")[0])
    return packages


def load_requirements(req_file: Path):
    pkgs = set()
    with req_file.open() as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            pkgs.add(line.split("==")[0].split(">=")[0])
    return pkgs


def main():
    imports = set()
    for py_file in REPO_ROOT.rglob("*.py"):
        if py_file.name == "verify_requirements.py" or "venv" in py_file.parts:
            continue
        imports.update(gather_imports(py_file))

    requirements = load_requirements(REPO_ROOT / "requirements.txt")
    missing = sorted(pkg for pkg in imports if pkg not in requirements)
    if missing:
        print("Missing packages:", ", ".join(missing))
        sys.exit(1)
    print("All imported packages are present in requirements.txt")


if __name__ == "__main__":
    main()
