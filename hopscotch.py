# hopscotch.py


Pattern = (  # B corner, matching A corner, B -> A X offset, B -> A Y offset
    ("ul", "ur", -1, 0),
    ("ur", "lr", 0, 1),
    ("ll", "ul", 0, -1),
    ("lr", "ll", 1, 0),
)

def hopscotch(tile_a, tile_b, grout_gap, angle, max_x, max_y):
    def spread_a(placement_b, depth=0):
        #print(f"{' ' * depth}spread_a({placement_b})")
        if placement_b is not None:
            for b_corner, a_corner, delta_x, delta_y in Pattern:
                spread_b(tile_a.place_at(a_corner,
                                         placement_b.at(b_corner,
                                                        delta_x * grout_gap,
                                                        delta_y * grout_gap),
                                         angle, 0, 0, max_x, max_y),
                         depth + 1)
    def spread_b(placement_a, depth=0):
        #print(f"{' ' * depth}spread_b({placement_a})")
        if placement_a is not None:
            for b_corner, a_corner, delta_x, delta_y in Pattern:
                spread_a(tile_b.place_at(b_corner,
                                         placement_a.at(a_corner,
                                                        -delta_x * grout_gap,
                                                        -delta_y * grout_gap),
                                         angle, 0, 0, max_x, max_y),
                         depth + 1)
    spread_b(tile_a.place_at("ll", (0, 0), angle, 0, 0, max_x, max_y))

