---
name: Placement Co-pilot
description: A career operations console that turns a resume into a guided placement route.
colors:
  primary: "#1738c8"
  primary-deep: "#102a9c"
  primary-soft: "#edf0ff"
  signal: "#f3df5f"
  signal-ink: "#151b0d"
  shell-ink: "#f7f8f2"
  shell-muted: "#c0c9ff"
  canvas: "#eef0ea"
  surface: "#ffffff"
  surface-quiet: "#f6f7f2"
  ink: "#101820"
  ink-soft: "#4f5d66"
  ink-faint: "#66737c"
  line: "#dfe3db"
  line-strong: "#c6cdc4"
  success: "#067647"
  success-soft: "#e9f8ef"
  warning: "#934807"
  warning-soft: "#fff5df"
  danger: "#b42318"
  danger-soft: "#fef1ef"
typography:
  display:
    fontFamily: "Instrument Sans, Segoe UI, system-ui, sans-serif"
    fontSize: "46px"
    fontWeight: 700
    lineHeight: 0.98
    letterSpacing: "-0.04em"
  headline:
    fontFamily: "Instrument Sans, Segoe UI, system-ui, sans-serif"
    fontSize: "18px"
    fontWeight: 700
    lineHeight: 1.2
    letterSpacing: "-0.025em"
  body:
    fontFamily: "Instrument Sans, Segoe UI, system-ui, sans-serif"
    fontSize: "14px"
    fontWeight: 400
    lineHeight: 1.5
    letterSpacing: "normal"
  label:
    fontFamily: "Cascadia Mono, SFMono-Regular, Consolas, monospace"
    fontSize: "9.5px"
    fontWeight: 700
    lineHeight: 1.2
    letterSpacing: "0.09em"
rounded:
  panel: "16px"
  signal: "18px"
  pipeline: "14px"
  route: "12px"
  control: "9px"
  small: "10px"
  pill: "999px"
spacing:
  xs: "4px"
  sm: "8px"
  md: "16px"
  lg: "22px"
  xl: "32px"
  section: "56px"
components:
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.surface}"
    rounded: "{rounded.control}"
    padding: "10px 14px"
  button-primary-hover:
    backgroundColor: "{colors.primary-deep}"
    textColor: "{colors.surface}"
    rounded: "{rounded.control}"
    padding: "10px 14px"
  button-secondary:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    rounded: "{rounded.control}"
    padding: "10px 14px"
  panel:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    rounded: "{rounded.panel}"
    padding: "22px"
  input:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    rounded: "{rounded.control}"
    padding: "10px 12px"
  nav-current:
    backgroundColor: "{colors.signal}"
    textColor: "{colors.signal-ink}"
    rounded: "{rounded.route}"
    padding: "10px"
  chip:
    backgroundColor: "{colors.surface-quiet}"
    textColor: "{colors.ink-soft}"
    rounded: "{rounded.pill}"
    padding: "3px 7px"
---

# Design System: Placement Co-pilot

## Overview

**Creative North Star: "The Placement Desk"**

Placement Co-pilot reads as a career operations console with the clarity of campus wayfinding. A saturated cobalt shell carries the route; chalk-white work surfaces hold the tasks; butter-yellow signals mark the next decision. The result should feel calm and credible, never like a pile of AI features bolted onto a dashboard.

The composition is deliberately asymmetric. A persistent route rail establishes position, a compact status bar keeps the session legible, and a two-column hero pairs the product promise with one clear next move. The pipeline band and workspace follow in task order: profile, matches, approvals, practice. The narrow signals rail keeps AI assistance status, agent activity, and guardrails visible without competing with the work.

Instrument Sans gives the product a modern institutional voice, while mono is reserved for numbers, identifiers, endpoints, and status labels. Soft ambient depth, 1px hairlines, and a fine dot-grid ground keep the page tactile without turning it into a card stack. The route is the signature; the next move is always the loudest object.

**Key Characteristics:**
- Cobalt route rail with numbered gates and a thin guiding line.
- Chalk dot-grid ground with paper-white task panels.
- Butter-yellow next-move card and current-gate marker.
- Flat job and application rows separated by hairlines.
- Self-hosted Instrument Sans with mono data labels.
- Explicit approval gate and visible agent traces.

## Colors

The palette is a saturated cobalt route, a single butter-yellow signal, and a small set of confirmation colors grounded by chalk and ink.

### Primary
- **Route Cobalt**: The shell, primary actions, active progress, and score emphasis. It is the route and the action, not a decorative wash.
- **Deep Cobalt**: Hover, pressed, and depth states for primary actions and the sidebar foot.
- **Cobalt Wash**: Quiet selected surfaces, input focus hovers, and the interview result block.

### Secondary
- **Signal Butter**: The next-move card and the current route gate. It is scarce by design.
- **Signal Ink**: Dark text and markers on butter surfaces.

### Neutral
- **Shell Chalk**: Primary text on cobalt and the sidebar wordmark.
- **Shell Mist**: Supporting route labels and upcoming steps.
- **Chalk Ground**: The page field, carrying a 22px dot grid at low contrast.
- **Panel White**: Task panels and the approval dialog.
- **Quiet White**: Chips, inset fields, empty states, and secondary surfaces.
- **Ink**: Primary text and high-emphasis numerals.
- **Soft Ink**: Supporting copy and descriptions.
- **Faint Ink**: Metadata, labels, and placeholder text.
- **Hairline**: Standard 1px dividers, card borders, and row separators.
- **Strong Hairline**: Input borders and controls that need more definition.

### Tertiary
- **Confirmed Green**: Grounded, approved, online, and AI-assisted states.
- **Confirmed Wash**: The corresponding green-tinted badge surfaces.
- **Attention Amber**: Pending approval and attention states.
- **Attention Wash**: The amber-tinted badge surface.
- **Stop Red**: Destructive actions and error emphasis.
- **Stop Wash**: The red-tinted error surface.

### Named Rules
**The One Route Rule.** Cobalt is the route and the action. The shell carries it; the task surfaces stay paper-white. Do not add a second competing accent.

**The Butter Means Now Rule.** Butter yellow appears only on the current gate and the next-move card, with their linked actions. If everything is yellow, nothing is next.

**The Green Means Confirmed Rule.** Green is reserved for grounded, approved, online, and used states. It never grades a score or fills a neutral chart.

## Typography

**Display Font:** Instrument Sans (with Segoe UI, system-ui)
**Body Font:** Instrument Sans (with Segoe UI, system-ui)
**Label/Mono Font:** Cascadia Mono (with SFMono-Regular, Consolas)

**Character:** A modern, slightly compressed grotesque with a calm institutional voice. The display and body share one face so the page feels authored rather than assembled; mono is a data voice, not a costume.

### Hierarchy
- **Display** (700, 46px / 0.98, -0.04em): Hero headline only; max 18ch, balanced, two lines on desktop and mobile.
- **Headline** (700, 18px / 1.2, -0.025em): Panel headings; the gate marker carries the route number beside it.
- **Title** (650-700, 13.5-14.5px / 1.25): Job titles, application rows, and modal subheads.
- **Body** (400, 14px / 1.5; 12px supporting): Task copy and descriptions; the hero paragraph is 15px / 1.6 and max 56ch.
- **Label** (700, 9.5px / 1.2, 0.09em, uppercase): Mono data labels, stats, field labels, route counts, and trace modes.

### Named Rules
**The Self-Hosted Voice Rule.** The display voice is Instrument Sans, served from `frontend/public/fonts/instrument-sans-latin.woff2`. Never let the page fall back to a platform display face.

**The Tight Headline Rule.** Display tracking stops at -0.04em. Headlines use balance and short measures, never stretched lettering, gradient fills, or all-caps shouting.

**The Data-Only Mono Rule.** Mono is for numbers, IDs, endpoints, scores, counts, and status labels. It is not a costume for every heading.

## Layout

The app shell is a 264px cobalt route rail plus a fluid page. A sticky 48px status bar spans the page. The main canvas is `min(1200px, 100%)` with 34px top padding, horizontal padding of `clamp(20px, 4vw, 42px)`, and 56px bottom padding.

The hero is a two-column grid of 1.35fr / 0.65fr with a 22-34px gap; the next-move card is at least 280px tall. The pipeline band follows as a 112px label column plus four equal stats. The workspace is a 1.5fr task column and a 0.72fr signals rail, with the rail sticky at `top: 84px` and an 18-20px gap between modules.

Responsive behavior:
- At 1120px the rail compresses to 240px.
- At 980px the shell becomes one column and the rail turns into four horizontal route gates.
- At 900px the hero and workspace become single-column; the signals rail is no longer sticky.
- At 720px the signals rail becomes one column and the topbar trims secondary metadata.
- At 640px the route gates become a compact four-up row; at 420px the gate marker sits above its 11px label.

The spacing rhythm is 4 / 8 / 16 / 22 / 32 / 56. Keep groups tight inside a panel and generous between modules; more space above a heading than below it.

## Elevation & Depth

The system is paper-not-plastic. Depth comes from tonal planes and 1px hairlines first; a single broad ambient shadow lifts the working plane. There are no hard offset shadows, glass panels, or colored halos.

### Shadow Vocabulary
- **Working-plane lift** (`0 1px 2px rgba(16, 24, 32, 0.04), 0 18px 40px -28px rgba(16, 24, 32, 0.35)`): Panels, the pipeline band, the next-move card, and the approval dialog.
- **Focus ring** (`0 0 0 3px rgba(23, 56, 200, 0.12)`): Text fields, paired with a cobalt border.
- **Keyboard outline** (`3px solid rgba(23, 56, 200, 0.4)`): Links, buttons, and the drop zone, offset by 2px.

Motion is restrained: the result meter is the one authored moment, animating `transform: scaleX` over 0.4s with `cubic-bezier(0.16, 1, 0.3, 1)`. Buttons and fields use 160ms state transitions; toast and dialog entrances are short and functional. `prefers-reduced-motion` removes the meter transition and smooth scrolling.

### Named Rules
**The Paper-Not-Plastic Rule.** Surfaces are flat paper-white at rest. Shadows are broad and ambient, never a hard offset block or a zero-offset colored ring.

## Shapes

The form language is rounded institutional hardware: generous but controlled. Task panels use 16px corners; the next-move signal uses 18px; the pipeline band uses 14px; route cells use 12px; buttons, inputs, and result blocks use 9-12px; chips and status pills use full 999px caps.

The signature geometry is the circular gate marker on the thin route line, with an oversized tabular match score at the other end of the page. No clipping, diagonal cuts, geometric masks, or decorative blobs.

## Components

### Buttons
- **Shape:** 9px radius, 10px x 14px padding, 12.5px / 650 label.
- **Primary:** Route Cobalt fill with white text. Hover shifts to Deep Cobalt; active presses down 1px.
- **Secondary:** Panel White fill, 1px Strong Hairline border, Ink text; hover shifts to Cobalt Wash. Focus uses the 3px cobalt keyboard outline.
- **Disabled:** 0.52 opacity and a not-allowed cursor; the label stays visible.

### Chips
- **Style:** Quiet White fill, Soft Ink text, 999px radius, 3px 7px padding, mono 9px.
- **State:** Job skills are read-only data chips. Status chips use Confirmed Wash / Attention Wash with matching text; never use success green for a neutral tag.

### Cards / Containers
- **Corner Style:** 16px panels; 14px pipeline; 18px signal card.
- **Background:** Paper-white panels on Chalk Ground; Quiet White for inset rows and empty states.
- **Shadow Strategy:** Working-plane lift only; no stacking of shadows.
- **Border:** 1px Hairline; Strong Hairline for fields and buttons.
- **Internal Padding:** 22px panels; 16px result blocks; 14-16px rows.

### Inputs / Fields
- **Style:** Panel White fill, 1px Strong Hairline, 9px radius, 10px 12px, Cobalt caret.
- **Focus:** Cobalt border plus the 3px cobalt wash ring; no glow.
- **Placeholder / Disabled:** Faint Ink placeholder; disabled controls drop to 0.52 opacity. Validation errors surface in a toast rather than an inline red field.

### Navigation
- **Style:** A persistent cobalt rail with four gates, a thin vertical route line, and circular markers. The current gate is butter with Signal Ink text; completed gates use Shell Chalk with a drawn check; upcoming gates use Shell Mist.
- **Mobile:** Four compact gates in a row, 11px labels, 22px markers; detail lines, counts, and chevrons are hidden. The current gate keeps the same butter surface.
- **Behavior:** Each gate links to its task section; the current gate exposes `aria-current="step"`.

### Approval Dialog
- **Style:** Native `<dialog>` with a Paper White shell, 16px corners, 820px max width, 88vh max height, and a calm 3px backdrop blur behind a 58% ink veil.
- **Structure:** Shield mark and title, explanatory line, three meta tiles, mono-labelled cover note and resume draft blocks, then a sticky footer with Cancel and the primary Approve action.
- **Behavior:** Focus enters the dialog; Escape and the Cancel button close it; the primary action records approval without submitting anything to the employer.

### Score Block
- **Style:** Cobalt Wash block with a 12px radius, 36px cobalt score, cobalt meter, and Soft Ink feedback.
- **Rule:** The score is a measurement, not a pass. It stays cobalt at every value; green is reserved for confirmed states.

### Agent Trace Row
- **Style:** Flat row with a small line icon, agent name, duration, action summary, and a mono AI/fallback pill. Newest first.
- **Tone:** The AI pill uses Confirmed Wash when AI assisted and Quiet White when deterministic fallback carried the run. No nested cards or timelines.

## Do's and Don'ts

### Do:
- **Do** keep the route rail cobalt and the task surfaces paper-white.
- **Do** reserve butter for the current gate and the next-move card.
- **Do** use self-hosted Instrument Sans for display and body, and mono only for data.
- **Do** separate modules with 1px hairlines and the broad ambient shadow.
- **Do** keep job and application rows flat, with separators rather than nested cards.
- **Do** make approval honest: approval records the decision; submission stays manual.
- **Do** let the route numbers carry sequence information; they are not decoration.

### Don't:
- **Don't** add a second competing accent or gradient text.
- **Don't** use success green for scores, neutral tags, or decorative charts.
- **Don't** add kickers or eyebrows above headings; the heading speaks for itself.
- **Don't** nest content cards inside panels; use rows and quiet surfaces.
- **Don't** use hard offset shadows, glass decoration, or geometric masks.
- **Don't** replace the self-hosted display face with a platform default.
- **Don't** add section numbers unless they map to the four-gate route.
