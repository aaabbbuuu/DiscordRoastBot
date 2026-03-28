"""HistoryCog — admin-only slash commands for message history indexing.

Provides ``/index``, ``/indexserver``, and ``/deepdive`` application commands
that fetch Discord message history and store it in the database for roast
context.  All commands require Administrator permission.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING

import discord
from discord import app_commands
from discord.ext import commands

if TYPE_CHECKING:
    from roast_master.database import Database

logger = logging.getLogger(__name__)


class HistoryCog(commands.Cog):
    """Admin commands for bulk-indexing channel message history into the database."""

    def __init__(self, bot: commands.Bot, db: Database) -> None:
        self.bot = bot
        self.db = db

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _index_channel(
        self,
        channel: discord.TextChannel,
        guild_id: str,
        days: int,
        *,
        user_filter: discord.Member | None = None,
        progress_callback=None,
    ) -> int:
        """Fetch and store messages from *channel* going back *days* days.

        Uses the raw ``db._db`` connection for bulk inserts with a single
        commit at the end, avoiding per-message commits for performance.

        Args:
            channel: The text channel to index.
            guild_id: The guild ID string.
            days: Number of days of history to fetch.
            user_filter: If set, only index messages from this member.
            progress_callback: Optional async callable receiving a status string.

        Returns:
            Number of messages indexed.
        """
        assert self.db._db is not None
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        prefix = self.bot.command_prefix if isinstance(self.bot.command_prefix, str) else "!"
        count = 0

        async for message in channel.history(limit=None, after=cutoff):
            if message.author.bot:
                continue
            if message.content.startswith(prefix):
                continue
            if user_filter and message.author.id != user_filter.id:
                continue

            user_id = str(message.author.id)
            created_at = message.created_at.replace(tzinfo=timezone.utc).isoformat()

            # Bulk insert — skip per-message commit by writing directly
            await self.db._db.execute(
                "INSERT INTO messages (user_id, guild_id, channel_id, content, created_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (user_id, guild_id, str(channel.id), message.content, created_at),
            )
            # Upsert user record (no commit yet)
            await self.db._db.execute(
                """
                INSERT INTO users (user_id, guild_id, first_seen, last_seen, total_messages)
                VALUES (?, ?, ?, ?, 1)
                ON CONFLICT(user_id) DO UPDATE SET
                    last_seen = excluded.last_seen,
                    total_messages = total_messages + 1
                """,
                (user_id, guild_id, created_at, created_at),
            )

            count += 1
            if count % 100 == 0 and progress_callback:
                await progress_callback(count)

        # Single commit for the entire batch
        await self.db._db.commit()
        return count

    # ------------------------------------------------------------------
    # /index
    # ------------------------------------------------------------------

    @app_commands.command(
        name="index",
        description="Index message history from a channel into the database",
    )
    @app_commands.describe(
        channel="Channel to index (defaults to current channel)",
        days="Days of history to fetch (default 30)",
    )
    @app_commands.default_permissions(administrator=True)
    async def index(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel | None = None,
        days: int = 30,
    ) -> None:
        """Index a single channel's message history."""
        target = channel or interaction.channel  # type: ignore[assignment]
        guild_id = str(interaction.guild_id)

        await interaction.response.defer()
        logger.info(
            "/index channel=#%s days=%d guild=%s invoked_by=%s",
            target.name, days, guild_id, interaction.user.id,
        )

        async def _progress(count: int) -> None:
            try:
                await interaction.edit_original_response(
                    content=f"📊 Indexing #{target.name}… {count} messages so far…",
                )
            except discord.HTTPException:
                pass

        try:
            total = await self._index_channel(target, guild_id, days, progress_callback=_progress)
            logger.info("/index complete: %d messages from #%s", total, target.name)
            await interaction.edit_original_response(
                content=f"✅ Indexed **{total}** messages from #{target.name} (last {days} days).",
            )
        except discord.Forbidden:
            logger.warning("No permission to read #%s", target.name)
            await interaction.edit_original_response(
                content=f"❌ No permission to read #{target.name}.",
            )
        except Exception:
            logger.exception("Error indexing #%s", target.name)
            await interaction.edit_original_response(
                content="❌ Something went wrong while indexing. Check the logs.",
            )

    # ------------------------------------------------------------------
    # /indexserver
    # ------------------------------------------------------------------

    @app_commands.command(
        name="indexserver",
        description="Index message history from ALL text channels in this server",
    )
    @app_commands.describe(days="Days of history to fetch (default 30)")
    @app_commands.default_permissions(administrator=True)
    async def indexserver(
        self,
        interaction: discord.Interaction,
        days: int = 30,
    ) -> None:
        """Index every text channel in the guild."""
        guild = interaction.guild
        if guild is None:
            await interaction.response.send_message("❌ This command must be used in a server.", ephemeral=True)
            return

        guild_id = str(guild.id)
        await interaction.response.defer()
        logger.info(
            "/indexserver days=%d guild=%s invoked_by=%s",
            days, guild_id, interaction.user.id,
        )

        text_channels = [ch for ch in guild.text_channels if isinstance(ch, discord.TextChannel)]
        total_messages = 0
        channels_done = 0
        channels_failed: list[str] = []

        for i, ch in enumerate(text_channels, start=1):
            try:
                await interaction.edit_original_response(
                    content=f"📊 Indexing channel {i}/{len(text_channels)}: #{ch.name}…",
                )
            except discord.HTTPException:
                pass

            try:
                count = await self._index_channel(ch, guild_id, days)
                total_messages += count
                channels_done += 1
                logger.info("Indexed #%s — %d messages", ch.name, count)
            except discord.Forbidden:
                channels_failed.append(ch.name)
                logger.warning("No permission to read #%s — skipping", ch.name)
            except Exception:
                channels_failed.append(ch.name)
                logger.exception("Error indexing #%s — skipping", ch.name)

            # Small delay between channels to avoid rate limits
            await asyncio.sleep(0.5)

        summary = (
            f"✅ Server indexing complete!\n"
            f"📊 **{total_messages}** messages from **{channels_done}/{len(text_channels)}** channels (last {days} days)."
        )
        if channels_failed:
            summary += f"\n⚠️ Skipped: {', '.join(channels_failed)}"

        logger.info(
            "/indexserver complete: %d messages, %d/%d channels",
            total_messages, channels_done, len(text_channels),
        )
        await interaction.edit_original_response(content=summary)

    # ------------------------------------------------------------------
    # /deepdive
    # ------------------------------------------------------------------

    @app_commands.command(
        name="deepdive",
        description="Fetch a user's messages across ALL channels",
    )
    @app_commands.describe(
        member="The user to deep-dive",
        days="Days of history to fetch (default 90)",
    )
    @app_commands.default_permissions(administrator=True)
    async def deepdive(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        days: int = 90,
    ) -> None:
        """Index a specific user's messages across every text channel."""
        guild = interaction.guild
        if guild is None:
            await interaction.response.send_message("❌ This command must be used in a server.", ephemeral=True)
            return

        guild_id = str(guild.id)
        await interaction.response.defer()
        logger.info(
            "/deepdive member=%s days=%d guild=%s invoked_by=%s",
            member.id, days, guild_id, interaction.user.id,
        )

        text_channels = [ch for ch in guild.text_channels if isinstance(ch, discord.TextChannel)]
        total_messages = 0

        for i, ch in enumerate(text_channels, start=1):
            try:
                await interaction.edit_original_response(
                    content=f"🔍 Scanning #{ch.name} ({i}/{len(text_channels)}) for {member.display_name}…",
                )
            except discord.HTTPException:
                pass

            try:
                count = await self._index_channel(
                    ch, guild_id, days, user_filter=member,
                )
                total_messages += count
            except discord.Forbidden:
                logger.debug("No permission to read #%s — skipping", ch.name)
            except Exception:
                logger.exception("Error scanning #%s for %s", ch.name, member.id)

            await asyncio.sleep(0.5)

        logger.info("/deepdive complete: %d messages for %s", total_messages, member.id)
        await interaction.edit_original_response(
            content=(
                f"✅ Deep-dive complete for **{member.display_name}**!\n"
                f"📊 Found **{total_messages}** messages across {len(text_channels)} channels (last {days} days)."
            ),
        )
