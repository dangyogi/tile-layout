# settings.py

import app
from utils import read_yaml, write_yaml, backup_file
from plan import Plan


Settings_filename = "settings.yaml"

def read_settings(filename=Settings_filename):
    return init_settings(read_yaml(filename))

def init_settings(settings):
    for wall_name, ws in settings['wall_settings'].items():
        for plan_name, plan in ws['plans'].items():
            ws['plans'][plan_name] = Plan(plan_name, plan, wall_name, {})
    return settings

def dump(settings):
    def unpack_data(value):
        if isinstance(value, (tuple, list)):
            return [unpack_data(x) for x in value]
        if isinstance(value, dict):
            return {name: unpack(name, value) for name, value in value.items()}
        return value
    def unpack(name, value):
        if name == 'plans':
            #print("unpack plans")
            return {plan_name: plan.dump() for plan_name, plan in value.items()}
        #print("unpack data")
        return unpack_data(value)
    return {name: unpack(name, value)
            for name, value in settings.items()}

def save_settings(filename=Settings_filename):
    print("save_settings")
    backup_file(filename)
    write_yaml(dump(app.Settings), filename)



if __name__ == "__main__":
    import app
    from walls import read_walls
    from colors import read_colors

    app.Colors = read_colors()
    app.Walls = read_walls()

    from pprint import pp

    pp(dump(read_settings()))
