# Design: The Lenny Growth Assistant

## Design principles

The UI is minimal, cinematic, editorial, spacious, and readable. It takes a restrained podcast/radio atmosphere from hero imagery, subtle grain, editorial type, and “On Air” source language; it is not a generic AI dashboard or fake audio console.

## Information architecture

Hero → Conversation → Sources → Artifacts via modal. Sessions are accessed through a drawer.

## Hero

The full-width hero presents the product title, description, corpus summary, and hero image. Its sticky header contains a Local/Cloud selector and readiness badge. Local is the browser default. The selector is a radio group whose selected state is updated by JavaScript and styled as an animated selection treatment.

## Conversation

The workspace orders assistant answer, provider tag, source pills, then an optional artifact card. A sticky multiline composer supports Enter to send and Shift+Enter for a newline. A loading row says transcripts are being searched and a grounded response generated. Errors use a toast plus provider-specific explanatory content. Sources show guest/timestamp and safely open their source URL.

## Sessions

Sessions open in an overlay drawer with New Conversation, Clear All, recency-ordered entries, selection, rename, and deletion. Selecting a session loads only its messages; the active ID is restored from browser storage when available.

## Artifacts

Artifact results appear as a **View Artifact** card. It opens a modal with title, type, safety state, Download, and Close controls. HTML uses an isolated iframe; Markdown renders in the modal. Close, backdrop click, and Escape dismiss the modal. Rejected HTML shows an error state and has no download.

## HTML security UX

- **Valid:** “Verified Safe,” render and download available.
- **Sanitized:** “Sanitized • Safe,” prohibited content removed before rendering.
- **Rejected:** “Blocked • Unsafe Code,” reason and safer re-request suggestion shown.
- **Error:** sanitization errors become a rejected artifact, preventing render/download.

## Responsive behavior

Desktop retains an expansive hero and workspace; the drawer overlays rather than permanently occupying a column. Tablet contracts content while retaining header controls. Mobile preserves the same vertical order with overlay drawer and modal rather than adding a permanent sidebar/panel.

## Accessibility

Actual markup includes labelled buttons, a labelled provider radio group with `aria-checked`, labelled textarea, live regions for messages/status/toasts, and dialog roles. Artifact cards are keyboard focusable and open with Enter/Space. Escape closes the artifact modal or drawer. The dark surface/light text palette provides contrast. Modal focus trapping and focus restoration are not implemented.

## Design decisions

- The hero is minimal so the first question remains central.
- Artifacts are modal so conversation stays primary and rendering remains isolated.
- Sessions are a drawer because history is navigation, not the main workspace.
- Local/Cloud is a named selector because it communicates two explicit providers.
- The podcast aesthetic is subtle to keep the experience editorial rather than theatrical.

