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
- Defensive URL validation prevents saved jobs and image proxy requests from targeting local or private network hosts

## Quick Start

```bash
mkdir -p marketplacelens && cd marketplacelens
curl -fsSL https://raw.githubusercontent.com/AlexRosbach/MarketPlaceLens/main/docker-compose.install.yml -o docker-compose.yml
docker compose up -d
```

Open:

```text
http://<your-host-ip>:8091
```

On first start, MarketPlaceLens asks you to create the first admin account.

## Deployment

### Deploy to Diploi

[![Launch with Diploi](https://diploi.com/launch-big.svg)](https://diploi.com/launch/AlexRosbach/MarketPlaceLens)

1. **Launch the project**

   Click the launch button above to create a new Diploi deployment.

2. **Add environment variables**

   In Diploi, open your deployment page and go to **Options > FastAPI > Environment**. Add any required environment variables.

3. **Preview the deployment**

   Open the provided preview URL from your Diploi deployment page.

For more information, please visit [diploi.com](https://diploi.com/).

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
