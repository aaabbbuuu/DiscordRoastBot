"""Async SQLite database layer for Smart Roast Bot.

Provides the :class:`Database` class that manages all persistence — users,
messages, roast history, scheduled roasts — and handles migration from the
legacy ``messages.json`` format.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path

import aiosqlite

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Schema DDL
# ---------------------------------------------------------------------------

_SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    user_id TEXT PRIMARY KEY,
    guild_id TEXT NOT NULL,
    first_seen TEXT NOT NULL,
    last_seen TEXT NOT NULL,
    total_messages INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    guild_id TEXT NOT NULL,
    channel_id TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE INDEX IF NOT EXISTS idx_messages_user ON messages(user_id);
CREATE INDEX IF NOT EXISTS idx_messages_guild ON messages(guild_id);
CREATE INDEX IF NOT EXISTS idx_messages_created ON messages(created_at);

CREATE TABLE IF NOT EXISTS roast_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    target_user_id TEXT NOT NULL,
    roaster_user_id TEXT NOT NULL,
    guild_id TEXT NOT NULL,
    roast_text TEXT NOT NULL,
    style TEXT NOT NULL DEFAULT 'savage',
    provider TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS scheduled_roasts (
    guild_id TEXT PRIMARY KEY,
    channel_id TEXT NOT NULL,
    cron_expression TEXT NOT NULL DEFAULT '0 12 * * *',
    enabled INTEGER NOT NULL DEFAULT 0
);
"""


class Database:
    """Async SQLite database wrapper for the roast bot."""

    def __init__(self, db_path: str = "data/roastbot.db") -> None:
        self.db_path = db_path
        self._db: aiosqlite.Connection | None = None

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def init(self) -> None:
        """Open the database connection and create tables/indexes."""
        os.makedirs(os.path.dirname(self.db_path) or ".", exist_ok=True)
        self._db = await aiosqlite.connect(self.db_path)
        self._db.row_factory = aiosqlite.Row
        await self._db.executescript(_SCHEMA)
        await self._db.commit()
        logger.info("Database initialised at %s", self.db_path)

    async def close(self) -> None:
        """Close the database connection."""
        if self._db:
            await self._db.close()
            self._db = None
            logger.info("Database connection closed.")

    # ------------------------------------------------------------------
    # Messages
    # ------------------------------------------------------------------

    async def add_message(
        self,
        user_id: str,
        guild_id: str,
        channel_id: str,
        content: str,
        created_at: str,
    ) -> None:
        """Insert a message and update the user record."""
        assert self._db is not None
        await self._db.execute(
            "INSERT INTO messages (user_id, guild_id, channel_id, content, created_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (user_id, guild_id, channel_id, content, created_at),
        )
        await self._upsert_user(user_id, guild_id, created_at)
        await self._db.commit()

    async def get_user_messages(
        self, user_id: str, guild_id: str, limit: int = 500
    ) -> list[dict]:
        """Return the most recent messages for a user in a guild."""
        assert self._db is not None
        cursor = await self._db.execute(
            "SELECT content, channel_id, created_at FROM messages "
            "WHERE user_id = ? AND guild_id = ? "
            "ORDER BY created_at DESC LIMIT ?",
            (user_id, guild_id, limit),
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]

    async def search_messages(
        self, user_id: str, guild_id: str, query: str
    ) -> list[dict]:
        """Search a user's messages by keyword (case-insensitive LIKE)."""
        assert self._db is not None
        cursor = await self._db.execute(
            "SELECT content, channel_id, created_at FROM messages "
            "WHERE user_id = ? AND guild_id = ? AND content LIKE ? "
            "ORDER BY created_at DESC",
            (user_id, guild_id, f"%{query}%"),
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]

    async def get_message_count(self, user_id: str, guild_id: str) -> int:
        """Return total message count for a user in a guild."""
        assert self._db is not None
        cursor = await self._db.execute(
            "SELECT COUNT(*) FROM messages WHERE user_id = ? AND guild_id = ?",
            (user_id, guild_id),
        )
        row = await cursor.fetchone()
        return row[0] if row else 0

    # ------------------------------------------------------------------
    # Users
    # ------------------------------------------------------------------

    async def get_or_create_user(self, user_id: str, guild_id: str) -> dict:
        """Return the user row, creating one if it doesn't exist."""
        assert self._db is not None
        now = datetime.now(timezone.utc).isoformat()
        await self._upsert_user(user_id, guild_id, now)
        cursor = await self._db.execute(
            "SELECT * FROM users WHERE user_id = ? AND guild_id = ?",
            (user_id, guild_id),
        )
        row = await cursor.fetchone()
        return dict(row) if row else {}

    async def get_leaderboard(
        self, guild_id: str, limit: int = 10
    ) -> list[dict]:
        """Return top users by message count in a guild."""
        assert self._db is not None
        cursor = await self._db.execute(
            "SELECT user_id, total_messages, first_seen, last_seen "
            "FROM users WHERE guild_id = ? "
            "ORDER BY total_messages DESC LIMIT ?",
            (guild_id, limit),
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]

    # ------------------------------------------------------------------
    # Roast history
    # ------------------------------------------------------------------

    async def add_roast(
        self,
        target_id: str,
        roaster_id: str,
        guild_id: str,
        text: str,
        style: str,
        provider: str,
    ) -> None:
        """Record a roast in history."""
        assert self._db is not None
        now = datetime.now(timezone.utc).isoformat()
        await self._db.execute(
            "INSERT INTO roast_history "
            "(target_user_id, roaster_user_id, guild_id, roast_text, style, provider, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (target_id, roaster_id, guild_id, text, style, provider, now),
        )
        await self._db.commit()

    async def get_recent_roasts(
        self, target_id: str, guild_id: str, limit: int = 10
    ) -> list[dict]:
        """Return the most recent roasts targeting a user."""
        assert self._db is not None
        cursor = await self._db.execute(
            "SELECT roast_text, style, provider, created_at "
            "FROM roast_history "
            "WHERE target_user_id = ? AND guild_id = ? "
            "ORDER BY created_at DESC LIMIT ?",
            (target_id, guild_id, limit),
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _upsert_user(
        self, user_id: str, guild_id: str, timestamp: str
    ) -> None:
        """Insert or update a user record."""
        assert self._db is not None
        await self._db.execute(
            """
            INSERT INTO users (user_id, guild_id, first_seen, last_seen, total_messages)
            VALUES (?, ?, ?, ?, 1)
            ON CONFLICT(user_id) DO UPDATE SET
                last_seen = excluded.last_seen,
                total_messages = total_messages + 1
            """,
            (user_id, guild_id, timestamp, timestamp),
        )

    # ------------------------------------------------------------------
    # Migration
    # ------------------------------------------------------------------

    async def migrate_from_json(self, json_path: str) -> int:
        """Migrate messages from legacy ``messages.json`` into the database.

        Only runs if the JSON file exists and the messages table is empty.
        Does **not** delete the JSON file afterwards.

        Args:
            json_path: Path to the ``messages.json`` file.

        Returns:
            Number of messages migrated.
        """
        assert self._db is not None

        if not Path(json_path).exists():
            logger.debug("No JSON file at %s — skipping migration.", json_path)
            return 0

        # Only migrate into an empty database
        cursor = await self._db.execute("SELECT COUNT(*) FROM messages")
        row = await cursor.fetchone()
        if row and row[0] > 0:
            logger.debug("Database already has messages — skipping migration.")
            return 0

        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data: dict = json.load(f)
        except (json.JSONDecodeError, OSError) as exc:
            logger.error("Failed to read %s for migration: %s", json_path, exc)
            return 0

        migrated = 0
        # The JSON format is: { "user_id": { "messages": [...], "first_seen": ..., ... } }
        for user_id, user_data in data.items():
            messages = user_data.get("messages", [])
            first_seen = user_data.get("first_seen", datetime.now(timezone.utc).isoformat())
            last_seen = user_data.get("last_seen", first_seen)
            total = user_data.get("total_messages", len(messages))

            # Insert user record
            await self._db.execute(
                """
                INSERT OR IGNORE INTO users (user_id, guild_id, first_seen, last_seen, total_messages)
                VALUES (?, ?, ?, ?, ?)
                """,
                (user_id, "unknown", first_seen, last_seen, total),
            )

            # Insert messages (no channel_id or timestamp in legacy data)
            for msg in messages:
                if not msg:  # skip empty strings
                    continue
                await self._db.execute(
                    "INSERT INTO messages (user_id, guild_id, channel_id, content, created_at) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (user_id, "unknown", "unknown", msg, first_seen),
                )
                migrated += 1

        await self._db.commit()
        logger.info("Migrated %d messages from %s", migrated, json_path)
        return migrated
