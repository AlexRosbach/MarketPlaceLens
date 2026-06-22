# Jobs and Sources

A job is a saved marketplace search. It stores source, URL, filters, polling interval, and notification choices.

## Quick Job

Use Quick job when starting with a natural search idea. The wizard guides through source, search terms, price, location, keyword filters, and delivery options.

## Manual Job

Use the manual editor for precise marketplace URLs. It supports provider cards, URL-parameter previews, Kleinanzeigen listing types, map-assisted location/radius criteria, and local keyword rules.

## Source Status

| Source | Status | Notes |
|---|---|---|
| Kleinanzeigen | Stable primary path | Supports public search/category URLs, listing type, price, keyword, age, location, and radius filters. |
| Facebook Marketplace | **In testing** | Facebook can return login, consent, location, or JavaScript shell pages to server requests. Optional Cookie headers may help when used privately. |
| mobile.de | **In testing** | Uses public search pages when embedded result data is visible to the server. Official API access is separate. |
| Marktplaats.nl | **In testing** | Uses public Marktplaats search result pages and maps listing cards into the normal review/watchlist workflow. |
| Generic HTML | Experimental | Basic parsing for simple link-card pages. |

## Location Handling

Text location examples:

```text
10115 · +50 km
Hamburg · +30 km
```

Map mode stores the clicked coordinate and reverse-geocodes it into a ZIP/place so Kleinanzeigen can receive a usable `locationStr` and `radius`.

## Platform Boundaries

MarketPlaceLens does not bypass logins, CAPTCHA, bot protection, blocked sessions, private APIs, or platform access controls.
