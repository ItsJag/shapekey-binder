import bpy
from bpy.app.handlers import persistent
from bpy.types import Object

from .shapekeys import (
    bind_shape_keys,
    mirror_shape_key_parameters,
    mirror_shape_key_positions,
    remove_leftover_shape_keys,
    setup_shapekey_drivers,
)


def get_binded_objects() -> list[Object]:
    binded_objects = []
    for object in bpy.data.objects:
        if not object.data:
            continue
        if not object.data.get("sp_binded_object"):
            continue
        if binded_objects.count(object):
            continue

        binded_objects.append(object)

    return binded_objects


@persistent
def bind_update(self, context):
    if not (binded_objects := get_binded_objects()):
        return
    active_object = bpy.context.object

    for target_object in binded_objects:
        if target_object.type != "MESH":
            # Shouldn't happen, but just in case
            binded_objects.remove(target_object)
            continue
        if active_object == target_object:
            continue
        source_object = target_object.data.get("sp_binded_object")
        if not source_object:
            continue

        if not getattr(source_object.data, "shape_keys"):
            continue
        # Adds shapekey data if it doesn't exist already
        if not getattr(target_object.data, "shape_keys"):
            target_object.shape_key_add(name="Basis", from_mix=False)

        SPPARAMETERS = source_object.data.spparameters
        if SPPARAMETERS.drivers_only:
            setup_shapekey_drivers(source_object, target_object)
            continue

        bind_shape_keys(source_object, target_object)
        remove_leftover_shape_keys(source_object, target_object)
        mirror_shape_key_positions(source_object, target_object)
        mirror_shape_key_parameters(source_object, target_object)


def register_binder():
    bpy.app.handlers.depsgraph_update_post.append(bind_update)


def unregister_binder():
    bpy.app.handlers.depsgraph_update_post.remove(bind_update)
