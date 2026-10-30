import ast
import importlib
import inspect
import pkgutil
import textwrap
import tkinter as tk

import tibia_mirror

# Fields Tk gives a widget while it runs; they are not written in its classes.
TK_FIELDS = {"_w", "_name", "tk", "master", "children", "widgetName", "_tclCommands", "_tkloaded"}


def get_widget_classes():
    """Every Tk widget class written in the app."""
    classes = []
    for module_info in pkgutil.walk_packages(tibia_mirror.__path__, "tibia_mirror."):
        if module_info.name == "tibia_mirror.__main__":
            continue  # importing it starts the app
        module = importlib.import_module(module_info.name)
        for _, cls in inspect.getmembers(module, inspect.isclass):
            if cls.__module__ == module.__name__ and issubclass(cls, tk.Misc):
                classes.append(cls)
    return classes


def get_tk_names(cls):
    """Every name Tk uses on a widget of this class."""
    tk_bases = [base for base in cls.__mro__ if base.__module__ == "tkinter"]
    return TK_FIELDS.union(*(vars(base) for base in tk_bases))


def get_set_fields(cls):
    """The names of every `self.<name> = ...` in the class."""
    tree = ast.parse(textwrap.dedent(inspect.getsource(cls)))
    return {
        node.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Attribute)
        and isinstance(node.ctx, ast.Store)
        and ast.unparse(node.value) == "self"
    }


def test_widget_classes_are_found():
    names = {cls.__name__ for cls in get_widget_classes()}

    assert {"AppWindow", "NameDialog", "NewRegionOverlay", "RowCard"} <= names


def test_custom_widgets_do_not_overwrite_tkinter_internals():
    """E.g. `self._name` is Tk's own name for a widget; replacing it breaks destroy()."""
    clashes = [
        f"{cls.__name__}.{name}"
        for cls in get_widget_classes()
        for name in sorted(get_set_fields(cls) & get_tk_names(cls))
    ]

    assert clashes == []
