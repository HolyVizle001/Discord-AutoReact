# Discord-AutoReact

**Clean, rate-limit conscious self-bot for automated reactions.**

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Discord.py-self](https://img.shields.io/badge/discord.py--self-2.x-7289da.svg)](https://github.com/dolfies/discord.py-self)

> Bulk react to messages in any channel or DM with configurable filters, emoji cycling, and **very strict** rate limiting so your account stays healthy.

---

### Important Disclaimer

This is a **self-bot**.  
Self-bots are against [Discord's Terms of Service](https://discord.com/terms).  
Using this can get your account disabled.  

I built this for personal showcase / convenience use and as a learning project.  
**You are responsible for how you use it.**  
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
- Beautiful terminal UI with progress bar and summary
- Dry-run mode so you can test safely
- Single clean config file

---

## Installation

```bash
git clone https://github.com/HolyVizle001/Discord-AutoReact.git
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
2. Press `Ctrl + Shift + I` or `F12` (DevTools)
3. Go to the **Application** tab
4. Scroll down to "token"
5. Copy the long string there

> Never share your token. Never commit `config.yaml`.

## Usage

```bash
python autoreact.py
```

### Recommended first run

Set these in `config.yaml`:

```yaml
dry_run: true
max_messages: 10
```

Run it once to confirm everything looks correct, then turn dry-run off.

---

## Config Guide (made using Ai)

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

## License

MIT – see [LICENSE](LICENSE).

---

Last note: this took fucking ages
