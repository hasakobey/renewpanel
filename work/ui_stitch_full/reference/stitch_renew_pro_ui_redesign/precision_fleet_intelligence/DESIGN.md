---
name: Precision Fleet Intelligence
colors:
  surface: '#f8f9ff'
  surface-dim: '#cbdbf5'
  surface-bright: '#f8f9ff'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#eff4ff'
  surface-container: '#e5eeff'
  surface-container-high: '#dce9ff'
  surface-container-highest: '#d3e4fe'
  on-surface: '#0b1c30'
  on-surface-variant: '#434654'
  inverse-surface: '#213145'
  inverse-on-surface: '#eaf1ff'
  outline: '#737686'
  outline-variant: '#c3c6d7'
  surface-tint: '#0854d7'
  primary: '#003ca3'
  on-primary: '#ffffff'
  primary-container: '#0051d5'
  on-primary-container: '#c8d4ff'
  inverse-primary: '#b4c5ff'
  secondary: '#4b5e86'
  on-secondary: '#ffffff'
  secondary-container: '#bbcffd'
  on-secondary-container: '#44587f'
  tertiary: '#004191'
  on-tertiary: '#ffffff'
  tertiary-container: '#0058be'
  on-tertiary-container: '#c4d5ff'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#dbe1ff'
  primary-fixed-dim: '#b4c5ff'
  on-primary-fixed: '#00174b'
  on-primary-fixed-variant: '#003ea7'
  secondary-fixed: '#d8e2ff'
  secondary-fixed-dim: '#b3c6f4'
  on-secondary-fixed: '#021a3f'
  on-secondary-fixed-variant: '#33466d'
  tertiary-fixed: '#d8e2ff'
  tertiary-fixed-dim: '#adc6ff'
  on-tertiary-fixed: '#001a42'
  on-tertiary-fixed-variant: '#004395'
  background: '#f8f9ff'
  on-background: '#0b1c30'
  surface-variant: '#d3e4fe'
typography:
  headline-xl:
    fontFamily: Space Grotesk
    fontSize: 36px
    fontWeight: '700'
    lineHeight: 44px
    letterSpacing: -0.02em
  headline-xl-mobile:
    fontFamily: Space Grotesk
    fontSize: 28px
    fontWeight: '700'
    lineHeight: 36px
    letterSpacing: -0.01em
  headline-lg:
    fontFamily: Space Grotesk
    fontSize: 28px
    fontWeight: '700'
    lineHeight: 36px
    letterSpacing: -0.015em
  headline-lg-mobile:
    fontFamily: Space Grotesk
    fontSize: 22px
    fontWeight: '700'
    lineHeight: 28px
    letterSpacing: -0.01em
  headline-md:
    fontFamily: Space Grotesk
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 28px
    letterSpacing: -0.01em
  kpi-display:
    fontFamily: Space Grotesk
    fontSize: 32px
    fontWeight: '700'
    lineHeight: 36px
    letterSpacing: -0.02em
  kpi-display-mobile:
    fontFamily: Space Grotesk
    fontSize: 24px
    fontWeight: '700'
    lineHeight: 30px
    letterSpacing: -0.01em
  kpi-subtext:
    fontFamily: Inter
    fontSize: 13px
    fontWeight: '500'
    lineHeight: 18px
  body-lg:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  body-sm:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '400'
    lineHeight: 16px
  table-header:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '600'
    lineHeight: 16px
    letterSpacing: 0.04em
  table-cell:
    fontFamily: Inter
    fontSize: 13px
    fontWeight: '400'
    lineHeight: 18px
  label-md:
    fontFamily: Inter
    fontSize: 13px
    fontWeight: '500'
    lineHeight: 18px
  label-sm:
    fontFamily: Inter
    fontSize: 11px
    fontWeight: '600'
    lineHeight: 14px
    letterSpacing: 0.02em
  code-num:
    fontFamily: Space Grotesk
    fontSize: 13px
    fontWeight: '500'
    lineHeight: 18px
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  space-xxs: 0.25rem
  space-xs: 0.5rem
  space-sm: 0.75rem
  space-md: 1rem
  space-lg: 1.5rem
  space-xl: 2rem
  space-xxl: 3rem
  gutter-desktop: 1.5rem
  gutter-mobile: 1rem
  sidebar-width: 17.5rem
  sidebar-collapsed: 4.5rem
  header-height: 4rem
---

## Brand & Style

This design system establishes a high-performance, analytical environment tailored for enterprise automotive fleet operations, dealership inventory management, and technical appraisal workflows. The aesthetic communicates engineering authority, operational transparency, and high-tempo clarity. It blends structured German-automotive precision with modern enterprise SaaS usability.

The interface leverages high-contrast data planes, utilitarian geometry, and micro-interactions optimized for rapid scanning. The visual narrative balances executive control with technical shop-floor execution: clean slate backdrops prevent eye fatigue during all-day dispatch and valuation tasks, while deep navy navigational anchors ground the application with institutional gravitas.

## Colors

The color system is calibrated for mission-critical automotive asset tracking, stock turnaround indexing (SKS), and high-density financial ledgers.

### Color Tiers
- **Primary Canvas (`#F8FAFC`):** Soft, low-strain neutral canvas providing separation from desktop light glare.
- **Card & Workspace Surface (`#FFFFFF`):** Pure white elevated planes for distinct focal isolation.
- **Tonal Layer 1 (`#F0F5FA`):** Subdued surface container applied to sub-panels, segmented button backgrounds, and table row zebra striping.
- **Tonal Layer 2 (`#EFF4FF`):** Soft blue-tinted fill designated for active selections, highlighted table rows, and primary KPI callout panels.
- **Structural Navy (`#0F254A`):** Deep commanding shade for root navigation rails, sub-app headers, and data table fixed header zones.
- **Royal Electric (`#0051D5`):** The primary interaction and action color. Carries primary CTAs, metric spikes, focus rings, and high-priority filters.
- **Borders & Rules (`#E2E8F0`):** Crisp 1px structural dividing lines across panels and table boundaries.

### State & Stock Ageing (SKS) Semantics
- **Normal / Healthy (0–30 Days):** Text `#166534`, Container `#DCFCE7`, Border `#BBF7D0`. Fast turnaround; low capital risk.
- **Watch / Moderate (31–60 Days):** Text `#92400E`, Container `#FEF3C7`, Border `#FDE68A`. Approaching threshold; targeted remarketing.
- **Action Required (61–90 Days):** Text `#C2410C`, Container `#FFEDD5`, Border `#FED7AA`. Mandatory appraisal or floorplan discount review.
- **Critical / Overdue (90+ Days):** Text `#B91C1C`, Container `#FEE2E2`, Border `#FECACA`. Severe depreciation warning; liquidator escalation.

## Typography

The typographic pairing balances modern technical precision with supreme functional legibility.

- **Headlines & Primary Metrics:** `Space Grotesk` introduces automotive engineered character with geometric aperture shapes. Always enforce `font-feature-settings: "tnum" 1` (tabular figures) on metric headings, inventory counts, currency tallies, and VIN displays to prevent layout jitter during data refreshes.
- **Body, Ledger Tables & Controls:** `Inter` handles all dense informational readouts, technical parameter lists, labels, and table cells. It provides high micro-scale legibility under dense informational clustering.
- **SKS Status Indicators & Chips:** `Inter` Semi-Bold in uppercase micro-scale (`11px`) with slight positive tracking (+0.02em) to guarantee instant status recognition across mobile and monitor displays.

## Layout & Spacing

The layout is structured on a strict 8px spatial interval, ensuring mathematical harmony and modular consistency across dense enterprise screens.

### Layout Grid & Canvas Architecture
- **Desktop (1280px+):** Fixed structural left rail (`sidebar-width`: 280px / collapsed: 72px) with a fluid primary content canvas. Canvas margins default to 24px (`space-lg`), utilizing a 12-column dynamic flex-grid with 24px gutters.
- **Tablet (768px – 1279px):** Auto-collapsing navigation rail down to icon-only (72px). Grid shifts to 6 columns with 16px (`space-md`) gutters.
- **Mobile (< 768px):** Navigation transitions to an off-canvas slide-out drawer anchored from the left. 4-column layout model with 16px page padding.

### Data Densities & Spacing Rhythm
- **Default Card Padding:** 20px (Desktop), 16px (Mobile).
- **Table Cell Padding:** 12px vertical by 16px horizontal (Standard density); 8px vertical by 12px horizontal (High-density stock logs).
- **Form Groups:** 16px vertical gap between form fields; 8px between label and interactive input container.

## Elevation & Depth

Visual hierarchy uses clean planar layering over harsh elevation, prioritizing 1px perimeter outlines paired with calibrated ambient soft shadows to define elevation.

- **Tier 0 (Base Canvas):** `#F8FAFC`, zero shadow.
- **Tier 1 (Surface Cards & Panels):** Pure `#FFFFFF` resting surface framed with `border: 1px solid #E2E8F0`. Shadow: `0 1px 3px 0 rgba(15, 37, 74, 0.04), 0 1px 2px -1px rgba(15, 37, 74, 0.02)`.
- **Tier 2 (Floating Modals, Flyouts & Drawers):** Shadow: `0 10px 15px -3px rgba(15, 37, 74, 0.08), 0 4px 6px -4px rgba(15, 37, 74, 0.04)`. Outlined with `border: 1px solid #CBD5E1`.
- **Tier 3 (Popovers, Tooltips & Instant Dropdowns):** Shadow: `0 20px 25px -5px rgba(15, 37, 74, 0.12), 0 8px 10px -6px rgba(15, 37, 74, 0.06)`.

Primary interactive cards feature a focused hover transition: border shifts from `#E2E8F0` to `#0051D5` at 40% opacity, paired with an ambient y-offset displacement of -2px.

## Shapes

The geometric framework is balanced: crisp internal controls live inside softly rounded container boundaries.

- **KPI Containers & Data Cards:** `12px` to `16px` border radius (`rounded-lg` / `rounded-xl`). Cards avoid overly round geometry to optimize usable square pixel area for dense data grids.
- **Buttons, Form Inputs & Search Fields:** `8px` (`rounded-md`). Delivers a tactile, responsive trigger footprint.
- **Status Badges, SKS Pills & Micro Counters:** Fully pill-shaped (`9999px`) to immediately distinguish categorical indicators from clickable rectangular action items.
- **Table Header Containers:** Upper corners inherit the parent card's `12px` radius; lower corners terminate squarely against the first data row.

## Components

### Buttons
- **Primary:** Background `#0051D5`, text `#FFFFFF`, height `40px` (desktop) / `44px` (touch mobile). Hover state: `#0040A8`. Focus ring: 3px `#0051D5` at 25% opacity.
- **Secondary / Header Filter:** Background `#FFFFFF`, border `1px solid #E2E8F0`, text `#0F254A`. Hover: `#F0F5FA` background with `#0051D5` text.
- **Dark Utility (Nav & Header contexts):** Background `#0F254A`, text `#FFFFFF`. Hover: `#1E3A6B`.

### SKS Status Pills (Stock Ageing Tracking)
Rendered as `inline-flex` items with `height: 24px`, padding `0 10px`, border radius `9999px`, and `border: 1px solid`:
- **0–30 Gün (Normal):** Text `#166534`, fill `#DCFCE7`, border `#BBF7D0`.
- **31–60 Gün (İzleme):** Text `#92400E`, fill `#FEF3C7`, border `#FDE68A`.
- **61–90 Gün (Aksiyon):** Text `#C2410C`, fill `#FFEDD5`, border `#FED7AA`.
- **90+ Gün (Kritik):** Text `#B91C1C`, fill `#FEE2E2`, border `#FECACA`.

### Data Tables
- **Header:** Sticky top position, background `#0F254A`, text `#FFFFFF` (`table-header` typography). Columns with active sorting display an inline directional arrow icon (`Material Symbols`).
- **Body Rows:** Base `#FFFFFF`, alternating zebra tint `#F8FAFC`. Hover highlight: `#EFF4FF`. Active row select checkbox embedded into the primary column.
- **Mobile Adaptation:** Tables are placed in a contained horizontal scroll chassis with an explicit right-side shadow gradient indicating scrollable content. Primary vehicle identifier (plate/VIN) stays pinned to the left edge during scroll.

### Form Inputs & Filters
- **Input Fields:** Height `40px`, border `1px solid #E2E8F0`, background `#FFFFFF`, text `#0F254A`, placeholder `#94A3B8`. Focus state shifts border to `#0051D5` with an offset shadow ring.
- **Segmented Vehicle Switchers:** Enclosed container `#F0F5FA` with 4px padding. Active state uses `#FFFFFF` elevation with a 1px border.

### Off-Canvas Mobile Navigation Drawer
- **Chassis:** Docked at `width: 280px`, background `#0F254A`, backdrop blur overlay `rgba(15, 37, 74, 0.5)`.
- **Navigation Links:** Height `44px`, text `#94A3B8`, active item with `#EFF4FF` background at 10% opacity, crisp `#0051D5` left border indicator (3px width), and white active typography.