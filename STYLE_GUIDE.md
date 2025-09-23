# SkyDesk Style Guide

## Brand Voice
- Confident, concierge-grade language that emphasizes precision and calm control.
- Focus on clarity over jargon; lean into aviation and travel operations metaphors when useful.

## Layout & Spacing
- Shell layout: `max-w-7xl` container with generous `px-4 sm:px-6 lg:px-8` gutters.
- Cards: 24px corner radius (`rounded-3xl`), subtle 1px border, layered drop shadows for depth.
- Vertical rhythm: default sections spaced by `space-y-6` on detail pages; `space-y-8` on dashboards.

## Color Palette
| Token | Tailwind Alias | Hex | Usage |
|-------|----------------|-----|-------|
| `bg` | `bg` | `#0a0b0f` | App background, full-bleed surfaces |
| `panel` | `panel` | `rgba(22,24,29,0.8)` | Translucent card layers |
| `muted` | `muted` | `#9aa4b2` | Secondary text, helper copy |
| `accent` | `accent` | `#7c5cff` | Primary CTAs, highlights |
| `accent-2` | `accent-2` | `#2dd4bf` | Secondary highlights, glows |
| Supporting | gradient blend | fuchsia/indigo | Ambient lighting flares |

## Typography
- Base font: Tailwind default sans (Inter stack).
- Headings: `font-semibold`, wide tracking for hero labels (`tracking-[0.3em]`).
- Body copy: `text-sm text-muted`; escalate to `text-white` for key figures.

## Components
- **Buttons**: Rounded-full pills, accent background with soft `shadow-lg shadow-accent/40`; hover states deepen opacity.
- **Secondary Buttons**: Outlined with `border-white/10`, text in `text-white/80`, lighten border/text on hover.
- **Forms**: Rounded-2XL inputs on translucent panels (`bg-white/10`), focus ring `focus:ring-2 focus:ring-accent/60`.
- **Selects**: Add `.theme-select` class for dark dropdown menus (`rgba(10,11,15,0.97)` options, white text).
- **Cards**: Use `.card` helper (semi-transparent background, subtle inner highlight) with 24px padding.

## Tabs
- Top tabs appear directly below the page header on detail pages.
- Order: `Overview`, `Communication`, `Documents`.
- Behavior: only one top panel visible at a time; smooth scroll to panel start on switch.
- Accessibility: use `role="tablist"`, `aria-selected` on buttons, and clearly toggle hidden state.

## Modals
- Use full-screen overlay with `bg-black/60`; modal card is `rounded-3xl`, `border border-white/10`, `bg-bg`.
- Title and helper text at top-left; “×” close control at top-right.
- Primary submit at bottom-right as an accent pill.
- Default focus moves to first interactive field when opened; overlay click and Escape close.

## Feedback Patterns
- Success: Emerald accent overlay (`border-emerald-500/40`, `bg-emerald-500/10`).
- Neutral info: Use `muted` text within translucent panels.
- Avoid harsh pure whites; rely on layered opacity.

## Motion & Interaction
- Hover transitions: `transition hover:bg-accent/90` for buttons; preserve smooth state changes.
- Sticky header retains blur (`backdrop-blur-xs`) to reinforce cockpit vibe.

## Assets
- Replace `static/logo.svg` with SkyDesk mark once finalized.
- Background glow elements positioned absolutely with gradient blur (see `base.html` for reference).
