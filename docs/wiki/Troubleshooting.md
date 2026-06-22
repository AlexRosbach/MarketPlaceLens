# Troubleshooting

## A Job Returns No Listings

Check recent run logs first. The source may have returned an empty page, a login page, a consent page, or a JavaScript shell.

## Facebook Marketplace Fails

Facebook Marketplace is **in testing**.

Try:

1. Use a normal Marketplace search or category URL.
2. Open the same URL in your browser.
3. If it only works while logged in, add a browser Cookie header in Settings.
4. Re-run the job.

Cookies can expire or be revoked. MarketPlaceLens stores the Cookie header locally and sends it only to `facebook.com`.

## mobile.de Fails

mobile.de is **in testing**. Use a concrete public search result URL. If mobile.de does not expose embedded vehicle result data to the server, the job records a connector error.

## Marktplaats.nl Fails

Marktplaats.nl is **in testing**. Use a concrete public search result URL such as `https://www.marktplaats.nl/q/fiets/`. If Marktplaats does not expose public listing cards to the server or blocks the request, the job records a connector error.

## AI Fails

Use **Test AI** in Settings. For Ollama or LM Studio, the first request may take longer while a local model loads.

## Database Locked Errors

Recent builds use a SQLite busy timeout and avoid holding job-side write transactions while waiting on external providers. If lock errors reappear, check whether a long-running job, AI provider, or notification target is hanging.

## Browser Shows Stale UI

MarketPlaceLens appends the build code to CSS and JavaScript URLs. If the UI still looks stale, do a hard reload.
