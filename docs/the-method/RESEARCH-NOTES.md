# RESEARCH NOTES — how this site was designed, and why

Written 2026-09-13, before any page was built. Four tracks. Each finding
carries a URL and a marker: **FETCHED** means the page was retrieved and
read; **SEARCH** means only a search engine's summary was seen. Anything that
could not be sourced is listed at the end as left out. Decisions are stated
with what they cost, in the register this project uses for its own rulings.

The brief that produced this file: a smart reader with no background must be
able to explain back, in their own words, what the tool is for, why it was
built this carefully, and how it works end to end. The site sells nothing.

---

## TRACK A — INFORMATION ARCHITECTURE

### What the evidence says

**Attention decays inside a page, steeply.** Nielsen Norman Group's
eye-tracking data: 57% of page-viewing time is spent above the fold, 74% in
the first two screenfuls, 81% in the first three. "The closer a piece of
information is to the top of the page, the higher the chance that it will be
read." — FETCHED, https://www.nngroup.com/articles/scrolling-and-attention/

Consequence: on a single long scroll, chapter 19 sits below roughly forty
screenfuls of chapters 1–18, in the part of the page that receives almost
none of the reading time. A chaptered site gives every chapter its own top.

**Chunking helps comprehension, and the "magic number" is smaller than seven.**
NN/g: "Presenting content in chunks makes scanning easier for users and can
improve their ability to comprehend and remember it," and warns against the
popular seven — Miller's own paper said plus or minus two, and later work
puts it at three to six. — FETCHED, https://www.nngroup.com/articles/chunking/
Cowan (2001) put working-memory capacity at "about four chunks in young
adults" against Miller's 1956 seven. — FETCHED (secondary),
https://en.wikipedia.org/wiki/Working_memory

Consequence: no list on this site exceeds six items without being grouped;
the funnel's six stages are shown as two groups of three; each chapter opens
with what it is about in one sentence.

**Learning and looking-up are different needs and should not share a page.**
Diataxis separates tutorials, how-to guides, reference and explanation as
"four distinct needs." Its tutorial page: "A tutorial serves the user's
acquisition of skills and knowledge — their study"; "All learning moves in
one direction: from the concrete and particular, towards the general and
abstract. The latter will emerge from the former." — FETCHED,
https://diataxis.fr/ and https://diataxis.fr/tutorials/

Does it apply here? Partly. This site has no how-to and no reference: nobody
is going to operate the tool from it. It is explanation with a tutorial's
ordering. What transfers is the ordering rule (concrete before abstract) and
the separation: the exact rulings, the module names and the sources are kept
out of the running text, behind a fold the reader opens on demand.

**Progressive disclosure works to one level and fails past two.** NN/g:
"Initially, show users only a few of the most important options. Offer a
larger set of specialized options upon request." It "fails if the
initial/secondary feature split is wrong" and users get lost beyond two
levels. — FETCHED, https://www.nngroup.com/articles/progressive-disclosure/

Consequence: exactly one fold level on every page. A chapter's running text
is the first level; "the exact rule" and "where this comes from" are the
second; nothing sits inside those.

**Length is managed by reader-initiated disclosure, not by hiding.** Gwern's
design page: "The solution to the length problem is to progressively expose
more beyond the default as the reader requests it," and pages should "be read
at multiple structural levels." — FETCHED, https://gwern.net/design

**Interaction turns a reader from passive to active, and forces the author
to disclose the model.** Bret Victor: without interaction "We form questions,
but can't answer them. We consider alternatives, but can't explore them"; the
reader must "blindly trust, or blindly don't." — FETCHED,
https://worrydream.com/ExplorableExplanations/
Distill: "Reactive diagrams allow for a type of communication not possible
in static mediums." — FETCHED, https://distill.pub/about/

Consequence: one interactive figure, where the model is small enough to be
honest about — the reverse-DCF inversion (chapter 7). The static version is
always on the page; the slider is added by JavaScript.

**Sidenotes keep provenance beside the text without breaking flow.** Tufte
CSS: sidenotes "don't force the reader to jump their eye to the bottom of
the page, but instead display off to the side in the margin." — FETCHED,
https://edwardtufte.github.io/tufte-css/

**Multi-page from file:// must use plain links.** A page opened from a local
file has an opaque origin; fetch() and XMLHttpRequest to another local file
are refused by the browser ("Cross origin requests are only supported for
protocol schemes: http, data, chrome, chrome-extension, https"). — SEARCH,
corroborated by MDN's CORS error page
https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/CORS/Errors/CORSRequestNotHttp
and two forum threads. Consequence: no single-page shell that loads chapter
fragments; every chapter is a real file reached by an ordinary link.

**Not found, and therefore not relied on:** any study comparing abandonment
on single-scroll versus chaptered sites; any NN/g or Smashing Magazine
measurement of reading-progress bars; Ciechanowski's or Red Blob Games'
stated design rationale; any evaluation of explorable explanations against
static text. The reading-progress bar is left out for lack of evidence; the
site says "chapter 7 of 23" instead, which is a fact rather than a gauge.

### Real examples examined

- **Stripe's documentation**: three columns, persistent sidebar, one page per
  topic. Named as a pattern; its authors' rationale was not found.
- **Bartosz Ciechanowski** (https://ciechanow.ski/archives/): single long
  scroll with interactive figures, one subject per essay. FETCHED (archive
  page only). No stated rationale found. Observation: each essay is ONE
  concept; this site has twenty-three, which is the case the pattern does
  not cover.
- **Gwern.net**: long pages made readable by collapsing sections and
  sidenotes. FETCHED.
- **Distill.pub**: interactive figures inside a chaptered article with a
  persistent table of contents. FETCHED (about page).
- **Tufte CSS**: sidenotes and margin figures. FETCHED.
- **Diataxis**: separation by reader need. FETCHED.

### DECISION

**A chaptered site: one HTML file per chapter, twenty-three chapters in two
parts, plus an index that is the map.** Every page carries the same sidebar
listing all chapters, a breadcrumb stating part and chapter number, a
one-sentence "this chapter" line at the top, and previous/next links naming
the neighbouring chapters. The index offers two routes: the whole book in
order, and a shorter route of seven chapters for a ten-minute reader. Each
chapter has exactly one fold level: "the exact rule" and "where this comes
from" open on demand.

Why this and not a single scroll: attention decay within a page (NN/g),
chunking (NN/g, Cowan), and the owner's own verdict on the previous build.
Why not a single-page app that swaps views: file:// forbids fragment loading,
and a real URL per chapter is bookmarkable and printable without any script.
Why not fewer, longer pages: the two parts are different design problems and
the chapters inside them are different again (Track B); one page per chapter
lets each carry its own pattern.

**What it costs.**
- No search across the whole book. Ctrl-F finds text on the current chapter
  only. Mitigated by the index listing every chapter with a one-line summary,
  and by chapter titles that say what they contain; not removed.
- Twenty-five files instead of one. The sidebar is repeated in every file, so
  a change to the chapter list must be made in every file. A generator script
  produces the files; editing one by hand and forgetting the others breaks
  the navigation silently. The generator is shipped alongside the site.
- Every page change loses scroll position and costs a page load. Mitigated
  by prev/next links that name the destination, so the reader knows what
  the next page is before leaving this one.
- Reading time is stated per chapter rather than measured by a progress bar,
  because no evidence for progress bars was found.

---

## TRACK B — A PATTERN PER CONTENT TYPE

The owner's requirement: the technical parts and the investing parts are
different jobs and must be presented differently. Six content types were
researched separately. Each gets its own pattern; the shared page frame,
palette and type keep them one site.

### B1. Teaching an unfamiliar concept (value, margin of safety, reverse DCF)

**Evidence.** The worked-example effect: "learners who studied worked
examples performed significantly better than learners who actively solved
problems" — Sweller and Cooper (1985), via FETCHED secondary
https://en.wikipedia.org/wiki/Worked-example_effect. It works for novices and
reverses for experts (Kalyuga et al. 2000, 2001, same source), which is fine
here: the reader is a novice by definition. Analogy: Gentner's
structure-mapping theory holds that useful analogies carry "connected systems
of relations," not surface resemblance — SEARCH. Diataxis: concrete before
abstract — FETCHED.

**Pattern chosen: worked example first, then the general idea, then one
analogy with matching structure.** Every concept in Part One is introduced
through NAME A, a fictional company with round numbers, before the concept is
named. The analogy is chosen so that its parts map onto the parts of the
concept (a bridge rated above its load maps onto value above price; a
thermometer that reads but does not prescribe maps onto the tool). Jargon
appears once, after the plain version. One interactive figure (reverse DCF)
because that is where "what would the number be if" is the actual lesson.

### B2. Explaining a decision process with stages and exits (the funnel)

**Evidence.** Scanlan (1989), IEEE Software: "structured flowcharts do
indeed aid algorithm comprehension, with a large difference found even for
the simplest algorithm" — SEARCH (paywalled; a 2022 eye-movement follow-up
exists and was not read, so the result is treated as supportive, not
settled). NN/g on wizards: one step per page, in prescribed order — SEARCH,
https://www.nngroup.com/articles/wizards/

**Pattern chosen: one flow diagram of the whole funnel, then a stage-by-stage
walk with the same four fields for every stage** (what happens; what the
tool does; what the owner does; what makes a name fall out). One case, NAME
A, is walked through the stages so the reader sees a single path, not a
matrix. The diagram and the walk use the same stage names in the same order.

### B3. Explaining a counterintuitive rule (pre-registration, DATA MISSING)

**Evidence.** Refutation text: Tippett (2010) reviews two decades of work
showing that text which states the misconception, explicitly flags it as
wrong, then gives the correct account produces more conceptual change than
plain exposition — SEARCH (primary paywalled). Nygard on decision records:
without the motivation recorded, newcomers "blindly accept" or "blindly
change" — FETCHED, https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions

**Pattern chosen: the wrong way shown first, in full, then the flag, then
the rule; both orderings side by side in one figure; and one real failure
story with numbers** (for pre-registration, the clinical-trial result:
57% of large trials reported a benefit before registration was required, 8%
after — Kaplan and Irvin 2015, FETCHED, see Track D). The reader is invited
to notice that the wrong way is the natural way.

### B4. Documenting system architecture for a non-engineer

**Evidence.** The C4 model: four levels, "System Context → Container →
Component → Code," as "hierarchical abstractions" — FETCHED,
https://c4model.com/. Simon Brown's stated rationale for non-technical
audiences was not on the fetched page and is not claimed.

**Pattern chosen: two zoom levels, never the code level, and one
request-journey narrative.** Level 1: the machine, the owner, and the two
outside services, with every arrow labelled by direction. Level 2: the
pieces inside the program and the walls between them, drawn as walls. Then
one figure's journey from a filing to the phone, told as a story with the
provenance attached at each step. Module names appear once, in a fold, after
the plain description. No code listings anywhere.

### B5. Presenting trade-offs and limits

**Evidence.** Nygard's decision record: Context, Decision, Status,
Consequences; "A particular decision may have positive, negative, and neutral
consequences, but all of them affect the team and project in the future" —
FETCHED. This is also the format the project's own rulings already use
("WHAT THIS COSTS").

**Pattern chosen: a decision-record box, the same shape everywhere:** what
was decided, why, and what it costs, in three labelled lines. Limits
(chapter 22) use a two-column list: the limit, and what the project does
about it, including "nothing". Comparison tables are used only where the
rows are genuinely parallel (the two orderings of pre-registration; the two
observers).

### B6. Citing provenance

**Evidence.** Tufte sidenotes — FETCHED (above). Gwern: notes are one of
several "structural levels" a page can be read at — FETCHED. The claim that
inline hyperlinks reduce comprehension (Carr, citing Zhu) was found only in
secondary paraphrase and one cited paper could not be confirmed as stated;
it is not relied on.

**Pattern chosen: numbered notes beside their sentence in the margin on wide
screens, and directly after the sentence on narrow ones (Tufte's placement), with the full source list at the end of
each chapter and on one sources page.** No external link sits in the running
text: a reader who wants the source sees a number; a reader who does not is
not pulled off the page. Where the project differs from its source, the note
says so.

---

## TRACK C — HOW IT LOOKS

### Colour with a job

**Evidence.** Tufte's chartjunk: elements "not necessary to comprehend the
information represented on the graph, or that distract the viewer from this
information"; "it is all non-data-ink or redundant data-ink" — FETCHED
(secondary), https://en.wikipedia.org/wiki/Chartjunk. ColorBrewer's three
families (sequential, diverging, qualitative) — FETCHED,
https://colorbrewer2.org/ (explanatory text not retrievable). Datawrapper:
"graphic elements should have a contrast ratio of at least 3:1 against
adjacent color(s)"; check with a colour-blindness simulator; prevalence
"~8% of men" and "0.5% of women" — FETCHED,
https://www.datawrapper.de/blog/colors-for-data-vis-style-guides/
National Eye Institute: "About 1 in 12 men have color vision deficiency";
the most common type "makes it hard to tell the difference between red and
green" — FETCHED,
https://www.nei.nih.gov/learn-about-eye-health/eye-conditions-and-diseases/color-blindness
Okabe and Ito's palette: "unambiguous both to colorblinds and
non-colorblinds"; vermilion instead of red because it stays "recognizable
also to protanopes"; a bluish green chosen to avoid confusion "with red or
brown" — FETCHED, https://jfly.uni-koeln.de/color/ (the palette is also
published as Wong, Nature Methods 8:441, 2011, not fetched).
WCAG 2.2 1.4.1: "Color is not used as the only visual means of conveying
information" — FETCHED,
https://www.w3.org/WAI/WCAG22/Understanding/use-of-color.html
IBM Carbon's palette page could not be fetched and is not cited. A source
for "how many hues a reader holds at once" was not found; the palette is
kept to five meanings on the chunking evidence instead.

**The colour system.** Five meanings, all from the Okabe–Ito palette, each
with a line colour and a fill tint. One meaning keeps one colour in every
diagram on the site. Nothing else is coloured.

| Meaning | Line / text | Fill tint | Where it may appear | Second signal |
|---|---|---|---|---|
| **Value** — what the business is worth; the owner's estimate | blue #0072B2 (text: #005A8E) | #D1E6F1 | value marks, fair-value labels, the owner's side of a diagram | square marker, label "value" |
| **Price** — what the market quotes | orange #E69F00 lines; text and thin strokes #8A5A00 | #FAEED1 | price marks, the market's side | circle marker, label "price" |
| **Pass** — a test passed, a signal arrived | green #009E73 (text: #00714F) | #D1EEE6 | gate outcomes, the success exit, a ping received | tick glyph, label |
| **Fail / alarm** — a test failed, a stop, an alert | vermillion #D55E00 (text: #A34500) | #F7E2D1 | gate outcomes, the failure exit, an alarm | cross glyph, label |
| **Missing** — could not be checked; DATA MISSING; unknown | grey #767676 (text: #5C5C5C) | #E6E6E6, always hatched | the third outcome, an absent signal, a dead machine | diagonal hatch, "?" label |
| **Owner** — a human decision | purple #CC79A7 fills; text and strokes #8B4A70 | #F6E7EF | anything the owner writes or decides | hand-drawn double border, label |
| Ink and paper | #1B1B1B on #FBFAF7 | | all text, the tool's boxes, walls, arrows | |

Blue against orange and green against vermillion are the pairs Okabe and Ito
chose to survive every common deficiency. The two pairs are never used to
mean opposite things in the same figure with only hue to tell them apart:
price/value carry circle/square markers, pass/fail carry tick/cross glyphs,
missing carries a hatch. The site commits to one light theme; a dark theme
would need every meaning re-checked and is not built.

**Contrast ratios checked** (WCAG formula, computed 2026-09-13, on paper
#FBFAF7 unless stated). Minimums: text 4.5:1, large text 3:1 (1.4.3,
FETCHED, https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html);
graphical objects 3:1 against adjacent colour (1.4.11, FETCHED,
https://www.w3.org/WAI/WCAG22/Understanding/non-text-contrast.html).

| Colour | on paper | Used for |
|---|---|---|
| ink #1B1B1B | 16.5 | body text |
| muted #5A5A5A | 6.6 | captions, notes |
| blue text #005A8E | 7.1 | text; blue line #0072B2 is 5.0 (strokes) |
| orange text #8A5A00 | 5.7 | text and thin strokes; #E69F00 is 2.2 and is used only for wide fills and thick marks with a dark outline |
| green text #00714F | 5.8 | text; #009E73 is 3.3 (strokes) |
| vermillion text #A34500 | 5.9 | text; #D55E00 is 3.7 (strokes) |
| grey text #5C5C5C | 6.4 | text; #767676 is 4.4 (strokes) |
| purple text #8B4A70 | 6.1 | text and strokes; #CC79A7 is 2.9 and is fill only |
| ink on any tint | ≥ 13.4 | labels inside filled shapes |
| tint against paper | 1.1 – 1.2 | a tint is never a boundary; every filled shape has a ≥3:1 outline |
| focus ring #005A8E | 7.1 | 3 px outline, 2 px offset |

### Typography for long reading on a phone

**Evidence.** Baymard: "The optimal line length for body text is 50–60
characters per line, including spaces" (citing Ruder), acceptable range
50–75; too-long lines lose the line start, too-short lines break rhythm —
FETCHED, https://baymard.com/blog/line-length-readability. System font
stacks avoid a network fetch; several large sites removed the bare
`system-ui` keyword after it selected a CJK font for Latin text on some
Windows locales — SEARCH. No external font is allowed by the brief anyway.

**Chosen:** explicit named stack (Segoe UI, Roboto, Helvetica Neue, Arial,
sans-serif), 17 px body on phones and 18 px on wide screens, line height
1.6, measure capped at 34em (about 66 characters), headings in the same
face and weight 600 so hierarchy comes from size and space, not from a
second face. Diagram text is never below 12 px at the diagram's natural
width and the diagrams scale with the viewport.

### Controls, navigation, keyboard

**Evidence.** WCAG 2.5.8: targets "at least 24 by 24 CSS pixels" — FETCHED,
https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html; 2.5.5
sets 44 by 44 at the enhanced level — SEARCH. WCAG 2.4.13 Focus Appearance:
the indicator "is at least as large as the area of a 2 CSS pixel thick
perimeter of the unfocused component" and "has a contrast ratio of at least
3:1 between the same pixels in the focused and unfocused states" — FETCHED,
https://www.w3.org/WAI/WCAG22/Understanding/focus-appearance.html

**Chosen:** every navigation link and control is at least 44 px tall; focus
is a 3 px solid outline in blue text colour with 2 px offset on every
focusable element; a "skip to content" link is the first element on every
page; the phone menu is a checkbox and label pair styled as a toggle, so it opens and
closes from the keyboard with no script (a closed details element cannot be
forced open by CSS on wide screens, which is why details was not used); the sidebar is a plain list of
links; previous/next are links, not buttons; the left and right arrow keys
move between chapters when JavaScript is on, and the same links work when
it is off. Nothing is a button that could have been a link.

### Diagrams

**Evidence.** Fluid SVG: keep viewBox, set width 100% and height auto —
SEARCH (MDN). Accessible SVG: role="img" with a title and description
referenced by aria-labelledby — SEARCH (Deque, W3C draft).

**Chosen:** every diagram is inline SVG with a viewBox, a title and a
description, scales to the column, and is designed to be read before its
caption. No mark that is not information: no drop shadows, no gradients, no
decorative icons. Colour carries meaning and never alone.

---

## TRACK D — WHERE THE IDEAS COME FROM

Nothing in the method was invented here. Each idea: origin, how it is
taught, and whether this project borrows it straight or departs from it.

### Margin of safety
Origin: Benjamin Graham, *The Intelligent Investor* (1949), chapter 20,
"Margin of Safety as the Central Concept of Investment", closing with the
motto "MARGIN OF SAFETY" as the three words that distil sound investment —
SEARCH (book text not online; wording consistent across secondary sources).
Beginner source: https://en.wikipedia.org/wiki/Margin_of_safety_(financial) — SEARCH.
**This project:** straight borrowing in principle. The departure is that the
cushion is a fixed fraction of the base-case value set by tier (0.85, 0.75,
0.65 — ruling E90), covering model and input error and explicitly not
scenario risk, which the pre-registered growth views carry. The commonly
quoted Buffett bridge analogy could not be verified against the 1984 speech
and is not used; the site uses its own bridge analogy without attributing it.

### Price versus value; Mr Market
"Long ago, Ben Graham taught me that 'Price is what you pay; value is what
you get.'" — Buffett, 2008 letter to Berkshire Hathaway shareholders, page
4 — FETCHED and extracted from
https://www.berkshirehathaway.com/letters/2008ltr.pdf
"As Ben Graham said: 'In the short-run, the market is a voting machine … but
in the long-run, the market is a weighing machine.'" — Buffett, 1993 letter
— FETCHED, https://www.berkshirehathaway.com/letters/1993.html
Mr Market: Graham, *The Intelligent Investor*, chapter 8; Buffett's
retelling: "Mr. Market appears daily and names a price at which he will
either buy your interest or sell you his"; "Mr. Market is there to serve
you, not to guide you. It is his pocketbook, not his wisdom, that you will
find useful." — FETCHED, https://www.berkshirehathaway.com/letters/1987.html
**This project:** straight borrowing.

### Circle of competence
"You only have to be able to evaluate companies within your circle of
competence. The size of that circle is not very important; knowing its
boundaries, however, is vital." — Buffett, 1996 letter — FETCHED,
https://www.berkshirehathaway.com/letters/1996.html
**This project:** borrowed, then made mechanical: two written rules exclude
whole classes (businesses whose revenue is a world price they do not set;
pharmaceuticals and biotech, because the growth view the method requires
would be a guess about approvals). The departure is that the boundary is
written down and enforced by the screen, not held in the head.

### Reverse DCF / market-implied expectations
Origin of the framing: Alfred Rappaport and Michael Mauboussin,
*Expectations Investing* (Harvard Business School Press 2001; revised
Columbia 2021). Their method: first "read" the expectations for cash flow
embedded in the price, then "anticipate the revision" — FETCHED,
https://www.expectationsinvesting.com/. Aswath Damodaran teaches implied
growth in his NYU Stern materials — SEARCH; no direct quotation is used.
**This project:** borrowed for the inversion (price in, implied growth out),
departs on what is done with it: the owner's growth view is written and
timestamped BEFORE the implied number is solved, and a view written after is
void. Rappaport and Mauboussin compare the two; this project forbids seeing
one before writing the other.

### Pre-registration, and what it prevents
p-hacking: Simmons, Nelson and Simonsohn (2011), "False-Positive
Psychology", Psychological Science 22(11) —
https://journals.sagepub.com/doi/10.1177/0956797611417632 — SEARCH.
HARKing: Kerr (1998), "HARKing: Hypothesizing After the Results are Known",
Personality and Social Psychology Review 2(3) —
https://journals.sagepub.com/doi/10.1207/s15327957pspr0203_4 — SEARCH.
Outcome switching: Chan et al. (2004), JAMA 291(20), 62% of trials had at
least one primary outcome changed, introduced or omitted against the
protocol — https://jamanetwork.com/journals/jama/fullarticle/198809 — SEARCH;
COMPare project, Oxford CEBM — https://www.compare-trials.org/project — SEARCH.
The before/after result: Kaplan and Irvin (2015), PLOS ONE 10(8): "17 of 30
studies (57%) published prior to 2000 showed a significant benefit" versus
"only 2 among the 25 (8%) trials published after 2000"; "Pre-registration
in clinical trials.gov was strongly associated with the trend toward null
findings." — FETCHED, https://doi.org/10.1371/journal.pone.0132382
Nosek et al. (2018), "The preregistration revolution", PNAS 115 —
https://www.pnas.org/doi/abs/10.1073/pnas.1708274114 — SEARCH.
**This project:** straight borrowing of the mechanism (write the hypothesis
before the data). Departure: the "data" is one number, the market-implied
growth rate, and the sanction is that the view is void for that name in that
cycle (ruling E28), with git history as the timestamp.

### Anchoring and confirmation bias
Tversky and Kahneman (1974), "Judgment under Uncertainty: Heuristics and
Biases", Science 185(4157): a wheel rigged to stop at 10 or 65, then an
estimate of the share of African countries in the UN; medians 25% and 45% —
FETCHED (secondary), https://en.wikipedia.org/wiki/Anchoring_effect; primary
https://www.science.org/doi/10.1126/science.185.4157.1124 — SEARCH.
Northcraft and Neale (1987), estate agents anchored on a manipulated listing
price while touring the property, Organizational Behavior and Human Decision
Processes 39(1) — SEARCH.
Wason (1960), the 2-4-6 task — SEARCH. Nickerson (1998), "Confirmation Bias:
A Ubiquitous Phenomenon in Many Guises", Review of General Psychology 2(2):
"the seeking or interpreting of evidence in ways that are partial to
existing beliefs, expectations, or a hypothesis in hand" — SEARCH,
https://journals.sagepub.com/doi/abs/10.1037/1089-2680.2.2.175
**This project:** these are the reason pre-registration is needed; the
project does not claim to have measured them itself.

### Tracking decisions not taken
Finding: there is no single named practice in finance. What exists: the
decision journal (widely attributed to Kahneman, popularised by Farnam
Street; the primary interview was not located — SEARCH); "resulting", Annie
Duke, *Thinking in Bets* (2018) — judging a decision by its outcome — SEARCH;
the process/outcome matrix, originally Russo and Schoemaker, popularised in
investing by Mauboussin — SEARCH; counterfactual thinking, Roese (1997),
Psychological Bulletin 121 — SEARCH; hindsight bias, Fischhoff (1975) and
Fischhoff and Beyth (1975) "I knew it would happen" — SEARCH. No vendor
product tracking a shadow book of rejected ideas was found.
**This project:** the shadow book is closest to a decision journal for
refusals only. Departure from the journal idea: it records no expectation
and no thesis, only the price on the day and one line naming what decided
it, because "a row that argues is a row that will be re-argued" (ruling
E114). It is read once a year, deliberately.

### Base rates and hindsight
Kahneman and Lovallo (1993), "Timid Choices and Bold Forecasts", Management
Science 39(1): inside view versus outside view — SEARCH,
https://pubsonline.informs.org/doi/10.1287/mnsc.39.1.17

### The dead man's switch
Origin: railway vigilance devices; "Vigilance control was developed to
detect this condition by requiring that the dead man's device be released
momentarily and re-applied at timed intervals." Software sense: the trigger
is a "non-event", such as a missing ping — FETCHED,
https://en.wikipedia.org/wiki/Dead_man%27s_switch. The monitoring service:
"listens for HTTP requests ('pings')"; "keeps silent as long as pings arrive
on time"; "raises an alert as soon as a ping does not arrive on time", with
a grace period — FETCHED, https://healthchecks.io/docs/
**This project:** straight borrowing.

### The tool measures, the owner decides
Automation misuse and disuse: Parasuraman and Riley (1997), "Humans and
Automation: Use, Misuse, Disuse, Abuse", Human Factors 39(2) — SEARCH,
https://journals.sagepub.com/doi/10.1518/001872097778543886
Least privilege: "Every program and every user of the system should operate
using the least set of privileges necessary to complete the job." —
Saltzer and Schroeder (1975), "The Protection of Information in Computer
Systems" — FETCHED, https://www.cs.virginia.edu/~evans/cs551/saltzer/
Identity before network: Google's BeyondCorp, Ward and Beyer (2014), ;login:
39(6) — SEARCH, https://www.usenix.org/publications/login/dec14/ward (PDF
refused the fetch; no quotation is used).
**This project:** least privilege is applied literally (each unit has a
verb list; the screen cannot write the config directory; the server serves
one path). The human-decides principle is the project's own governing rule
and is stated as such; the literature is cited as the reason it matters,
not as its source.

### Left out because not verified
- Buffett's bridge-and-trucks analogy (primary text not reachable).
- "Every market price is already a DCF" as a Damodaran quotation.
- Kahneman's "cheap notebook" quotation.
- Any Dalio material; Skitka (1999); ICMJE's 2005 statement; Registered
  Reports; Rappaport 1986; Penman; Essentia's performance claim; IBM
  Carbon's guidance; a source for "five to seven hues"; Zhu on hyperlinks.
