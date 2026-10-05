"""The decision playbook generator.

`tools/build_playbook.py` renders `docs/playbook/`: one HTML file per step
of the chain, one per name, an index that is the funnel as navigation, a
rulings page and a git-log page. Everything on those pages is read from
the repository's own sources at build time -- FRAMEWORK.md, FRAMEWORK-
EDITS.md, the watchlist, the reports and reference files, the CLI's own
argparse help, the git log -- and nothing is composed by the generator:
where a verdict appears it is the owner's, quoted.

Modules:
    sources    parsers for every input
    placement  which ruling binds which step (the one hand-kept table)
    steps      the step list: the chain and the cycle
    render     HTML, CSS and the small script
"""
