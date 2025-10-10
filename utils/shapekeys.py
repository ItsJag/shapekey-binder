import bpy
from bpy.types import Object, ShapeKey

from .drivers import create_driver, remove_driver


def get_active_shape_key_index(source_object: Object, target_object: Object):
    index = target_object.data.shape_keys.key_blocks.find(source_object.active_shape_key.name)
    return index


def mirror_shape_key_parameters(source_object: Object, target_object: Object):
    if bpy.context.object.data == target_object.data:
        return

    # print(target_object, bpy.context.object)
    target_object.show_only_shape_key = source_object.show_only_shape_key
    target_object.active_shape_key_index = get_active_shape_key_index(source_object, target_object)


def remove_leftover_shape_keys(source_object: Object, target_object: Object):
    SPPARAMETERS = source_object.data.spparameters
    source_shape_keys = source_object.data.shape_keys
    target_shape_keys = target_object.data.shape_keys
    target_drivers = target_shape_keys.animation_data.drivers

    # Remove shapekeys that no longer exist in the base object
    for target_key in target_shape_keys.key_blocks:
        if not getattr(target_shape_keys, "animation_data"):
            target_shape_keys.animation_data_create()

        if not source_shape_keys.key_blocks.get(target_key.name):
            if SPPARAMETERS.full_mirror:
                target_object.shape_key_remove(target_key)

            elif target_drivers.find(f'key_blocks["{target_key.name}"].value'):
                target_object.shape_key_remove(target_key)


def mirror_shape_key_positions(source_object: Object, target_object: Object):
    if bpy.context.object.data == target_object.data:
        return

    source_shape_keys = source_object.data.shape_keys
    target_shape_keys = target_object.data.shape_keys
    for target_key in target_shape_keys.key_blocks:
        if not (source_key := source_shape_keys.key_blocks.get(target_key.name)):
            continue

        target_index = target_shape_keys.key_blocks.find(target_key.name)
        source_index = source_shape_keys.key_blocks.find(source_key.name)
        if source_index != target_index:
            move_shape_key(target_object, target_key, source_index)


# Thanks to Cirno, extremely intelligent approach (that i don't understand)
# https://blenderartists.org/t/reorder-bpy-prop-collection-data-shape-keys-key-blocks/1215584
def move_shape_key(object: Object, shape_key: ShapeKey, target_index: int):
    shape_keys = object.data.shape_keys
    index_shape_key = shape_keys.key_blocks[target_index]

    shape_key_data = [vertex.co.copy() for vertex in shape_key.data]
    index_data = [vertex.co.copy() for vertex in index_shape_key.data]

    for index, vertex in enumerate(shape_key.data):
        vertex.co = index_data[index]
    for index, vertex in enumerate(index_shape_key.data):
        vertex.co = shape_key_data[index]

    # print(shape_key.name, index_shape_key.name)
    if shape_keys.animation_data.drivers.find(f'key_blocks["{shape_keys.name}"].value'):
        create_driver(shape_keys, index_shape_key, "KEY", "value")  # type: ignore
    else:
        remove_driver(index_shape_key, shape_keys, "value")  # type: ignore

    shape_key_name = shape_key.name
    index_shape_key_name = index_shape_key.name
    index_shape_key.name = "_temp_name"

    shape_key.name = index_shape_key_name
    index_shape_key.name = shape_key_name


def bind_shape_keys(source_object: Object, target_object: Object):
    source_shape_keys = source_object.data.shape_keys
    target_shape_keys = target_object.data.shape_keys

    if not getattr(target_shape_keys, "animation_data"):
        target_shape_keys.animation_data_create()

    # Creates new shapekeys from the base object onto the binded object
    for base_key in source_shape_keys.key_blocks:
        if not target_shape_keys.key_blocks.get(base_key.name):
            target_object.shape_key_add(name=base_key.name, from_mix=False)

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
