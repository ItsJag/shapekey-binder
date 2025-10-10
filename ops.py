import bpy
from bpy.types import Operator
from bpy.utils import register_class, unregister_class

from .utils.binder import bind_update, get_binded_objects
from .utils.drivers import remove_driver


class OSB_OT_bind(Operator):
    """Binds the selected meshes to the active one"""

    @classmethod
    def poll(cls, context):
        if len(bpy.context.selected_objects) <= 1:
            cls.poll_message_set("Select more than one object.")
            return False

        return True

    bl_idname = "osb.bind"
    bl_label = "Bind Selected to Active"
    bl_description = "Binds the selected meshes to the active one"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        active_mesh = bpy.context.object
        selected_meshes = bpy.context.selected_objects

        for object in selected_meshes:
            if object.type != "MESH":
                continue
            if not object.data:
                continue
            if object == active_mesh:
                continue

            object.data["sp_binded_object"] = active_mesh

        bind_update(self, context)
        self.report({"INFO"}, "Objects binded!")

        return {"FINISHED"}


class OSB_OT_unbind(Operator):
    """Unbinds the selected meshes"""

    bl_idname = "osb.unbind"
    bl_label = "Unbind Selected Objects"
    bl_description = "Unbinds the selected meshes"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        selected_meshes = bpy.context.selected_objects

        for object in selected_meshes:
            if not object.data:
                continue
            if not object.data.get("sp_binded_object"):
                continue

            del object.data["sp_binded_object"]

            # Clears shapekey drivers
            target_shape_keys = object.data.shape_keys
            for target_key in target_shape_keys.key_blocks:
                remove_driver(target_key, target_shape_keys, "value")  # type: ignore

        return {"FINISHED"}


class OSB_OT_purge(Operator):
    """Purges all binded objects"""

    bl_idname = "osb.purge"
    bl_label = "Purge All Binded Objects"
    bl_description = "Unbinds all binded objects"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        binded_objects = get_binded_objects()

        for object in binded_objects:
            if not object.data:
                continue
            if not object.data.get("sp_binded_object"):
                continue

            del object.data["sp_binded_object"]

            if object.type != "MESH":
                continue

            # Clears shapekey drivers
            target_shape_keys = object.data.shape_keys
            for target_key in target_shape_keys.key_blocks:
                remove_driver(target_shape_keys, target_key, "value")  # type: ignore

        return {"FINISHED"}


def register_ops():
    register_class(OSB_OT_bind)
    register_class(OSB_OT_unbind)
    register_class(OSB_OT_purge)


def unregister_ops():
    unregister_class(OSB_OT_bind)
    unregister_class(OSB_OT_unbind)
    unregister_class(OSB_OT_purge)
