# Cognigenesis Branding

Cognigenesis uses a dark, high-contrast visual system designed to communicate a small trusted kernel surrounded by an expanding capability field.

## Logo

Primary vector asset:

```text
assets/brand/cognigenesis-logo.svg
```

The mark combines:

- a central execution kernel
- intersecting cognitive/capability loops
- four boundary nodes representing observable authority edges
- a cyan → violet → magenta intelligence gradient

Use the SVG as the canonical source asset. Export PNG variants from it only when a host application requires raster upload.

Recommended raster export sizes:

- 512×512 — AionUi custom agent avatar
- 256×256 — application icon
- 128×128 — compact UI avatar
- 64×64 — small launcher icon

## Theme

Canonical theme tokens:

```text
assets/brand/theme.json
```

Reusable CSS variables/components:

```text
assets/brand/theme.css
```

### Core palette

| Token | Hex | Purpose |
|---|---|---|
| Background | `#05070D` | primary canvas |
| Surface | `#0B1020` | panels/cards |
| Elevated surface | `#11182B` | active/raised UI |
| Border | `#1B2440` | structure |
| Primary text | `#F3F7FF` | high-priority text |
| Secondary text | `#A7B0C3` | supporting text |
| Cyan | `#62F5FF` | reasoning/thought |
| Violet | `#8B7CFF` | tools/execution |
| Magenta | `#C96CFF` | artifacts/evolution |
| Success | `#54E6A8` | successful execution |
| Warning | `#FFC857` | caution |
| Danger | `#FF6B7A` | denied/failed authority |

## AionUi

AionUi currently exposes an **Upload image** control for Custom Agents.

Use a 512×512 PNG exported from:

```text
assets/brand/cognigenesis-logo.svg
```

Display name:

```text
Cognigenesis
```

Command remains:

```text
cogni-acp
```

The AionUi host controls its surrounding application theme; Cognigenesis theme assets are the canonical design system for Cognigenesis-owned interfaces, launchers, dashboards, documentation, and future ACP UI surfaces.
