# Frontend Design Notes & Guidelines

This document outlines the aesthetic direction and reusable assets for the new FastAPI frontend.

## Target Aesthetic

The goal is a **simple, clear, minimalistic** design suitable for a **peaceful and calm literary contest**.

## Analysis of `app/static/` (Flask Assets)

*   **CSS (`style.css`, `forms.css`):**
    *   **Direct Reuse:** Not recommended due to coupling with Flask templates and size.
    *   **Inspiration:** Highly valuable. The existing styles established a good foundation aligned with the target aesthetic.
    *   **Key Elements to Adapt:**
        *   **Fonts:** `'Source Sans Pro'` (body), `'Playfair Display'` (headings).
        *   **Color Palette:**
            *   Background: `#f7f5f0` (light beige/off-white)
            *   Text: `#35302a` (dark brown-gray)
            *   Links: `#5e6b4c` (muted green)
            *   Borders/Accents: `#e0d8c9` (light grayish-beige)
        *   **Layout:** Centered content (`max-width: 1120px`), clear separation using borders, potentially a fixed header.
*   **JS (`script.js`, `roadmap/`):**
    *   **Direct Reuse:** Unlikely due to dependencies on Flask/Jinja rendering.
    *   **Inspiration:** Minimal. We are building interactions based on API calls.
*   **Images (`images/`):**
    *   **Direct Reuse:** Yes. Icons and thematic SVGs are suitable.
    *   **Specific Files to Copy:** `favicon.*`, `apple-touch-icon.png`, `android-chrome-*.png`, `*.svg`, `duelo-plumas-share.jpg`.

## Frontend Development Plan

1.  **Copy Reusable Images:** Transfer selected image assets from `app/static/images/` to `frontend/images/`.
2.  **Adapt CSS:** Create/modify `frontend/css/style.css` using the Flask app's fonts, color palette, and layout concepts as a strong foundation. Apply styles incrementally as components are built.
3.  **Implement Pages:** Follow the `frontend/flask_pages_inventory.md` document, building HTML structure and JS interactions, styling them according to these guidelines. 