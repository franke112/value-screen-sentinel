"""The book's order, its reading routes and the old addresses (2026-11-09).

The redesign of 2026-11-09: a prologue with the story of the tests, Part
One as the method stands now, the tests chapter in the middle, Part Two cut
from nine chapters to four, and the close. The nine old machine chapters
stay in content2*.py as a library of sections; content3.py assembles the
new chapters out of them, so the prose of both languages is kept and no
section is retyped.

Chapter numbers are never written in the text: a reference is the token
[[ch:slug]] ("chapter 14"), [[Ch:slug]] ("Chapter 14") or [[n:slug]]
("14"), resolved at build time, so the next reordering cannot leave a
wrong number behind.
"""

#: (part key, slugs in order). The prologue carries no chapter number.
PARTS = [
    ("prologue", ["prologue"]),
    ("part1", ["01-the-problem", "02-value", "03-this-project", "04-the-screen",
               "05-refusal", "06-what-gets-read", "07-reverse-dcf",
               "08-pre-registration", "09-three-outcomes", "10-the-funnel",
               "11-the-decision", "12-shadow-book"]),
    ("tests", ["tested"]),
    ("part2", ["machine-reads", "machine-watches", "bug-museum", "limits"]),
    ("close", ["close"]),
]

UNNUMBERED = {"prologue"}

#: Old slugs that keep their content under a new address.
RENAMED = {"22-limits": "limits", "23-close": "close"}

#: Two routes through the book beside the ten-minute page. A chapter may be
#: on both; the prologue and the close are.
ROUTES = {
    "investor": ["prologue", "01-the-problem", "02-value", "04-the-screen",
                 "05-refusal", "07-reverse-dcf", "08-pre-registration",
                 "11-the-decision", "12-shadow-book", "tested", "close"],
    "builder": ["prologue", "03-this-project", "06-what-gets-read",
                "09-three-outcomes", "10-the-funnel", "machine-reads",
                "machine-watches", "bug-museum", "limits", "close"],
}

#: Every address the old book had that is gone, and where its content went.
#: Each gets a one-line page that sends the reader on.
REDIRECTS = {
    "13-why-a-machine": "machine-reads",
    "14-the-pieces": "machine-reads",
    "15-the-record": "machine-reads",
    "16-the-rules-file": "machine-reads",
    "17-the-nightly-run": "machine-watches",
    "18-dead-mans-switch": "machine-watches",
    "19-the-phone": "machine-watches",
    "20-the-boundary": "limits",
    "21-the-page": "machine-watches",
    "22-limits": "limits",
    "23-close": "close",
}


def ordered_slugs():
    return [slug for _, slugs in PARTS for slug in slugs]


def part_of(slug):
    return next(key for key, slugs in PARTS if slug in slugs)
