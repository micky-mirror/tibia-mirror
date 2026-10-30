import ast
import pathlib
import tkinter as tk


def test_custom_widgets_do_not_overwrite_tkinter_internals():
    """E.g. `self._name` is Tk's own name for a widget; replacing it breaks destroy()."""
    reserved = set(dir(tk.Canvas)) | set(dir(tk.Frame)) | {"_w", "_name", "children", "master"}
    clashes = []
    for path in (pathlib.Path(__file__).parent.parent / "tibia_mirror" / "ui").rglob("*.py"):
        for cls in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if not isinstance(cls, ast.ClassDef):
                continue
            if not {ast.unparse(b) for b in cls.bases} & {"tk.Canvas", "tk.Frame"}:
                continue
            for node in ast.walk(cls):
                if (
                    isinstance(node, ast.Attribute)
                    and isinstance(node.ctx, ast.Store)
                    and ast.unparse(node.value) == "self"
                    and node.attr in reserved
                ):
                    clashes.append(f"{path.name}:{node.lineno} {cls.name}.{node.attr}")
    assert clashes == []
