# Penguin Court Design System

Source inspiration:
- Claude design language from `VoltAgent/awesome-design-md`
- Workspace structure inspired by Linear

Reference sources:
- Claude DESIGN.md: https://raw.githubusercontent.com/VoltAgent/awesome-design-md/main/design-md/claude/DESIGN.md
- Linear product site: https://linear.app/

## 1. Design Intent

Build Penguin Court as a warm, trustworthy legal AI workspace.

The visual mood should feel like:
- a serious legal document room, not a flashy AI landing page
- a premium editorial product, not a dashboard made of generic cards
- a focused workflow console, not a chat toy

This project must combine:
- Claude's warm editorial atmosphere and parchment-toned palette
- Linear's disciplined product structure and workspace clarity

The result should feel calm, high-credibility, and operational.

## 2. Product Framing

This is not a generic AI assistant.

It is a workflow product centered on one fixed chain:

`case intake -> trial simulation -> opponent behavior -> win-rate analysis -> replay report`

The interface must make that chain legible at all times.

Users should always know:
- where they are in the process
- what the current stage means
- what action advances the case
- what evidence, disputes, and risks matter right now

## 3. Visual Direction

### 3.1 Atmosphere

Primary feeling:
- warm
- thoughtful
- document-like
- judicial
- restrained

Secondary feeling:
- precise
- productized
- process-driven

Avoid:
- futuristic neon AI aesthetics
- startup gradient branding
- loud motion
- excessive gamification

### 3.2 Color System

Use a warm neutral palette inspired by Claude.

Core colors:
- page background: `#f5f4ed`
- elevated light surface: `#faf9f5`
- warm border: `#e8e6dc`
- primary text: `#141413`
- secondary text: `#5e5d59`
- muted text: `#87867f`
- dark surface: `#30302e`
- accent terracotta: `#c96442`
- accent terracotta hover: `#d97757`
- focus ring blue: `#3898ec`

Rules:
- all grays must stay warm
- accent color budget is one primary accent only
- no purple
- no bright product blue except accessibility focus states
- no obvious gradient branding

## 4. Typography

The hierarchy must use editorial serif for authority and clean sans for utility.

Headline style:
- serif
- medium weight
- tight line-height
- book-title presence

UI style:
- sans-serif
- neutral
- easy to scan

Recommended implementation fallback if custom fonts are unavailable:
- headlines: `Georgia`, `Times New Roman`, serif
- body/UI: `"Geist", "Segoe UI", "Helvetica Neue", Arial, sans-serif`
- mono/meta: `"JetBrains Mono", "SFMono-Regular", Consolas, monospace`

Rules:
- serif only for major headings and section anchors
- sans for body, controls, labels, navigation, status
- no Inter-as-default look
- no oversized screaming headlines
- data and IDs should use tabular or mono treatment when useful

## 5. Layout System

### 5.1 Overall Structure

The product should use Linear-style information architecture, not Linear's visual skin.

Primary shell:
- top header with product identity and current case context
- stage progress band near the top
- main workspace area
- right-side context panel on desktop
- bottom or inline action area for the next step

### 5.2 Main Workspace

The main workspace should prioritize the current stage.

Desktop layout:
- left: main stage canvas
- right: case context and supporting signals

Mobile layout:
- current stage canvas first
- supporting context second
- actions last

### 5.3 Section Rhythm

Use generous whitespace and clear containment.

Rules:
- prefer layout over card grids
- avoid three equal feature cards
- use dividers, panels, and rhythm instead of card soup
- keep content width controlled
- major sections must breathe

## 6. Component Language

### 6.1 Stage Progress

The stage progress strip is mandatory.

It must:
- show all five major business stages clearly
- distinguish current, completed, and upcoming states
- feel operational, not decorative

### 6.2 Primary Action Area

Each stage should expose one clear primary action cluster.

Rules:
- actions must be directly tied to the current stage
- avoid overwhelming users with too many equal-priority buttons
- primary CTA may use terracotta
- secondary actions should use warm neutral surfaces

### 6.3 Panels

Panels should feel like paper or dossier surfaces.

Rules:
- light surfaces on parchment background
- minimal shadows
- border-led depth
- medium rounded corners, not pills
- no glassmorphism

### 6.4 Legal Data Blocks

For claims, issues, evidence, and risk items:
- prefer grouped lists
- use labels and short descriptions
- emphasize scanability
- keep metadata compact

## 7. Motion

Motion should be subtle and purposeful.

Allowed:
- fade-up entry on major blocks
- small progress transitions
- hover polish on buttons and selectable rows
- smooth state interpolation between stages

Avoid:
- bouncing UI
- cinematic parallax
- glowing hover effects
- long choreographed storytelling motion

Motion principles:
- fast
- quiet
- transform/opacity only
- mobile-safe

## 8. Page-Specific Guidance

### 8.1 Launch / Overview

The launch area should feel like an editorial control desk.

It should:
- introduce the system briefly
- foreground the case or case selection
- make the main workflow visible immediately

It should not:
- behave like a generic AI homepage
- use marketing slogans everywhere
- rely on decorative hero cards

### 8.2 Case Intake

This stage should feel like structured dossier intake.

Use:
- grouped fields
- strong labels
- warm neutral form surfaces
- clear validation

Avoid:
- enterprise admin-table aesthetics
- noisy multi-column form chaos

### 8.3 Trial Simulation

This is the core stage and the visual center of the product.

Use:
- one dominant scene panel
- current stage title
- current narrative text
- direct progression actions

### 8.4 Opponent Behavior

This should feel like tactical briefing, but still legal and calm.

Use:
- likely arguments
- likely evidence
- likely strategies
- recommended response lines

Avoid:
- war-room sci-fi visuals

### 8.5 Win-Rate Analysis

Use:
- one central win-rate number or meter
- positive factors
- negative factors
- evidence gap actions

Do not make this look like a finance dashboard.

### 8.6 Replay Report

This stage should look closest to a legal work product.

Use:
- stage path
- key observations
- evidence checklist
- next-step plan

This section should feel exportable and trustworthy.

## 9. Hard Constraints

Do not do any of the following:
- no purple AI palette
- no generic SaaS card mosaic
- no giant glass cards
- no heavy dark shadows
- no Lucide-default look unless already required by repo
- no full-screen marketing hero unrelated to the workflow
- no random illustration style clashes
- no emoji

## 10. Implementation Priority

When implementing, keep this order:
1. establish color and typography tokens
2. establish shell layout and stage progress
3. establish stage-first workspace hierarchy
4. refine surfaces and action hierarchy
5. add light motion polish

## 11. Acceptance Test

The design is correct only if:
- the page reads as a legal AI system, not a generic AI site
- the workflow chain is obvious without explanation
- the first impression feels warm and credible
- the workspace feels operational and productized
- the interface remains calm even with dense information
