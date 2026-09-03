# Python Tool Panel

Authenticated web panel for running and monitoring benign Python utilities you control.

It is deliberately not a C2, reverse-shell, covert persistence, credential collection, or traffic-flooding platform.

## Password

Do not store `XBOXMOP` in source code. Generate an Argon2 hash:

`python -c "from argon2 import PasswordHasher; print(PasswordHasher().hash('XBOXMOP'))"`

Put the generated hash into `.env` as `PANEL_PASSWORD_HASH`.

## Deploy

1. Copy `.env.example` to `.env`.
2. Set `SESSION_SECRET` to a long random value.
3. Set `PANEL_PASSWORD_HASH`.
4. Run `docker compose up -d --build`.
5. Put HTTPS in front with your hosting provider's reverse proxy.

Docker Compose uses `restart: unless-stopped`, so the panel returns after container or host restart when Docker is enabled at boot.

## Git deployment

Commit the project to a private Git repository. Never commit `.env`, passwords, tokens, or private keys. Deploy on a host that supports Docker Compose.

## Add tools

Drop `.py` files into `tools/`. The dashboard discovers them automatically. Each tool is isolated in its own process and stdout/stderr is captured in `logs/`.

## Error visibility

Open a tool page to see its live log output. Failed exits remain visible as process status and captured output.
