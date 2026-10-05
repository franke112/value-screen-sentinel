"""Which ruling binds which step. THE ONE HAND-KEPT TABLE.

A ruling is placed on exactly one step -- the step where it binds -- or
listed as cross-cutting. `tests/test_playbook.py` holds that every
numbered entry in FRAMEWORK-EDITS.md is in one of the two, so a new
ruling fails the build's tests until someone places it. `ALSO` is a
see-also: a step that cites a ruling placed elsewhere, linking to its
home. It does not count as a placement.
"""

PLACEMENT: dict[str, tuple[str, ...]] = {
    "screen": ("E1", "E2", "E3", "E4", "E5", "E6", "E7", "E8", "E10", "E13",
               "E43", "E44", "E45", "E46", "E48", "E49", "E51", "E51.1",
               "E51.2", "E52", "E52.1", "E63", "E96", "E96.1", "E127",
               "B11", "B19", "B41", "B47", "B48"),
    "intake": ("E111", "B40"),
    "pipeline": ("E11", "E12"),
    "gate-1": ("B1", "B2", "B25"),
    "gate-2": (),
    "gate-3": ("B3", "B4", "B20", "B35", "E30", "E112", "E118", "E119", "E123",
               "E126"),
    "gate-4": ("B5", "E99"),
    "gate-5": (),
    "hard-kills": ("B7", "B9", "B10", "E9"),
    "conviction": ("B6", "B8", "B44", "B50"),
    "basis": ("E124", "E125", "E15", "E17", "E19", "E20", "E21", "E22", "E24", "E25", "E26",
              "E31", "E40", "E41", "E58", "E58.1", "E59", "E59.1", "E60",
              "E69", "E78", "E78.1", "E79", "E79.1", "E83", "E85", "E86",
              "E98", "E103", "E104", "E106", "E107", "E108", "E110", "E113",
              "B14", "B16", "B18", "B21", "B24", "B37", "B38", "B39", "B46"),
    "flow": ("E23", "E33", "E34", "E34.1", "E36", "E61", "E61.1", "E70",
             "E82", "E105", "E115", "E117", "E120", "B33"),
    "net-debt": ("E14", "E35", "E35.1", "E55", "E56", "E62", "E65", "E66",
                 "E67", "E68", "E68.1", "E68.2", "E71", "E72", "E73", "E74",
                 "E81", "E84", "E89", "E128", "E129", "B13", "B42", "B43"),
    "divisor": ("E16", "E18", "E38", "E53", "E54", "E75", "E75.1", "E80",
                "E88", "E91", "B15", "B17", "B36"),
    "growth-view": ("E109", "E95"),
    "strike": ("E28", "E29", "E32", "E37", "E39", "E87", "E94", "B23", "B26",
               "B34"),
    "tier-mbp": ("C2", "E76", "E77", "E90", "E100", "E101", "B22"),
    "verdict": ("E27",),
    "watch-priced": (),
    "watch-gated": ("B49",),
    "entry": ("C1",),
    "held": ("C4", "E42", "E102"),
    "exit": ("B45",),
    "dropped": (),
    "shadow-book": ("E114",),
    # the cycle
    "nightly": ("C3", "E47", "E97", "E121", "E122"),
    "checkin": (),
    "weekly-screen": ("E93", "E116"),
    "disclosure-watch": (),
    "refresh": ("E92",),
    "overview-page": ("F1", "F2"),
    "upkeep": (),
}

#: Rulings that bind no single step: they govern the file, the sessions or
#: the rebuild itself.
CROSS_CUTTING: tuple[str, ...] = ("A1", "A2", "A3", "D2")

#: See-also. Not a placement.
ALSO: dict[str, tuple[str, ...]] = {
    "watch-priced": ("E27", "E90", "E47"),
    "watch-gated": ("E27", "E92"),
    "dropped": ("E114", "E45"),
    "exit": ("C4", "E42", "C1"),
    "entry": ("E90", "E27", "E77"),
    "held": ("C1", "E100", "E92"),
    "intake": ("E12", "E109", "E76"),
    "pipeline": ("E93", "E111"),
    "gate-1": ("E11", "E12", "E63"),
    "gate-2": ("E30", "B9"),
    "gate-5": ("E92",),
    "conviction": ("E99", "E30"),
    "hard-kills": ("E30", "E45", "E79", "E83", "B46", "E119"),
    "strike": ("E19", "E20", "E90", "E109"),
    "growth-view": ("E28", "E94", "E111"),
    "tier-mbp": ("E28", "E29", "E99"),
    "screen": ("E93", "E97", "E12"),
    "nightly": ("E92", "E27", "E90"),
    "weekly-screen": ("E12", "E96", "E51"),
    "refresh": ("E104", "E103"),
    "upkeep": ("B45", "E114", "E49"),
    "checkin": ("E93",),
    "disclosure-watch": ("E92",),
    "verdict": ("E114", "E111", "E99"),
    "shadow-book": ("B45",),
}


def home_of(key: str) -> str | None:
    for step, keys in PLACEMENT.items():
        if key in keys:
            return step
    return None
