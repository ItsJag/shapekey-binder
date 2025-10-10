from bpy.types import ID, FCurve


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
