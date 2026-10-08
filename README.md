# Discord-AutoReact

**Clean, rate-limit conscious self-bot for automated reactions.**

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Discord.py-self](https://img.shields.io/badge/discord.py--self-2.x-7289da.svg)](https://github.com/dolfies/discord.py-self)

> Bulk react to messages in any channel or DM with configurable filters, emoji cycling, and **very strict** rate limiting so your account stays healthy.

---

### ⚠️ Important Disclaimer

This is a **self-bot**.  
Self-bots are against [Discord's Terms of Service](https://discord.com/terms).  
Using this can get your account disabled.  

I built this for personal archival / convenience use and as a learning project.  
**You are solely responsible for how you use it.**  
I am not responsible for any account actions Discord takes.

---

## Features

- React to the last **N** messages, messages containing keywords, or everything in a channel
- Multiple emojis with **cycle** or **random** mode
- User whitelist / blacklist
- Skip messages you already reacted to
- Only react to completely unreacted messages (optional)
- Message age filter (avoid reacting to brand-new messages)
- **Smart rate limiter**
  - Random delay between reactions
  - Configurable batch size + cooldown
  - Automatic handling of 429s
- Beautiful terminal UI with progress bar and summary
- Dry-run mode so you can test safely
- Single clean config file

---

## Screenshots

```
╭────────────────── Discord-AutoReact v1.2.1 ──────────────────╮
│ Logged in as  YourName#0001                                  │
│ Target        #general                                       │
│ Mode          last_n                                         │
│ Dry-run       False                                          │
╰──────────────────────────────────────────────────────────────╯

Found 47 messages to react to.

Reacting… ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 47/47 0:01:52

          Run Summary
┏━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━┓
┃ Metric               ┃ Count ┃
┡━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━┩
│ Messages scanned     │   50  │
│ Successfully reacted │   47  │
│ Failed               │    0  │
│ Skipped by filters   │    3  │
└──────────────────────┴───────┘
```

---

## Installation

```bash
git clone https://github.com/YOUR_USERNAME/Discord-AutoReact.git
cd Discord-AutoReact

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

pip install -r requirements.txt
```

---

## Setup

1. Copy the example config:

```bash
cp config.example.yaml config.yaml
```

2. Edit `config.yaml` and put your **user token** and the **channel ID**.

### How to get your token

1. Open Discord in your browser
2. Press `Ctrl + Shift + I` (DevTools)
3. Go to the **Network** tab
4. Send a message or switch channels
5. Click any request → Headers → look for `authorization`

> Never share your token. Never commit `config.yaml`.

### How to get a channel ID

Enable Developer Mode in Discord settings → right-click the channel → Copy Channel ID.

---

## Usage

```bash
python autoreact.py
```

That’s it. The bot will log in, fetch messages according to your config, and start reacting with the configured delays.

### Recommended first run

Set these in `config.yaml`:

```yaml
dry_run: true
max_messages: 10
```

Run it once to confirm everything looks correct, then turn dry-run off.

---

## Configuration Guide

| Key | Description | Default |
|-----|-------------|---------|
| `token` | Your Discord user token | – |
| `channel_id` | Target channel / DM | – |
| `emojis` | List of emojis (unicode or `<:name:id>`) | `["🔥"]` |
| `emoji_mode` | `cycle` or `random` | `cycle` |
| `mode` | `last_n`, `keyword`, or `all` | `last_n` |
| `max_messages` | How many messages to consider | `50` |
| `keywords` | Only used in keyword mode | `[]` |
| `min_delay` / `max_delay` | Delay range between reactions | `1.4` – `2.8` |
| `batch_size` | Reactions before a longer pause | `12` |
| `batch_cooldown` | Seconds to sleep after a batch | `18` |
| `dry_run` | Simulate only | `false` |
| `skip_already_reacted` | Don’t re-react | `true` |

The default rate-limit values are intentionally conservative.  
Going much lower than ~1.3s average is asking for trouble.

---

## Rate Limiting Philosophy

Discord’s reaction endpoints are not the most generous.  
This tool prioritises **account safety** over speed:

- Randomised delay on every reaction
- Extra jitter so the pattern doesn’t look robotic
- Forced cooldown every N reactions
- Proper handling of actual 429 responses

You can tune it, but the defaults have been tested on normal accounts without issues.

---

## Project Structure

```
Discord-AutoReact/
├── autoreact.py          # Main script
├── config.example.yaml   # Example configuration
├── requirements.txt
├── LICENSE
└── README.md
```

---

## Contributing

Found a bug or have a clean improvement?  
Open an issue or PR. Keep it simple and well-tested.

---

## License

MIT – see [LICENSE](LICENSE).

---

**Stay safe and don’t be stupid with your token.**
