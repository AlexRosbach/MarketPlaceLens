# Installation

## Requirements

- Docker 20.10+
- Docker Compose v2

## Docker Compose

```bash
mkdir -p marketplacelens && cd marketplacelens
curl -fsSL https://raw.githubusercontent.com/AlexRosbach/MarketPlaceLens/main/docker-compose.install.yml -o docker-compose.yml
docker compose up -d
```

Open:

```text
http://<your-host-ip>:8091
```

Complete the first-run setup screen and create the initial admin password.

## Environment Variables

| Variable | Default | Purpose |
|---|---|---|
| `MARKETPLACELENS_DB_PATH` | `/data/marketplacelens.db` | SQLite path |
| `MARKETPLACELENS_POLL_ENABLED` | `true` | Enables background polling |
| `MARKETPLACELENS_MIN_POLL_MINUTES` | `30` | Minimum job interval |
| `MARKETPLACELENS_DEFAULT_POLL_MINUTES` | `60` | Default job interval |
| `MARKETPLACELENS_ADMIN_USERNAME` | `admin` | First admin username |
| `TELEGRAM_BOT_TOKEN` | empty | Optional Telegram bot |
| `TELEGRAM_CHAT_ID` | empty | Optional Telegram target |
| `MARKETPLACELENS_WEBHOOK_URL` | empty | Optional webhook target |

## Updating

```bash
docker compose pull
docker compose up -d
```

Schema migrations run automatically during startup.

## Reset Admin Password

If you lose admin access, reset an admin password directly inside the container:

```bash
docker exec -it marketplacelens reset-password
docker exec marketplacelens reset-password --username admin --password "MyNewPass123"
```

The command updates the local SQLite database, enables the selected admin account, and does not require the web app to be reachable.
