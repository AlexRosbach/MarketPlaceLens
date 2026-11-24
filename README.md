<div align="center">

<img src="app/static/assets/marketplacelens-logo.png" alt="MarketPlaceLens logo" width="96" height="96">

# MarketPlaceLens

**Self-hosted marketplace watcher for Kleinanzeigen and other public marketplace searches.**

[![Version](https://img.shields.io/badge/version-0.4.1-24745a)](https://github.com/AlexRosbach/MarketPlaceLens)
[![License: MIT](https://img.shields.io/badge/license-MIT-22c55e)](LICENSE)
[![Docker Hub](https://img.shields.io/docker/pulls/alexrosbach/marketplacelens?color=0ea5e9)](https://hub.docker.com/r/alexrosbach/marketplacelens)

MarketPlaceLens runs recurring marketplace search jobs, collects matching listings, and gives you a local dashboard to review, hide, save, contact, and watch interesting items.

[Documentation](docs/documentation.md) · [Wiki draft](docs/wiki/Home.md) · [Changelog](CHANGELOG.md) · [Docker Hub](https://hub.docker.com/r/alexrosbach/marketplacelens)

</div>

## Why It Is Different

Most marketplace providers are optimized for browsing inside one platform. MarketPlaceLens is built for focused buying research across saved searches:

- More granular search control: combine provider search URLs with local include, exclude, required keyword, category, price, age, location, radius, status, and watchlist filters.
- Better matching workflow: normalize listings into one local review queue, hide noise, keep contacted items, and save promising items to watchlists instead of repeating the same provider searches.
- Built-in AI assistance: turn natural-language buying intent into quick-job drafts, generate buyer messages, and add listing assessments that highlight fit, price plausibility, missing details, and visible risk signs.
- Self-hosted ownership: data, settings, cookies, API keys, watchlists, and review history stay on the operator's server.
- No lock-in to one marketplace UI: supported sources can evolve independently while the review, notification, and AI workflow stays the same.

## Support and Legal

MarketPlaceLens is free and open source. If it helps you or saves you time, you can support ongoing development voluntarily. Support does not buy support priority, features, or access.

<a href="https://www.buymeacoffee.com/alexrosbaci" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/v2/default-blue.png" alt="Buy Me a Coffee" height="42"></a>

MarketPlaceLens is an app by Alex Rosbach. Legal notice and project contact information are maintained on [lanlens.org/privacy.html](https://lanlens.org/privacy.html).

## Status

| Source | Status | Notes |
|---|---|---|
| Kleinanzeigen | Stable | Main supported connector for public search/category URLs |
| Facebook Marketplace | **In testing** | Often returns login, consent, location, or JavaScript-only pages |
| mobile.de | **In testing** | Public HTML support is limited; official API access is separate |
| Marktplaats.nl | **In testing** | Public Dutch search result URLs are supported; platform access limits still apply |
| Generic HTML | Experimental | Basic parser for simple result pages |

## Screenshots

Demo data, no real listings.

| Dashboard | Jobs |
|---|---|
| ![Dashboard](docs/screenshots/marketplacelens-dashboard.png) | ![Jobs](docs/screenshots/marketplacelens-jobs.png) |

| Listings | Mobile review |
|---|---|
| ![Listings](docs/screenshots/marketplacelens-listings.png) | ![Mobile review](docs/screenshots/marketplacelens-mobile-review.png) |

## Features

- Recurring marketplace jobs with price, keyword, age, listing type, ZIP/place, and radius filters
- Listing browser, swipe review, watchlists, seen/hidden/contacted states
- Marking a listing as contacted automatically saves it to the user's default watchlist
- Clickable ZIP/place map action for listing locations
- Optional Telegram and webhook notifications
- Optional AI buyer text, quick-job drafts, and listing assessments
- Multi-user login with admin settings and user-owned jobs
- German/English UI, dark/light mode, and mobile layouts
- Public marketplace and image fetches validate and pin public destination addresses; configure network egress restrictions as defense in depth.

## Quick Start

```bash
mkdir -p marketplacelens && cd marketplacelens
curl -fsSL https://raw.githubusercontent.com/AlexRosbach/MarketPlaceLens/main/docker-compose.install.yml -o docker-compose.yml
docker compose up -d
```

Open:

```text
http://127.0.0.1:8091
```

On first start, MarketPlaceLens asks you to create the first admin account. For trusted LAN access, explicitly set `MARKETPLACELENS_BIND_ADDRESS=0.0.0.0`. Set `MARKETPLACELENS_COOKIE_SECURE=true` behind an HTTPS reverse proxy. Existing sessions require a fresh sign-in after upgrading.

To reset an admin password from the container CLI:

```bash
docker exec -it marketplacelens reset-password
docker exec -it marketplacelens reset-password --username admin
```

## Docker Images

```bash
docker pull alexrosbach/marketplacelens:0.4.1
docker pull alexrosbach/marketplacelens:latest
docker pull alexrosbach/marketplacelens:dev
```

- `0.4.1` is the current release
- `latest` tracks the latest stable release
- `dev` tracks the current development build

## Documentation

- [Full documentation](docs/documentation.md)
- [Wiki draft](docs/wiki/Home.md)
- [Installation](docs/wiki/Installation.md)
- [Jobs and sources](docs/wiki/Jobs-and-Sources.md)
- [Listings and watchlists](docs/wiki/Listings-and-Watchlists.md)
- [AI and automation](docs/wiki/AI-and-Automation.md)
- [Troubleshooting](docs/wiki/Troubleshooting.md)

## Responsible Use

MarketPlaceLens is intended for private self-hosted use with marketplace URLs you are allowed to access. It does not bypass logins, CAPTCHA, bot protection, private APIs, rate limits, or platform access controls.

## License

MIT License, see [LICENSE](LICENSE).


### New-price comparison (experimental)
Open **New-price comparison & price history** on a listing or review card. Configure `MARKETPLACELENS_EBAY_CLIENT_ID` and `MARKETPLACELENS_EBAY_CLIENT_SECRET` in your local environment for the official eBay Browse API (production access required). Results are possible matches, not guaranteed identical products; compare condition, model and shipping. Without credentials the UI shows search links only. Amazon Creators API support is disabled by default. Only enable `MARKETPLACELENS_AMAZON_APPROVED=true` after obtaining explicit approval for this comparison and price-alert-enabled application and ensuring the applicable display/affiliate requirements are met. Configure `MARKETPLACELENS_AMAZON_CLIENT_ID`, `MARKETPLACELENS_AMAZON_CLIENT_SECRET`, `MARKETPLACELENS_AMAZON_PARTNER_TAG` and the credential version (default `3.2`). The API returns featured offers, not a comprehensive lowest-price guarantee; show available new/used offers with links and retrieval time. Amazon data is not stored in listing price history or used in alerts. No scraping or invented prices. Both provider responses are cached in memory for 15 minutes. See https://partnernet.amazon.de/help/operating/policies and https://partnernet.amazon.de/creatorsapi/docs/en-us/introduction.


### Performance and reliability
Search results are cached for two minutes per user/source/query/session, images for ten minutes within a 32 MiB memory budget. Availability checks are bounded and only revisit stale, unseen listings. Price history and optional target-price notifications are based on marketplace listings, not Amazon prices. Notification delivery is asynchronous and retried up to five times (at-least-once; duplicate delivery is possible after an ambiguous network failure). `GET /api/connector-health` exposes aggregate run metrics to administrators.


### Duplicate candidates and maintenance
The price details panel also lists possible cross-source duplicates with a conservative title/model/price/location match. Results are suggestions only and never delete or merge listings. Radius filters outside supported sources are marked unverified and hidden rather than claiming a verified distance. Full geocoding remains a follow-up.

Use `docker exec marketplacelens python -m app.cli.housekeeping backup /data/backups/backup.db` for a consistent SQLite backup (new filename required). Use `docker exec marketplacelens python -m app.cli.housekeeping cleanup --days 180` to preview old, unprotected rows; add `--apply` only after a verified backup. Schedule these commands externally if required. Keep backups private and use unique filenames. Automatic retention/rotation is not enabled.


### Optional local MCP companion
Install `requirements-mcp.txt` into a separate Python environment. Run `python -m app.mcp_companion` via a local MCP client using stdio, setting `MARKETPLACELENS_DB_PATH` to the local SQLite database and `MARKETPLACELENS_MCP_USER_ID` to an explicitly chosen enabled user's numeric ID. The connection is read-only and every tool is scoped to that user, including when the chosen user is an admin. No remote HTTP transport or remote authentication is provided; protect the database and local process environment with OS permissions. Tools: list jobs, search listings/watchlisted items and read price history. Never expose the database mount publicly.

Provider comparisons are loaded on demand and limited to 30 uncached queries per hour per process. A price difference before shipping is shown only for a high-overlap candidate, not a verified product identity. Failed polling jobs back off up to six hours. Listing, review and watchlist data are loaded when their respective view is opened.
