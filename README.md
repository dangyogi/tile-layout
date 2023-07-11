# tile-layout

Crude program to help with ceramic tile layout.

This directly supports fractional numbers to make measurements in inches easier.

## Files:

### colors.csv

Defines the colors available for grout colors and tile colors.  These are in
addition to the standard TK colors.

The colors.csv in the repository may not be that useful to you, depending on
what grout company and tile company you use.

    Columns:
        name,value

    value can be any TK color value, e.g., blue or #123456.

Reader: colors.read_colors(filename='colors.csv') -> \{name: value\}

### shapes.yaml

This file defines the various shapes that tiles may have.

The shapes.yaml in the repository may define all that you need.

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

For <shape_types>, only polygon is currently accepted.

is_rect defaults to false.

### tiles.yaml

This defines all of the tiles available to make patterns out of.  Each tile
has either a uniform color or an image.  Images are only currently supported
for square and rectangular tiles.

The tiles.yaml in the repository probably has some useful tiles for your project,
but also probably has many useless tiles.  You'll need to modify it to include
what tiles you might use.

    <name>:
        shape: <name>
        <shape param>: <exp>
        color: <color>
        image: <filename>

Reader: tiles.read_tiles(colors, filename="tiles.csv") -> \{name: tile\}

### walls.yaml

This file defines the walls the you need to tile.  These could also be other
surfaces (e.g., floors).

The walls.yaml file in the repository would only serve as an example
for other tiling projects.  You'll need to replace this with definitions of
your own walls (or floors).

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

    The panels define any area that must be tiled around.  These may be
    cabinets, windows, outlets, etc.  They always appear on top of any
    tile patterns.

### layouts.yaml

The layouts.yaml file defines tile patterns (i.e., "layouts") that your
settings.yaml file can refer to, much like calling a function in a programming 
language.

The layouts.yaml file in the repository includes many patterns that should be
useful to everybody.  You may not need to add anything to this.

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

Only type is required here.  But each type has additional tags.

#### Built-in step types:

To place one tile:

    place
        tile:
        angle:

    angle defaults to 0.

To compose a step out of a sequence of smaller steps:

    sequence:
        steps:
            - <step>

    Each step may include skip: <exp>.  The step is skipped if skip is true.
    This allows for alternative "plan A"/"plan B" steps within a sequence.

To repeat a step (either horizontally, or vertically, or at an angle):

    repeat:
        step: <step>
        start: [<x>, <y>]
        increment: [<x>, <y>]
        times: <exp>
        step_width_limit: <exp>
        step_height_limit: <exp>
        index_start: <exp>

    Only step and increment are required.

    times defaults to None (meaning infinite in both directions).

    To cover a wall with repeat, you need to use it twice at two
    levels:

        - an inner repeat that repeats horizontally to make a row of tiles.
        - and an outer repeat that repeats the above repeat
          vertically to fill the wall.

To divide the wall into sections, such that each section is 
individually cropped.

Note, this looks a bit crude on the screen due to TK limitations...

    section:
        pos: [<x>, <y>]
        size: [<width>, <height>]
        <plan>

    For <plan>, see plans in settings.yaml, excluding grout_color.

#### Layout step types:

This is how you use a layout, from layouts.yaml, as a step in larger plan. 

    type: <layout name>
    trace: [<trace_flag>]
    <param>: <exp>

### settings.yaml

This defines the various "plans" to tile each wall in the walls.yaml file.

The settings.yaml file in the repository would only serve as an example
for other tiling projects.  You'll need to replace this with your own plans
for your own walls.

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

