# tile-layout
Crude program to help with ceramic tile layout.

This directly supports fractional numbers to make measurements in inches easier.

## Files:

### colors.csv

Columns: Name, value (can be any TK color value, e.g., blue or #123456)

Reader: colors.read_colors(filename='colors.csv') -> \{name: value\}

### shapes.yaml

    <name>:
        type: <shape_type>
        parameters: [<name>]
        constants:
            name: <exp>
        points:
            - pair
        flipped:
            shape: <name>
            arguments: [<exp>]
        skip_x: <exp>
        skip_y: <exp>
        is_rect: true|false

For shape_types, only polygon is currently accepted.

is_rect defaults to false.

### tiles.yaml

    <name>:
        shape: <name>
        <shape param>: <exp>
        color: <color>
        image: <filename>

Reader: tiles.read_tiles(colors, filename="tiles.csv") -> \{name: tile\}

### walls.yaml

    <name>:
        grout: [<width>, <height>]
        constants:
            name: <exp>
        <panel name>:
            pos: [<x>, <y>]
            size: [<width>, <height>] or <diameter>
            color: <color>
            image: <filename>
            skip: true|false

### layouts.yaml

    <name>:
        description: <string>
        parameters: [<name>]
        defaults:
            <param name>: <exp>
        <step>

### step

All steps may use the following tags:

    name: step_name
    trace: [<trace_flag>]
    index_by_counter: <name>
    constants:
        <name>: <exp>
    type: <step type>
    offset: [<x>, <y>]
    delta: [<x>, <y>]
    delta_x: <x>
    delta_y: <y>

Only type is required.

#### Built-in step types:

    place
        tile:
        angle:

    sequence:
        steps:
            - <step>

    Each step may include skip: <exp>.

    repeat:
        step: <step>
        start: [<x>, <y>]
        increment: [<x>, <y>]
        times: <exp>
        step_width_limit: <exp>
        step_height_limit: <exp>
        index_start: <exp>

    section:
        pos: [<x>, <y>]
        size: [<width>, <height>]
        <plan>

    For <plan>, see plans in settings.yaml, excluding grout_color.

#### Layout step types:

    type: <layout name>
    trace: [<trace_flag>]
    <param>: <exp>

### settings.yaml

    default_wall: <wall name>
    wall_settings:
        <wall name>:
            default_plan: <plan name>
            plans:
                <plan name>:
                    alignment:
                        angle: <exp>
                        x_offset: <exp>
                        y_offset: <exp>
                    grout_color: <color>
                    grout_gap: <exp>
                    layout: <step>

