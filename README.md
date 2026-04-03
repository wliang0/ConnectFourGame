# Connect Four

Two-player Connect Four over the internet. Each player runs a local binary — no browser, no accounts. A lightweight relay server handles matchmaking and move passing.

## How it works

Both players connect outward to a relay server hosted on Railway. The server pairs the first two connections and relays moves between them. All game logic runs locally on each client.

```
Player 1 ──► Railway relay server ◄── Player 2
```

## Project structure

```
client.py     # Game client — build this into a binary for distribution
server.py     # Relay server — deploy this to Railway
game.py       # ConnectFour game logic (shared by client)
Procfile      # Railway deployment config
pyproject.toml
```

## Setup

Requires Python 3.13+ and [Poetry](https://python-poetry.org).

```bash
poetry install
```

## Deploying the server (Railway)

1. Install the [Railway CLI](https://docs.railway.app/develop/cli)
   ```bash
   brew install railway
   ```

2. Log in and deploy
   ```bash
   railway login
   railway init
   railway up
   ```

3. In the Railway dashboard, go to your project → **Settings → Networking → Add TCP Proxy**.
   Set the target port to `5000`. Railway will give you a hostname and port, e.g.:
   ```
   caboose.proxy.rlwy.net:30828
   ```

4. Update the constants at the top of `client.py`:
   ```python
   HOST = "caboose.proxy.rlwy.net"
   PORT = 30828
   ```

The server runs continuously and supports multiple simultaneous games. Players are paired in the order they connect.

## Building the client binary

```bash
poetry run pyinstaller --onefile client.py
```

The binary is output to `dist/client`. This is the file you send to other players — they don't need Python installed.

> **Note:** The binary is platform-specific and will only run on Apple Silicon Macs. Rebuild on the target platform if needed.

## Playing

1. Make sure the server is deployed and `HOST`/`PORT` in `client.py` match your Railway TCP proxy.
2. Build the binary and distribute `dist/client` to the other player.
3. **You run the binary first** — you'll see:
   ```
   Connecting to caboose.proxy.rlwy.net:30828...
   Connected! Waiting for your opponent to join...
   ```
4. **Opponent runs their binary** — the game starts automatically.
5. Tokens (X/O) and who goes first are assigned randomly by the server.

### macOS security warning

On first launch, macOS may block the binary with a message saying it could not verify it is free of malware. This is expected for unsigned binaries. To allow it:

1. Open **System Settings → Privacy & Security**
2. Scroll down to the blocked app and click **Open Anyway**
3. Click **Open** on the confirmation dialog

This only needs to be done once.

## Re-deploying after changes

If you update `server.py`, redeploy with:
```bash
railway up
```

If you update `client.py` (e.g. after a new Railway TCP address), rebuild the binary and redistribute it:
```bash
poetry run pyinstaller --onefile client.py
```
