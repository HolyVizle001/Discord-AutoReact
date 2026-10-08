#!/usr/bin/env python3
"""
Discord-AutoReact
A clean, rate-limit conscious self-bot for automated reactions.

This tool is provided for educational and personal use only.
Self-bots violate Discord's Terms of Service. Use at your own risk.
"""

from __future__ import annotations

import asyncio
import logging
import random
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Set

import discord
import yaml
from rich.console import Console
from rich.logging import RichHandler
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
)
from rich.panel import Panel
from rich.table import Table

# ---------------------------------------------------------------------------
# Constants & Console
# ---------------------------------------------------------------------------

VERSION = "1.2.1"
CONSOLE = Console()
LOG = logging.getLogger("autoreact")


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

@dataclass
class Config:
    token: str
    channel_id: int
    user_whitelist: List[int] = field(default_factory=list)
    user_blacklist: List[int] = field(default_factory=list)
    emojis: List[str] = field(default_factory=lambda: ["🔥"])
    emoji_mode: str = "cycle"  # cycle | random
    mode: str = "last_n"       # last_n | keyword | all
    max_messages: int = 50
    keywords: List[str] = field(default_factory=list)
    min_age_seconds: int = 5
    min_delay: float = 1.4
    max_delay: float = 2.8
    jitter: float = 0.4
    batch_size: int = 12
    batch_cooldown: float = 18.0
    dry_run: bool = False
    skip_already_reacted: bool = True
    only_unreacted: bool = False
    log_level: str = "INFO"

    @classmethod
    def from_yaml(cls, path: Path) -> "Config":
        if not path.exists():
            CONSOLE.print(
                f"[bold red]Config file not found:[/] {path}\n"
                f"Copy [cyan]config.example.yaml[/] → [cyan]config.yaml[/] and edit it."
            )
            sys.exit(1)

        with path.open("r", encoding="utf-8") as f:
            raw = yaml.safe_load(f) or {}

        # Basic validation
        if not raw.get("token") or raw["token"] == "YOUR_TOKEN_HERE":
            CONSOLE.print("[bold red]Error:[/] Please set a valid token in config.yaml")
            sys.exit(1)

        if not raw.get("channel_id"):
            CONSOLE.print("[bold red]Error:[/] channel_id is required")
            sys.exit(1)

        return cls(
            token=str(raw["token"]).strip(),
            channel_id=int(raw["channel_id"]),
            user_whitelist=[int(x) for x in raw.get("user_whitelist", [])],
            user_blacklist=[int(x) for x in raw.get("user_blacklist", [])],
            emojis=raw.get("emojis") or ["🔥"],
            emoji_mode=str(raw.get("emoji_mode", "cycle")).lower(),
            mode=str(raw.get("mode", "last_n")).lower(),
            max_messages=int(raw.get("max_messages", 50)),
            keywords=[str(k).lower() for k in raw.get("keywords", [])],
            min_age_seconds=int(raw.get("min_age_seconds", 5)),
            min_delay=float(raw.get("min_delay", 1.4)),
            max_delay=float(raw.get("max_delay", 2.8)),
            jitter=float(raw.get("jitter", 0.4)),
            batch_size=int(raw.get("batch_size", 12)),
            batch_cooldown=float(raw.get("batch_cooldown", 18.0)),
            dry_run=bool(raw.get("dry_run", False)),
            skip_already_reacted=bool(raw.get("skip_already_reacted", True)),
            only_unreacted=bool(raw.get("only_unreacted", False)),
            log_level=str(raw.get("log_level", "INFO")).upper(),
        )


# ---------------------------------------------------------------------------
# Rate Limiter
# ---------------------------------------------------------------------------

class SmartRateLimiter:
    """
    Conservative rate limiter that respects Discord's reaction limits
    while still feeling responsive.
    """

    def __init__(self, cfg: Config):
        self.min_delay = cfg.min_delay
        self.max_delay = cfg.max_delay
        self.jitter = cfg.jitter
        self.batch_size = cfg.batch_size
        self.batch_cooldown = cfg.batch_cooldown
        self._count = 0
        self._last_reaction = 0.0

    async def wait(self) -> None:
        now = time.monotonic()
        elapsed = now - self._last_reaction

        # Base random delay
        base = random.uniform(self.min_delay, self.max_delay)
        extra = random.uniform(0, self.jitter)
        target = base + extra

        if elapsed < target:
            await asyncio.sleep(target - elapsed)

        self._count += 1
        self._last_reaction = time.monotonic()

        # Longer pause every batch
        if self._count % self.batch_size == 0:
            cooldown = self.batch_cooldown + random.uniform(0, 4)
            LOG.info(f"Batch limit reached ({self.batch_size}). Cooling down {cooldown:.1f}s…")
            await asyncio.sleep(cooldown)


# ---------------------------------------------------------------------------
# Core Logic
# ---------------------------------------------------------------------------

class AutoReact:
    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.limiter = SmartRateLimiter(cfg)
        self.emoji_index = 0
        self.stats = {
            "scanned": 0,
            "reacted": 0,
            "skipped": 0,
            "failed": 0,
        }

        intents = discord.Intents.default()
        intents.message_content = True
        intents.messages = True
        intents.reactions = True

        self.client = discord.Client(intents=intents)

        @self.client.event
        async def on_ready():
            await self._run()

    def _next_emoji(self) -> str:
        if self.cfg.emoji_mode == "random":
            return random.choice(self.cfg.emojis)
        emoji = self.cfg.emojis[self.emoji_index % len(self.cfg.emojis)]
        self.emoji_index += 1
        return emoji

    def _should_react(self, message: discord.Message) -> bool:
        # Age filter
        age = (discord.utils.utcnow() - message.created_at).total_seconds()
        if age < self.cfg.min_age_seconds:
            return False

        # User filters
        author_id = message.author.id
        if self.cfg.user_whitelist and author_id not in self.cfg.user_whitelist:
            return False
        if author_id in self.cfg.user_blacklist:
            return False

        # Keyword mode
        if self.cfg.mode == "keyword":
            content = (message.content or "").lower()
            if not any(kw in content for kw in self.cfg.keywords):
                return False

        # Already reacted / unreacted filters
        # We check emoji presence (fast + reliable enough for this use case)
        if self.cfg.skip_already_reacted or self.cfg.only_unreacted:
            has_any = len(message.reactions) > 0
            has_my_emoji = any(
                str(r.emoji) in self.cfg.emojis for r in message.reactions
            )

            if self.cfg.only_unreacted and has_any:
                return False
            if self.cfg.skip_already_reacted and has_my_emoji:
                return False

        return True

    async def _react_to(self, message: discord.Message, emoji: str) -> bool:
        if self.cfg.dry_run:
            LOG.info(f"[DRY-RUN] Would react {emoji} to {message.id}")
            return True

        try:
            await message.add_reaction(emoji)
            return True
        except discord.HTTPException as e:
            if e.status == 429:
                retry = getattr(e, "retry_after", 5) or 5
                LOG.warning(f"Rate limited. Sleeping {retry:.1f}s")
                await asyncio.sleep(retry + 1)
                try:
                    await message.add_reaction(emoji)
                    return True
                except Exception:
                    return False
            LOG.error(f"Failed to react to {message.id}: {e}")
            return False
        except Exception as e:
            LOG.error(f"Unexpected error on {message.id}: {e}")
            return False

    async def _collect_messages(self, channel: discord.abc.Messageable) -> List[discord.Message]:
        messages: List[discord.Message] = []
        limit = self.cfg.max_messages if self.cfg.mode in ("last_n", "all") else 200

        LOG.info(f"Fetching up to {limit} messages…")

        async for msg in channel.history(limit=limit):
            self.stats["scanned"] += 1
            if self._should_react(msg):
                messages.append(msg)

        # oldest first so reactions feel more natural
        messages.reverse()
        return messages

    async def _run(self) -> None:
        try:
            channel = self.client.get_channel(self.cfg.channel_id)
            if channel is None:
                # Fallback for DMs
                channel = await self.client.fetch_channel(self.cfg.channel_id)

            if channel is None:
                CONSOLE.print(f"[bold red]Could not find channel {self.cfg.channel_id}[/]")
                await self.client.close()
                return

            CONSOLE.print(
                Panel.fit(
                    f"[bold]Logged in as[/] [cyan]{self.client.user}[/]\n"
                    f"[bold]Target[/]      {channel}\n"
                    f"[bold]Mode[/]        {self.cfg.mode}\n"
                    f"[bold]Dry-run[/]     {self.cfg.dry_run}",
                    title=f"Discord-AutoReact v{VERSION}",
                    border_style="bright_blue",
                )
            )

            targets = await self._collect_messages(channel)

            if not targets:
                CONSOLE.print("[yellow]No messages matched your filters.[/]")
                await self.client.close()
                return

            CONSOLE.print(f"[green]Found {len(targets)} messages to react to.[/]\n")

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(bar_width=40),
                MofNCompleteColumn(),
                TimeElapsedColumn(),
                console=CONSOLE,
                transient=False,
            ) as progress:
                task = progress.add_task("Reacting…", total=len(targets))

                for msg in targets:
                    emoji = self._next_emoji()
                    success = await self._react_to(msg, emoji)

                    if success:
                        self.stats["reacted"] += 1
                        LOG.debug(f"Reacted {emoji} → {msg.id}")
                    else:
                        self.stats["failed"] += 1

                    progress.advance(task)
                    await self.limiter.wait()

            self._print_summary()
        except Exception as e:
            LOG.exception(f"Fatal error: {e}")
        finally:
            await self.client.close()

    def _print_summary(self) -> None:
        table = Table(title="Run Summary", show_header=True, header_style="bold magenta")
        table.add_column("Metric", style="cyan")
        table.add_column("Count", justify="right")

        table.add_row("Messages scanned", str(self.stats["scanned"]))
        table.add_row("Successfully reacted", f"[green]{self.stats['reacted']}[/]")
        table.add_row("Failed", f"[red]{self.stats['failed']}[/]")
        table.add_row("Skipped by filters", str(self.stats["skipped"]))

        CONSOLE.print()
        CONSOLE.print(table)
        if self.cfg.dry_run:
            CONSOLE.print("\n[bold yellow]This was a dry-run. No reactions were actually added.[/]")

    def start(self) -> None:
        try:
            self.client.run(self.cfg.token)
        except discord.LoginFailure:
            CONSOLE.print("[bold red]Login failed. Check your token.[/]")
            sys.exit(1)
        except KeyboardInterrupt:
            CONSOLE.print("\n[yellow]Interrupted by user.[/]")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def setup_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level, logging.INFO),
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(console=CONSOLE, rich_tracebacks=True, show_path=False)],
    )
    # Quieten discord.py a bit
    logging.getLogger("discord").setLevel(logging.WARNING)
    logging.getLogger("discord.http").setLevel(logging.WARNING)


def main() -> None:
    config_path = Path("config.yaml")
    cfg = Config.from_yaml(config_path)
    setup_logging(cfg.log_level)

    CONSOLE.print(
        f"[bold bright_blue]Discord-AutoReact[/] [dim]v{VERSION}[/]\n"
        f"[dim]Educational tool – self-bots are against Discord ToS[/]\n"
    )

    bot = AutoReact(cfg)
    bot.start()


if __name__ == "__main__":
    main()
