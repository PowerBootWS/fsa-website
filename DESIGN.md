---
name: Full Steam Ahead
description: Power Engineering exam prep for working Canadian operators
colors:
  bg-deep: "#05090F"
  carbon: "#0D1117"
  iron: "#141A24"
  plate: "#1C2333"
  plate-edge: "#252F42"
  orange: "#E8720C"
  orange-glow: "#FF8C2A"
  amber: "#F5A623"
  steel-dim: "#2A4A6E"
  green-light: "#52A882"
  off-white: "#F4F5F7"
  gray-light: "#C8D0DA"
  gray-mid: "#a8b4c0"
typography:
  display:
    fontFamily: "'Barlow Condensed', sans-serif"
    fontSize: "clamp(2.6rem, 6vw, 4.5rem)"
    fontWeight: 600
    lineHeight: 1.1
    letterSpacing: "normal"
  headline:
    fontFamily: "'Barlow Condensed', sans-serif"
    fontSize: "clamp(1.8rem, 2.8vw, 2.5rem)"
    fontWeight: 700
    lineHeight: 1.2
    letterSpacing: "normal"
  title:
    fontFamily: "'Barlow Condensed', sans-serif"
    fontSize: "1.05rem"
    fontWeight: 700
    lineHeight: 1.2
    letterSpacing: "0.03em"
  body:
    fontFamily: "'IBM Plex Sans', sans-serif"
    fontSize: "1rem"
    fontWeight: 400
    lineHeight: 1.7
    letterSpacing: "normal"
  label:
    fontFamily: "'Barlow Condensed', sans-serif"
    fontSize: "0.7rem"
    fontWeight: 600
    lineHeight: 1
    letterSpacing: "0.1em"
rounded:
  none: "0"
  xs: "2px"
  sm: "4px"
  md: "5px"
spacing:
  xs: "8px"
  sm: "16px"
  md: "24px"
  lg: "32px"
  xl: "48px"
components:
  button-primary:
    backgroundColor: "{colors.orange}"
    textColor: "{colors.off-white}"
    rounded: "{rounded.sm}"
    padding: "1rem 2.2rem"
    typography: "display"
  button-primary-hover:
    backgroundColor: "{colors.orange-glow}"
  button-secondary:
    backgroundColor: "transparent"
    textColor: "{colors.gray-light}"
    rounded: "{rounded.sm}"
    padding: "1rem 1.8rem"
  button-secondary-hover:
    textColor: "{colors.off-white}"
  paper-card:
    backgroundColor: "{colors.plate}"
    rounded: "{rounded.none}"
    padding: "1.4rem"
  paper-card-hover:
    backgroundColor: "{colors.plate}"
  nav-cta:
    backgroundColor: "{colors.orange}"
    textColor: "{colors.off-white}"
    rounded: "{rounded.sm}"
    padding: "0.5rem 1.1rem"
---

# Design System: Full Steam Ahead

## 1. Overview

**Creative North Star: "The Boilerplate"**

This system is built like the instrument panel of a live boiler room: everything exactly where it needs to be, nothing decorative, stakes obvious from a glance. The aesthetic is industrial precision — not the styled version of industrial, but the real thing. Dark surfaces that read under plant-floor fluorescents. Orange that means hot, not branding. Type that communicates first and decorates never.

The system rejects its antitheses by name. No purple gradients, glassmorphism, or TailwindUI templates — visual signals that this is a SaaS product built by people who've never touched a boiler. No institutional blues and white backgrounds — that's the SOPEEC textbook, exactly what FSA is replacing. No Coursera-cheerfulness (stock photos of students smiling at laptops, gamification badges) — operators see through performative enthusiasm. And not the red/black gym-supplement aesthetic of trades bootcamp brands — gritty means precise, not loud.

The surface is carbon (#0D1117), not a safety-signal grey. The primary accent is heat (#E8720C). Every design choice should pass this test: *would a 3rd-class engineer who's been running this shift since 4am trust this screen?*

**Key Characteristics:**
- Five-step dark tonal surface stack (bg-deep → carbon → iron → plate → plate-edge)
- One primary accent: orange, used sparingly as heat and signal
- Amber as secondary warmth for data highlights and tags
- Square-cornered cards; slightly-rounded buttons (4px only)
- Barlow Condensed for all display/heading/label type; IBM Plex Sans for prose
- Elevation through tonal layering — shadows reserved for interaction state only
- Uppercase labels with tracked spacing; never on body copy

## 2. Colors: The Carbon Stack

Five surface steps form a dark material hierarchy. Accents are heat.

### Primary
- **Industrial Orange** (#E8720C): The only primary accent. Used on CTAs, hover states, active borders, and key data highlights. Its rarity is the point — every appearance of orange is a signal, not decoration.
- **Orange Glow** (#FF8C2A): Hover and glow variant of primary. Used exclusively on button hover and active states — never as a background at rest.

### Secondary
- **Amber Hot** (#F5A623): Secondary warmth. Used on calculation-type tags, stat highlights, and amber text emphasis. Distinct from orange — amber reads as "important data," not "action."

### Tertiary
- **Safety Green** (#52A882): Status only. Regulation-type tags, passing states, success signals. Never decorative.
- **Steel Blue** (#3A6EA5 / dim: #2A4A6E): Divider accents, muted interactive elements. Used at low opacity as a resting border before hover activates orange.

### Neutral
- **Void** (#05090F): Footer and deepest backdrops. The floor of the surface stack.
- **Carbon** (#0D1117): Body background. This is the page; everything else layers above it.
- **Iron** (#141A24): Section fills, nav background. One step above carbon.
- **Plate** (#1C2333): Card and surface backgrounds. Named for boiler plate.
- **Plate Edge** (#252F42): Card borders, dividers. The surface's seam.
- **Off White** (#F4F5F7): Primary body text. Not pure white — reduces harshness against carbon.
- **Gray Light** (#C8D0DA): Secondary text, button ghost labels.
- **Gray Mid** (#a8b4c0): Muted text — card descriptions, captions. Never body copy.

### Named Rules
**The One Signal Rule.** Orange appears on ≤1 element at a time per viewport section. When everything is orange, nothing is. If a section already has an orange CTA, supporting elements use amber or stay neutral.

**The No-Warm-Background Rule.** The body background is carbon: cold, deep, near-black. Never substitute a warm-tinted near-white "for contrast" — that's the AI training data trap and it kills the industrial register instantly.

## 3. Typography

**Display Font:** Barlow Condensed (Google Fonts — 400, 600, 700, 800 loaded)
**Body Font:** IBM Plex Sans (Google Fonts — 300, 400, 500, 600 loaded)

**Character:** Barlow Condensed is compressed and industrial — built for width-constrained environments like instrument labels and field specs. IBM Plex Sans is engineered-neutral: technical without being cold, readable in long blocks. The pairing is compression + clarity; the display font shouts, the body font explains.

### Hierarchy
- **Display** (700, clamp(2.6rem, 6vw, 4.5rem), line-height 1.1): Hero H1 only. Barlow Condensed, often uppercase. Maximum 4.5rem — do not exceed.
- **Headline** (700, clamp(1.8rem, 2.8vw, 2.5rem), line-height 1.2): Section headings. Barlow Condensed.
- **Title** (700, 1.05–1.15rem, line-height 1.2, letter-spacing 0.03em): Card headings, sub-section labels. Barlow Condensed, uppercase.
- **Body** (400, 1rem, line-height 1.7): All prose. IBM Plex Sans. Cap line length at 65–75ch; do not let body text stretch full-width on large viewports.
- **Label** (600, 0.65–0.72rem, letter-spacing 0.08–0.15em, uppercase): Tags, badge text, micro-labels. Barlow Condensed. Minimum size 0.65rem — do not go smaller.

### Named Rules
**The Two-Face Rule.** Barlow Condensed for display, headline, title, and label. IBM Plex Sans for body. Never mix: no IBM Plex Sans headlines, no Barlow body paragraphs. The boundary is firm.

**The Ceiling Rule.** Hero display type is clamped at 4.5rem max. Letter-spacing on condensed display type must stay ≥ -0.02em (never cramped). `text-wrap: balance` on H1–H3 for even line breaks.

## 4. Elevation

This system uses **tonal layering as its primary depth mechanism**: bg-deep → carbon → iron → plate → plate-edge form a five-step material stack. The further a surface is from the page background (carbon), the more elevated it reads — no shadows required.

Shadows are **interaction-state signals only**, never ambient decoration. A card at rest is flat on its tonal layer. On hover, a shadow appears to confirm the state change. This keeps the resting state clean and ensures every shadow communicates something ("you can interact with this") rather than just sitting there.

### Shadow Vocabulary
- **Hover lift** (`0 16px 40px rgba(0,0,0,0.5)`): Cards on hover. Pure black shadow — depth into the void beneath.
- **Orange glow** (`0 10px 28px rgba(232,114,12,0.35)`): Primary button on hover. The only colored shadow. Signals the primary action.
- **Nav ambient** (`0 2px 24px rgba(0,0,0,0.6)`): Nav bar on scroll. Anchors the nav to the top of the viewport.

### Named Rules
**The Flat-By-Default Rule.** Every surface is flat at rest. Shadows appear only on hover or focus — never as a resting ambient. If you're adding a `box-shadow` to an element that doesn't change state, remove it.

## 5. Components

### Buttons
Compressed, uppercase, tracked — shaped like field equipment labels, not marketing buttons.
- **Shape:** 4px radius (slightly rounded, not square — a small concession to affordance)
- **Primary:** Orange (#E8720C) background, off-white text, Barlow Condensed 700 1.15rem, 0.08em letter-spacing, uppercase, padding 1rem 2.2rem. Hover: orange-glow background + translateY(-2px) + orange glow shadow.
- **Secondary / Ghost:** Transparent background, gray-light text, 1px rgba(200,208,218,0.3) border. Hover: steel-light border, white text. Same type specs as primary.
- **Nav CTA:** Identical to Primary but smaller (0.5rem 1.1rem padding) — nav-scaled.

### Cards
- **Corner Style:** Square (border-radius: 0) — the signature industrial treatment. Cards look like panels, not bubbles.
- **Background:** Plate (#1C2333)
- **Border:** 1px plate-edge + 3px plate-edge bottom border at rest. On hover: 3px bottom border becomes orange.
- **Shadow Strategy:** Flat at rest. Hover: `0 16px 40px rgba(0,0,0,0.5)` lift + translateY(-4px).
- **Internal Padding:** 1.4rem

### Tags / Chips
- **Shape:** 2px radius — minimal rounding
- **Calculation/Theory:** Amber (#F5A623) background, bg-deep text, amber border. High contrast amber-on-black.
- **Regulation:** rgba(61,122,95,0.15) background, green-light text, rgba(61,122,95,0.25) border. Subtle, contextual.
- **Type:** Barlow Condensed 600, 0.65rem, uppercase, 0.08em tracking

### Navigation
- **Style:** Fixed, full-width. Background `rgba(5,9,15,0.97)` with `backdrop-filter: blur(16px) saturate(1.4)`. 2px orange bottom border — the orange line is the nav's identity mark.
- **Links:** IBM Plex Sans 500 0.9rem, gray-light at rest → white on hover. No underlines.
- **Dropdowns:** Iron (#141A24) background, plate-edge border, 2px orange top border — mirrors the nav's own orange mark. 4px radius.
- **Scrolled state:** Border-bottom dims to `rgba(232,114,12,0.6)`, ambient shadow activates.
- **Mobile:** Hamburger below ~900px; full-width overlay menu.

### Paper Cards (Signature Component)
The exam paper selection grid — the most distinctive component on the site. Square-cornered with a paper code (e.g. "2A1") as an orange label + 24px orange divider bar, uppercase paper name, gray description, type tag. This is the system at its most compressed and precise: field-spec typography meeting card layout.

## 6. Do's and Don'ts

### Do:
- **Do** use square corners (border-radius: 0) on cards. It's the most identifiable mark of this system.
- **Do** apply `text-transform: uppercase` and `letter-spacing: 0.06–0.15em` to all Barlow Condensed labels, nav links, and button text.
- **Do** keep orange rare. One orange CTA per section. If more accent is needed, use amber.
- **Do** use IBM Plex Sans for all body copy and keep it at 1rem / 1.7 line-height with a 65–75ch column width max.
- **Do** use tonal steps for depth first — float a card on plate (#1C2333) above iron (#141A24) before reaching for a shadow.
- **Do** match WCAG 2.1 AA: off-white (#F4F5F7) on carbon (#0D1117) clears 4.5:1. Gray-mid (#a8b4c0) on carbon is at the boundary — use only for captions/descriptions, not body.
- **Do** include `@media (prefers-reduced-motion: reduce)` for every entrance animation and scroll-triggered transition.

### Don't:
- **Don't** use purple gradients, glassmorphism cards, or TailwindUI templates. This is not a SaaS tool — those visual signals immediately kill credibility with working operators.
- **Don't** use white or near-white backgrounds. The system is dark by identity, not by trend. A white section anywhere on the page breaks the carbon stack.
- **Don't** use warm-tinted near-white backgrounds (cream, sand, linen, paper). The carbon background is cold; warmth is carried by orange and amber accents, not by the surface.
- **Don't** use stock photos of students smiling at laptops or add gamification badges. The Coursera/Udemy aesthetic reads as performative to operators — it signals "built for beginners who need encouragement," not "built for people who've been doing this for years."
- **Don't** go red/black with aggressive-bold CTAs. Gritty means precise, not loud. The aggressive-trades aesthetic (gym supplement, bootcamp bro) reads as try-hard and misses the FSA register entirely.
- **Don't** use `border-left` greater than 1px as a colored accent stripe on cards at rest (the existing FAQ card's 4px left border is a known technical debt). Rewrite with full borders, tonal tinting, or remove the accent entirely.
- **Don't** use gradient text (`background-clip: text`). Use a solid orange or amber color on emphasis words; never a gradient.
- **Don't** add an eyebrow kicker (`ABOUT`, `PROCESS`, etc.) above every section heading. It's AI grammar. One deliberate structural marker per page is a design decision; eyebrows on every section is a scaffold.
- **Don't** exceed 4.5rem on hero display type. At 6rem+ the page is shouting — the boilerplate instrument panel doesn't shout.
