"""Part One — the method. Chapters 1 to 12.

Every claim about the system is read from the repository (ruling numbers
and module names are given in the folds). Every claim about investing or
about where an idea came from is cited to a URL in the chapter's sources.
Jargon appears once, after the plain version, marked with <dfn>.
"""

from diagrams import ALL as FIG


class Notes:
    """Numbered notes, Tufte-style: the note is emitted inline at the point
    of reference as a span, so it floats beside the sentence on a wide
    screen and follows the sentence on a narrow one. flush() is kept for
    the templates and returns nothing."""

    def __init__(self):
        self.n = 0

    def ref(self, txt):
        self.n += 1
        n = self.n
        return (f'<a class="noteref" href="#n{n}" id="r{n}" aria-label="note {n}">{n}</a>'
                f'<span class="note" id="n{n}" role="note"><span class="nn">{n}</span>{txt}</span>')

    def flush(self):
        return ""


def fold(title, inner):
    return f'<details class="fold"><summary>{title}</summary><div class="inner">{inner}</div></details>'


def decision(decided, why, cost):
    return (f'<dl class="decision"><dt>Decided</dt><dd>{decided}</dd>'
            f'<dt>Why</dt><dd>{why}</dd><dt>Cost</dt><dd>{cost}</dd></dl>')


def example(inner, tag="Worked example: NAME A"):
    return f'<div class="example"><span class="tag">{tag}</span>{inner}</div>'


def wrong(inner, tag="The natural way, which is wrong"):
    return f'<div class="wrong"><span class="tag">{tag}</span>{inner}</div>'


def right(inner, tag="The rule"):
    return f'<div class="right"><span class="tag">{tag}</span>{inner}</div>'


CHAPTERS = []


def chapter(slug, title, lede, minutes, short, body, sources):
    CHAPTERS.append(dict(slug=slug, title=title, lede=lede, minutes=minutes,
                         short=short, body=body, sources=sources))


# ---------------------------------------------------------------------------
# 1. THE PROBLEM
# ---------------------------------------------------------------------------
N = Notes()
chapter(
    "01-the-problem", "The problem",
    "About two thousand companies you could buy a piece of, one person, a few evenings a week, and no way to know whether you are fooling yourself.",
    5, True,
    f"""
<p>Start with the size of it. On the exchanges one Swedish private investor can reach through an ordinary brokerage account, there are roughly two thousand companies large enough to be worth considering.{N.ref("The tool's own list holds 2,011 instruments across the large and mid-sized companies of the United States, Europe and the Nordic exchanges. See chapter 4.")} Each one publishes a report every three months. Each report runs to dozens of pages. Nobody with a job reads two thousand of them.</p>
{N.flush()}
<p>So people do not read them. They buy on a story instead. A friend mentions a company. A newspaper says a sector is hot. A price has gone up for a year, which feels like evidence. Or a price has fallen by half, which feels like a bargain. None of these is a reason. They are how a person ends up owning something they cannot describe, at a price they cannot justify, with no idea what would make them sell.</p>

<p>Here is the harder part. Suppose you decide to do it properly. You pick a company, read its reports, work out what you think it is worth, and buy it below that. Good. Now ask: how do you know your number was not bent by the price you had already seen? How do you know you did not read the report looking for reasons to buy, and find them, because people always find them? How do you know that the twenty companies you rejected were not the ones you should have bought, given that you never checked?</p>

<p>These are not rhetorical questions. They are the questions this whole project exists to answer, and the honest first answer to each is: you do not know. You cannot know from the inside. A person deciding alone has no way to tell a good decision from a lucky one, or a careful reading from a motivated one.</p>

<p>Everything that follows is a set of habits for a person who has accepted that, and a machine built to keep the habits in place when the person is tired, or excited, or has a stake in the answer.</p>

<h2>What the rest of this site is</h2>
<p>Part One is the method: what it means to buy a piece of a business for less than it is worth, how two thousand names become five, why most of the five are refused, and how a decision is written down so it cannot be quietly rewritten. Part Two is the machine: a small program on a rented server that runs every night, measures, and refuses to decide.</p>

<p>Nothing here is a shortcut. If you finish it you will not know which company to buy. You will know what it takes to find out, and why the finding out cannot be skipped.</p>
""",
    [("The tool's universe files and their count", "repo: config/universe/, VSS-PROJECT-BRIEF-2026-09-10.md §4.6")],
)

# ---------------------------------------------------------------------------
# 2. WHAT VALUE INVESTING IS
# ---------------------------------------------------------------------------
N = Notes()
chapter(
    "02-value", "What value investing is",
    "A piece of a real business is worth something. The market quotes a price for it every day. Those are two different numbers, and the gap between them is the whole opportunity.",
    9, True,
    f"""
{example('''
<p>NAME A is a company that makes something ordinary and sells it every year. Last year, after paying its staff, its suppliers and its taxes, and after spending what it needed to keep its factories working, it had 10 left over per share. It has done roughly that for a decade. It owes nobody very much.</p>
<p>That 10 per share of spare cash, year after year, is what you are actually buying when you buy one share. Not a ticker, not a chart. A claim on a stream of cash from a business that exists.</p>
''')}

<p>Here is the first idea, and it is the one everything else rests on. When you buy a share, you buy a fraction of a real business that earns real money. That fraction is called a <dfn>share</dfn>, and the company's spare cash after everything it must pay is called its <dfn>free cash flow</dfn>. The business is worth something: some amount that a sensible person would pay for the right to that stream of cash for as long as it lasts. That amount is its <dfn>value</dfn>.</p>

<p>The second idea: every trading day, the market quotes a number at which you can buy or sell that share. That number is the <dfn>price</dfn>. The price moves every minute. The value of the business does not. A factory does not become worth less between Tuesday and Wednesday because the people trading its shares got nervous.</p>

<p>Price and value are not the same number, and most of the time nobody knows how far apart they are. That is the opportunity. Benjamin Graham, who taught this at Columbia in the 1930s, put it in a sentence his student Warren Buffett has repeated for fifty years: "Price is what you pay; value is what you get."{N.ref("Buffett, letter to Berkshire Hathaway shareholders for 2008, page 4, crediting Graham. Source in the fold below.")}</p>
{N.flush()}

{FIG["price_vs_value"]()}

<p>Graham had a way of making the difference vivid. Imagine you own a share of a business together with a partner who is slightly unhinged. Every day he names a price at which he will buy your half or sell you his. Some days he is euphoric and names a silly high price. Some days he is despairing and names a silly low one. He does not mind being ignored. The mistake is to let his mood tell you what the business is worth. The opportunity is to sell to him when he is euphoric and buy from him when he is despairing, and otherwise to get on with your life.{N.ref("Graham, The Intelligent Investor, chapter 8; retold by Buffett in his 1987 letter: 'Mr. Market is there to serve you, not to guide you. It is his pocketbook, not his wisdom, that you will find useful.'")} Graham called the partner Mr Market.</p>
{N.flush()}

<h2>Margin of safety</h2>
<p>You will never know the value exactly. You will estimate it, and your estimate will be wrong by some amount you cannot know in advance. So you do not buy at your estimate. You buy well below it, and the distance between your estimate and the most you will pay is your room to be wrong.</p>

<p>Think of a road bridge. The engineer calculates it can carry a certain load, then posts a limit well below that. Not because the calculation is careless, but because the calculation is a calculation, the steel is real, and the truck is heavy. The gap between the posted limit and the calculated load is what lets the bridge survive the engineer's mistakes. Graham called the same gap, applied to buying a business, the <dfn>margin of safety</dfn>, and named it the central concept of investment.{N.ref("Graham, The Intelligent Investor (1949), chapter 20, 'Margin of Safety as the Central Concept of Investment'. The bridge picture here is the site's own; a similar one is often attributed to Buffett but could not be verified against a primary text and is not claimed as his.")}</p>
{N.flush()}

{FIG["margin_of_safety"]()}

<h2>Why patience is the mechanism, not a personality trait</h2>
<p>This is the part people get backwards. Patience sounds like a virtue you either have or do not. Here it is not a virtue. It is a step in the procedure.</p>

<p>If you have decided that NAME A is worth 100 and you will pay at most 85, then on every day the price is 93 the correct action is nothing. Not "wait and see". Nothing, as a decision, taken and recorded. The opportunity only exists because most participants cannot do nothing: they must be invested, or they must act on news, or they must show activity to someone. A person who can sit at 93 for a year and buy at 84 on the one day it gets there is not calmer than the others. They have simply written the number down in advance, and the number is doing the waiting for them.</p>

<p>Graham again, through Buffett: "In the short-run, the market is a voting machine, but in the long-run, the market is a weighing machine."{N.ref("Buffett, 1993 letter to shareholders, quoting Graham. Source in the fold.")} Votes are cheap and fast. Weight takes time to show. The method is built for the weighing.</p>
{N.flush()}

{fold("Where this comes from", '''
<ul>
<li>"Price is what you pay; value is what you get." Buffett, 2008 shareholder letter, page 4, crediting Graham. <span class="how">The site's author extracted the sentence from the letter's PDF.</span></li>
<li>Mr Market: Graham, The Intelligent Investor, chapter 8; Buffett's retelling, 1987 letter.</li>
<li>Voting machine and weighing machine: Buffett, 1993 letter, quoting Graham.</li>
<li>Margin of safety: Graham, The Intelligent Investor, chapter 20.</li>
</ul>
<p>Where this project differs from Graham: the cushion is a fixed fraction set by how well the business is understood (chapter 11), and it is written down before the price is looked at (chapter 8). Graham described the principle; the project makes it a rule with a number.</p>
''')}
""",
    [
        ("Buffett, 2008 letter to shareholders (page 4: 'Price is what you pay; value is what you get')", "https://www.berkshirehathaway.com/letters/2008ltr.pdf"),
        ("Buffett, 1987 letter to shareholders (Mr Market)", "https://www.berkshirehathaway.com/letters/1987.html"),
        ("Buffett, 1993 letter to shareholders (voting machine, weighing machine)", "https://www.berkshirehathaway.com/letters/1993.html"),
        ("Margin of safety (financial), Wikipedia", "https://en.wikipedia.org/wiki/Margin_of_safety_(financial)"),
    ],
)

# ---------------------------------------------------------------------------
# 3. THIS PROJECT'S FLAVOUR
# ---------------------------------------------------------------------------
N = Notes()
chapter(
    "03-this-project", "This project's flavour",
    "One person's version of the method, with four habits that make it unusual, and a tool built around those habits rather than around a market.",
    6, False,
    f"""
<p>Value investing is a broad church. This is one person's version of it, and it was described by the owner, in the owner's own words, before any of it was built:</p>

<blockquote><p>"a tool that we can read reports and follow the stocks we have catched with the screener and then evaluated and make a tool that gives me the ability to follow the companies and then make an educated 'guess' and buy it when i think it is undervalued and we can make some cash"</p><cite>The owner, describing the project.</cite></blockquote>

<p>Read that carefully, because every part of it turned into a rule. <em>Read reports</em>: the figures come from the company's own filings, not from a data vendor's summary. <em>Catched with the screener</em>: a coarse mechanical pass over two thousand names finds the few worth reading. <em>Follow the companies</em>: a watchlist, checked nightly. <em>An educated guess</em>: the owner's own view of how the business will grow, written down as a view, not dressed up as a forecast. <em>Buy it when I think it is undervalued</em>: the owner decides. Not the tool.</p>

<h2>Four habits that make this version distinctive</h2>

<h3>1. Figures come only from the company's own filings</h3>
<p>A number in this system has to come from the report the company itself published: its quarterly or annual accounts, or a regulatory filing. Not a news article about the report. Not a vendor's cleaned-up version. Every figure carries where it came from, which period it covers, and the page it was read from. A figure without that is not a figure; it is a rumour with decimal places. Chapter 6 shows what this costs and why it is paid.</p>

<h3>2. The owner's view is written before the market's number is seen</h3>
<p>The method works out what growth the current price is assuming (chapter 7). Before that number is calculated, the owner writes down what growth he actually believes, with reasons, and the file is timestamped. If the market's number was seen first, the owner's view is void for that company in that round. Chapter 8 explains why this rule exists and what it borrows from clinical trials.</p>

<h3>3. A failed test is final, and never widened to let a name through</h3>
<p>When a company fails a test on something other than price, a lower price does not bring it back. Only a named new fact can: a new filing, a changed forecast from the company, a profit warning. And when a rule turns out to be badly designed, it is deleted or replaced by a dated ruling that says what the change cost. It is not quietly loosened because a particular name was almost through. Chapters 5 and 16.</p>

<h3>4. Every refusal is tracked</h3>
<p>Most of what the method looks at, it refuses. A system that only measures what it bought cannot tell whether its refusals were right. So every refusal is recorded with the price on the day and one line naming the reason, and measured against the market afterwards. Chapter 12.</p>

<h2>What this is not</h2>
<p>It is not a trading system. It does not predict prices, it has no view on next week, and it will never tell you to buy anything. It is a way of reading, deciding and recording, for a person who has accepted that most of the time the right answer is no, and who wants to be able to check afterwards whether the no was right.</p>

{decision(
    "The tool measures; the owner decides. No automated step may write a verdict, enter a company into the process, assign a confidence level or set a buy price.",
    "A person deciding alone cannot tell a careful reading from a motivated one. A machine that also decided would inherit the person's motivations and add its own errors. Keeping the decision with the person, and the measurement with the machine, makes each auditable.",
    "The owner does all the judging, by hand, every time. Nothing is faster for it. The machine cannot rescue a bad decision; it can only make sure the decision was written down before the outcome was known.",
)}
""",
    [("The owner's description of the project, verbatim", "repo: the brief for this site"),
     ("What automated steps may and may not do", "repo: reference/FRAMEWORK-EDITS.md rulings E92, E93, E97; README.md")],
)

# ---------------------------------------------------------------------------
# 4. THE SCREENER
# ---------------------------------------------------------------------------
N = Notes()
chapter(
    "04-the-screen", "The screener: two thousand to a handful",
    "A coarse mechanical pass that removes what can be faulted on public figures, so that a person's reading time goes only to what survives. It finds nothing. It only removes.",
    10, False,
    f"""
<p>Two thousand names, one reader. The only way through is to remove most of them without reading them, using questions coarse enough that a machine can ask them of public figures. That pass is the <dfn>screener</dfn>, and the most important thing to understand about it is what it does not do: it does not find good companies. It removes companies that fail a small number of coarse tests, and hands whatever is left to a person.</p>

{FIG["screen_filter"]()}

<h2>Where the two thousand come from</h2>
<p>The list is fixed and dated: the members of the main American, European and Nordic indices for large and mid-sized companies, written to files on a stated day and kept under version control. The list is never fetched live, so a run on any day can be repeated later on exactly the same names.{N.ref("The universe files under config/universe/ carry their date in the filename; index membership is never fetched at run time (vss/universe.py). 2,011 instruments on 2026-09-10.")} Funds, trusts, blank-cheque companies and foreign-listing wrappers are removed on the source list's own type field, never by guessing from the name.</p>
{N.flush()}

<h2>The steps, in order, and why each question is asked</h2>

<h3>Step 0: names already owned or already decided</h3>
<p>A small exclusion list of companies the owner already holds or has already ruled on. There is no point screening a name whose answer is known. An entry on that list that matches nothing is reported as inert, so the list cannot quietly rot.</p>

<h3>Filter 1: has the price fallen enough, but not too much?</h3>
<p>The method is looking for businesses the market has temporarily lost interest in. So the first question is whether the price sits between 15 and 50 percent below its highest point of the last year. Less than 15 and nothing has happened. More than 50 and the working assumption is that something is actually broken, which is a different kind of company and out of scope.{N.ref("Framework §3 gate 1; the band is implemented once in vss/rules.py and reused by both the screener and the nightly run.")}</p>
{N.flush()}
<p>Two more questions ride with this one. Has the company been listed for at least five years? A younger listing does not have enough reported history to test, and a company spun out of another counts as new.{N.ref("Ruling E52 and E52.1: a listing younger than five years is rejected on missing data, and a spin-off is a new listing.")} And is the business one the method can judge at all? Chapter 5 covers that boundary.</p>
{N.flush()}

<h3>Filter 2: can the business be faulted on three coarse figures?</h3>
<p>For the survivors, and only the survivors, the tool fetches accounts and asks three questions. Did the business generate spare cash over the last twelve months? Is its debt, net of cash, no more than two and a half times its yearly operating earnings before interest, tax, depreciation and amortisation, a figure abbreviated as <dfn>EBITDA</dfn>? And has revenue avoided falling, against the same quarter a year earlier, two quarters in a row?{N.ref("Thresholds live in config/screener_filter2.yaml, each citing its framework section: free cash flow positive (a coarsening of gate 3's six-of-eight quarters, because quarterly cash-flow history is unavailable for much of the list); net debt to EBITDA at most 2.5×, ruling E44; two consecutive year-on-year quarterly revenue declines kill, ruling E45.")}</p>
{N.flush()}
<p>The debt cap has its own history. The first version used a looser limit, three and a half times, on the argument that a coarse filter must not lose a name the careful reading would keep. Four days later a test run showed 72 names passing the loose limit and then failing the method's own stricter test later on. Letting them through bought nothing but reading time. The cap was tightened by a dated ruling that records the count.{N.ref("Rulings E2 (2026-08-22, 3.5×) and E44 (2026-08-26, 2.5×), with the 72-name measurement in the ruling text.")}</p>
{N.flush()}

<h3>Ranking: which survivors get read first</h3>
<p>What is left is ordered on two figures. How profitable is the business relative to everything it owns, measured as operating profit over total assets. And how cheap is it relative to what the whole business would cost to buy, measured as operating profit over that cost. Each survivor is ranked on both, the two rank positions are added, and the list is sorted. No weights, no score, no threshold.{N.ref("Ruling E6 as amended by E43. An earlier version used a profitability measure whose denominator went to zero for businesses that own little, so the top thirteen placings went to the thirteen names nearest that pole; it was replaced.")} Banks, insurers and property companies cannot be ranked on the first figure and are listed separately on the second alone, never mixed in.</p>
{N.flush()}

<h3>What comes out</h3>
<p>The top twenty are watched for price movements. Three to five are proposed for reading. None of them carries a value, a buy price or a confidence level. The screener's output is a reading list, and a person reads it.</p>

<h2>What a screen cannot see</h2>
<ul>
<li><strong>Why the price fell.</strong> A 30 percent fall on a rumour and a 30 percent fall on a fraud look identical to filter 1. The reason is the first thing the reader has to find out, and it is the subject of the next chapter.</li>
<li><strong>Anything the vendor's figures get wrong.</strong> The accounts come from a data vendor at this stage, not from the filings. A wrongly labelled line passes through unnoticed. One such line was found only because it failed to match any filed figure for any of five companies checked by hand.{N.ref("Ruling E43: the vendor's 'gross profit' line did not reconcile to any filed line for any of five test names, and was replaced by operating profit in the ranking.")}</li>
<li><strong>A name it never fetched accounts for.</strong> Accounts are fetched only for filter 1's survivors. A test that reads an industry label cannot see a company that never got that far. That silence is a fact about the fetch, not about the company, and the tool says so.{N.ref("Ruling E96: 'The string limb is blind where the fetch has not reached.'")}</li>
<li><strong>Whether a company is any good.</strong> Nothing in this chapter is a judgement. It is a list of things that were not faulted on a coarse test.</li>
</ul>
{N.flush()}

<p>One more honesty. The screener replays past dates using today's accounts against that day's prices, because the vendor serves only the latest accounts. A replay is therefore not evidence of what the screen would have found on that day, and every replay report says so in a banner at the top.</p>

{fold("The exact rules", '''
<p>Framework §3 (gates 1 to 5) and the screener rulings E2, E6, E43, E44, E45, E46, E48, E52, E93, E96, E97 in <code>reference/FRAMEWORK-EDITS.md</code>. Thresholds: <code>config/screener_filter2.yaml</code>. Code: <code>vss/screen.py</code>, <code>vss/filters.py</code>, <code>vss/universe.py</code>, <code>vss/ranking.py</code>. Two technical figures, a momentum indicator and a moving average, are computed and printed but never used as filters, because on a real past purchase either direction of such a filter would have discarded one of the two relevant days.</p>
''')}
""",
    [("Screener design and rulings", "repo: reference/FRAMEWORK-EDITS.md E2, E6, E43, E44, E45, E52, E93, E96, E97; config/screener_filter2.yaml; vss/screen.py; vss/filters.py")],
)

# ---------------------------------------------------------------------------
# 5. WHY A NAME IS REFUSED
# ---------------------------------------------------------------------------
N = Notes()
chapter(
    "05-refusal", "Why a name is refused, and why that is the normal outcome",
    "Most companies that reach the reader are sent away. The gates are designed to say no, a failed gate stays failed, and refusing to judge a business you cannot judge is a real answer.",
    9, False,
    f"""
<p>By the time a name reaches a person, it has survived a coarse screen. It is cheap-ish, it makes money, it has not obviously broken. The temptation is to think the hard part is done. It is not. The reading is where most names are refused, and refusal is the expected result, not a disappointment.</p>

<h2>The gate that does most of the refusing: why did the price fall?</h2>
<p>The screen found companies whose price fell. The reader's first job is to name the reason, and put it in one of four boxes.</p>
<ul>
<li><strong>A: the mood changed.</strong> Nothing about the business changed; the story people tell about it did.</li>
<li><strong>B: the whole sector was sold.</strong> Money left an industry and took this company with it.</li>
<li><strong>C: a one-off cost with a number on it.</strong> A fine, a write-down, a factory fire. It happened once and its size is known.</li>
<li><strong>D: something is actually broken.</strong> A product that no longer sells, a customer that left, a regulator that has changed the rules for good.</li>
</ul>
<p>A, B and C pass. D fails, and the rule is stricter than it looks: if the reader cannot say with confidence which box it is, it is D.{N.ref("Framework §3 gate 2: four disconnect classes; 'if you cannot classify confidently, it is D.' A real name was dropped on class D on 2026-09-08.")} Not knowing why a price fell is not neutral. It is the most common way to buy a broken business.</p>
{N.flush()}

{example('''
<p>NAME A's price is 35 percent below last year's high, so it passed filter 1. The reader opens the last four reports. Revenue is flat. The fall began the week the company's largest customer, a fifth of its sales, announced it would make the product itself from next year. That is a lost customer that is not coming back: box D. NAME A fails gate 2 and leaves. Its cheapness was never the question.</p>
''')}

{FIG["name_fails_gate"]()}

<h2>The other gates</h2>
<p>A name that passes the "why" gate is then tested on its accounts over the last two years: debt within a stated multiple of earnings, interest covered at least five times by operating profit, spare cash generated in at least six of the last eight quarters, no auditor's doubt about the company continuing, no change of auditor, no restated accounts. Then it needs a dated event within ninety days that could make the market look again: a results date, a product decision, a ruling. "Eventually the market will realise" is not an event.{N.ref("Framework §3 gates 3 and 5. Gate 4, a valuation discount against peers, is recorded as DATA MISSING for every name because the peer figures it needs have never been assembled; it is not deleted, and returns when they exist (ruling E99).")}</p>
{N.flush()}

<p>Then there are seven <dfn>hard kills</dfn>: things that end the reading on their own, whatever else looks good. Revenue falling two quarters running. Margins shrinking while revenue is flat. Two cuts to the company's own forecast in a year. Three missed earnings in two years. Debt above a stated multiple or close to breaking a lending agreement. Both the chief executive and the finance chief leaving within a year. Stock or unpaid invoices piling up faster than sales.{N.ref("Framework §4.2. 'Any one invalidates.'")}</p>
{N.flush()}

<h2>Why a failed gate is final</h2>
{wrong('''
<p>NAME A failed on a lost customer at a price of 60. Six months later the price is 40. Surely at 40 it is worth another look? The price has done half the work.</p>
''')}
{right('''
<p>The price was never the problem. NAME A failed on a fact about its business, and at 40 that fact is still true. A name that failed on something other than price is parked as <dfn>WATCH-GATED</dfn>, and the only thing that can bring it back is a named new fact: a new filing, a changed forecast, a warning. A price level cannot reopen it, because a price alert would wake it into the same gate it is already known to fail.</p>
''', "The rule, and why")}
<p>This is written into the method as a ruling with a number, and it is the reason the tool keeps two kinds of waiting list apart. A name that is merely too expensive waits for a price. A name that failed a gate waits for a fact.{N.ref("Ruling E27 splits the old single 'watch' status into WATCH-PRICED and WATCH-GATED; the retired spelling is refused by the code with a message pointing at the ruling.")}</p>
{N.flush()}

<p>The same finality applies to the rules themselves. When two limbs of a gate were found to measure nothing useful, they were removed, and the ruling that removed them says "not widened, not softened, removed". A rule is either in force or it has been retired by a dated decision. There is no third state where it is bent for a name that nearly passed.{N.ref("Ruling E30, 2026-08-25, deleting two limbs of gate 3 that measured the volatility of reported figures rather than the quality of the business, having changed no verdict across five names.")}</p>
{N.flush()}

<h2>The circle: refusing what you cannot judge</h2>
<p>Some businesses are refused before any gate, not because they are bad but because the method cannot be run on them honestly. The method needs the owner to write down a believable range for how the business will grow (chapter 8). For some businesses that is not a judgement anyone can make.</p>
<ul>
<li>A company whose revenue is a world price it does not set, multiplied by a volume: a miner, an oil producer, a bulk shipper. Its bad case is not slower growth but a halved price, which is a different business, not a lower number in the same arithmetic.{N.ref("Ruling E96, 2026-08-31: 'This is a limit of the METHOD, and it is not a judgement about the industry.' Sixteen industry patterns; regulated utilities, contracted output and semiconductors expressly excluded from the rule.")}</li>
<li>A drug developer, whose growth is a guess about approvals the owner has no way to assess.{N.ref("Ruling E51.")}</li>
</ul>
{N.flush()}
<p>Buffett's phrase for this is the <dfn>circle of competence</dfn>: "The size of that circle is not very important; knowing its boundaries, however, is vital."{N.ref("Buffett, 1996 letter to shareholders.")} What this project adds is that the boundary is written down as a rule and enforced by the screen, so that a spectacularly cheap miner cannot tempt anyone into pretending the method applies. Such a name is never watched at all, not even on its price, because there is no level it could reach that would mean anything.{N.ref("Ruling E97: a name outside the circle 'is NEVER WATCHED AT ALL, not even on its drawdown'.")}</p>
{N.flush()}

<p>Refusing a business you cannot judge is not a cop-out. It is the only answer that does not require pretending.</p>

{fold("The exact rules", '''
<p>Framework §3 (gates), §4.2 (hard kills), §4.4 (conviction score). Rulings E27 (the two waiting lists), E30 (deletion of two limbs), E51 and E96 (the circle), E97 (never watched), E99 (gate 4 as DATA MISSING). Code: the status list in <code>vss/rules.py</code>, the circle lists under <code>config/</code>.</p>
''')}
""",
    [
        ("Buffett, 1996 letter to shareholders (circle of competence)", "https://www.berkshirehathaway.com/letters/1996.html"),
        ("Circle of competence, Wikipedia", "https://en.wikipedia.org/wiki/Circle_of_competence"),
        ("Gates, hard kills and the circle rulings", "repo: reference/FRAMEWORK.md §3–§4; reference/FRAMEWORK-EDITS.md E27, E30, E51, E96, E97, E99"),
    ],
)

# ---------------------------------------------------------------------------
# 6. WHAT GETS READ
# ---------------------------------------------------------------------------
N = Notes()
chapter(
    "06-what-gets-read", "What gets read",
    "Only the company's own filings. Every figure with its origin, period and page. Nothing stretched, scaled or annualised to fill a gap. A concrete example of the wrong kind of number and what believing it would cost.",
    8, False,
    f"""
<p>Once a name survives the gates, the reading changes character. The screen used a vendor's summary of the accounts because that is the only thing that scales to two thousand names. From here on, every figure that will touch a decision comes from the document the company itself published.</p>

<h2>The rule, in one sentence</h2>
<p>A figure is admissible if it can be pointed to: this filing, this period, this page. Everything else is hearsay.</p>

<p>That sounds obvious and is violated constantly. A data vendor's "revenue" might be the company's revenue, or it might be revenue with one segment reclassified, or it might be last year's number the vendor has not updated. A news article's "profit rose 12 percent" might be operating profit, net profit, or adjusted profit on the company's own definition. None of these are lies. They are just not the figure, and a person who builds a valuation on them has built it on something they cannot check.</p>

<p>So the tool's reading code fetches only company filings and regulatory documents, and refuses to follow links or search.{N.ref("The source module's own description: 'Primary source ONLY: a company IR release or a regulatory filing. Never a news article about one. This module does not search, guess or follow links.'")} For American companies it reads the structured data companies must file with the regulator. For Nordic companies it reads the exchange's own disclosure feed. For everything else, a person reads the PDF and types the figure in, with the page number beside it.</p>
{N.flush()}

<h2>Every figure carries three things</h2>
<ol>
<li><strong>Where it came from.</strong> The document, and the page or the tag within it.</li>
<li><strong>What period it covers.</strong> A quarter, a half year, a year, and which one.</li>
<li><strong>Whether a person has checked it.</strong> A figure enters as unchecked. It becomes checked only when the owner has read it back against the page named beside it, and the record says which kind of check it survived: matched to the regulator's structured data, matched across two separate documents, or read back against the same page it came from, which is the weakest kind and says so.{N.ref("Ruling E40 and the verification kinds in vss/manual.py: tagged, cross-document, same page. Unchecked is not the same state as absent: 'UNVERIFIED is the state a figure is entered in, and it is what section 5 refuses on. It is NOT the same state as absent.'")}</li>
</ol>
{N.flush()}
<p>The valuation refuses to run on an unchecked figure. Not warns: refuses, and the command exits with an error. A figure nobody has read back is a figure nobody has read.</p>

<h2>Nothing is stretched to fit</h2>
<p>The valuation works on twelve months of cash flow. Suppose the company has reported three quarters of this year and you want a full year. The tempting move is to take the nine months and multiply by four thirds. The method forbids it. A figure of the wrong length is missing, not a figure adjusted to fit.{N.ref("Framework §5 basis rule (rulings E19, E20): 'Nothing here is annualised and nothing is scaled — a figure of the wrong length is DATA MISSING, never a figure adjusted to fit.'")} Twelve months are assembled from four actual quarters, all four checked, and the report names all four beside the figure. A twelve-month figure that ends on a different date from the other figures in the same calculation is also refused, with both dates printed, because two windows are not a ratio.</p>
{N.flush()}
<p>The same strictness applies to things that look trivial. A share count must be stated by the company, not derived. A zero is a claim about the company and needs a basis: the line exists and reads zero, or the company says the item is nil, or the whole report was searched and the record says so. A figure converted from one currency to another names the rate and the date, and a change of unit is not a rate.{N.ref("Rulings E22 and following (the share count), E25 (a zero is a claim), E98 (a rate and a date; a unit is not a rate).")}</p>
{N.flush()}

<h2>The wrong kind of number, and what it would have cost</h2>
{example('''
<p>NAME A is listed in London. Its shares are quoted in pence. Its accounts, and therefore the owner's estimate of its value, are in pounds. The first draft of the tool's overview page took the value in pounds, the price in pence, and computed how far apart they were. The answer it printed was that the price was about 12,700 percent away from the value.</p>
<p>Nobody would have bought on that number; it was absurd on sight. But the same defect, on a name where the units differed by a factor of ten instead of a hundred, would have printed a distance that looked merely surprising. The fix was not to convert. It was to refuse: where the two currencies are not the same code, the distance is missing and the seam is named.</p>
''', "A real defect, with the name removed")}
<p>The defect and the rule that replaced it are written into the page generator's own comments, so the next person to touch that code meets the number before the arithmetic.{N.ref("The page generator's own rule: 'NO ARITHMETIC CROSSES A UNIT SEAM ... A distance computed across it would read as roughly −12,700%, which is the shape of the defect this project has already met once.' The first draft printed +10,543% on one name and +12,791% in a dry-run table.")}</p>
{N.flush()}

<p>A second example from the same family. A data vendor's price history for one large company switched, for four weeks, between two scales: one adjusted for a share split and one not. The computed fall from the year's high was 52 percent. The true figure was about 4. A check was built that treats a jump one way followed by a matching jump back as proof of two scales in one column, because real corporate events do not reverse themselves, and that treats a lone jump as suspect unless the day traded at many multiples of normal volume, which real repricings do and feed errors do not.{N.ref("vss/series_sanity.py, ruling K4. Measured: two real large single-day moves traded at roughly 24× and 14× their median volume; the corrupted halvings traded at 0.7× to 2.6×.")}</p>
{N.flush()}

<p>Believing either number would not have cost a wrong purchase directly. It would have cost something worse: a system whose figures nobody could trust, and therefore a system nobody would use on the night it mattered.</p>

{decision(
    "Figures come only from the issuer's own documents, carry origin, period and page, and are never scaled, annualised or borrowed across windows. The valuation refuses to run on a figure nobody has read back.",
    "A figure that cannot be pointed to cannot be checked, and a figure that cannot be checked will eventually be wrong on the night it matters.",
    "Reading is slow. Some companies cannot be valued at all for months because a figure they never state is missing. The tool says which figure, and waits.",
)}
""",
    [("Primary-source and provenance rulings", "repo: vss/source.py; reference/FRAMEWORK.md §5 basis rule; reference/FRAMEWORK-EDITS.md E19, E20, E22, E25, E40, E98; vss/overview.py (the unit seam); vss/series_sanity.py (ruling K4)")],
)

# ---------------------------------------------------------------------------
# 7. THE REVERSE DCF
# ---------------------------------------------------------------------------
# Static table for the explorable (same arithmetic as site.js)
def _value_at(g, fcf0=10.0, rate=0.095, term=0.025, years=10):
    v, cf = 0.0, fcf0
    for t in range(1, years + 1):
        cf *= (1 + g)
        v += cf / (1 + rate) ** t
    v += cf * (1 + term) / (rate - term) / (1 + rate) ** years
    return v


def _implied(price):
    lo, hi = -0.9, 1.0
    for _ in range(100):
        mid = (lo + hi) / 2
        if _value_at(mid) < price:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


_rows = "".join(f'<tr><td class="num">{p}</td><td class="num">{_implied(p)*100:.1f}%</td></tr>' for p in (100, 130, 160, 200, 250, 320))

N = Notes()
chapter(
    "07-reverse-dcf", "The reverse DCF",
    "Do not ask what a business is worth. Ask what the price is assuming, and whether you believe it. Same arithmetic, run backwards, and a different kind of question comes out.",
    10, True,
    f"""
<p>Here is the usual way to value a business. You guess how fast its cash flow will grow. You add up the cash you expect it to throw off for the next ten years, discounted because money later is worth less than money now, and add something for the years after that. Out comes a number. You compare the number to the price. That procedure has a name, <dfn>discounted cash flow</dfn>, usually shortened to DCF.</p>

<p>It has a well-known problem. The number that comes out depends almost entirely on the growth you guessed, and the growth you guessed depends, if you are honest, on what you already wanted the answer to be. "What is it worth?" is a question that invites you to deceive yourself, because any answer can be reached by choosing the guess.</p>

<h2>The inversion</h2>
<p>Now run the same arithmetic backwards. Start from the price the market is quoting today. Ask: what growth rate would the business need, for the next ten years, for that price to be exactly fair? The arithmetic is identical; you are solving for a different unknown. Out comes not a value but an assumption: the growth the market is currently betting on.</p>

<p>That number can be judged. "Is this business going to grow its cash at 14 percent a year for a decade?" is a question a person who has read the reports can have an opinion about. It has a shape. You can look at what the company has done for the last ten years, what its market is doing, what it would have to sell to get there, and say: I do not believe that. Or: I believe more than that. "What is it worth?" is unanswerable. "Do I believe that?" is a judgement, and judgements are what people are for.</p>

{FIG["dcf_vs_reverse"]()}

<h2>An analogy</h2>
<p>A used car is advertised at a price. You could try to work out what the car is "worth", and you would find that the answer depends on how many years of trouble-free driving you assume. Or you could ask the other question: at this price, how many years of trouble-free driving is the seller asking me to believe in? If the price only makes sense if the car runs another twelve years without a repair, and it has 200,000 kilometres on it, you have your answer, and you got it without ever needing to know what the car is "worth".</p>

<h2>Try it</h2>
<p>NAME A produces 10 per share in spare cash a year. Fix the arithmetic the way this project fixes it: ten years of growth, then a terminal growth of 2.5 percent a year, all discounted at 9.5 percent. The only free number is the growth rate. Here is what various prices are assuming.</p>

<div class="tbl"><table>
<thead><tr><th class="num">Price per share</th><th class="num">Growth the price assumes, per year for ten years</th></tr></thead>
<tbody>{_rows}</tbody>
</table></div>

<div class="explore js-only" id="rdcf-explore" hidden>
<label for="rdcf-price">Move the price and watch the assumption move</label>
<input type="range" id="rdcf-price" min="80" max="400" step="5" value="160">
<output id="rdcf-price-out" for="rdcf-price"></output>
<output id="rdcf-out" aria-live="polite"></output>
<p class="hint">Same arithmetic as the table. With scripts off, the table is the figure.</p>
</div>

<p>Read the table from the right. At 100, the price assumes the cash barely grows. At 250, it assumes growth that very few businesses sustain for a decade. The method does not tell you which is true. It tells you what you would have to believe, and hands the believing back to you.</p>

<h2>How this project fixes the arithmetic, and what it admits</h2>
<p>The inputs are the twelve-month spare cash from the filings, the company's net debt, and a share count the company has stated. The horizon is ten years, the growth after that 2.5 percent. The discount rate is 9.5 percent, and the method is unusually candid about what that number is: not an estimate of what the market demands, but the owner's own hurdle, set at what an index fund is expected to return over the long run plus two to three points for carrying the risk of one company. It is the same for every company, which knowingly demands a little more of a Swedish business than an American one, and the report prints the bias rather than hiding it. In the ruling's own words, the rate "will never be verified against anything. It is a preference and says so."{N.ref("Ruling E29. The engine: vss/valuation.py. Every buy price is printed with its value at a rate half a point lower and half a point higher, so the reader sees how much the number leans on the preference.")}</p>
{N.flush()}

<h2>Where the idea comes from</h2>
<p>Reading the growth embedded in a price, rather than forecasting growth to find a price, was worked out and popularised by Alfred Rappaport and Michael Mauboussin in <em>Expectations Investing</em>, first published in 2001. Their summary of the method is two steps: read the price, then anticipate the revision.{N.ref("Rappaport and Mauboussin, Expectations Investing (Harvard Business School Press 2001; revised edition Columbia 2021). Their site states the method as 'Read the price. Then anticipate the revision.'")} Aswath Damodaran teaches the same inversion under the name implied growth. This project borrows the inversion whole. Where it departs is in what happens next: Rappaport and Mauboussin compare the market's assumption with the analyst's; this project requires the analyst's view to be on record before the market's number is even calculated. That is the next chapter.</p>
{N.flush()}

{fold("The exact rule", '''
<p>Framework §5 as rebuilt by rulings E28 and E29: the reverse DCF is the sole engine; two older methods, comparing to past multiples and to peers, are shown beside it as context and never averaged in. Inputs: filed twelve-month free cash flow, net debt, a stated share count. Horizon ten years, terminal growth 2.5 percent, hurdle 9.5 percent, solved by bisection for the growth rate that makes the equity value per share equal the price. Code: <code>vss/valuation.py</code>, function <code>implied_growth</code>.</p>
''')}
""",
    [
        ("Rappaport and Mauboussin, Expectations Investing (book site)", "https://www.expectationsinvesting.com/"),
        ("The reverse DCF engine and the hurdle rate", "repo: vss/valuation.py; reference/FRAMEWORK-EDITS.md E28, E29"),
    ],
)

# ---------------------------------------------------------------------------
# 8. PRE-REGISTRATION
# ---------------------------------------------------------------------------
N = Notes()
chapter(
    "08-pre-registration", "Pre-registration: write the belief before you see the number",
    "Calculate what the price assumes first and whatever you write afterwards lands suspiciously close to it. Every human does this. So the belief is written first, timestamped, and a view written after the number was seen is void.",
    10, True,
    f"""
<p>The last chapter ended with a question: do I believe the growth the price is assuming? Here is the problem with answering it.</p>

{wrong('''
<p>You calculate that NAME A's price assumes 11 percent growth a year. Now you sit down to write what you think NAME A will actually grow. You have read the reports. You think about it carefully. You write down 10 percent, with reasons.</p>
<p>The reasons are real. The number is not. It is 11 with a small discount for modesty. If the price had assumed 6 percent, you would have written 5 or 7, with equally real reasons. The number you saw first became the centre of the range you thought you were choosing freely.</p>
''', "The natural order, which is wrong")}

<p>This is not a character flaw. It is one of the most reliably reproduced findings in the study of judgement. In a 1974 experiment, people watched a wheel of fortune stop at a number, then estimated what share of African countries belonged to the United Nations. The wheel was rigged to stop at 10 or at 65. The people who saw 10 guessed about 25 percent; the people who saw 65 guessed about 45. They knew the wheel was random. It did not help.{N.ref("Tversky and Kahneman, 'Judgment under Uncertainty: Heuristics and Biases', Science 185 (1974). The effect is called anchoring.")} A later study gave estate agents a tour of a house and a listing price; the agents' valuations tracked the listing price they had been shown, and they denied being influenced by it.{N.ref("Northcraft and Neale, 'Experts, Amateurs, and Real Estate', Organizational Behavior and Human Decision Processes 39 (1987).")}</p>
{N.flush()}
<p>Add to this the tendency to read evidence in favour of the belief you already hold, documented in hundreds of studies under the name <dfn>confirmation bias</dfn>,{N.ref("Nickerson, 'Confirmation Bias: A Ubiquitous Phenomenon in Many Guises', Review of General Psychology 2 (1998).")} and the picture is clear. A person who has seen the market's number and then writes their own is not writing their own.</p>
{N.flush()}

<h2>The rule</h2>
{right('''
<p>Before the growth implied by the price is calculated, the owner writes three growth rates, a low case, a base case and a high case, each with its reasons, into a file that is timestamped and kept under version control. Only then is the implied number solved. If the implied number was seen first, the view is void for that company in that round, and cannot be used.</p>
''', "The rule, in force since 2026-08-25")}

{FIG["two_orderings"]()}

<p>The ordering is the whole mechanism. Nothing about the arithmetic changes. What changes is that the owner's belief exists as a dated record before the number that could have bent it. When the two are compared, the comparison means something: either the market is asking for more growth than the owner believes, or less, and the owner's side of that comparison was not manufactured to fit.</p>

<p>The record is enforced by the version-control history, which cannot be edited without leaving a trace. A superseded view is not deleted; it is marked as superseded and left in the file, so that the sequence of what the owner believed, and when, is preserved.{N.ref("Ruling E28: 'A view written after the implied growth has been seen is VOID and may not be used for that name in that cycle.' Ruling E95: a superseded view is marked, kept, and refused by the code. The view files record what figures had already been printed before the view was written, which is what makes a late view detectable.")}</p>
{N.flush()}

<h2>Where this comes from: the clinical trial</h2>
<p>Science had exactly this problem and solved it the same way. A researcher who collects data first and then decides what hypothesis to test can always find something that looks significant, by choosing after the fact which outcome to report. The practices have names: <dfn>p-hacking</dfn>, trying analyses until one works; <dfn>HARKing</dfn>, hypothesising after the results are known; <dfn>outcome switching</dfn>, quietly reporting a different outcome from the one the trial was designed to measure.{N.ref("Simmons, Nelson and Simonsohn, 'False-Positive Psychology', Psychological Science 22 (2011); Kerr, 'HARKing', Personality and Social Psychology Review 2 (1998); Chan et al., JAMA 291 (2004), finding that 62 percent of trials had at least one primary outcome changed, introduced or omitted against the protocol.")}</p>
{N.flush()}
<p>The fix was <dfn>pre-registration</dfn>: write down the hypothesis and the outcome you will measure, in a public registry, before collecting the data. The evidence that it matters is stark. A study of large, expensive heart-disease trials funded by one American agency found that 57 percent of trials published before 2000 reported a significant benefit. After 2000, when registration in advance became required, that fell to 8 percent. Same kind of trial, same kind of funding. The difference was that the answer could no longer be chosen after the fact.{N.ref("Kaplan and Irvin, 'Likelihood of Null Effects of Large NHLBI Clinical Trials Has Increased over Time', PLOS ONE 10 (2015): '17 of 30 studies (57%) published prior to 2000 showed a significant benefit' against '2 among the 25 (8%) trials published after 2000'; 'Pre-registration in clinical trials.gov was strongly associated with the trend toward null findings.'")}</p>
{N.flush()}

<p>This project borrows the mechanism whole. The hypothesis is the growth view. The data is one number, the growth implied by the price. The registry is a file under version control. The penalty for looking first is that the view does not count.</p>

<h2>What it costs, said plainly</h2>
<p>The method's estimate of value now rests on a growth assumption that is a stated opinion and will never be verified. The ruling that introduced it says so in those words. Earlier rulings had raised the evidence bar on figures that move the answer by less than one percent; this one moves it by thirty. The project's answer is that verification effort should follow how much a number matters, not how easy it is to check, and that the one number that matters most is the one that can only be protected by ordering, because it cannot be checked at all.{N.ref("From the framework's §5 as amended by E28: 'Verification effort follows sensitivity, not availability.'")}</p>
{N.flush()}

{fold("Where this comes from", '''
<ul>
<li>Anchoring: Tversky and Kahneman, Science 185 (1974), the wheel-of-fortune experiment. Northcraft and Neale (1987) on estate agents.</li>
<li>Confirmation bias: Nickerson (1998); the original demonstration is Wason (1960).</li>
<li>Pre-registration in science: Simmons, Nelson and Simonsohn (2011); Kerr (1998); Chan et al. (2004); Kaplan and Irvin (2015); Nosek et al., 'The preregistration revolution', PNAS 115 (2018).</li>
<li>This project's rule: ruling E28 (2026-08-25) and E95 (superseded views), <code>reference/growth-views/</code>.</li>
</ul>
<p>Where this differs from its source: a scientific pre-registration is public and the hypothesis is tested against many data points. Here the registry is private, the "data" is one number, and the penalty is that the view is void rather than that a paper is rejected. The mechanism is the same: the belief must exist, dated, before the thing that could bend it.</p>
''')}
""",
    [
        ("Tversky and Kahneman (1974), Judgment under Uncertainty, Science", "https://www.science.org/doi/10.1126/science.185.4157.1124"),
        ("Anchoring effect (the wheel experiment described), Wikipedia", "https://en.wikipedia.org/wiki/Anchoring_effect"),
        ("Northcraft and Neale (1987), Experts, Amateurs, and Real Estate", "https://www.sciencedirect.com/science/article/abs/pii/074959788790046X"),
        ("Nickerson (1998), Confirmation Bias", "https://journals.sagepub.com/doi/abs/10.1037/1089-2680.2.2.175"),
        ("Simmons, Nelson and Simonsohn (2011), False-Positive Psychology", "https://journals.sagepub.com/doi/10.1177/0956797611417632"),
        ("Kerr (1998), HARKing", "https://journals.sagepub.com/doi/10.1207/s15327957pspr0203_4"),
        ("Chan et al. (2004), Selective reporting of outcomes in randomized trials, JAMA", "https://jamanetwork.com/journals/jama/fullarticle/198809"),
        ("Kaplan and Irvin (2015), Likelihood of Null Effects of Large NHLBI Clinical Trials Has Increased over Time, PLOS ONE", "https://doi.org/10.1371/journal.pone.0132382"),
        ("Nosek et al. (2018), The preregistration revolution, PNAS", "https://www.pnas.org/doi/abs/10.1073/pnas.1708274114"),
        ("The pre-registration rule", "repo: reference/FRAMEWORK-EDITS.md E28, E95; reference/growth-views/"),
    ],
)

# ---------------------------------------------------------------------------
# 9. THE THREE OUTCOMES
# ---------------------------------------------------------------------------
N = Notes()
chapter(
    "09-three-outcomes", "The three outcomes",
    "Every test ends PASS, FAIL or DATA MISSING. The third is not a weaker version of the second, and a system that quietly records 'could not check' as 'failed' will lie to you in both directions.",
    6, False,
    f"""
<p>Most checklists have two outcomes. A box is ticked or it is not. The method has three, and the third is the one that makes the other two trustworthy.</p>

{FIG["three_doors"]()}

<h2>Why two is not enough</h2>
{wrong('''
<p>The test asks whether NAME A's debt is within the limit. The vendor has no debt figure for NAME A this quarter. The test cannot be run. So the box is left unticked, and unticked means failed, and NAME A is removed.</p>
<p>Later, NAME B: same test, same missing figure. But NAME B is a name the reader likes, so the missing figure is noticed, chased, found in the filing, and it passes.</p>
''', "The two-outcome version, which is wrong twice")}
<p>The first error is that NAME A was removed for a fact about the data vendor, not a fact about NAME A. The second error is worse: whether a missing figure counts as a fail now depends on whether anyone cared enough to chase it, which means it depends on what the reader already wanted. The two-outcome checklist has quietly become a way of laundering preferences.</p>

{right('''
<p>Every test ends in exactly one of three states. PASS: the test ran and the figure cleared it. FAIL: the test ran and the figure did not. DATA MISSING: the test could not run, because the figure is absent, stale, of the wrong length, or not yet checked by a person. No test may be silently skipped, and DATA MISSING is never counted as FAIL.</p>
''', "The rule")}

<p>This is the second of the five operating rules the whole method is written under, and it appears at every layer of the tool. The screener counts a name rejected because a figure said so and a name rejected because a figure was absent in different columns, and never adds them together.{N.ref("Framework §0 rule 2: 'Every screening criterion gets an explicit PASS / FAIL / DATA MISSING verdict. No criterion may be silently skipped.' In the screener's universe code: 'DATA MISSING is a THIRD STATE ... counted in different columns and never added together.' The filter configuration's missing-data policy is pass through, chosen so vendor coverage gaps do not masquerade as quality failures.")} The nightly run separates a verdict about a company from a blocker about the data: stale prices, an unresolved event date, a missing stop. In the tool's founding sentence, "stale or unresolved data produces a blocker, never a verdict. The tool would rather tell you it cannot judge than judge on bad data."{N.ref("README, opening. The blocker codes and the verdict codes are separate lists in vss/rules.py.")}</p>
{N.flush()}

<h2>The third outcome is information</h2>
<p>DATA MISSING is not an absence of result. It is a result, and it tells the reader two things: that this test says nothing about the company, and that there is a figure to go and find. It is also, honestly recorded, a description of how much of the method is actually running. One of the method's five gates, a comparison of valuation against peers, has been DATA MISSING for every company ever examined, because the peer figures it needs have never been assembled. The gate was not deleted to make the count look better. It stays, marked, until the figures exist.{N.ref("Ruling E99: 'A criterion nobody can evaluate is not a criterion a company has failed.'")}</p>
{N.flush()}

<p>A related state deserves a mention. A figure that a person has typed in but not yet read back against its page is UNVERIFIED, which is not the same as missing: it is present, named, and refused by the valuation until checked. And a figure that was searched for in a full report and is genuinely not there is NOT PRESENTED, which is not the same as zero. Each of these is its own state because collapsing them would let one kind of ignorance impersonate another.{N.ref("Verification states in vss/manual.py and ruling E85.")}</p>
{N.flush()}

{decision(
    "Three outcomes for every test, at every layer, and the third is never merged into the second.",
    "A missing figure is a fact about the data. Recording it as a fact about the company introduces an error whose direction depends on who was paying attention.",
    "Reports are full of DATA MISSING. Some names sit unvalued for weeks waiting for one figure. The reader sees exactly how little the method can currently say, which is uncomfortable and is the point.",
)}
""",
    [("The three-outcome rule at each layer", "repo: reference/FRAMEWORK.md §0 rule 2; vss/rules.py (verdict and blocker codes); vss/universe.py; config/screener_filter2.yaml; reference/FRAMEWORK-EDITS.md E85, E99")],
)

# ---------------------------------------------------------------------------
# 10. THE FUNNEL
# ---------------------------------------------------------------------------
N = Notes()
chapter(
    "10-the-funnel", "The funnel: six statuses",
    "Every company the method has touched sits in exactly one of six states. For each: what happens there, what the tool does, what the owner does, and what makes a name fall out.",
    9, False,
    f"""
<p>A company that the method has noticed is always in exactly one state, and the state is written in the owner's watchlist file. The six states, in the tool's own spellings, are INTAKE, PIPELINE, WATCH-GATED, WATCH-PRICED, HELD and DROPPED.{N.ref("The status list in vss/rules.py. A retired seventh spelling, plain WATCH, is refused by the code with a message pointing at the ruling that split it.")} The order below is the order a name would travel if everything went well, which it almost never does.</p>
{N.flush()}

{FIG["funnel"]()}

<div class="stage"><h3>INTAKE: read, not watched</h3><dl>
<dt>What happens</dt><dd>A name is being studied. Its filings are read, figures are entered and checked, a growth view may be written. Nothing about it is watched yet.</dd>
<dt>The tool does</dt><dd>Fetches its filings on request, stores its figures with provenance, reports what is verified and what is missing. It does not watch the price.</dd>
<dt>The owner does</dt><dd>Reads. Decides whether to enter the name into the process at all.</dd>
<dt>Falls out when</dt><dd>The owner decides it is not worth entering. Nothing automatic happens here.</dd>
</dl></div>
<p>This state exists because of a deadlock the method created for itself: the growth view has to be written before the value is solved, but entering a name used to stamp the date and freeze a gate, so a name could not be studied without being committed to. INTAKE is "read, not watched", and it carries no entry stamp.{N.ref("Ruling E111, 2026-09-04, resolving the deadlock ruling E109 had created. The code refuses an INTAKE entry that carries any of the fields that only an entered name may have.")}</p>
{N.flush()}

<div class="stage"><h3>PIPELINE: entered</h3><dl>
<dt>What happens</dt><dd>The owner has entered the name. The date of entry and the price's high point are stamped and frozen, so the "how far has it fallen" gate is judged as of that day and does not drift as the price moves.</dd>
<dt>The tool does</dt><dd>Watches for the company's own disclosures: periodic reports, changes to its forecast, profit warnings. Nothing else. Leadership changes, buybacks, deals and shareholder notices are filtered out, on the owner's test: would this make me redo the valuation?</dd>
<dt>The owner does</dt><dd>Works through the gates, the hard kills, the reading, the growth view, the valuation.</dd>
<dt>Falls out when</dt><dd>A gate fails on something other than price (to WATCH-GATED), a hard kill or a class D reason is found (to DROPPED), or the business turns out to be outside the circle (to DROPPED).</dd>
</dl></div>
<p>Because entry freezes a gate and that freezing cannot be undone by re-running anything, the scheduled screen is forbidden from entering a name. It may propose. Only the owner, by hand, enters.{N.ref("Ruling E93: 'entering a PIPELINE name stamps dd_at_entry and peak_date and E12 freezes Gate 1 at that moment — and unlike a fair value, that is not undone by re-striking.' The flag that would allow it is absent from the scheduled unit and must stay absent.")}</p>
{N.flush()}

<div class="stage"><h3>WATCH-GATED: waiting for a fact</h3><dl>
<dt>What happens</dt><dd>The name failed a gate on something that was not its price. It waits.</dd>
<dt>The tool does</dt><dd>Watches its disclosures, as for PIPELINE. Does not watch its price, because no price would change the answer.</dd>
<dt>The owner does</dt><dd>Nothing, until a named new fact arrives. Then re-reads.</dd>
<dt>Falls out when</dt><dd>The owner decides the fact will never come (to DROPPED), or a new fact reopens the gate (back to PIPELINE).</dd>
</dl></div>

<div class="stage"><h3>WATCH-PRICED: waiting for a price</h3><dl>
<dt>What happens</dt><dd>The reading is done, the value is struck, the most the owner will pay is computed. The price is above it. The name waits for the price alone.</dd>
<dt>The tool does</dt><dd>Every night, compares the settled closing price to the buy line and reports the distance. Points when the price crosses it. The line is a computed buy price or there is no line: a level typed in by hand for a name never valued is a reminder, and the name is not buyable at it.</dd>
<dt>The owner does</dt><dd>Waits. Re-values on the company's next report.</dd>
<dt>Falls out when</dt><dd>The price crosses the line and the owner buys (to HELD), or a new report changes the reading (back to PIPELINE, or to DROPPED).</dd>
</dl></div>

<div class="stage"><h3>HELD: owned</h3><dl>
<dt>What happens</dt><dd>The owner has bought. A stop, a price at which the position is sold regardless, was set before entry and is recorded.</dd>
<dt>The tool does</dt><dd>Every night, checks the price against the stop and reports a breach as the first thing on the page. A held name with no stop is a blocker, reported before anything else.</dd>
<dt>The owner does</dt><dd>Re-values on every report. Sells at the stop or when the reason for buying is gone.</dd>
<dt>Falls out when</dt><dd>The owner sells. The sale is recorded and measured against the market from its own date.</dd>
</dl></div>

<div class="stage"><h3>DROPPED: refused</h3><dl>
<dt>What happens</dt><dd>The name has been refused: a hard kill, a class D reason, outside the circle, or the owner's judgement.</dd>
<dt>The tool does</dt><dd>Does not watch it at all. Records the refusal in the shadow book with the price of the day and one line of reason (chapter 12).</dd>
<dt>The owner does</dt><dd>Nothing. Reads the shadow book once a year.</dd>
<dt>Falls out when</dt><dd>It does not. A dropped name can be re-entered at INTAKE by the owner, as a new decision, with a new record.</dd>
</dl></div>

<h2>The thing to notice</h2>
<p>Every arrow between the boxes is the owner's act. The tool measures where a name stands, reports it, and points when something crosses a line. It never moves a name. If the owner does nothing, nothing moves. That is a design decision, and chapter 13 says why.</p>

{fold("The exact rules", '''
<p>Statuses: <code>vss/rules.py</code>. INTAKE: ruling E111. PIPELINE entry stamps and the frozen gate: rulings E12 and E93. The two waiting lists: ruling E27. The disclosure filter: <code>vss/watch.py</code>. The nightly price comparison: <code>vss/runner.py</code>, <code>vss/rules.py</code>. Sales: ruling B45, <code>vss/sales.py</code>. Refusals: ruling E114, <code>vss/shadowbook.py</code>.</p>
''')}
""",
    [("Statuses and the rulings that govern moves between them", "repo: vss/rules.py; vss/watch.py; reference/FRAMEWORK-EDITS.md E12, E27, E93, E111, E114")],
)

# ---------------------------------------------------------------------------
# 11. THE DECISION
# ---------------------------------------------------------------------------
N = Notes()
chapter(
    "11-the-decision", "The decision",
    "Never 'a buy'. A buy below price X, under conditions Y, with stop Z, all written before the money moves. The discount demanded scales with how well the owner believes he understands the business.",
    8, False,
    f"""
<p>The method's fourth operating rule reads: a stock is not "a buy". A stock is a buy below price X, under conditions Y, with stop Z, and if you cannot specify all three the work is not finished.{N.ref("Framework §0 rule 4.")} This chapter is about those three letters.</p>
{N.flush()}

{FIG["buy_price"]()}

<h2>X: the most the owner will pay</h2>
<p>Chapter 8 produced the owner's base-case growth view. Chapter 7's arithmetic, run forwards with that view, gives a value per share. That is the owner's estimate of what NAME A is worth, and it is wrong by an amount nobody knows. So it is not the buy price.</p>

<p>The buy price is the value multiplied by a cushion, and the cushion depends on how sure the owner is. The method calls the levels of sureness <dfn>tiers</dfn>, and there are three. A tier 1 name, one the owner understands well and which has a strong balance sheet and something durable pushing it along, gets a buy price of 85 percent of value. A tier 2 name, less sure or in a cyclical business, gets 75. A tier 3 name, where the reason for owning it has had to be re-described along the way, gets 65.{N.ref("Ruling E90, 2026-08-30. Tier is not a feeling: it comes from a conviction score built from gates passed, warning signs and good signs, and tier 1 additionally requires a fortress balance sheet and a secular tailwind. 'A score alone does not make a tier 1.'")} The cushion is there to absorb errors in the model and in the inputs, which in this project's own reviews have typically been five to fifteen percent of value. It is not there to absorb the business doing badly; the low-case growth view carries that, and it is printed beside the buy price as information, not folded into it.</p>
{N.flush()}

<p>The buy price is printed with two companions: the same price recomputed with the discount rate half a point lower and half a point higher. The owner sees how much the number leans on a rate that is, by the method's own admission, a preference. A proposal that the tool should veto any decision that reverses inside that band was refused, with a reason worth quoting: such a rule could only ever remove a conclusion, never produce one, "and this framework's diagnosed defect is that it cannot say yes."{N.ref("Ruling E29. 'Fragility is DISPLAYED, never ADJUDICATED.'")}</p>
{N.flush()}

<h2>Y: the conditions</h2>
<p>A price alone is not enough. The name must still be inside the reading that produced the value: the dated event that was supposed to make the market look again must still be on the calendar, the latest report must contain no hard kill, and the growth view must be the one on record, not a revised one. If the company reports between the valuation and the purchase, the valuation is redone. A buy price struck on figures that have since changed is not a buy price; the tool marks a value struck on a superseded method or on figures it can no longer rebuild as nulled, not as slightly old.{N.ref("Rulings E39 and E87.")}</p>
{N.flush()}

<h2>Z: the exit, decided first</h2>
<p>Before any purchase, the owner writes a stop: a price at which the position is sold, whatever the story is at the time. It is set when the owner has no stake in the answer. Once the shares are owned, every reason not to sell will seem compelling, which is precisely why the number was written earlier. The tool refuses to treat a held name as complete without one, and reports a missing stop ahead of everything else on the page.{N.ref("A held name with no stop is a blocker, reported before any verdict. Framework §6.4 also names thesis stops: sell when the reason for owning is gone, such as a second cut to the company's own forecast.")}</p>
{N.flush()}

<h2>What the tool does with all this</h2>
<p>It computes X from the value and the tier, because both of those are the owner's inputs and the multiplication is not a judgement. It refuses to accept X typed in by hand; doing so fails the run with a conflict, because a buy price that did not come from a value and a tier is a number with no origin.{N.ref("README: 'Writing an mbp: key by hand fails the run with a provenance conflict.' The cushions in force are 0.85, 0.75 and 0.65; an earlier set, 0.80, 0.70 and 0.60, is kept in the code only for three figures struck under it and marked as superseded wherever they print.")} Every night it reports the distance from the settled price to X, and whether Z has been breached. It never says buy. It says: 4 percent above the line, or 2 percent below it, and the rest is the owner's.</p>
{N.flush()}

<h2>The cushion in plain language</h2>
<p>How much of a discount you demand should depend on how likely you are to be wrong, and how likely you are to be wrong depends on how well you understand what you are buying. A business you have followed for years, with no debt and a tailwind, you may buy at a modest discount to your estimate, because your estimate is worth something. A business you can only half explain, you should buy only at a steep discount, because your estimate is mostly guess and the discount is doing the work. The tiers put numbers on that, and the numbers are the same for every company in the same tier, so the owner cannot quietly grant a favourite a smaller cushion.</p>

{decision(
    "A decision is three written numbers, X, Y and Z, produced in that order, before purchase. X is computed from the owner's value and tier and may not be typed in.",
    "A decision that exists only as a feeling of confidence cannot be checked afterwards. Three numbers with dates can.",
    "Nothing is bought quickly. Between a company reporting and the owner being permitted to act, every figure is re-read and the value re-struck. Opportunities that require speed are not opportunities for this method.",
)}
""",
    [("Rules for the buy price, the tiers and the stop", "repo: reference/FRAMEWORK.md §0 rule 4, §4.4, §5.3, §6.4; reference/FRAMEWORK-EDITS.md E29, E39, E87, E90; vss/rules.py; vss/valuation.py")],
)

# ---------------------------------------------------------------------------
# 12. THE SHADOW BOOK
# ---------------------------------------------------------------------------
N = Notes()
chapter(
    "12-shadow-book", "The shadow book",
    "Every refusal is measured against the market afterwards. A system that only measures what it bought cannot learn, and a process that only refuses, and never scores its refusals, cannot be shown to be wrong.",
    7, False,
    f"""
<p>By now the shape of the method should be clear: it mostly says no. Of the names it has read closely, it has, at the time of writing, refused every one. That raises an uncomfortable question. How would anyone know if the method were simply too strict? A process that never buys never has a bad purchase to point to. It also never has a good one. Its record is spotless and says nothing.</p>

<p>The owner's ruling put it this way: "This framework has evaluated names and refused all of them, and nothing in it measures what a refusal cost or saved. A process that only refuses, and never scores its refusals, cannot be falsified."{N.ref("Ruling E114, 2026-09-08.")}</p>
{N.flush()}

<h2>What is recorded</h2>
<p>The <dfn>shadow book</dfn> is a table with one row per refusal. Each row records six facts and nothing else: the company, the date of the verdict, what the verdict was and whether it stands, the settled closing price on that date in the company's own currency, the value if one had been struck, and one line naming what decided it.</p>

{FIG["refusal_tracked"]()}

<p>What is deliberately not recorded matters as much. No thesis. No expectation of what the price will do. No target. In the ruling's words, "a row that argues is a row that will be re-argued." The book is a record of decisions and prices, not a record of opinions about them.</p>

<h2>What is measured</h2>
<p>From the verdict date forward, the refused name's return is set beside the return of an index over the same period, in the same currency, and, this is the part that took an amendment, the same kind of return. A share's return includes its dividends; an index's may or may not. The first version of the rule let a name whose dividends the vendor did not record be compared as a bare price against an index that included dividends, which would have made every refusal look a little wiser than it was. The rule was amended one day after it was written: where dividends cannot be established, the row is DATA MISSING rather than a flattering comparison. The owner's reason: "a shadow book exists to be able to say the method does not work, and one that systematically flatters the refusals cannot do that."{N.ref("Ruling E114 as amended 2026-09-09. The book stores the unadjusted close, a fact that never changes, and derives the total return beside it at reading time, saying so.")}</p>
{N.flush()}

<h2>Four limits, stated by the ruling itself</h2>
<ol>
<li><strong>It measures what happened, never whether the verdict was right.</strong> A refused name that rose may have risen for exactly the reasons the verdict declined to bet on. The book cannot tell the difference, and does not pretend to.</li>
<li><strong>It is not a signal.</strong> Nothing in it triggers an alert, enters a name, or feeds a valuation. No other part of the program reads it. It is read once a year, on purpose, because a scoreboard glanced at weekly is a reason to change a rule for the wrong reason.</li>
<li><strong>Both sides are the same kind of return</strong>, as above, or the row is missing.</li>
<li><strong>A verdict written on a weekend is re-dated</strong> to the last weekday before it, and the row says so. The walk-back crosses weekends and nothing else, because a weekday with no price could be a holiday or a data outage, and the tool cannot tell those apart.</li>
</ol>

<h2>Where this comes from, and where it does not</h2>
<p>Nobody in finance has a standard name for this. The nearest relatives are the decision journal, a habit recommended by Daniel Kahneman and popularised by writers on decision-making: write down what you decided, why, and what you expect, before the outcome; and the distinction, made in the poker literature by Annie Duke and in investing by Michael Mauboussin, between judging a decision by its process and judging it by its outcome, where the second is a mistake with a name, "resulting".{N.ref("Duke, Thinking in Bets (2018); Mauboussin, More Than You Know, popularising a process-versus-outcome matrix originally from Russo and Schoemaker. The decision-journal advice is widely attributed to Kahneman; a primary interview could not be located and is not cited.")} The underlying psychology is hindsight: once an outcome is known, people believe they expected it.{N.ref("Fischhoff, 'Hindsight ≠ Foresight', Journal of Experimental Psychology: Human Perception and Performance 1 (1975); Fischhoff and Beyth, 'I knew it would happen', Organizational Behavior and Human Performance 13 (1975).")}</p>
{N.flush()}
<p>The shadow book departs from the decision-journal idea in one way, on purpose. A journal records the expectation. This book refuses to, because an expectation on record is an argument waiting to be resumed. It records only what was decided, when, and at what price, and lets the market supply the rest a year later.</p>

{decision(
    "Every refusal is recorded with its date, price and one-line reason, and measured against an index afterwards. Nothing else about it is written down, nothing in the program reads the book, and it is read once a year.",
    "A method that never buys has a perfect record that proves nothing. The only way to find out whether the refusals were right is to measure them, and the only way to keep the measurement from bending the rules is to look at it rarely.",
    "The book cannot say whether a verdict was right, only what the price did. That is a weaker claim than it looks like, and the ruling says so in its first limit.",
)}
""",
    [
        ("Hindsight bias, Wikipedia (Fischhoff 1975; Fischhoff and Beyth 1975)", "https://en.wikipedia.org/wiki/Hindsight_bias"),
        ("The shadow book ruling and code", "repo: reference/FRAMEWORK-EDITS.md E114 (2026-09-08, amended 2026-09-09); vss/shadowbook.py"),
    ],
)
