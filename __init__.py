import bpy
from bpy.app.handlers import persistent
from bpy.props import PointerProperty
from bpy.types import ID, FCurve, Object, Operator, Panel, PropertyGroup, ShapeKey
from bpy.utils import register_class, unregister_class


# region Parameters
class SP_parameters(PropertyGroup):
    full_mirror: bpy.props.BoolProperty(
        name="Full Shapekey Mirroring",
        description="Deletes shapekeys from the binded object if they aren't in the active object",
        default=True,
    )
    drivers_only: bpy.props.BoolProperty(
        name="Drivers only",
        description="Only adds drivers and nothing else",
        default=False,
    )


# endregion


# region Main Function
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

        SPPARAMETERS = target_object.data.spparameters
        if SPPARAMETERS.drivers_only:
            setup_shapekey_drivers(source_object, target_object)
            continue

        mirror_shape_keys(source_object, target_object)
        remove_leftover_shape_keys(source_object, target_object)
        mirror_shape_key_positions(source_object, target_object)
        mirror_shape_key_parameters(source_object, target_object)


# endregion


# region Utilities
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


def get_active_shape_key_index(source_object: Object, target_object: Object):
    index = target_object.data.shape_keys.key_blocks.find(source_object.active_shape_key.name)
    return index


def mirror_shape_key_parameters(source_object: Object, target_object: Object):
    if bpy.context.object.data == target_object.data:
        return

    # print(target_object, bpy.context.object)
    target_object.show_only_shape_key = source_object.show_only_shape_key
    target_object.active_shape_key_index = get_active_shape_key_index(source_object, target_object)


def mirror_shape_keys(source_object: Object, target_object: Object):
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


def create_driver(source_id: ID, target_id: ID, id_type: str, data_path: str, variable_name: str = "sb_bind"):
    driver = target_id.driver_add(data_path).driver
    driver.expression = variable_name
    if var := driver.variables.get(variable_name):
        driver.variables.remove(var)

    var = driver.variables.new()
    var.name = variable_name
    target = var.targets[0]
    target.id_type = id_type
    target.id = source_id
    target.data_path = f'key_blocks["{target_id.name}"].{data_path}'


def update_driver(source_id: ID, target_id: ID, driver: FCurve, data_path: str, variable_name: str = "sb_bind"):
    if not (var := driver.driver.variables.get(variable_name)):
        return

    target = var.targets[0]
    target.id = source_id
    target.data_path = f'key_blocks["{target_id}"].{data_path}'


def remove_driver(source_id: ID, target_id: ID, data_path: str, variable_name: str = "sb_bind"):
    if not (driver := target_id.animation_data.drivers.find(f'key_blocks["{source_id.name}"].{data_path}')):
        return

    if var := driver.driver.variables.get(variable_name):
        driver.driver.variables.remove(var)

    if not len(driver.driver.variables):
        target_id.animation_data.drivers.remove(driver)


# endregion


# region Operators
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


# endregion


# region UI
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


# endregion


# region Registration
def register():
    register_class(SP_parameters)
    register_class(OSB_OT_bind)
    register_class(OSB_OT_unbind)
    register_class(OSB_OT_purge)
    register_class(OSB_PT_mainpanel)

    bpy.app.handlers.depsgraph_update_post.append(bind_update)

    bpy.types.Mesh.spparameters = PointerProperty(type=SP_parameters, override={"LIBRARY_OVERRIDABLE"})


def unregister():
    del bpy.types.Mesh.spparameters

    bpy.app.handlers.depsgraph_update_post.remove(bind_update)
    unregister_class(SP_parameters)
    unregister_class(OSB_OT_bind)
    unregister_class(OSB_OT_unbind)
    unregister_class(OSB_OT_purge)
    unregister_class(OSB_PT_mainpanel)


if __name__ == "__main__":
    register()
# endregion
