---
name: Precision Automotive Fleet Intelligence
colors:
  surface: '#f8f9ff'
  surface-dim: '#c5dcfd'
  surface-bright: '#f8f9ff'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#eff4ff'
  surface-container: '#e6eeff'
  surface-container-high: '#dce9ff'
  surface-container-highest: '#d3e4ff'
  on-surface: '#031c36'
  on-surface-variant: '#434654'
  inverse-surface: '#1b314c'
  inverse-on-surface: '#eaf1ff'
  outline: '#737686'
  outline-variant: '#c3c6d7'
  surface-tint: '#0353da'
  primary: '#003da6'
  on-primary: '#ffffff'
  primary-container: '#0052d9'
  on-primary-container: '#cbd6ff'
  inverse-primary: '#b4c5ff'
  secondary: '#006780'
  on-secondary: '#ffffff'
  secondary-container: '#76dcff'
  on-secondary-container: '#006077'
  tertiary: '#5900c4'
  on-tertiary: '#ffffff'
  tertiary-container: '#732de3'
  on-tertiary-container: '#e1d0ff'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#dbe1ff'
  primary-fixed-dim: '#b4c5ff'
  on-primary-fixed: '#00174b'
  on-primary-fixed-variant: '#003ea8'
  secondary-fixed: '#b7eaff'
  secondary-fixed-dim: '#6cd3f7'
  on-secondary-fixed: '#001f28'
  on-secondary-fixed-variant: '#004e61'
  tertiary-fixed: '#eaddff'
  tertiary-fixed-dim: '#d2bbff'
  on-tertiary-fixed: '#25005a'
  on-tertiary-fixed-variant: '#5a00c6'
  background: '#f8f9ff'
  on-background: '#031c36'
  surface-variant: '#d3e4ff'
typography:
  display-lg:
    fontFamily: Space Grotesk
    fontSize: 36px
    fontWeight: '700'
    lineHeight: 44px
    letterSpacing: -0.03em
  headline-lg:
    fontFamily: Space Grotesk
    fontSize: 28px
    fontWeight: '600'
    lineHeight: 36px
    letterSpacing: -0.02em
  headline-lg-mobile:
    fontFamily: Space Grotesk
    fontSize: 22px
    fontWeight: '600'
    lineHeight: 28px
    letterSpacing: -0.01em
  headline-md:
    fontFamily: Space Grotesk
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 28px
    letterSpacing: -0.01em
  headline-sm:
    fontFamily: Space Grotesk
    fontSize: 16px
    fontWeight: '600'
    lineHeight: 24px
    letterSpacing: 0em
  metric-kpi-xl:
    fontFamily: Space Grotesk
    fontSize: 32px
    fontWeight: '700'
    lineHeight: 38px
    letterSpacing: -0.02em
  metric-kpi-md:
    fontFamily: Space Grotesk
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 30px
    letterSpacing: -0.01em
  body-lg:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
    letterSpacing: -0.01em
  body-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
    letterSpacing: 0em
  body-sm:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '400'
    lineHeight: 16px
    letterSpacing: 0.01em
  table-data:
    fontFamily: Inter
    fontSize: 13px
    fontWeight: '400'
    lineHeight: 18px
    letterSpacing: 0em
  table-numeric:
    fontFamily: Inter
    fontSize: 13px
    fontWeight: '500'
    lineHeight: 18px
    letterSpacing: 0.02em
  label-caps:
    fontFamily: Space Grotesk
    fontSize: 11px
    fontWeight: '600'
    lineHeight: 14px
    letterSpacing: 0.08em
  label-ui:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '500'
    lineHeight: 16px
    letterSpacing: 0.01em
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  space-2xs: 0.125rem
  space-xs: 0.25rem
  space-sm: 0.5rem
  space-md: 0.75rem
  space-base: 1rem
  space-lg: 1.25rem
  space-xl: 1.5rem
  space-2xl: 2rem
  space-3xl: 2.5rem
  space-4xl: 3rem
  sidebar-width-expanded: 17.5rem
  sidebar-width-collapsed: 4.5rem
  header-height: 4rem
  gutter-desktop: 1.5rem
  gutter-mobile: 1rem
---

## Brand & Style

This design system establishes a high-performance, mission-critical operations environment tailored for premium automotive lifecycle tracking, inventory management, and telemetry intelligence. The aesthetic merges executive boardroom prestige with industrial-grade technical precision.

### Aesthetic Movement & Tone
- **Style Archetype:** Modern Technical Precision with High-Density Corporate Ergonomics.
- **Tone:** Authoritative, calculated, reliable, and frictionless.
- **Visual Tenet:** Data-first density without cognitive clutter. Operational metrics, VIN registries, telemetry indicators, and financial lifecycles sit on crisp, disciplined surfaces framed by surgical divider rules.
- **Contrast Philosophy:** Dark, monolithic navigational anchors juxtaposed against luminous, high-clarity content planes to focus mechanical attention onto real-time alerts and fleet status vectors.

## Colors

The palette establishes an immediate operational hierarchy, balancing enterprise clarity with assertive status reporting.

### Functional Application
- **Executive Navigational Anchor:** `sidebar-bg` (`#0B1D30`) houses high-level application switching, contextual dealership switches, and system status, paired exclusively with `sidebar-text` (`#DCE6F2`) for zero eye-fatigue over extended shifts.
- **Canvas & Elevation Layering:** Base layouts sit on `page-bg` (`#F4F7FB`). Elevated cards and telemetry pods use `surface` (`#FFFFFF`), while grouped tables, headers, and inset metric docks alternate between `surface-soft` (`#F8FAFD`) and `surface-blue` (`#EDF4FF`).
- **Primary Driving Action:** Primary brand interactions use `primary` (`#0052D9`), transitioning to `primary-hover` (`#0044B5`) on engagement, with `primary-soft` (`#EAF1FF`) reserved for active state highlights, selection chips, and focused row states.
- **Status & Telemetry Tiers:** Strict two-tone status pairings are enforced. Alerts never appear as raw text on white; they must use the calibrated background tokens:
  - **Success (Operational/Nominal):** `#15803D` over `#EAF8EF`
  - **Warning (Maintenance Required/Inspection Pending):** `#A86408` over `#FFF5DF`
  - **Danger (Critical Fault/Contract Breach):** `#C6283D` over `#FFF0F2`
- **Secondary Telemetry Vectors:** `accent-cyan` (`#0891B2`) denotes dynamic IoT streaming, vehicle diagnostics, and charging states; `accent-purple` (`#7C3AED`) identifies valuation models, automated reconditioning paths, and lifecycle milestones.

## Typography

The typographic hierarchy implements an intentional division between structural telemetry indices and readable administrative flows:

- **Space Grotesk** is deployed across viewports for all major headings, modal titles, and high-impact analytics KPI callouts. Its geometric construction gives automotive technical readouts an authentic instrument-cluster presence.
- **Inter** governs high-density tabular ledgers, parameters, vehicle history logs, and standard form controls, guaranteeing crisp rendering at sub-14px sizes.
- **Tabular Numerics Rule:** Every monetary valuation, VIN sequence, odometer log, fuel level percentage, and maintenance timestamp must enforce font feature settings `font-variant-numeric: tabular-nums;` (or `font-feature-settings: "tnum" 1`). This eliminates horizontal jitter across updating rows and metrics counters.
- **All-Caps Technical Micro-labels:** `label-caps` must be rendered in uppercase with positive tracking (`letterSpacing: 0.08em`) to designate status pills, column categories, and sensor parameters.

## Layout & Spacing

The design system implements a high-density, fluid-responsive operational layout optimized for widescreen workstation displays (1440px–1920px) while maintaining fluid integrity down to handheld diagnostics devices (375px).

### Layout Geometry
- **App Shell Structure:** Fixed dual-tier layout consisting of a persistent dark navigation sidebar (`#0B1D30`) docked to the left, paired with a persistent top utility header (`header-height: 4rem`) docked above the dynamic viewport canvas.
- **Grid Architecture:** 
  - **Desktop (≥1280px):** 12-column fluid grid, 24px (`space-xl`) outer margins, 24px (`space-xl`) gutters.
  - **Tablet (768px – 1279px):** 8-column fluid grid, 20px margins, 16px (`space-base`) gutters.
  - **Mobile (≤767px):** 4-column fluid grid, 16px (`space-base`) margins, 12px (`space-md`) gutters. Sidebar collapses into an off-canvas drawer.
- **Rhythm & Metrics Matrix:** Spacing values scale strictly on an 8pt base grid with a 4pt sub-grid for micro-controls, input padding, and tight table rows. Dense table rows adhere to a compact 40px vertical rhythm, while standard rows occupy 48px.

## Elevation & Depth

This system avoids heavy, blurred atmospheric drop shadows in favor of **Tonal Layers and Structural Micro-Borders**, maintaining an authentic industrial software aesthetic.

### Depth Hierarchy
1. **Level 0 (App Canvas):** Base background `#F4F7FB`. Raw and non-elevated.
2. **Level 1 (Structural Cards & Data Pods):** Pure `#FFFFFF` surface bounded by a crisp 1px solid `#E2E8F0` border. No shadow is applied under normal conditions; depth is created strictly by value contrast against the `#F4F7FB` backdrop.
3. **Level 2 (Hovered Records & Context Cards):** Retains 1px border with a faint, tight ambient shadow: `0 4px 12px -2px rgba(20, 43, 69, 0.06), 0 2px 4px -1px rgba(20, 43, 69, 0.03)`.
4. **Level 3 (Dropdown Menus, Flyout Filters, Popovers):** Elevated surface `#FFFFFF` bounded by `#E2E8F0` with directional depth: `0 10px 24px -4px rgba(20, 43, 69, 0.10), 0 4px 8px -2px rgba(20, 43, 69, 0.04)`.
5. **Level 4 (Modals & Emergency Telemetry Overlays):** Positioned over an explicit `#0B1D30` backdrop at 65% opacity (`backdrop-filter: blur(4px)`). Shadow: `0 24px 48px -12px rgba(11, 29, 48, 0.25)`.

## Shapes

The interface embraces a **Soft / High-Precision** geometry (`roundedness: 1`). Radii are kept small and measured, reinforcing machine-tooled discipline without feeling aggressive or purely brutalist.

### Radius Assignments
- **Micro Radii (2px):** Checkbox boxes, progress bar indicators, status tags.
- **Standard Base Radii (4px / `0.25rem`):** Buttons, inputs, search boxes, tab containers, chip indicators.
- **Card & Container Radii (8px / `0.5rem` / `rounded-lg`):** Telemetry panels, operational data cards, dialog modals, interactive data tables.
- **Large Framing Radii (12px / `0.75rem` / `rounded-xl`):** Heavy analytics dashboards and full-page canvas viewport wrappers.
- **Circular (9999px):** Purely reserved for avatars, icon badge notifications, and live GPS vehicle beacons on tracking maps.

## Components

### Buttons
- **Primary:** Filled `#0052D9`, text `#FFFFFF`, height 38px (32px compact), 4px radius. Font: Inter 13px/600. Hover: `#0044B5`. Active: `#003794`. Focus: 2px ring `#0052D9` offset by 2px `#FFFFFF`.
- **Secondary / Ghost Outline:** Surface `#FFFFFF`, 1px solid border `#E2E8F0`, text `#142B45`. Hover: background `#F8FAFD`, border `#CBD5E1`.
- **Soft Primary:** Surface `#EAF1FF`, border transparent, text `#0052D9`. Hover: background `#DDE8FD`.
- **Danger:** Surface `#C6283D`, text `#FFFFFF`. Subtle variant uses background `#FFF0F2` with text `#C6283D`.

### Input Fields & Search Bars
- Background: `#FFFFFF` (resting) or `#F8FAFD` (table inline edit).
- Border: 1px solid `#E2E8F0`. Focus state: border `#0052D9`, 0 0 0 1px `#0052D9`.
- Typography: Inter 14px, placeholder `#718096`, input value `#142B45`.
- Affixes: VIN decoders and plate lookups include a left icon in `#64748B` and an optional right-aligned verification badge.

### Status Chips & Badges
- Strict pill architecture (`radius: 4px` or `9999px`, height: 22px, padding: `0 8px`).
- Always use high-contrast status duos:
  - **Active / Operational:** BG `#EAF8EF`, Text `#15803D`.
  - **In Workshop / Servicing:** BG `#FFF5DF`, Text `#A86408`.
  - **Critical Alert / Grounded:** BG `#FFF0F2`, Text `#C6283D`.
  - **Telemetry Stream Active:** BG `#EDF4FF`, Text `#0891B2`.

### Cards & Telemetry Pods
- Background: `#FFFFFF`. Border: 1px solid `#E2E8F0`. Corner radius: 8px.
- Padding: 20px standard, 16px compact.
- Header structure: Space Grotesk title with secondary Inter context label, separated from body by 1px solid `#EDF1F6` divider.

### Data Tables (Fleet Inventory & Financial Ledgers)
- Header: `#F8FAFD` background, 1px solid `#E2E8F0` bottom boundary. Column titles in `label-caps` (`#64748B`).
- Rows: Clean `#FFFFFF` base, alternating optional `#F8FAFD` row shading for 15+ column datasets. Bottom border 1px solid `#EDF1F6`.
- Hover: Entire row shifts to `#EDF4FF` with pointer cursor.
- Numeric alignment: Columns with currency, mileage, or quantities are right-aligned with `tabular-nums`.

### Checkboxes & Radios
- Size: 16x16px. Border: 1.5px solid `#CBD5E1`. Radius: 3px (checkbox), round (radio).
- Checked: Background `#0052D9`, border `#0052D9`, checkmark `#FFFFFF`.

### Automotive Specific: Vehicle Profile Strip
- Inset bar featuring vehicle plate (monospaced high-contrast badge), VIN copy trigger, quick-status dot, and real-time fuel/battery meter. Background `#F8FAFD` with 1px border `#E2E8F0`.