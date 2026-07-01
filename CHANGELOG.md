# Changelog

All notable changes to MarketPlaceLens are documented here.

## Unreleased

- Added a container `reset-password` CLI for resetting and re-enabling an admin account directly in SQLite.
- README and full documentation now explain the product advantage over native marketplace searches: granular search rules, a unified review workflow, and built-in AI assistance.
- README now uses the LanLens-style Buy Me a Coffee button and explains that voluntary support does not buy support priority, features, or access.
- README screenshots now use consistent laptop and docking-station demo listings instead of mismatched product images.
- Docker build context now excludes local databases, session secrets, caches, Git metadata, and generated screenshots.
- FastAPI is updated so dependency resolution pulls a Starlette release with current security fixes.
- Test discovery now works from a clean checkout without requiring callers to set `PYTHONPATH` manually.
- Saved job URLs and proxied listing image URLs now reject localhost, `.local`, and private/reserved network hosts before outbound fetches.

## [0.4.1] - 2026-06-18

### Changed

- Sanitized public demo data in documentation, tests, and screenshots to avoid private-looking names, places, or local context.
- Refreshed README and screenshot examples with neutral demo content.

## [0.4.0] - 2026-06-18

### Added

- Listing location chips now include a map action that opens the advertisement ZIP/place in an OpenStreetMap dialog.
- First visit now chooses the UI language from the browser language when the user has not saved a language preference yet.
- Facebook Marketplace settings now include a setup guide for Marketplace URLs and optional browser Cookie headers.
- First-run setup now shows a scraping and platform-rules notice before the admin account form.
- Listing cards now show whether a buyer has already contacted the seller, with a quick toggle in list and swipe views.
- Facebook Marketplace jobs can use an optional locally stored Cookie header from the admin settings when the URL only works in an authenticated browser session.
- The review flow now uses larger product-focused cards with inline actions inspired by the Kramlet card layout.
- Quick jobs can now generate a structured search draft from one natural-language sentence through the configured AI provider.
- Admin settings now include an AI provider test action to verify OpenAI/Ollama/LM Studio connectivity from the running container.
- Job notification choices now present background polling, Telegram, and webhook delivery as first-class options in both quick and manual job setup.
- Admins can now delete individual run errors or clear all run-error logs to reset the dashboard error counter.
- Listings can now show an optional saved AI assessment that summarizes fit and visible caution signs directly on listing and review cards.
- AI listing assessments now have a separate automatic mode for visible listing batches, with an in-settings warning about potential token usage.
- AI listing assessments can now be enabled for newly found listings during job runs, so fresh matches can arrive with a product, price, and description quality note already attached.

### Changed

- Marking a listing as contacted now automatically adds it to the user's default watchlist.
- AI listing assessment prompts now judge whether an article is useful for the saved search and compare the asking price with a cautious currently usual used-market range.
- AI buyer text suggestions now keep the configured buyer name for the signature only and prevent it from being used as the seller greeting.
- Facebook Marketplace search URLs copied from the `marketplace/np/.../search` view are normalized to the standard Marketplace search path before fetching.
- Facebook setup copy is now more task-oriented: users first create a Marketplace URL job, then add a browser Cookie only when Facebook requires a logged-in session.
- AI listing assessment prompts now focus on whether the product, price, and description make the listing worthwhile and qualitative.
- Facebook Cookie settings now fail fast with a clear message when the stored browser Cookie lacks the logged-in `c_user`/`xs` session pair.
- Facebook Marketplace requests now normalize pasted browser headers to the real Cookie value and include browser navigation headers.
- The Listings view now uses a compact modern work header with job run controls, search, view switching, filters, pagination, and a mobile bottom navigation.
- Listing tiles and swipe cards now use the fuller Scan Card treatment, while list view keeps the compact scan row with actions on the right and mobile-friendly stacked actions.
- Language, version, and light/dark theme controls now match Kramlet's bottom-right floating display-options control instead of living in the top header.
- Review cards are now more Kramlet-like on phones, with the actions inside the product card and compact mobile sizing so a listing fits into one screen more reliably.
- The Review section is now labeled Swipe/Swipen and its product cards show the same marketplace date, ZIP, and place details as listing cards.
- Language and light/dark theme controls now use Kramlet-style quick buttons on login and in the main header instead of select menus.
- Settings now use LanLens-style tabs for Notifications, Facebook, AI, Watchlists, Users, Recent runs, and Account instead of one long admin stack.
- Notification settings are split into Telegram, webhook, and delivery-rule cards for clearer channel configuration.
- The default watchlist is now saved per user, and non-admin users can manage their own Watchlist settings tab.
- UI cards, buttons, and list items now use stronger shadows, hover motion, and subtle entrance animation with reduced-motion support.
- Run-error cleanup controls now use clearer copy in the dashboard and settings.

### Fixed

- Job map clicks now reverse-geocode the selected point into a ZIP/place so Kleinanzeigen location and radius searches can use the map selection.
- Listing status updates no longer collide with long-running job-side AI assessment or notification waits, because job writes are committed before external provider calls.
- Settings reads no longer rewrite the default watchlist row on every request, and SQLite now waits for short writer locks instead of returning intermittent internal server errors while job runs are active.
- AI quick jobs now clean price constraints out of the search query, infer notebook searches as Kleinanzeigen `Elektronik > Notebooks`, and avoid saving Kleinanzeigen footer links as fake results when a search page has no real listing cards.
- Ollama AI calls now use the OpenAI-compatible completion token limit field, preventing reasoning models such as Qwen from returning an empty visible message after spending the budget on reasoning tokens.
- Listing action buttons and job-form save controls now wrap and stay reachable more defensively on narrow screens.
- Kleinanzeigen "Passwort vergessen?" and "Erstelle ein Konto" account-page artifacts are now filtered at parse time, excluded from listing API responses, and cleaned from existing local data on startup.
- Mobile listing, watchlist, settings, and swipe screens were audited; the floating language/theme control no longer covers card actions on phones, listing titles get full width before badges, and settings tabs use a denser two-column mobile layout.
- Listings now respect iPhone safe-area spacing, keep the job selector and run action visible outside the collapsible filter panel, and show run errors as toasts.
- Each job run now rechecks unseen listings and records whether they are active, reserved, deleted, or currently unknown.
- Kleinanzeigen scans now read listing dates from `time` metadata and, when a result card omits the date, from the listing detail page before saving the listing. Cards no longer show an "unknown" date chip when the source still does not provide a date.
- Duplicate listing refreshes now backfill missing marketplace fields such as price, location, description, and image; invalid Kleinanzeigen account links are cleaned up; notifications sit above the floating display controls; and watchlist chevrons render as proper icons.
- Listing and review cards now label the marketplace listing date plus ZIP code and place instead of showing an unlabeled location or internal discovery time.
- Mobile swipe-card action buttons no longer scroll under the right edge or clip the Seen button.
- Mobile listing controls now align the collapsed filter chevron and watchlist split-button chevrons cleanly.
- HTML pages now load build-versioned CSS and JavaScript assets to prevent stale mobile browser caches from showing raw translation keys after updates.
- Local Ollama and LM Studio calls now get a longer provider timeout, which avoids failing while local models are still loading.
- Kleinanzeigen paginated scans now keep the HTTP client open while following result pages.
- Kleinanzeigen parsing now uses dedicated result-card selectors instead of the generic HTML fallback.
- Kleinanzeigen jobs now pass text location and radius hints to the source URL and avoid exact ZIP text filtering for radius-based searches.
- Existing duplicate listings are re-evaluated during profile runs so corrected filters can restore previously hidden items.
- Listing page-size controls now honor 50 and 100 item options, with 100 as the default.
- Facebook connector errors now distinguish anonymous access/login blocks from empty result pages.
- Responsive controls, listing cards, pagination, and headers wrap more defensively to avoid UI overlaps.

## [0.3.0] - 2026-06-08

### Added

- First-run setup screen for creating the initial admin password.
- Persistent session secret generation at startup when no secret is supplied.
- Editable URL-parameter rows for existing search URLs.
- Per-job oldest-listing limit, defaulting to 365 days.
- Dashboard source summary and recent-run widgets.
- Docker Hub image documentation for `alexrosbach/marketplacelens`.
- One-line Docker Compose install file using the published image.
- Public/private-use source compliance note for marketplace connectors.

### Changed

- Listing controls are collapsed by default while the listing page itself remains visible.
- Kleinanzeigen fetching follows public pagination links to import more available listings.
- Settings use a tabbed admin/account layout.
- UI shadows, cards, and mobile wrapping were tuned to reduce overlap and improve depth.
- Docker/image version advanced to `0.3.0`.

## [0.2.1] - 2026-06-08

### Added

- Per-user buyer profile fields for AI inquiry generation.
- Account settings for display name, location, contact note, and preferred message signature.
- AI inquiry prompts now include the current user's profile data when configured.

## [0.2.0] - 2026-06-08

### Added

- Guided quick-job wizard with step validation and mobile-friendly flow.
- mobile.de as a dedicated source option and connector.
- Multi-user roles with admin-only global settings and user-owned jobs for normal users.
- Multiple watchlists with default watchlist selection and per-listing watchlist menus.
- Optional AI-generated inquiry texts through OpenAI API, Ollama, or LM Studio.
- Tinder-style listing review mode with swipe-to-seen and double-click watchlisting.
- Version metadata endpoint, Docker build args, and visible app version badge.
- Normal project documentation, screenshots, security policy, license, and issue templates.

### Changed

- README now describes the product as a normal self-hosted application.
- Standard listing views hide `seen` and `hidden` listings unless explicitly filtered.
- The listing browser starts collapsed by default.
- UI styling was refreshed with a clearer MarketPlaceLens visual identity.

### Notes

- Facebook Marketplace and mobile.de can block anonymous server requests. MarketPlaceLens now reports those cases as explicit connector errors instead of silent empty runs.

## [0.1.0] - 2026-06-08

### Added

- Initial self-hosted FastAPI/SQLite marketplace watcher.
- Docker Compose deployment.
- Local web UI with jobs, listings, settings, and notifications.
- Kleinanzeigen, Facebook Marketplace, and generic HTML source handling.
- Telegram and webhook notification support.
