# tile-layout
Crude program to help with ceramic tile layout.

This directly supports fractional numbers to make measurements in inches easier.

## Expression Syntax:

Spaces are required on either side of all binary operators so they don't get confused with
unary operators or fractions.

Spaces are prohibited following unary operators.

Parenthesis are currently unsupported.

fraction: `-? <integer> | -? <integer>.<integer>/<integer> | -? <integer>/<integer>`

num: `-? <constant_name> | -? !<integer> | <fraction> | -? <name> (\. <name>)*`

  No spaces are allowed in numbers.  The ! operator is square-root.

term: `num ([*/] num)*`

exp: `term ([-+] term)*`

pair: `exp (, exp)?`

## Files:

### colors.csv

Columns: Name, value (can be any TK color value)

Reader: colors.read_colors(filename='colors.csv') -> \{name: value\}

### shapes.yaml

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
