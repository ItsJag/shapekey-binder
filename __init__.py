from .ops import register_ops, unregister_ops
from .ui import register_ui, unregister_ui


def register():
    register_ui()
    register_ops()


def unregister():
    unregister_ui()
    unregister_ops()


if __name__ == "__main__":
    register()
