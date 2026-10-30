"""The .exe leaves some modules out, so the app must start without them."""

import ast
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).parent.parent
SPEC = ROOT / "Tibia Mirror.spec"


def get_excluded_modules():
    """The names in the `excludes` list of the spec."""
    tree = ast.parse(SPEC.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.keyword) and node.arg == "excludes":
            return [
                item.value
                for item in ast.walk(node.value)
                if isinstance(item, ast.Constant) and isinstance(item.value, str)
            ]
    raise AssertionError("the spec has no excludes list")


def test_the_excluded_modules_are_read_from_the_spec():
    assert {"socket", "_socket", "ssl", "typing_extensions"} <= set(get_excluded_modules())


def test_the_app_imports_without_the_modules_the_exe_leaves_out():
    blocked = get_excluded_modules()
    code = f"import sys\nsys.modules.update(dict.fromkeys({blocked!r}))\nimport tibia_mirror.app\n"

    result = subprocess.run([sys.executable, "-c", code], cwd=ROOT, capture_output=True, text=True)

    assert result.returncode == 0, result.stderr
