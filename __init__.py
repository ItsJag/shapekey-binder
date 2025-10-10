from .ops import register_ops, unregister_ops
from .props import register_props, unregister_props
from .ui import register_ui, unregister_ui
from .utils.binder import register_binder, unregister_binder


def register():
    register_props()
    register_ui()
    register_ops()
    register_binder()


def unregister():
    unregister_binder()
    unregister_props()
    unregister_ui()
    unregister_ops()


if __name__ == "__main__":
    register()
