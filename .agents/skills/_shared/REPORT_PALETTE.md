# Shared Report Palette

Every report generated in this repository uses this exact `:root` token block (unified with the Techmeme-inspired theme in `personal-wiki`). Do not invent hex literals in a skill's `<style>` — use these variables. All foreground/background pairs below pass WCAG AA ($\ge 4.5:1$ for body text, $\ge 3:1$ for borders and fills).

```css
:root {
  /* Page & surface (Techmeme / Morning Brief unified theme) */
  --paper:          #ffffff;
  --paper-top:      #f4f6f8;
  --ink:            #111111;
  --ink-strong:     #174a61;
  --muted:          #556677;
  --rule:           #cccccc;
  --rule-soft:      #d8e0e6;
  --surface:        #ffffff;
  --surface-alt:    #f4f6f8;
  --link:           #002848;
  --link-visited:   #902050;
  --link-hover-bg:  #d0e8f4;
  --navy:           #174a61;
  --navy-hover:     #578aa1;
  --sisnav-hover:   #25607b;

  /* Verdict semantic tokens — four distinct hues, colour-blind safe when paired with text labels */
  --keep-ink:       #145a32;   /* forest green — KEEP / HOLD / SHORTLIST */
  --keep-bg:        #e8f4ec;
  --keep-rule:      #8ec5a1;

  --accumulate-ink: #0f4c81;   /* slate blue — ACCUMULATE / BUY / ADD / STAGE 2 BREAKOUT */
  --accumulate-bg:  #e7f0f9;
  --accumulate-rule:#8fb4da;

  --trim-ink:       #7c4700;   /* warm amber — TRIM / WAIT FOR SUPPORT / ROLL */
  --trim-bg:        #fbf2e1;
  --trim-rule:      #dfba73;

  --exit-ink:       #8b1e1e;   /* brick red — EXIT / REJECT / CLOSE / STAGE 4 */
  --exit-bg:        #fbeaea;
  --exit-rule:      #dca1a1;

  --watch-ink:      #424b54;   /* neutral slate — WATCH / ARCHIVED / PENDING */
  --watch-bg:       #eef0f2;
  --watch-rule:     #b8c0c8;

  /* Callout accents (matching personal-wiki .exec-theme-box and .deepdive-container) */
  --primer-accent:  #d4a017;   /* gold — Executive Synthesis / Primer box */
  --primer-tint:    #fdfbe8;
  --rule-accent:    #0f4c81;   /* slate blue — Rule Explained box */
  --rule-tint:      #eef4fa;
  --case-accent:    #174a61;   /* Techmeme navy — Deep-Dive / Case Note box */
  --case-tint:      #fcfdfe;
  --warn-accent:    #8b1e1e;   /* brick — Risk / Conflict callout */
  --warn-tint:      #fcf1f1;
}
```
