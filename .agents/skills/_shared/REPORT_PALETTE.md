# Report Colour Palette (binding for every HTML report)

Every report uses only the colours below. Do not invent hex codes, do not use colour names (`red`, `green`), and do not use emoji as status markers. Put the `:root` block at the top of each report's `<style>`, then use the `var(--...)` tokens everywhere.

Every text colour is checked against its background for WCAG 2.1 AA (at least 4.5:1 for body text). The ratios are listed so that a future change can be checked the same way.

## 1. Tokens

```css
:root {
  /* Neutral base, taken from the Wikipedia desktop palette */
  --ink:          #202122;  /* body text: 16.1:1 on white */
  --ink-strong:   #111827;  /* headings: 18.7:1 on white */
  --muted:        #54595d;  /* captions, sources, secondary text: 7.1:1 on white */
  --rule:         #a2a9b1;  /* table borders, dividers */
  --rule-soft:    #d1d5db;  /* card borders, dashed bridges */
  --surface:      #ffffff;  /* page background */
  --surface-alt:  #f8f9fa;  /* table header rows, howto blocks */
  --link:         #0645ad;  /* links: 8.5:1 on white */
  --link-visited: #0b0080;

  /* Verdict and status colours. Each has a text colour and a tint, both AA on each other. */
  --keep-ink:        #14532d;  /* 8.3:1 on --keep-tint */
  --keep-tint:       #dcfce7;
  --accumulate-ink:  #1e3a8a;  /* 8.5:1 on --accumulate-tint */
  --accumulate-tint: #dbeafe;
  --trim-ink:        #78350f;  /* 8.2:1 on --trim-tint */
  --trim-tint:       #fef3c7;
  --exit-ink:        #7f1d1d;  /* 8.2:1 on --exit-tint */
  --exit-tint:       #fee2e2;
  --watch-ink:       #374151;  /* 9.4:1 on --watch-tint */
  --watch-tint:      #f3f4f6;

  /* Callout blocks */
  --primer-accent:   #0645ad;  --primer-tint:   #eaf3ff;
  --howto-accent:    #54595d;  --howto-tint:    #f8f9fa;
  --case-accent:     #1e3a8a;  --case-tint:     #ffffff;
  --trigger-accent:  #92400e;  --trigger-tint:  #fef3c7;
  --example-accent:  #166534;  --example-tint:  #f0fdf4;
  --takeaway-accent: #1e3a8a;  --takeaway-tint: #eff6ff;
}
```

## 2. Meaning of each colour

- **Keep** (`--keep-*`): the position stays as it is. Use for KEEP, KEEP_COMPOUNDING, HOLD, and Stage 2 confirmed.
- **Accumulate** (`--accumulate-*`): add on a pullback. Use for ACCUMULATE, ACCUMULATE_ON_DIP, and Top-3 setups.
- **Trim** (`--trim-*`): reduce exposure but keep part of it. Use for TRIM, TRIM_PROFIT_BOOKING, and Stage 3 warnings.
- **Exit** (`--exit-*`): sell the position or treat the level as a hard stop. Use for EXIT, REPLACE_UNDERPERFORMER, HARD STOP hit, and Stage 4 breakdowns.
- **Watch** (`--watch-*`): no action yet, but a level is being monitored. Use for WATCH, WATCH ONLY, and awaiting confirmation.

## 3. How to render a verdict

Use a span with a class, not a coloured emoji:

```html
<span class="verdict verdict-trim">TRIM</span>
```

Classes: `verdict-keep`, `verdict-accumulate`, `verdict-trim`, `verdict-exit`, `verdict-watch`. The matching CSS is in `book_components.css`.

## 4. Tables, charts, and pass/fail

- Table header rows use `--surface-alt` with `--ink-strong` text. Borders use `--rule`.
- Validator pass/fail cells use text only, styled with `--keep-ink` for PASS and `--exit-ink` for FAIL. Do not rely on colour alone: write the word as well.
- Charts (if any) use the verdict inks for series, and must include a text legend. Do not add other colours.

## 5. Accessibility

- Never place body text on a tint below 4.5:1.
- Never convey a verdict by colour alone. The label text always appears.
- Print: the report must still be readable in greyscale, so the labels carry the meaning.
