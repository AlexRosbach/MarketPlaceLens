# Security Policy

MarketPlaceLens is intended for small self-hosted deployments. Keep it behind a trusted network or reverse proxy, use a strong session secret, and restrict outbound network access.

## Reporting a Vulnerability

Use the repository's [Security tab](https://github.com/AlexRosbach/MarketPlaceLens/security) and select **Report a vulnerability** when private vulnerability reporting is available. If it is unavailable, open a public issue requesting a private contact channel **without including technical details, credentials, or data**. The maintainer must enable private vulnerability reporting in repository settings.

## Operational Notes

- The first-run setup requires a non-default password; existing installations with the legacy default password must use the documented container password reset command.
- Set `MARKETPLACELENS_COOKIE_SECURE=true` for HTTPS deployments.
- Compose binds to loopback by default. Explicitly configure the bind address for trusted LAN access or use an authenticated TLS reverse proxy.
- Marketplace and image fetches reject non-public destinations; also enforce network-level egress restrictions in sensitive environments.
- Administrator-configured AI and webhook endpoints may intentionally use private networks. Configure only trusted endpoints and limit administrative access.
- Treat Telegram tokens, webhook URLs, Facebook session cookies, AI API keys, and database backups as secrets.
- The app does not intentionally automate logins, bypass CAPTCHA, rotate proxies, or send messages to sellers.
