# Report Colour Palette (binding for every HTML report)

Every report uses only the colours below. Do not invent hex codes, do not use colour names (`red`, `green`), and do not use emoji as status markers. Put the `:root` block at the top of each report's `<style>`, then use the `var(--...)` tokens everywhere.

Every text colour is checked against its background for WCAG 2.1 AA (at least 4.5:1 for body text). The ratios are listed so that a future change can be checked the same way.

## 1. Tokens

```css
:root {
  --paper: #f4f6f4;
  --paper-top: #edf3ef;
  --ink: #202923;
  --ink-strong: #202923;
  --muted: #526158;
  --rule: #dce3dd;
  --rule-soft: #dce3dd;
  --surface: #ffffff;
  --surface-alt: #eef3ef;
  --link: #176547;
  --link-visited: #176547;
  --keep-ink: #14532d;
  --keep-tint: #dcfce7;
  --accumulate-ink: #176547;
  --accumulate-tint: #e5f1ea;
  --trim-ink: #78350f;
  --trim-tint: #fef3c7;
  --exit-ink: #a34242;
  --exit-tint: #fff0f0;
  --watch-ink: #374151;
  --watch-tint: #f3f4f6;
  --primer-accent: #176547; --primer-tint: #e5f1ea;
  --howto-accent: #526158; --howto-tint: #eef3ef;
  --case-accent: #176547; --case-tint: #ffffff;
  --trigger-accent: #92400e; --trigger-tint: #fef3c7;
  --example-accent: #166534; --example-tint: #f0fdf4;
  --takeaway-accent: #176547; --takeaway-tint: #e5f1ea;
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
