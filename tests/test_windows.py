import ast
import pathlib

UI = pathlib.Path(__file__).parent.parent / "tibia_mirror" / "ui"


def calls(tree):
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            yield node


def is_toplevel(call):
    return ast.unparse(call.func) == "tk.Toplevel"


def is_close_handler(call):
    """keep_open(win), or win.protocol("WM_DELETE_WINDOW", ...)."""
    name = ast.unparse(call.func)
    if name == "keep_open":
        return True
    first = call.args[0] if call.args else None
    return (
        name.endswith(".protocol")
        and isinstance(first, ast.Constant)
        and first.value == "WM_DELETE_WINDOW"
    )


def test_every_extra_window_handles_a_close_request():
    """Tk's default for a close request (Alt+F4) destroys the window behind the app's back."""
    missing = []
    for path in sorted(UI.rglob("*.py")):
        for cls in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if not isinstance(cls, ast.ClassDef):
                continue
            windows = sum(is_toplevel(call) for call in calls(cls))
            handlers = sum(is_close_handler(call) for call in calls(cls))
            if windows > handlers:
                missing.append(f"{path.name}: {cls.name} creates {windows}, handles {handlers}")
    assert missing == []
