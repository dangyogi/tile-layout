# settings.py

from utils import read_yaml, write_yaml, backup_file
from plan import Plan


Settings_filename = "settings.yaml"

def read_settings(filename=Settings_filename):
    return init_settings(read_yaml(filename))

def init_settings(settings):
    for wall_name, ws in settings['wall_settings'].items():
        for plan_name, plan in ws['plans'].items():
            ws['plans'][plan_name] = Plan(plan_name, plan, wall_name)
    return settings

def dump(settings):
    return {name: ([plan.dump() for plan in value] if name == 'plans' else value)
            for name, value in settings.items()}

def save_settings(filename=Settings_filename):
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
