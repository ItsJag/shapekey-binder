import bpy
from bpy.types import Object

from .drivers import create_driver

def bind_shape_keys(source_object: Object, target_object: Object):
    source_shape_keys = source_object.data.shape_keys
    target_shape_keys = target_object.data.shape_keys

    if not getattr(target_shape_keys, "animation_data"):
        target_shape_keys.animation_data_create()

    setup_shapekey_drivers(source_object, target_object)


def setup_shapekey_drivers(source_object: Object, target_object: Object):
    source_shape_keys = source_object.data.shape_keys
    target_shape_keys = target_object.data.shape_keys

    if not getattr(target_shape_keys, "animation_data"):
        target_shape_keys.animation_data_create()

    create_driver(source_object, target_object, "OBJECT", "show_only_shape_key")

    target_drivers = target_shape_keys.animation_data.drivers
    for base_key in source_shape_keys.key_blocks:
        if not (target_key := target_shape_keys.key_blocks.get(base_key.name)):
            continue

        # Links the shapekey to a driver if no driver is found
        if target_drivers.find(f'key_blocks["{target_key.name}"].value'):
            continue

        # print(base_key, target_key)
        create_driver(source_shape_keys, target_key, "KEY", "value")  # type: ignore
