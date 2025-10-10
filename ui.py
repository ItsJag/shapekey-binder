import bpy
from bpy.types import Panel
from bpy.utils import register_class, unregister_class


class OSB_PT_mainpanel(Panel):
    bl_label = "Shapekey Binder"
    bl_description = ""
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "data"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        object = bpy.context.object
        col = layout.column(align=True)
        col.operator("osb.bind")
        col.operator("osb.unbind")
        col.operator("osb.purge")

        if not bpy.context.object:
            return
        if not bpy.context.object.type == "MESH":
            return

        SPPARAMETERS = object.data.spparameters

        col.prop(SPPARAMETERS, "full_mirror")
        col.prop(SPPARAMETERS, "drivers_only")

        if bpy.context.object.data.get("sp_binded_object"):
            box = layout.box()
            box.label(text=f"Binded to: {bpy.context.object.data.get('sp_binded_object').name}")


def register_ui():
    register_class(OSB_PT_mainpanel)


def unregister_ui():
    unregister_class(OSB_PT_mainpanel)
