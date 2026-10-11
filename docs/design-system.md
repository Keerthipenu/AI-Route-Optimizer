# ROUTEFORGE Design System

## Direction

The product uses a premium logistics control-room language: a calm charcoal workspace, thin operational dividers, compact data, editorial headings, and one acid-lime action/route accent. The map is the primary visual object. Decoration is deliberately restrained.

## Tokens

| Role | Value |
|---|---|
| Canvas | `#101210` |
| Panel | `#171A17` |
| Elevated panel | `#1C201B` |
| Divider | `#30362D` |
| Primary text | `#EEF1E9` |
| Muted text | `#929B8C` |
| Route / action accent | `#C7F464` |
| Secondary analytical accent | `#F39A55` |

Typography uses Manrope for interface text and DM Mono for labels, measurements, and operational metadata, with local sans-serif/monospace fallbacks if web fonts are unavailable. Spacing follows a 4 px base rhythm. Controls and panels use square or near-square corners to keep the interface technical rather than playful.

## Components and states

- Sidebar: compact navigation plus dataset and route constraints.
- Hero: small mono kicker, concise heading, restrained context line.
- Primary action: solid acid lime with dark text; clear hover and keyboard focus.
- Map: offline coordinate plane with labelled stops, depot marker, and a single highlighted route.
- Timeline: dense rows, explicit return leg, per-leg and cumulative distance.
- Metrics: border-led group rather than repeated floating cards.
- Explanation callout: lime rule and plain-language evidence.
- Empty state: instructive callout that says no calculation has run.
- Error state: Streamlit's accessible error surface populated with user-facing validation text.
- Loading state: the primary action communicates calculation through Streamlit's run state; no fake live telemetry.
- Success state: route, validation-aware metrics, explanation, and export actions appear together.

## Responsive behavior

The wide layout prioritizes map plus timeline. Streamlit columns collapse naturally on narrower screens; navigation remains in the collapsible sidebar, metrics wrap, and headings use a responsive type size. No required control depends on hover.

## Design-tool record

MagicPath was used for a rendered 1440 px dashboard exploration named **ROUTEFORGE — Dashboard Exploration**. It established the final hierarchy, map emphasis, acid-lime selection language, timeline treatment, and compact comparison layout. Figma connectivity was verified, but the connected Starter plan exposed a View seat, so no Figma file was claimed or used as an implementation source.
