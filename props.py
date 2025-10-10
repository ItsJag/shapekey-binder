import bpy
from bpy.props import BoolProperty, PointerProperty
from bpy.types import PropertyGroup
from bpy.utils import register_class, unregister_class


class SP_parameters(PropertyGroup):
    full_mirror: BoolProperty(
        name="Full Shapekey Mirroring",
        description="Deletes shapekeys from the binded object if they aren't in the active object",
        default=True,
    )
    drivers_only: BoolProperty(
        name="Drivers Only",
        description="Only adds drivers and nothing else",
        default=False,
    )


def register_props():
    register_class(SP_parameters)

    bpy.types.Mesh.spparameters = PointerProperty(type=SP_parameters, override={"LIBRARY_OVERRIDABLE"})


def unregister_props():
    unregister_class(SP_parameters)

    del bpy.types.Mesh.spparameters
