# MarketPlaceLens Documentation

MarketPlaceLens is a self-hosted marketplace watcher. It turns user-supplied search URLs into recurring jobs, stores normalized listings locally, and gives users a focused workflow for reviewing, saving, hiding, contacting, and assessing items.

## What MarketPlaceLens Does Better

Marketplace-native searches are useful for casual browsing, but they usually stop at one provider's result page and a handful of fixed filters. MarketPlaceLens adds a buyer-focused layer on top:

- It combines provider-side searches with more granular local rules for include, exclude, and required keywords, categories, price limits, listing age, location/radius, status, watchlists, and ownership.
- It keeps a persistent review workflow so users can hide bad matches, save promising items, track contacted listings, and avoid re-reviewing the same noise after every search.
- It can use built-in AI to translate a plain-language buying intent into a job draft, assess whether a listing fits the search, flag missing or risky details, and draft a buyer message for manual sending.
- It keeps marketplace data and decisions in a self-hosted database instead of scattering them across browser tabs, provider accounts, and chat notes.
- It gives admins one place for notifications, multi-user ownership, run logs, AI provider settings, and source-specific troubleshooting.

## 1. Installation

Requirements:

- Docker 20.10+
- Docker Compose v2

Install with the published release image:

```bash
mkdir -p marketplacelens && cd marketplacelens
curl -fsSL https://raw.githubusercontent.com/AlexRosbach/MarketPlaceLens/main/docker-compose.install.yml -o docker-compose.yml
docker compose up -d
```

Open:

```text
http://<your-host-ip>:8091
```

On first start, MarketPlaceLens displays a platform-rules notice and then creates the first admin password. No normal deployment ships with a default password.

For local development:

```bash
cp .env.example .env
docker compose up -d --build
```

### Resetting Admin Access

If an admin password is lost, use the container CLI to reset it directly in SQLite:

```bash
docker exec -it marketplacelens reset-password
docker exec marketplacelens reset-password --username admin --password "MyNewPass123"
```

The command enables the selected admin user and updates its password hash without depending on a running API session.

## 2. Core Concepts

### Jobs

A job is a saved search. It stores:

- source type
- source URL
- poll interval
- listing type options
- local filters
- notification choices
- owning user

Admins can manage all jobs. Normal users can create, run, edit, and delete their own jobs.

### Listings

A listing is a normalized result imported from a job run. Listings carry title, price, location, category, marketplace URL, image URL, source status, user status, watchlist state, contacted state, and optional AI assessment text.

### Watchlists

Every user can choose a default watchlist. A normal watch action saves the listing to that default list. Marking a listing as contacted also adds it to the default watchlist, because contacted items should remain easy to find later.

### Review Mode

Review mode shows one listing at a time with image, price, location, source, AI assessment, and actions. Users can open the source listing, save to watchlist, mark contacted, mark seen, or generate AI text.

## 3. Source Status

| Source | Status | Notes |
|---|---|---|
| Kleinanzeigen | Stable primary path | Best-supported connector. Supports public search/category URLs, price, age, keyword, location/radius, and listing type handling. |
| Facebook Marketplace | **In testing** | Works only when Facebook returns listing links to the server. Facebook frequently returns login, consent, location, or JavaScript shell pages. Optional Cookie headers are stored locally and sent only to `facebook.com`. |
| mobile.de | **In testing** | Reads public search pages when embedded vehicle result data is available. The official mobile.de Search API needs separate Basic Auth access. |
| Generic HTML | Experimental | Basic fallback for simple link-card result pages. It is not a universal parser. |

MarketPlaceLens does not bypass login walls, CAPTCHA, bot protection, private APIs, blocked sessions, or platform access controls.

Saved job URLs and proxied listing images are rejected when they target localhost, `.local`, private IP, loopback, link-local, multicast, or reserved network ranges. This keeps marketplace fetches pointed at public sources rather than the host's own LAN services.

## 4. Creating Jobs

Use **Quick job** when starting from a simple idea. The wizard guides through:

1. source
2. search term
3. category
4. price and location limits
5. keyword rules
6. polling and notification choices

Use **New job** when you already have a concrete marketplace URL. The manual editor includes provider cards, URL parameter previews, Kleinanzeigen listing-type controls, text or map-based location criteria, keyword rules, and delivery settings.

For Kleinanzeigen, a text location such as `10115 · +50 km` is translated into URL parameters. If the map mode is used, MarketPlaceLens reverse-geocodes the clicked point into a ZIP/place first and then uses that resolved location for Kleinanzeigen.

## 5. Listing Workflow

Listings can be:

- filtered by status, job, watchlist, text, price, and sort order
- viewed in list or tile mode
- opened on the original marketplace
- marked seen or hidden
- saved to a watchlist
- marked contacted
- shown on a map by ZIP/place
- enriched with AI assessment text

Listing and swipe cards use product-focused motion inspired by Kramlet: cards enter with a short stagger, lift subtly on hover, images zoom within the card frame, and the swipe card follows the pointer while dragging before it settles back or advances.

The default active listing view excludes seen and hidden items unless the user explicitly changes filters.

## 6. Notifications

Notification settings are split into Telegram and webhook configuration cards. Each job decides whether it sends Telegram and/or webhook notifications.

Global rate limiting avoids aggressive polling. Per-job intervals are constrained by the configured minimum interval.

## 7. AI Features

AI is disabled by default. Admins can enable it and configure an OpenAI-compatible provider:

- OpenAI API
- Ollama
- LM Studio

AI can generate:

- buyer inquiry text for manual copying
- structured quick-job drafts
- listing assessments

Listing assessments focus on fit to the saved search, practical value, resale potential, visible risk signs, missing details, and whether the price looks plausible against a typical used-market range.

AI requests may send listing title, price, description, source metadata, match data, and user-provided buyer profile fields to the configured provider.

## 8. Users and Roles

Admin users can:

- manage all jobs and listings
- manage users and roles
- configure notifications, AI, Facebook settings, watchlists, and run logs
- clear individual or all run errors

Normal users can:

- manage their own jobs
- review listings from their own jobs
- use watchlists
- choose a default watchlist
- edit account and buyer profile fields
- change their password

## 9. Settings

Settings are grouped into:

- Notifications
- Facebook
- AI
- Watchlists
- Users
- Recent runs
- Account

Facebook settings include a setup guide and optional Cookie header field. The Cookie value is masked in UI/API responses and is intended only for private self-hosted use when the URL works in the admin's own browser session.

## 10. Updating

Pull the latest release image:

```bash
docker compose pull
docker compose up -d
```

For checkout-based installs:

```bash
git pull
docker compose up -d --build
```

SQLite schema migrations run during startup.

## 11. Troubleshooting

### Source returns no listings

Check the run logs first. Some platforms return empty HTML, login pages, consent pages, or JavaScript shells to server requests.

### Facebook fails

Facebook Marketplace is **in testing**. If the URL works only in your browser, add a browser Cookie header in Settings. Cookies expire, can be revoked, and may still not make the server response usable.

### mobile.de fails

mobile.de is **in testing**. Use a concrete public search result URL. If mobile.de returns no embedded result data or blocks the request, MarketPlaceLens records a connector error.

### AI request fails

Use **Test AI** in Settings. Local Ollama and LM Studio models can take longer on the first request while the model loads.

### Browser shows stale UI

The app appends the build code to local CSS and JavaScript URLs. If a browser still shows old controls, do a hard reload.

## 12. Version Metadata

`GET /api/version` returns:

- `version`
- `build_code`
- `commit`
- `branch`
- `created`

The build code also appears in the sidebar badge.

## 13. Compliance Boundaries

MarketPlaceLens is intended for private self-hosted use with URLs the operator is allowed to access.

- No login automation
- No CAPTCHA bypass
- No proxy rotation
- No aggressive polling
- No automatic seller messaging
- No public redistribution of marketplace data
- No local thumbnail mirroring; images are proxied on demand

The maintainer does not guarantee third-party platform compatibility and does not take responsibility for misuse, blocked accounts, denied access, data processing, or third-party policy violations.
