"""Part Two — the machine. Chapters 13 to 23.

Same pedagogy as Part One: plain version first, the technical word once,
after it. Every fact about the system is read from the repository: the unit
files under deploy/, the module docstrings under vss/, and the rulings.
"""

from content1 import Notes, fold, decision, example, wrong, right, chapter
from diagrams import ALL as FIG

# ---------------------------------------------------------------------------
# 13. WHY THE METHOD NEEDED A MACHINE
# ---------------------------------------------------------------------------
N = Notes()
chapter(
    "13-why-a-machine", "Why the method needed a machine",
    "A method on paper decays: you forget, you drift, you re-argue a settled question the day a price moves. The machine's job is to measure and to remember. It is built, deliberately, not to decide.",
    7, True,
    f"""
<p>Everything in Part One could be done with a notebook. For a while it was. Here is what happens to a method that lives in a notebook.</p>

<p>You forget. Six names on a watchlist, each with a buy price and a stop, and on a Tuesday evening in March you do not remember which report you last valued NAME B on. You drift. The cushion was 25 percent, but this one is nearly there and you understand it well, so 22 would be fine, just this once. You re-argue. A price falls 8 percent in a day, and a question you settled in writing three weeks ago is suddenly open again, because now there is a stake in the answer. None of this is stupidity. It is what a person does with a rule when the person is tired, or excited, or has money on the line. Part One is a set of habits designed to be hard to bend, and habits are exactly what a person under pressure bends first.</p>

<p>So the method was given a machine: a small program on a rented server that runs every night, fetches the day's prices, compares them with the lines the owner has already written down, and reports. It remembers what the owner decided and when. It does not get excited.</p>

<h2>The governing principle</h2>
<p>The tool measures. The owner decides. That is the whole design, and it is enforced, not merely intended.</p>

{FIG["measure_decide"]()}

<p>What the machine may do is a short list of verbs. It may fetch prices and filings. It may compute a fixed set of figures. It may compare a price to a line. It may write a report and a page. It may point at a name that needs the owner's attention. It may say that a figure is missing. What it may never do is longer, and every item is written into the code as a refusal: it never writes a verdict, never enters a company into the process, never assigns a tier, never sets a value or a buy price or a stop, never moves a name from one status to another. In the tool's own summary, it computes market data only, and "everything requiring judgment is a MANUAL field you fill in by hand; the tool never computes, guesses, defaults or back-fills any of it."{N.ref("README. The scheduled screen 'may SNAPSHOT, RANK and REPORT; it never enters a name' (ruling E93). A refresh 'FETCHES, EXTRACTS and REPORTS; it never decides' (ruling E92). The price watch 'points once per crossing and writes nothing' (ruling E97). The page generator: 'this project's design is that the page measures and I decide.'")}</p>
{N.flush()}

<h2>Why the non-autonomous design is the harder one</h2>
<p>It would be easier to build a program that decides. Give it the rules and let it mark names as bought or refused; it would never get tired. It would also inherit every weakness of its author and add its own, and nobody would be able to tell which was which, because the decision and the measurement would be one thing.</p>

<p>Keeping them apart costs work at every layer. Each automated step is given its list of allowed verbs and a mechanical check that it did nothing else: the refresh command runs under an assertion that the owner's file was not touched; the scheduled screen is started without the one flag that would let it enter a name, and the unit that starts it cannot write to the folder the file lives in; the page generator runs under a test that takes a census of every file in the repository before and after and asserts not one byte moved.{N.ref("The assertion assert_no_watchlist_write in the refresh module; the absent --write-pipeline flag and the read-only config directory in the scheduled screen's unit; the census test on the overview generator, described in the project brief §4.7.")} A program that cannot decide has to be prevented from deciding at every point where deciding would be convenient.</p>
{N.flush()}

<p>There is a body of research on what happens when people work alongside automation, and its recurring finding is that people stop checking things the machine seems to have checked. The term is automation misuse: over-reliance that leads to monitoring failures.{N.ref("Parasuraman and Riley, 'Humans and Automation: Use, Misuse, Disuse, Abuse', Human Factors 39 (1997).")} A tool that renders a verdict invites exactly that. A tool that renders a distance and a list of what it could not check does the opposite: it hands the reader an unfinished job, every night, with the unfinished parts named.</p>
{N.flush()}

<p>The rest of Part Two is how that principle is built: how the pieces are separated, how the record is kept honest, how the rules stay above the code, what happens at half past ten every night, how the owner finds out when it does not happen, and how the result reaches a phone without opening a door into the machine.</p>

{decision(
    "The program measures and reports. Every decision is the owner's, made by hand, and the program is built so that it cannot make one even by accident.",
    "A method that decides inherits its author's biases and hides them inside the measurement. Separating the two keeps both checkable, and keeps the owner reading rather than trusting.",
    "Every allowed verb has to be fenced with a check that nothing else happened, at every layer. The owner does all the deciding, on every name, every time, and nothing about the machine makes that faster.",
)}
""",
    [
        ("Parasuraman and Riley (1997), Humans and Automation: Use, Misuse, Disuse, Abuse", "https://journals.sagepub.com/doi/10.1518/001872097778543886"),
        ("What each automated step may and may not do", "repo: README.md; reference/FRAMEWORK-EDITS.md E92, E93, E97; vss/refresh.py; vss/screenwatch.py; vss/overview.py"),
    ],
)

# ---------------------------------------------------------------------------
# 14. HOW THE PROGRAM IS PUT TOGETHER
# ---------------------------------------------------------------------------
N = Notes()
chapter(
    "14-the-pieces", "How the program is put together",
    "Seven kinds of piece and the walls between them. The interesting part is not what each piece does but what it is forbidden from doing.",
    9, False,
    f"""
<p>The program is a set of small parts, each with one job, and the design question was never "what should each part do" but "what must each part be unable to do". This chapter walks the parts as a picture and then names the walls. There is no code in it.</p>

{FIG["pieces_walls"]()}

<h2>The seven kinds of piece</h2>

<h3>Fetching: bringing figures in from outside</h3>
<p>One part fetches daily prices and keeps a copy on disk, so that when the price service is down the run has yesterday's figures marked as stale rather than nothing at all. Another reads the structured data American companies must file with their regulator. Two more read the Nordic exchanges' own disclosure feeds, which is where a Swedish or Norwegian company's reports actually appear. One reads a company's spreadsheet appendix through a map, committed with the code, that says which cell is which figure. One fetches a company's own report page and nothing else: it does not search, guess or follow links. And one hands a fetched document to a language model with a narrow instruction: pull out the stated figures and quote the sentence each came from; never derive, estimate or reconcile a figure, never decide whether something is material, never write prose.{N.ref("Module descriptions in vss/fetch.py, vss/xbrl.py, vss/nordic.py, vss/oslo.py, vss/appendix.py, vss/source.py and vss/extract.py; README on the extractor: it 'never derives, estimates or reconciles a figure, never decides materiality, and never writes prose.'")}</p>
{N.flush()}
<p>The forbidden thing, for every fetcher: it may not judge what it fetched. It brings a figure in with its origin attached, and stops.</p>

<h3>The record: keeping every figure</h3>
<p>One part writes one row per company per run into a small database, so the history can be rebuilt later. One keeps the run record for each valuation, the eight things that must be declared before a value may be printed (chapter 15). One keeps a snapshot of every screening run, the raw prices and the list of names, so the run can be replayed exactly. One holds hand-entered figures for companies no feed serves, each marked as checked or not. One tests whether a price series is a real measurement or a feed artefact.{N.ref("vss/store.py, vss/runrecord.py, vss/snapshot.py, vss/manual.py, vss/series_sanity.py.")}</p>
{N.flush()}
<p>The forbidden thing: the record never fills a gap. A figure that was not fetched is absent, and stays absent.</p>

<h3>Computing: the arithmetic, kept pure</h3>
<p>The parts that compute figures, apply the rules and solve the valuation do no input and no output. They do not read files, do not touch the network, and do not know what time it is; the date is always handed to them. This is a wall, not a convention: it means a computed figure can be reproduced later from the same inputs and will come out the same, because nothing in the computation could have depended on the world outside it.{N.ref("The rules module: 'This module performs ZERO I/O. No file access, no network, no logging, and deliberately no datetime.now().' The metrics module is the same, with the as-of date always passed in.")}</p>
{N.flush()}

<h3>Reporting: the report and the page</h3>
<p>One part writes the nightly report in a fixed order: when the run happened and how fresh the data was; then blockers, the things that stopped a judgement; then actions, the things that need the owner; then the full table of every name. Another generates the one-page overview that reaches the phone (chapter 21). A third assembles a research briefing for a name being read, which is a collection of the figures and their sources, not a view.{N.ref("vss/report.py, vss/overview.py, vss/briefing.py.")}</p>
{N.flush()}
<p>The forbidden thing: no report says buy, sell, or good. It says how far, how fresh, and what is missing.</p>

<h3>The screen</h3>
<p>The parts from chapter 4: the fixed list of names, the two filters, the ranking, and a wrapper that runs them on a Saturday morning. Plus one small part, and it is the only piece in the screener allowed to write into the owner's file: the one that enters a proposed name. It runs only when the owner starts it by hand.{N.ref("vss/screen.py, vss/filters.py, vss/universe.py, vss/ranking.py, vss/screenwatch.py; vss/pipeline.py is 'the only module in the screener that writes to the file holding the owner's live positions', and the scheduled unit is started without the flag that would invoke it.")}</p>
{N.flush()}

<h3>Watching</h3>
<p>Two parts. One watches the disclosure feeds for the names on the waiting lists and reports only three kinds of document: a periodic report, a change to the company's own forecast, a profit warning. Everything else the exchange publishes is rejected and the rejection printed. The other watches the prices of the screener's top twenty against an indicative level and points, once, when a price crosses it. The level is a distance from a rough value, not a buy line, and the ruling says so.{N.ref("vss/watch.py; vss/pricewatch.py, ruling E97: 'a distance, not a buy line'.")}</p>
{N.flush()}

<h3>The heartbeat</h3>
<p>One part whose only job is to make a run that did not happen look different from a run that had nothing to say. Chapter 18.</p>

<h3>The runner</h3>
<p>One part ties the nightly run together: load the owner's file, fetch, compute, assess, report. All the reading and writing of the run lives here and in the fetch, store and report parts, so that everything else can stay pure.{N.ref("vss/runner.py: 'All I/O lives here and in fetch/store/report. rules.py and metrics.py stay pure.'")}</p>
{N.flush()}

<h2>The two walls</h2>
<p>The first wall is around the owner's file. It holds every status, every tier, every value, every stop: the decisions. No part that runs on a schedule may write to it. The refresh command asserts it did not. The scheduled screen's unit cannot write to the folder. A hand-typed buy price in the file fails the run outright, because a buy price must come from a value and a tier or it has no origin.{N.ref("Rulings E92 and E93; README on the provenance conflict; the read-only configuration directory in deploy/vss-screen.service.")}</p>
{N.flush()}
<p>The second wall is around the arithmetic. Nothing that computes may fetch, and nothing that fetches may compute. A figure crosses from one side to the other only through the record, with its origin attached. This is what makes a number reproducible, and what makes a wrong number traceable to the fetch that brought it in rather than lost inside a calculation.</p>

{fold("The commands, for the curious", '''
<p>The program is run from the command line as <code>python -m vss</code> followed by one of sixteen sub-commands. The ones a reader of this site has met: <code>run</code> (the nightly run), <code>screen</code> (the weekly screen), <code>watch</code> (disclosures), <code>refresh</code> (re-read a company's figures on a report date), <code>earnings</code>, <code>xbrl</code>, <code>nordic</code>, <code>manual</code>, <code>appendix</code> (the ways figures come in), <code>briefing</code> (assemble a reading), <code>overview</code> (the page), <code>checkin</code> (the heartbeat's own timer), <code>sales</code> (closed positions measured against the index), <code>shadow</code> (the shadow book). Every one of them prints a report to standard output and logs to standard error, and none of them writes a decision.</p>
''')}
""",
    [("Module layout and each module's stated scope", "repo: vss/*.py module docstrings; vss/__main__.py; README.md")],
)

# ---------------------------------------------------------------------------
# 15. WHERE THE DATA LIVES AND HOW IT IS KEPT HONEST
# ---------------------------------------------------------------------------
N = Notes()
chapter(
    "15-the-record", "Where the data lives and how it is kept honest",
    "Every figure with its origin, every valuation with its eight declarations, every run with its own row. Why a valuation that cannot complete its record prints nothing rather than a number with a warning.",
    8, False,
    f"""
<p>Part One said every figure carries where it came from. This chapter is about where that goes, and about the one rule that keeps the whole record trustworthy: a number with a gap in its origin is not printed with a caveat. It is not printed.</p>

{FIG["figure_journey"]()}

<h2>Four places a figure can live</h2>
<ul>
<li><strong>The run database.</strong> One row per company per nightly run: the price, the computed figures, the verdict codes, the blockers. Nothing reads it back yet; it exists to accumulate, so the history can be reconstructed later.{N.ref("vss/store.py.")}</li>
<li><strong>The fundamentals store.</strong> Every period of accounts ever fetched for a company, kept for good. A quarter never displaces a year. A store that pruned old periods would make an old valuation impossible to rebuild.{N.ref("Ruling E49: the store retains every period it has ever fetched. Ruling E17: a quarter never displaces a year.")}</li>
<li><strong>The screener snapshots.</strong> One small database per screening run, holding raw daily prices, never computed figures, plus the list of names, the rejections and a fetch status per company. The last four price snapshots are kept; every ranking is kept forever, because every future comparison stands on it.{N.ref("vss/snapshot.py; retention described in the project brief §6.5.")}</li>
<li><strong>The owner's file.</strong> Statuses, tiers, values, stops, notes, and hand-entered figures. Tracked under version control, on the owner's decision, so that the history of decisions is in the history of the file.{N.ref("README on config/watchlist.yaml, tracked since 2026-08-25.")}</li>
</ul>
{N.flush()}

<h2>The run record: eight declarations or nothing</h2>
<p>A valuation is not a number. It is a number plus everything that was decided to get it. So before a value may be printed, the run record for that valuation must declare eight things: which share count was used and as of when; how share-based pay was treated; where the company books its interest, and therefore what "free cash flow" means for it; every item in the bridge from the value of the whole business to the value of its shares; the arithmetic conventions; the discount rate with its anchor and the growth rate with the view it came from; the three as-of dates and the price date; and the origin of every input.{N.ref("vss/runrecord.py: 'A RUN WITHOUT A COMPLETE RECORD DOES NOT PRINT A FAIR VALUE. Not \\'prints one with a warning\\'.'")}</p>
{N.flush()}

<h2>Why refusing beats continuing</h2>
{wrong('''
<p>Seven of the eight declarations are in place. The share count is present but the date it was stated is not. Print the value anyway, with a note: "share count date unknown". The owner will see the note.</p>
''', "The reasonable-sounding way, which is wrong")}
{right('''
<p>The valuation raises an error and prints no value for that company. The report says which declaration is missing. The other companies in the same run are unaffected: one name's missing declaration is that name's DATA MISSING, never a reason to stop the run for the rest.</p>
''', "What the code does")}
<p>The note would be read the first time and not the tenth. A number on a page is a number; the caveat beside it is decoration, and decoration gets ignored. The only caveat that cannot be ignored is the absence of the number. So the record refuses, and the refusal is a line in the report that says what to go and find.</p>

<p>Two levels of refusal exist, and it is worth being exact. A bad or missing figure for one company degrades that company's row and nothing else; the nightly run is built so that one name never breaks it. A corrupt owner's file, a malformed entry or a hand-typed buy price, stops the whole run before it starts, loudly, because a run on a corrupt file would write corrupt rows into the record for every name.{N.ref("The runner catches per-name exceptions and continues ('one name never breaks it'); the configuration loader fails the whole run on a malformed entry or a provenance conflict.")}</p>
{N.flush()}

<h2>Checked, unchecked, absent, not there</h2>
<p>A figure's verification state travels with it. It enters unchecked. A person reads it back against the page named beside it and marks it checked, and the mark says which kind of check: against the regulator's structured data, across two separate documents, or against the same page it came from. Where a figure was searched for in a full report and is not there, the record says so, which is different from a zero and different from absent.{N.ref("Verification kinds: ruling E40 and vss/manual.py. Not presented: ruling E85. A zero needs a basis: ruling E25.")}</p>
{N.flush()}
<p>Two independent readings agreeing is what makes a figure the owner's. Where two readings disagree, the figure is re-extracted before anyone escalates it, because the first question about a disagreement is whether one reading was simply wrong.{N.ref("Ruling E104.")}</p>
{N.flush()}

<h2>Aborting a screen on a hole</h2>
<p>The screener has one place where it stops rather than continues: when a quarterly comparison it needs cannot be formed because a quarter is missing, it breaks the run rather than killing a name on a hole. A revenue-decline test that fails a company for a quarter the vendor did not supply would be exactly the two-outcome error of chapter 9, at scale.{N.ref("vss/filters.py, the revenue limb: a comparison the quarters cannot form 'breaks the run rather than kill on a hole'.")}</p>
{N.flush()}

{decision(
    "A valuation prints a value only with a complete record of eight declarations; otherwise it prints nothing for that name and says what is missing. One name's failure never stops the run; a corrupt owner's file stops it before it starts.",
    "A caveat beside a number is read once. An absent number is read every time.",
    "Names sit valued at nothing for as long as one declaration is missing, and the report is longer for saying why. The owner spends evenings finding share-count dates.",
)}
""",
    [("The record, the run record and the store", "repo: vss/store.py; vss/runrecord.py; vss/snapshot.py; vss/manual.py; vss/runner.py; reference/FRAMEWORK-EDITS.md E17, E25, E40, E49, E85, E104")],
)

# ---------------------------------------------------------------------------
# 16. THE RULES FILE
# ---------------------------------------------------------------------------
N = Notes()
chapter(
    "16-the-rules-file", "The rules file",
    "A written framework, amended only by dated, numbered rulings. A rule question and a bug go to different files. Writing the rule before the situation arises is what stops you bending it once you have a stake in the answer.",
    8, True,
    f"""
<p>The method exists as a document before it exists as code. That is not a figure of speech. There is a file, the framework, with numbered sections from 0 to 11, and there is a second, much longer file of rulings that amend it, each with a letter or a number, a date, and the statement that the owner ruled it. The code implements the rulings. It does not make them.</p>

<h2>Three files, three jobs</h2>
<ul>
<li><strong>The framework.</strong> The method itself: the gates, the hard kills, the valuation, the entry and exit discipline, the position sizing. It holds no dated holdings and no market data, so it never goes stale. It is at version 2.3.</li>
<li><strong>The rulings.</strong> Every ambiguity, deviation and amendment, in lettered series. A for structural fixes. B for real ambiguities in the gates, each raised with a date and either decided or left open, and an open one is a question the owner owes an answer to. C for money-relevant ambiguities. D for consistency fixes. E for rulings on the tooling and, later, the substantive rules, E1 to E114 at the time of writing. F, the newest series, for the overview page. The file is appended to and never rewritten.{N.ref("reference/FRAMEWORK.md and reference/FRAMEWORK-EDITS.md. The rulings file opens: 'Each item is a place where a human reading it knows what you mean and a machine does not. I have not applied any of these — every one changes a rule, and they are your rules.'")}</li>
<li><strong>The backlog.</strong> Things wrong in the code. Its first lines draw the line: "A rule question goes to the rulings file and gets a letter; a defect goes here and gets fixed. Nothing in this file is a decision the owner owes an answer to."{N.ref("reference/BACKLOG.md, opening.")}</li>
</ul>
{N.flush()}

<p>The separation between the second and third files is the important one. A threshold that is wrong because the rule was wrong is a ruling. A threshold that is wrong because the code misread the rule is a bug. Mixing them lets a bug fix quietly change a rule, or a rule change hide inside a bug fix. Every threshold in the code cites the ruling that set it, and the screener's thresholds live in a configuration file where each one names its framework section, not in the code at all.{N.ref("config/screener_filter2.yaml, each limb citing its section or ruling; module docstrings throughout vss/ citing E-numbers as the authority for a threshold or a field.")}</p>
{N.flush()}

<h2>Why the rule is written first</h2>
{wrong('''
<p>NAME A is at 91, the buy line is 85, and the owner has just re-read the reports and feels more confident than the tier allows. The sensible thing is to move it to tier 1, which puts the line at 89. Then wait for 89.</p>
''', "What happens without a written rule")}
{right('''
<p>A change to a cushion is a dated ruling, and it takes effect at each company's next scheduled reassessment, never immediately. A buy line that crosses because the cushion moved arms nothing.</p>
''', "The rule, E100")}
<p>The whole point of writing a rule before the situation arises is that at that moment you have no stake in the answer. When the situation arrives, you do, and the rule you wrote earlier is the only version of you that was thinking clearly. The rulings say "written before the code" on their face, and the version-control history is treated as evidence of the order.{N.ref("Ruling E100 on cushion changes. The project brief §1.2: 'A ruling is written BEFORE the code that implements it, and many say so on their face.'")} A session that changes what the code does without a ruling behind it is, in the project's own words, doing the wrong thing.{N.ref("The project brief, §0.")}</p>
{N.flush()}

<h2>Every ruling states its price</h2>
<p>The rulings are written in an unusual register: declarative, absolute where a rule is absolute, and explicit about what a decision costs. A deletion names what was lost by deleting. A new requirement names what it will make slower. This site's decision boxes copy that shape from the rulings.</p>

<h2>Rules that were withdrawn</h2>
<p>A rules file that only ever grows is suspicious. This one records its own reversals, and they are the best evidence that the process works, because each one shows a rule being corrected by a dated decision rather than quietly bent.</p>
<ul>
<li><strong>A gate with two limbs that measured nothing.</strong> Two tests of stability in reported figures were found to be measuring currency and season, not the business, and to have changed no verdict across five companies. Deleted, with the sentence "not widened, not softened, removed".{N.ref("Ruling E30, 2026-08-25.")}</li>
<li><strong>A debt cap loosened for the wrong reason.</strong> The first screener cap was set loose, on the principle that a coarse filter must not lose a name the careful reading would keep. Four days later a test run showed 72 names passing the loose cap and failing the method's own stricter test. Tightened, with the count in the ruling.{N.ref("Ruling E2 replaced by E44, 2026-08-26.")}</li>
<li><strong>A buy-price formula superseded, with the old figures kept.</strong> When the cushion was moved from the low-case value to the base-case value, three buy prices already struck under the old formula were not silently recomputed. They were kept, marked as superseded wherever they print, and the old multipliers stay in the code with a comment saying why.{N.ref("Rulings E28, E32 and E90. The code keeps both multiplier tables: 'MBP_TIER_MULTIPLIER above is KEPT for the superseded paths' history.'")}</li>
<li><strong>A citation that did not exist.</strong> The commit that built the phone tunnel cited a framework section as prohibiting a server. The section does not exist. The ruling that followed says: "The citation was asserted without reading the file and is withdrawn here." The commit message is immutable; the ruling is the correction of record.{N.ref("Ruling F1, 2026-09-13.")}</li>
<li><strong>A requirement withdrawn the day it was ruled.</strong> Ruling F1 required the phone page to mark itself stale after 26 hours. Ruling F2, the same day, withdrew that requirement as unbuildable: a static file cannot compare its own age to the time it is read without a script, and the same ruling forbids scripts. The two limbs contradicted each other; one fell. What remained, the page stating its own age twice, was implemented that day.{N.ref("Ruling F2, 2026-09-13.")}</li>
</ul>
{N.flush()}

<p>None of these is an embarrassment. Each is a rule meeting reality and being corrected on the record, with the cost named, by the person entitled to change it. A method that cannot show a withdrawal has either never been tested or is hiding something.</p>

{decision(
    "The framework is amended only by dated, numbered rulings the owner makes. Code cites the ruling it implements. A rule question and a defect go to different files.",
    "A rule written before the situation arises is written by someone with no stake in the answer. A rule that lives only in the code can be changed by a bug fix.",
    "Change is slow. A threshold the owner knows is wrong stays wrong until a ruling is written, and some open questions have stayed open for weeks. The rulings file is over eleven thousand lines.",
)}
""",
    [("The framework, the rulings and the backlog", "repo: reference/FRAMEWORK.md; reference/FRAMEWORK-EDITS.md (A1–A3, B1–B48, C1–C4, D1–D2, E1–E114, F1–F2); reference/BACKLOG.md; config/screener_filter2.yaml")],
)

# ---------------------------------------------------------------------------
# 17. THE NIGHTLY RUN
# ---------------------------------------------------------------------------
N = Notes()
chapter(
    "17-the-nightly-run", "The nightly run",
    "At half past ten a clock fires. Prices are re-checked against decisions already made, files are written, and the run leaves by one of two exits: a quiet signal to an outside observer, or a shout to the owner's phone.",
    7, False,
    f"""
<p>Servers do not have a person sitting at them. To make something happen at the same time every day, you write two small files for the operating system's scheduler. One is a <dfn>timer</dfn>: it says when. The other is a <dfn>service</dfn>: it says what. The scheduler here is the one built into modern Linux, called systemd, and the files are called units.{N.ref("deploy/vss.timer and deploy/vss.service.")}</p>
{N.flush()}

{FIG["nightly_cycle"]()}

<h2>When</h2>
<p>Every day at 22:30, after the last European and American exchanges have closed and prices have settled. If the machine was off at 22:30, the timer runs the job as soon as the machine is back, rather than skipping the day.{N.ref("OnCalendar=*-*-* 22:30:00; Persistent=true.")}</p>
{N.flush()}

<h2>What</h2>
<p>The nightly run loads the owner's file, fetches the day's prices, computes the fixed set of figures, compares each price with the lines already written for that name, writes the report, writes one row per name into the run database, and then generates the overview page. The page generation runs last and is arranged so that if it fails, the run is still a success: the report and the database row come first, and a failure to draw the page is logged as a warning, not a failure of the night.{N.ref("The overview page 'rides on the same unit after the report and database row are written and cannot break the run'.")}</p>
{N.flush()}

<h2>What it cannot touch</h2>
<p>The run is fenced by the operating system, not only by its own code. It sees the whole system as read-only. It sees the owner's home directory as read-only. The only two folders it may write are the data folder and the reports folder. It cannot gain any new permissions once started, and it is killed if it runs for more than fifteen minutes.{N.ref("ProtectSystem=strict; ProtectHome=read-only; ReadWritePaths= the data and reports folders only; NoNewPrivileges=true; TimeoutStartSec=15min.")} This is the first wall from chapter 14, drawn by a different hand: even if the code had a bug that tried to write a decision into the owner's file, the operating system would refuse.</p>
{N.flush()}

<h2>The two exits</h2>
<p>A run ends in one of two ways, and each way makes a different sound.</p>
<ul>
<li><strong>Success.</strong> Immediately after the run completes, a separate one-line script sends a single, empty request to an outside monitoring service. It carries no company name, no price, no report, no machine name: one request to an opaque address, meaning "the run happened". If that request itself fails, the run is still counted a success; a failed signal must not turn a good night into a bad one.{N.ref("ExecStartPost=- the ping script; the leading dash means its failure does not fail the unit. The script's own comment: 'WHAT LEAVES THE MACHINE: one HTTP GET to an opaque UUID. No ticker, no price, no report, no hostname, no body.'")}</li>
<li><strong>Failure.</strong> If the run exits with an error or is killed for running too long, the scheduler starts a second unit whose only job is to notify. That unit runs a plain shell script, deliberately not the program's own language, because the thing that broke may be the program's own environment. The script pushes a message to the owner's phone saying which unit stopped and what that means, with the last eight lines of the log.{N.ref("OnFailure=vss-failure@%n.service; deploy/vss-notify-failure.sh. The heartbeat module: 'It is deliberately a plain curl in a shell script and NOT this package: the failure being reported may well BE this package.'")}</li>
</ul>
{N.flush()}

<p>Notice the asymmetry. Success is silent on the phone. The owner does not want a message every night saying nothing happened; a message that always arrives is a message that stops being read. Success makes its sound somewhere else, to an observer whose job is to notice if the sound stops. That is chapter 18.</p>

<h2>The weekly run</h2>
<p>The screener runs on the same pattern, on Saturday mornings at 08:00, on Friday's settled prices, with a four-hour limit and a stricter fence: the folder holding the owner's file is not writable to it at all. That single line is the ruling "the scheduled screen never enters a name" written in the scheduler's language.{N.ref("deploy/vss-screen.timer: Sat 08:00; the service's read-only configuration directory, described in the project brief as 'E93 in one line'. Measured 2026-08-31: about 38 minutes, 3,495 fundamentals requests, zero throttles.")} A third timer, at 09:30 every day, belongs to the dead man's switch.</p>
{N.flush()}

{fold("The units, in words", '''
<p><code>vss.timer</code> fires <code>vss.service</code> at 22:30 daily, catching up if missed. The service is one-shot, runs the nightly command in a sandbox writable only at the data and reports folders, pings the outside observer on success, and starts <code>vss-failure@vss.service</code> on failure. <code>vss-screen.timer</code> fires <code>vss-screen.service</code> on Saturdays at 08:00 with the configuration folder read-only. <code>vss-checkin.timer</code> fires <code>vss-checkin.service</code> at 09:30 daily. <code>vss-failure@.service</code> is a template: the name of the failed unit is filled in and passed to the notifier script, which always exits successfully, because "a failure notifier that can fail is a second thing to monitor".</p>
''')}
""",
    [("The scheduler units and scripts", "repo: deploy/vss.timer, deploy/vss.service, deploy/vss-screen.timer, deploy/vss-checkin.timer, deploy/vss-failure@.service, deploy/vss-ping-healthcheck.sh, deploy/vss-notify-failure.sh, deploy/README.md")],
)

# ---------------------------------------------------------------------------
# 18. THE DEAD MAN'S SWITCH
# ---------------------------------------------------------------------------
N = Notes()
chapter(
    "18-dead-mans-switch", "The dead man's switch",
    "A crashed run and a run with nothing to say used to look identical: both were silence. Now one observer shouts when something breaks on the machine, and another alarms on the absence of a signal, which is the only alarm a dead machine can still raise.",
    9, True,
    f"""
<p>Here is the failure that the whole of this chapter exists to remove. The nightly run sends a message to the owner's phone only when a name needs attention. Most nights, no name does, and the phone is quiet. Now suppose the run crashed at 22:30 on a Tuesday and has been dead ever since. The phone is quiet. The two situations, "nothing needs you" and "nothing has run for a week", produce exactly the same experience: silence. In the tool's own words, "a monitor whose failure mode is silence is a monitor that stops being believed the first time you find out the hard way."{N.ref("vss/heartbeat.py, opening.")}</p>
{N.flush()}

<h2>The name, and where it comes from</h2>
<p>Trains have a handle the driver must hold or press at intervals. If the driver collapses, the handle is released and the brakes apply. It is called a dead man's handle, and the design idea is that safety must not depend on a signal being sent, because a person who cannot send it is exactly the case it exists for. It must depend on a signal that keeps arriving, with the alarm on its absence.{N.ref("Wikipedia, Dead man's switch: 'Vigilance control was developed to detect this condition by requiring that the dead man's device be released momentarily and re-applied at timed intervals.'")} The software version is called a <dfn>dead man's switch</dfn>, and it works the same way: something expects a regular signal, and raises the alarm when the signal does not come.</p>
{N.flush()}

{FIG["two_observers"]()}

<h2>Two observers, because there are two kinds of dead</h2>
<p>A machine can be alive and broken, or it can be dead. These need different observers, because an observer that lives on the machine dies with it.</p>

<h3>Observer one lives on the machine</h3>
<p>When the run fails, the scheduler starts the notifier from chapter 17, which pushes to the phone what stopped and the last lines of the log. This is the fast observer: it fires while the failure is happening, and it can describe it. Its weakness is that it needs the machine to be up, the scheduler to be running, and the timer to have fired. A timer that was disabled after a reboot starts nothing, so nothing fails, so nothing shouts, and that is precisely the failure that looks most like a quiet week.</p>
<p>So observer one has a second leg on its own timer: every morning at 09:30, a separate job checks whether a completed run is on record and whether the nightly timer is still enabled. It runs on its own timer deliberately: "if the check on the run shared a timer with the run, the failure that stopped the run would stop the check, and the switch would be wired to its own power supply."{N.ref("deploy/vss-checkin.timer, comment. The run also records its own completion in a table, with a bar of 72 hours for the nightly and 10 days for the weekly, and a test run or a single-name run does not reset the clock.")}</p>
{N.flush()}

<h3>Observer two lives outside</h3>
<p>None of that helps if the machine is off, the network is down, or the whole scheduler is stopped. A dead machine cannot page itself. The only thing that can notice a dead machine is something that is not on it: an outside service that expects one signal a day and raises an alarm when the signal does not arrive by a deadline.{N.ref("vss/heartbeat.py: 'a dead VPS cannot page itself... Closing that needs an OUTSIDE observer — a service that expects a ping and alerts on its ABSENCE.'")} That is the empty request from chapter 17's success exit. The outside service "keeps silent as long as pings arrive on time" and "raises an alert as soon as a ping does not arrive on time", with a grace period after the expected time.{N.ref("The monitoring service's own documentation; the suggested settings in the example environment file are a one-day period and a six-hour grace.")}</p>
{N.flush()}

<h2>Why absence beats error</h2>
<p>An error message needs a sender. Every sender can fail in a way that prevents sending: the process crashed before reaching that line, the network was down, the machine was off. An alarm on absence needs nothing from the failing side. It is the only kind of alarm whose coverage includes the case where the thing being watched no longer exists. That is why the successful run makes a sound to the outside observer and no sound to the phone: the sound is not for the owner, it is for the thing that will notice when the sound stops.</p>

<p>The owner's words when this leg was added: "a dead VPS is exactly the case I want covered and no ping leaves data."{N.ref("deploy/vss-ping-healthcheck.sh, quoting the owner, 2026-09-01.")}</p>
{N.flush()}

<h2>Why the notification address stays out of the repository</h2>
<p>The phone notifications go through a public push service where anyone who knows a topic's name can post to it. The topic name is therefore the only secret the service has, and it lives in a file in the owner's home directory that is never committed. The program reads it from the environment first, then from that file, and never writes, logs or prints it. The same file holds the outside observer's address. The repository contains an example file with both left blank.{N.ref("deploy/vss.env.example: 'THE REAL FILE IS NEVER COMMITTED: the topic is the only secret ntfy has.' vss/env.py reads the environment first, then the file.")} The topic is outbound only: nothing in the project ever reads from it, so even a leaked name lets an outsider post noise to the owner's phone, not read anything.</p>
{N.flush()}

<h2>What is not covered, said rather than implied</h2>
<ul>
<li>The weekly screen has no outside signal of its own. A dead weekly screen is caught only by the morning check-in.</li>
<li>A machine that is up, pinging, and wrong. The outside observer proves the run finished, not that it was right.</li>
<li>The outside observer itself being down.</li>
<li>The phone tunnel (chapter 19) has no failure notification, for a reason that chapter explains.</li>
</ul>

<h2>A defect the design found in itself</h2>
<p>On 2026-09-13 the page server restarted seven times in a row because of a missing directory, and the notifier sent seven messages. Each one said that no report had been written for the day, because that sentence had been written for the nightly run and reused for every unit. For a page server that never writes a report, the sentence was false. The fix, recorded as a backlog item and committed the same day, gives each unit its own accurate sentence about what its stopping means.{N.ref("Backlog item B-13; commit 'the failure notifier says what stopped, not \"no report was written\" for every unit'.")} A notifier that lies, even slightly, is on its way to being ignored.</p>
{N.flush()}

{decision(
    "Two observers. One on the machine that describes what broke; one outside that alarms on the absence of a daily signal. The success exit signals the outside observer and says nothing to the phone.",
    "Silence has to mean one thing. The only alarm that covers a dead machine is one raised by something that is not on it.",
    "A second external service, whose own outage is uncovered. A signal that leaves the machine every night, kept to one empty request so that nothing about the book leaves with it.",
)}
""",
    [
        ("Dead man's switch, Wikipedia", "https://en.wikipedia.org/wiki/Dead_man%27s_switch"),
        ("Healthchecks.io documentation (alarm on a missing ping)", "https://healthchecks.io/docs/"),
        ("The heartbeat module and the units", "repo: vss/heartbeat.py; deploy/vss-checkin.timer; deploy/vss-ping-healthcheck.sh; deploy/vss-notify-failure.sh; deploy/vss.env.example; reference/BACKLOG.md B-13"),
    ],
)

# ---------------------------------------------------------------------------
# 19. THE PHONE PROBLEM
# ---------------------------------------------------------------------------
N = Notes()
chapter(
    "19-the-phone", "The phone problem",
    "A decision is useless on a server in another country when the price moves. The last mile of the investing problem, and the shape built to cover it: the machine dials out, nothing dials in, and the front door asks who you are before anything behind it is reachable.",
    9, False,
    f"""
<p>Everything so far produces a page on a rented server in a data centre. The owner is on a train in Sweden with a phone. The price of a name on the waiting list has just crossed its line. The page knows. The owner does not. This is not an infrastructure problem; it is the last step of the investing problem, and if it is not solved the rest was decoration.</p>

<h2>The constraint that makes it hard</h2>
<p>The page holds the whole book: every held name, every stop, every buy line, every value. Getting it to a phone means getting it off the machine, and every way of doing that opens something. The question is what to open, and the rules that govern the answer were written down as a ruling before it was built. Its shape: the page may leave the machine only through a gate that checks identity; the server that hands it over may listen only to the machine itself; no inbound port may be opened; the firewall stays as it was.{N.ref("Ruling F1, limbs (a) and (b), 2026-09-13.")}</p>
{N.flush()}

<h2>The shapes that were ruled out</h2>
<p>The record does not list alternatives that were considered and rejected; it lists what is prohibited, and each prohibition is the shape of a tempting answer.</p>
<ul>
<li><strong>Open a door in the wall.</strong> Run a web server, open its port in the firewall, point a phone at it. Fast, and it turns a machine that accepts nothing from the internet into one that accepts connections from anyone who finds the address. The deployment notes: "Any change that opens a port, binds [every interface], or adds an Access Bypass policy reverses the intent of this deployment and must be ruled on, not merged."{N.ref("deploy/TUNNEL-NOTES.md, first paragraph.")} During the build, the server did bind to every interface for three minutes, because a configuration line that looked like an address was a port. It was found and fixed the same morning, and it is the first of three bugs the notes record.</li>
<li><strong>Put the address in plain public DNS without the gate.</strong> Reachable from anywhere, and it would route around the identity check entirely. The notes: "A DNS-only record would bypass Access entirely."</li>
<li><strong>Add a rule that lets some traffic skip the identity check.</strong> The gate provider evaluates such rules first. One would make the book public "instantly and silently". It is prohibited by the ruling, in bold.</li>
</ul>
{N.flush()}

<h2>The shape that was built</h2>
{FIG["tunnel"]()}

<p>Follow the arrows. On the machine, a small web server holds the page and listens only to the machine itself: it is bound to the address that means "this computer and nothing else", so nothing outside can reach it directly, ever.{N.ref("The server binds the loopback address only. The notes call that one line load-bearing: without it the server would bind every interface, publicly.")} Beside it runs a second small program, a tunnel client, which does one thing: it dials out to a relay service on the internet and keeps that connection open. The direction matters and is the whole design. The machine makes an outbound connection, the same kind a browser makes when it loads a web page. The firewall was not touched. The only thing the internet can reach on this machine is the remote login port that was already there.{N.ref("deploy/TUNNEL-NOTES.md: the tunnel client 'makes an outbound connection... the firewall is unchanged', and the only public listener is the remote-login port that was already there.")}</p>
{N.flush()}

<p>Now the owner opens the page's address on a phone. The request goes to the relay, not to the machine. Before the relay does anything, a front door asks who is asking. The front door accepts exactly one email address. It sends a one-time code to that address and to no other; a different address does not even receive a code, because the policy refuses before a code is issued. With the code entered, the door opens for 24 hours. Only then does the relay pass the request down the connection the machine opened earlier, the machine's own server answers with the page, and the page travels back up the same line to the phone.{N.ref("Cloudflare Access: one application, one policy allowing one email, one-time PIN as the only identity provider, 24-hour session. Verified 2026-09-13: two other addresses received no PIN at all.")}</p>
{N.flush()}

<p>The idea that access should depend on who you are and not on which network you are on has a name in the security literature and a history: it is the principle Google described in 2014 when it moved its internal tools onto the public internet behind identity checks, and it was given the label zero trust earlier by an industry analyst. This project did not invent the shape; it borrowed the smallest possible version of it.{N.ref("Ward and Beyer, 'BeyondCorp: A New Approach to Enterprise Security', ;login: 39(6), 2014; Kindervag, Forrester Research, 2010. Neither text is quoted here; the attribution is a pointer, not a claim about their wording.")}</p>
{N.flush()}

<h2>What this costs, from the ruling</h2>
<p>The page passes through a company's infrastructure the owner does not control, and that company decrypts it at its edge. In the ruling's words: "The page is plaintext at their edge: holdings, states, gate results, MBPs and stops, readable by Cloudflare and by anyone who compels or breaches Cloudflare. This is not mitigable within this architecture. It is the price of reading the book on a phone from an arbitrary network, and I am paying it knowingly." The front door is single-factor: whoever controls the mailbox controls the page. And the tunnel client had to run as a system service with a credential the owner's own account cannot read, which means it cannot use the failure notifier from chapter 17. If the tunnel dies, the page stops loading and the phone stays silent. The nightly run and its own alerting do not depend on it.{N.ref("Ruling F1: 'WHAT THIS COSTS' under limbs (a) and (b); deploy/TUNNEL-NOTES.md, 'Units — Option C'.")}</p>
{N.flush()}

{decision(
    "The page reaches the phone through an outbound tunnel to a relay, behind a front door that admits one address by one-time code. The server listens only to the machine itself. No port is opened.",
    "A decision that cannot reach the owner when the price moves was not worth making. Every inbound shape opens the machine; the outbound shape opens only a page, and only to one person.",
    "The page is readable by the relay operator. The door is single-factor. The tunnel cannot page the phone when it dies. Each is written into the ruling as the price.",
)}
""",
    [
        ("Ward and Beyer (2014), BeyondCorp: A New Approach to Enterprise Security, ;login:", "https://www.usenix.org/publications/login/dec14/ward"),
        ("Ruling F1 and the tunnel notes", "repo: reference/FRAMEWORK-EDITS.md F1; deploy/TUNNEL-NOTES.md; deploy/vss-tunnel.service; deploy/vss-overview.service"),
    ],
)

# ---------------------------------------------------------------------------
# 20. THE BOUNDARY
# ---------------------------------------------------------------------------
N = Notes()
chapter(
    "20-the-boundary", "The boundary",
    "One file served, every other path refused. The folder behind the server holds dozens of private files. The difference between one file exposed and all of them is a single block of configuration, and removing it would expose everything silently.",
    5, False,
    f"""
<p>Chapter 19 got a page to the phone. This chapter is about the two words "a page", because the server that hands it over sits in a folder full of things that must not travel.</p>

{FIG["boundary"]()}

<h2>What is in the folder</h2>
<p>The page is written into the reports folder, beside every nightly report, the shadow book, the record of sales, the pre-purchase notes for names being considered, and the research briefings. On the day the tunnel was built, the folder held 93 files. All but one are the owner's private research, and several of them are precisely the documents whose contents the whole method is built to protect from being seen early: the owner's growth views and reasoning.{N.ref("deploy/TUNNEL-NOTES.md, THE BOUNDARY: 'reports/ held 93 files on 2026-09-13'.")}</p>
{N.flush()}

<h2>The rule</h2>
<p>The server has one rule with two halves. A request for the root address is answered with the overview page. A request for any other path, anything at all, is answered with "not found" and zero bytes. That is the entire published surface: one address.{N.ref("Verified 2026-09-13 after the last fix: a request for the root returned the page; a request for one of the other files in the folder returned 404 with 0 bytes; the only listening address on the machine was the loopback one; a request to the public name without a login was redirected to the front door.")}</p>
{N.flush()}

<h2>Why one block of configuration matters</h2>
<p>The rule is a few lines in the server's configuration file. Remove the half that says "everything else: not found", and the server's default behaviour takes over, which is to serve whatever file the request names. Every file in the folder would then be one address away, behind the same front door but no longer behind anything else. Nothing would fail. Nothing would alarm. The page would keep loading exactly as before. The ruling names this: "That block is the boundary; the deployment notes say so, and any change to it is a ruling, not a merge."{N.ref("Ruling F1, limb (b), WHAT THIS COSTS.")}</p>
{N.flush()}

<p>This is the general shape of a boundary worth worrying about: a constraint whose removal changes nothing visible. The three bugs found during the build were all of this kind. The server bound to every network interface for three minutes, and nothing complained. A missing directory made the server restart seven times, and only the notifier's repetition revealed it. A configuration line in the wrong form made the server answer every request from the relay with a blank page of zero bytes and a success code, because the line doubled as a filter on which requests it would answer at all.{N.ref("deploy/TUNNEL-NOTES.md, 'Three bugs found during the build — all fixed'.")} Each was found by testing the thing directly, not by waiting for an alarm, because none of them would have raised one.</p>
{N.flush()}

<p>The security literature has a name for the principle the block enforces, and it is fifty years old: every program should operate using the least set of privileges necessary to complete the job.{N.ref("Saltzer and Schroeder, 'The Protection of Information in Computer Systems', 1975.")} The server's job is one file. Its privilege is one address.</p>
{N.flush()}

{decision(
    "The server answers one address with one file and everything else with not found. The block that enforces this is named as the boundary, and changing it requires a ruling.",
    "The folder holds the owner's private research. A default file server would expose all of it with no visible change.",
    "A configuration whose regression is silent. The only defence is a written rule that changes to it are rulings, and a test that asks the server for something it must refuse.",
)}
""",
    [
        ("Saltzer and Schroeder (1975), The Protection of Information in Computer Systems", "https://www.cs.virginia.edu/~evans/cs551/saltzer/"),
        ("The boundary, as recorded", "repo: deploy/TUNNEL-NOTES.md; deploy/vss-overview.service; reference/FRAMEWORK-EDITS.md F1 limb (b)"),
    ],
)

# ---------------------------------------------------------------------------
# 21. THE PAGE THAT ARRIVES
# ---------------------------------------------------------------------------
N = Notes()
chapter(
    "21-the-page", "The page that arrives",
    "What the owner sees on the phone, and the rules on what it may say: a distance from a price, never a verdict; no buy-side condition without the conditions that qualify it; its own age stated twice so a stale page cannot pass as fresh.",
    8, False,
    f"""
<p>The page is one file: no server logic, no framework, no script. It opens from a local file on the owner's own machine just as it does through the tunnel, and it is built to be read on a phone in the order a person would actually ask questions.{N.ref("vss/overview.py; the design rules are each backed by a test, described in the project brief §4.7.")}</p>
{N.flush()}

<h2>Three questions, in order</h2>
<ol>
<li><strong>Does anything need me today?</strong> One block at the top, in plain sentences. Either "nothing", or the two or three things that do: a buy line crossed, a stop breached, a held name with no stop, a dated event within seven days. The list of kinds is closed, so the block cannot grow into a feed. Beside it, always, is what was checked, because "nothing needs you" and "nobody looked" are otherwise the same silence.</li>
<li><strong>Where is everything against its value?</strong> One card per name. A card, not a table, because a table is for comparing forty things and a card is for recognising one. The price large; the value and the buy line beside it; a year of settled closing prices drawn as a small line; and a track showing where the price sits between half the value and half again, on a scale that is never rescaled per name. A picture never replaces a figure.</li>
<li><strong>What is coming?</strong> The unresolved dated events, nearest first. A long note is folded, never cut short, because "an ellipsis on a record is a record nobody can read."</li>
</ol>

<h2>The rules on what it may say</h2>

<h3>A distance, never a verdict</h3>
<p>The page uses green and red. It uses them to say how far a price is from a line, in five bands whose boundaries are the method's own numbers, and for nothing else. A name can be green and need nothing; the name that needs the owner can be red. Colour is never applied to a whole card, because a green card reads as approval. A name that is cheap but has failed a gate is drawn muted, with the reason stated in words, so that a cheap closed door does not read as an invitation. No colour anywhere carries meaning on its own.{N.ref("vss/overview.py: 'THE DISTANCE SCALE... it is a MEASUREMENT, never a verdict. It says HOW FAR, and nothing about whether to act.' Bands at 0, 5, 25 and 75 percent.")}</p>
{N.flush()}

<h3>No buy-side condition without the conditions that qualify it</h3>
<p>If the page says that a price is below its buy line, the same sentence says what else must be true: that the reading is current, that the conditions from chapter 11 hold. Not a line below. The same sentence, because "the reader who stops after the first half is the reader this page is for."{N.ref("vss/overview.py: 'A BUY-SIDE CONDITION NEVER STANDS ALONE. The qualifying clause goes in the SAME SENTENCE, not a line below it.'")}</p>
{N.flush()}

<h3>It states its own age, twice</h3>
<p>A run that fails writes nothing. The server keeps serving the last good page. The page looks identical to a fresh one, and the owner reads last Thursday's states believing they are tonight's. That failure is invisible to every alarm in chapter 18, because the run either happened or it did not, and the page's age is a different question. So the page prints the exact time it was generated, with the timezone, in the header, visible on a phone without scrolling, and again in the first sentence of the footer. The page cannot mark itself stale, because that would need a script and scripts are forbidden; it can only make its age impossible to miss, and the subtraction is the owner's.{N.ref("Ruling F1 limb (c) requirement 1, and ruling F2 withdrawing requirement 2. Implemented 2026-09-13.")}</p>
{N.flush()}

<h3>It never chooses</h3>
<p>Where the record holds two valuations for a name and nothing says which is current, the page prints DATA MISSING and links both. It does not take the newer one. A sort order is not a decision, and the page must not answer a question the owner has not.{N.ref("vss/overview.py: 'it never chooses (two run records and no entry naming one ⇒ DATA MISSING and both linked — a filename sort must not answer E39's question)'.")}</p>
{N.flush()}

<h2>Why a page that renders no opinion is more useful</h2>
<p>A page that said "buy NAME A" would be read for its verdict, and the verdict would be right or wrong, and the owner would learn nothing either way about whether the reading behind it was sound. A page that says "NAME A is 3 percent above its line, the line was struck on the June report, the next report is in nine days, and one figure is unverified" gives the owner every fact needed to decide and withholds the one thing that would let the owner stop thinking. It is more work to read. That is what it is for.</p>

{decision(
    "The page shows state, distance and age. It renders no verdict on any name, colours nothing as approval, qualifies every buy-side sentence in the same sentence, and prints its own generation time twice.",
    "The page is the thing the owner acts on. Anything it decided would be decided without the reading, and anything it hid about its own age would be believed.",
    "It cannot warn that it is stale; the owner must read the time and subtract. It never gives the answer, so every night the owner does the thinking again.",
)}
""",
    [("The overview page generator and its rulings", "repo: vss/overview.py; vss/render.py; reference/FRAMEWORK-EDITS.md F1, F2")],
)

# ---------------------------------------------------------------------------
# 22. WHAT IT DOES NOT DO
# ---------------------------------------------------------------------------
N = Notes()
chapter(
    "22-limits", "What it does not do",
    "The security limits, stated as the deployment notes state them. Then the method's limits: it cannot tell you a business is good, it cannot make you patient, it cannot stop you overriding it, and it refuses to decide anything for you. The last is deliberate.",
    7, False,
    f"""
<p>This chapter is a list, and the list is not softened. Every item below is written in the project's own records, most of them under a heading that reads "What this does NOT protect against".</p>

<h2>Security</h2>
<ul class="limits">
<li><span class="what">The relay operator can read the page.</span><span class="does">Nothing. The ruling calls it not mitigable within this architecture and accepts it as the price of reading the book on a phone from an arbitrary network.</span></li>
<li><span class="what">The front door is single-factor. Whoever controls the mailbox controls the page.</span><span class="does">Nothing beyond the mailbox's own security. Stated in the ruling.</span></li>
<li><span class="what">A 24-hour session on an unlocked phone stays open until it expires.</span><span class="does">Nothing. The phone's lock is the control.</span></li>
<li><span class="what">One bypass rule at the gate provider makes the page public instantly and silently.</span><span class="does">Prohibited by ruling, in bold. No mechanism prevents it.</span></li>
<li><span class="what">The page's public name appears in certificate logs, so it is discoverable.</span><span class="does">Nothing. "Obscurity is not the control; Access is."</span></li>
<li><span class="what">The account that controls the domain, the tunnel and the gate is secured by the same mailbox as the front door.</span><span class="does">Nothing yet. Recorded.</span></li>
<li><span class="what">If the tunnel dies, the phone is not told.</span><span class="does">Nothing. The tunnel runs as a system service that cannot use the failure notifier. The nightly run and its alerting do not depend on it.</span></li>
<li><span class="what">The page cannot mark itself stale.</span><span class="does">It prints its generation time twice. The requirement to mark itself was withdrawn as unbuildable.</span></li>
<li><span class="what">The boundary is one configuration block whose removal is silent.</span><span class="does">Named as the boundary; any change is a ruling. A test asks the server for a file it must refuse.</span></li>
</ul>
<p>Every line above is taken from the deployment notes and the two rulings on the page.{N.ref("deploy/TUNNEL-NOTES.md, 'What this does NOT protect against'; ruling F1; ruling F2.")}</p>
{N.flush()}

<h2>Monitoring</h2>
<ul class="limits">
<li><span class="what">The weekly screen has no outside signal.</span><span class="does">The morning check-in is the only cover.</span></li>
<li><span class="what">A machine that is up and wrong pings as if it were right.</span><span class="does">Nothing. The observer proves a run finished, not that it was correct.</span></li>
<li><span class="what">The outside observer can itself be down.</span><span class="does">Nothing.</span></li>
</ul>

<h2>The method</h2>
<ul class="limits">
<li><span class="what">It cannot tell you a business is good.</span><span class="does">It can tell you a business was not faulted on a fixed set of coarse tests, and what growth its price assumes. Whether the business is good is a reading, and the reading is the owner's.</span></li>
<li><span class="what">One of its five gates has never run.</span><span class="does">Recorded as DATA MISSING for every name, kept, and waiting for the peer figures it needs.</span></li>
<li><span class="what">Its estimate of value rests on a growth view that will never be verified, and a discount rate that is a preference.</span><span class="does">Both are written down before the price is seen, and the sensitivity to the rate is printed beside every buy price. The ruling says both things in those words.</span></li>
<li><span class="what">It cannot make you patient.</span><span class="does">It can make the waiting a written number rather than a mood, and report the distance every night. Whether the owner buys at 93 anyway is not the tool's to prevent.</span></li>
<li><span class="what">It cannot stop you overriding it.</span><span class="does">The owner's file is the owner's. Every status, tier and value in it can be edited by hand, and the tool will faithfully report whatever it finds there. What it will not do is compute a buy price from a value that has no record, or accept one typed in.</span></li>
<li><span class="what">It refuses to decide anything for you.</span><span class="does">This one is deliberate, and it is the design. See below.</span></li>
</ul>

<h2>Why the last one is on purpose</h2>
<p>Everything in this list except the last item is a limit the project would remove if it could. The last is the reason the project exists. A tool that decided would be trusted, and a trusted tool stops being checked, and a tool that is not checked is wrong in ways nobody notices until the money is gone. The tool's refusal to decide is what forces the owner to keep reading, every night, with the unfinished parts of the job named on the page. It is slower than being told. It is the only version of this that can be audited afterwards, by the owner, against a record the owner wrote before the outcome was known.</p>
""",
    [("The recorded limits", "repo: deploy/TUNNEL-NOTES.md; vss/heartbeat.py (what is not covered); reference/FRAMEWORK-EDITS.md E28, E29, E99, F1, F2")],
)

# ---------------------------------------------------------------------------
# 23. CLOSE
# ---------------------------------------------------------------------------
N = Notes()
chapter(
    "23-close", "The slow way, made survivable",
    "The method was written before the code, and the code cannot overrule it. Every refusal is measured. Every rule states its price, including the ones that were wrong and were withdrawn. This is not a shortcut.",
    4, True,
    f"""
<p>Start from where the site started. Two thousand companies, one person, no way to know from the inside whether a decision was careful or lucky. Here is what was built in answer, in one paragraph.</p>

<p>A written method, amended only by dated rulings the owner makes. A coarse screen that removes what can be faulted on public figures and finds nothing. A reading that uses only the company's own documents, with every figure carrying its origin and its period, and a valuation that prints nothing rather than a number with a gap. An inversion that asks what the price assumes instead of what the business is worth, and a rule that the owner's belief must be on record, dated, before that number exists. Three outcomes for every test, so that not knowing is never recorded as failing. A decision that is three written numbers, produced in order, before the money moves. A book of every refusal, measured against the market afterwards and read once a year. And a machine that runs every night, measures, remembers, and is built so that it cannot decide.</p>

<h2>Three things to take away</h2>
<p><strong>The method was written before the code, and the code cannot overrule it.</strong> Every threshold in the program cites the ruling that set it. A change to what the program does without a ruling behind it is, by the project's own standard, the wrong thing. The rules are above the code because rules written with no stake in the answer are the only rules worth having when there is one.</p>

<p><strong>Every refusal is measured.</strong> The method has said no to every name it has read closely. That record proves nothing on its own. The shadow book exists so that, a year from now, the owner can find out whether the refusals were expensive, and the ruling that created it says its purpose is "to be able to say the method does not work".</p>

<p><strong>Every rule states its price, including the ones that were withdrawn.</strong> A gate with two limbs that measured nothing was removed with the words "not widened, not softened, removed". A requirement on the phone page was ruled in the morning and withdrawn the same afternoon as unbuildable, with the reason written down. A citation in a commit message turned out to point at a section that does not exist, and the correction is on the record. These are not embarrassments. They are the evidence that the process corrects itself in writing, by the person entitled to correct it, rather than by drift.</p>

<h2>What this is</h2>
<p>The owner's own summary of the thesis is the one this site was built to carry: there are no easy ways to make money in this; it takes time, and knowledge is acquired with time, and the tool is that time, kept.</p>

<p>Nothing here will tell you what to buy. If you have followed it, you know what it takes to find out: a boundary you have written down, a screen that only removes, a reading from the source, a belief on record before the number, three outcomes, three numbers, and a book of what you turned away. This is not a shortcut. It is the slow way, made survivable.</p>
""",
    [("The rulings cited in this chapter", "repo: reference/FRAMEWORK-EDITS.md E30, E114, F1, F2; VSS-PROJECT-BRIEF-2026-09-10.md §0–§1")],
)
