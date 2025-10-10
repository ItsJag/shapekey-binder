import bpy
from bpy.types import Object


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
