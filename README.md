# tile-layout
Crude program to help with ceramic tile layout.

This directly supports fractional numbers to make measurements in inches easier.

## Expression Syntax:

fraction
: `-? <integer> | -? <integer>.<integer>/<integer> | -? <integer>/<integer>`

num
: `-? <constant_name> | -? !<integer> | <fraction>`

  No spaces are allowed in numbers.  The ! operator is square-root.

term
: `num ((' * '|' / ') num)*`
  Spaces are required on either side of * and / so they don't get confused with fractions.
  Notice, there are no parenthesis to group + or - within * or /.

exp
: `term ([-+] term)*`

pair
: `exp (, exp)?`

## Files:

### colors.csv

Columns: Name, value (can be any TK color value)

Reader: colors.read_colors(filename='colors.csv') -> \{name: value\}

### shapes.yaml

|
name:
    type: polygon
    parameters: name (, name)*
    constants:
        name: exp
    points:
        - pair

### tiles.yaml

Reader: tiles.read_tiles(colors, filename="tiles.csv") -> \{name: tile\}

### walls.yaml
