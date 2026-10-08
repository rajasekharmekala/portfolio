# Report Voice: how every report should read

Read this before writing any section of any report (newsletter, audit, options review, company dossier, archive review).
It applies on top of REPORT_EDITORIAL_STANDARD.md, which covers structure, data, and the validator floors.

## 1. The model

A Wikipedia article gives the reader a neutral lead, clear headings, and sources. A good textbook then explains each idea until the reader can use it. Write like the two together: the structure of an encyclopedia, and the patience of a teacher who assumes the reader is intelligent but new to this.

Neutral means you do not hype or moralize. It does not mean cold. Every claim gets a reason, and every reason gets a consequence.

## 2. Every heading is explained

Every H2 and every H3 gets its own explanation in prose. Do not let a heading sit above a table or a list with nothing between them.

Each explanation does four things, roughly in this order:
1. **Says what the thing is**, in plain words, with one everyday comparison if it is technical.
2. **Says why it matters** to this reader, in this report.
3. **Says what the data shows here**, with the specific numbers, and what they mean.
4. **Says what follows**: the consequence, the decision it supports, and the level or event that would change it.

Then it ties the subsection to the next one. Ending a subsection on a bridge sentence is what makes a report read as one argument instead of a pile of tables.

A subsection with a table gets prose before the table (what to look for and how to read one row) and prose after it (what the numbers add up to). Do not copy cells into sentences. Explain what the cells mean together.

## 3. Reasoning, consequences, and tie-ups

- Use "because", "which means", "so", and "unless" to show the chain. "Sales grew 22 percent, which means the company is earning more from each sale, so the margin question in section 4 matters." A bare fact with no link is not yet an explanation.
- Every verdict names its rule and the number that triggered it. "KEEP, because the stock is above its 50-day average and the trend has not broken. It becomes a TRIM if it closes below 1,320 for two sessions."
- Every section ends with what it means for the reader, in their terms ("What this means for you", or "What this means for an owner" in a company dossier). Then the bridge.
- Where signals conflict, say so and say which one you weight and why.
- When the honest answer is "we do not know", say what would tell us, and by when.

## 4. Writing style

- Plain English. Short sentences are fine. Vary their length and their openings.
- Define each technical term the first time it appears, with an analogy. After that, use it consistently.
- Address the reader as "you" when giving advice, and "the company" or "the index" when describing.
- One idea per paragraph. Three to six sentences is typical for a subsection paragraph.
- Explain the number and then the meaning. "RSI is 27.7. Below 30 is called oversold, which means the stock has fallen unusually fast. It does not mean it has to bounce, and here the trend is still down."
- Do not repeat a sentence pattern across sections. If three paragraphs in a row start with "The stock", rewrite two of them.
- Do not pad. If a paragraph only repeats the table, cut it or add the reasoning it is missing.

## 5. Banned phrases and patterns

These sound like a template and are rejected by `validate_report.py`:

- Signposting filler: "This section", "In this section", "The following table", "Below is", "As the table shows", "It is important to note", "It should be noted", "Let us explore", "We will examine"
- Connective filler: "Furthermore", "Moreover", "Additionally", "In conclusion", "In summary", "Overall, it is clear that"
- Vague intensifiers and jargon-as-decoration: "delve", "landscape", "robust", "game-changer", "unlock", "leverage" (as a verb), "navigate the"
- Hand-off phrases: "letting the data speak for itself", "speak for themselves"
- Placeholder text: "pending revalidation", "carried forward", "Technical Revalidation Pending", "to be confirmed later" (unless the date is named and the reason is given)

## 6. Examples

Weak (template voice):
> This section examines the Bull List. The following table shows the stocks. It is important to note that the Bull List is robust.

Strong (book voice):
> The Bull List is the short list of stocks that have just completed a Stage 2 breakout, the phase where a stock moves from a base into a sustained uptrend. Twenty-two of the thirty names passed every hurdle. The other eight are on the list because they fail one hurdle, usually volume, and that matters: a breakout on thin trading is easier to reverse. The table below lists each name with its tier, but the reading that matters is the one in the next paragraph: most of the names sit in Industrials, which is the sector that led the market this week, so the list is telling the same story as section 2.

Weak:
> Holdings with a verdict of TRIM should be reduced. Stop: 1,320. Risk: moderate.

Strong:
> The verdict for this holding is TRIM, and the reason is the stop rule, not a feeling about the company. The stop is 1,320, which sits 6.8 percent below today's close. If the stock closes below 1,320 for two sessions, the position becomes a forced exit, which means you sell the whole holding rather than a part. Trimming now, by a third, reduces the amount you lose if that happens while keeping some exposure if the stock recovers.

Weak (company dossier):
> The company operates in the renewable energy sector. Revenue grew. Margins are healthy. Verdict: Accumulate.

Strong (company dossier):
> The company makes transformers that step electricity voltage up and down for solar farms, so its sales follow how fast solar capacity is being built. Revenue grew 31 percent last year, but the more useful number is the order book: at 2.4 times annual sales, the company has enough signed work to keep its plants busy for more than two years. That is why the verdict is Accumulate on a dip rather than Buy now. The stock sits 9 percent below its 200-day average, and a close above 1,450 on rising volume would change the advice to wait for a pullback to 1,300 because the easy part of the move would be over.

## 7. Checklist before you publish a section

- Does every H2 and H3 have its own explanatory prose?
- Does each verdict name its rule and its trigger?
- Does every table have a reading guide before it and a meaning after it?
- Does the last paragraph of the section tie to the next one?
- Did you remove every phrase from section 5?
- If you read the section aloud, would a sensible newcomer follow it without re-reading?
