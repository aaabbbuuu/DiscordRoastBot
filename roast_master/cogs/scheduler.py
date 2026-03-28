"""SchedulerCog — automated roast-of-the-day via a background task loop.

Provides the ``/scheduleroast`` admin command to configure a channel and time
for daily scheduled roasts, and a :pymod:`discord.ext.tasks` loop that fires
every 60 seconds to check whether any guild is due for a roast.
"""

from __future__ import annotations

import logging
import random
from datetime import datetime, timezone
from typing import TYPE_CHECKING

import discord
from discord import app_commands
from discord.ext import commands, tasks

if TYPE_CHECKING:
    from roast_master.ai.engine import AIEngine
    from roast_master.database import Database

logger = logging.getLogger(__name__)


class SchedulerCog(commands.Cog):
    """Admin-configurable scheduled roasts using a background task loop."""

    def __init__(self, bot: commands.Bot, db: Database, engine: AIEngine) -> None:
        self.bot = bot
        self.db = db
        self.engine = engine
        # Track last execution per guild to avoid duplicate roasts in the same minute
        self._last_fired: dict[str, str] = {}

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def cog_load(self) -> None:
        """Start the background scheduler loop."""
        self._roast_loop.start()
        logger.info("SchedulerCog loaded — background loop started.")

    async def cog_unload(self) -> None:
        """Stop the background scheduler loop."""
        self._roast_loop.cancel()
        logger.info("SchedulerCog unloaded — background loop stopped.")

    # ------------------------------------------------------------------
    # /scheduleroast
    # ------------------------------------------------------------------

    @app_commands.command(
        name="scheduleroast",
        description="Configure the daily roast-of-the-day for this server",
    )
    @app_commands.default_permissions(administrator=True)
    @app_commands.describe(
        channel="Channel where scheduled roasts will be posted",
        enabled="Enable or disable scheduled roasts",
        hour="Hour of day in UTC to post (0-23, default 12)",
        minute="Minute of the hour to post (0-59, default 0)",
    )
    async def scheduleroast(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel,
        enabled: bool,
        hour: int = 12,
        minute: int = 0,
    ) -> None:
        """Save scheduled-roast configuration for the current guild."""
        # Validate hour/minute ranges
        if not (0 <= hour <= 23):
            await interaction.response.send_message(
                "❌ Hour must be between 0 and 23.", ephemeral=True,
            )
            return
        if not (0 <= minute <= 59):
            await interaction.response.send_message(
                "❌ Minute must be between 0 and 59.", ephemeral=True,
            )
            return

        guild_id = str(interaction.guild_id)
        channel_id = str(channel.id)
        # Store as "M H * * *" cron-style in the existing cron_expression column
        cron_expr = f"{minute} {hour} * * *"

        try:
            assert self.db._db is not None
            await self.db._db.execute(
                "INSERT OR REPLACE INTO scheduled_roasts "
                "(guild_id, channel_id, cron_expression, enabled) "
                "VALUES (?, ?, ?, ?)",
                (guild_id, channel_id, cron_expr, int(enabled)),
            )
            await self.db._db.commit()

            status = "✅ Enabled" if enabled else "⛔ Disabled"
            time_str = f"{hour:02d}:{minute:02d} UTC"

            embed = discord.Embed(
                title="⏰ Scheduled Roast Configuration",
                color=discord.Color.orange(),
            )
            embed.add_field(name="Status", value=status, inline=True)
            embed.add_field(name="Channel", value=channel.mention, inline=True)
            embed.add_field(name="Time", value=time_str, inline=True)
            embed.set_footer(text=f"Guild: {guild_id}")

            logger.info(
                "/scheduleroast guild=%s channel=%s time=%s enabled=%s",
                guild_id, channel_id, time_str, enabled,
            )
            await interaction.response.send_message(embed=embed)
        except Exception:
            logger.exception("Error saving scheduled roast config for guild %s", guild_id)
            await interaction.response.send_message(
                "❌ Failed to save configuration. Try again later.",
                ephemeral=True,
            )

    # ------------------------------------------------------------------
    # Background task loop
    # ------------------------------------------------------------------

    @tasks.loop(seconds=60)
    async def _roast_loop(self) -> None:
        """Check every 60 seconds if any guild is due for a scheduled roast."""
        try:
            assert self.db._db is not None
            cursor = await self.db._db.execute(
                "SELECT guild_id, channel_id, cron_expression "
                "FROM scheduled_roasts WHERE enabled = 1",
            )
            rows = await cursor.fetchall()

            if not rows:
                return

            now = datetime.now(timezone.utc)
            current_hm = f"{now.hour:02d}:{now.minute:02d}"

            for row in rows:
                guild_id: str = row["guild_id"]
                channel_id: str = row["channel_id"]
                cron_expr: str = row["cron_expression"]

                # Parse "M H * * *" format
                scheduled_minute, scheduled_hour = self._parse_cron(cron_expr)
                scheduled_hm = f"{scheduled_hour:02d}:{scheduled_minute:02d}"

                if current_hm != scheduled_hm:
                    continue

                # Avoid firing twice in the same minute
                if self._last_fired.get(guild_id) == current_hm:
                    continue

                self._last_fired[guild_id] = current_hm
                await self._fire_scheduled_roast(guild_id, channel_id)

        except Exception:
            logger.exception("Error in scheduled roast loop.")

    @_roast_loop.before_loop
    async def _before_roast_loop(self) -> None:
        """Wait until the bot is ready before starting the loop."""
        await self.bot.wait_until_ready()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_cron(cron_expr: str) -> tuple[int, int]:
        """Parse a simple ``"M H * * *"`` cron expression.

        Returns:
            A ``(minute, hour)`` tuple.
        """
        parts = cron_expr.split()
        return int(parts[0]), int(parts[1])

    async def _fire_scheduled_roast(self, guild_id: str, channel_id: str) -> None:
        """Pick a random active user and send a roast to the configured channel."""
        try:
            channel = self.bot.get_channel(int(channel_id))
            if channel is None:
                try:
                    channel = await self.bot.fetch_channel(int(channel_id))
                except discord.NotFound:
                    logger.warning(
                        "Scheduled roast channel %s not found for guild %s.",
                        channel_id, guild_id,
                    )
                    return
                except discord.Forbidden:
                    logger.warning(
                        "No access to scheduled roast channel %s in guild %s.",
                        channel_id, guild_id,
                    )
                    return

            # Pick a random active user from the leaderboard
            leaderboard = await self.db.get_leaderboard(guild_id, limit=20)
            if not leaderboard:
                logger.info(
                    "No active users in guild %s — skipping scheduled roast.",
                    guild_id,
                )
                return

            target = random.choice(leaderboard)
            target_user_id: str = target["user_id"]

            # Resolve the Discord user for display name
            display_name = f"User {target_user_id}"
            member = None
            guild = self.bot.get_guild(int(guild_id))
            if guild is not None:
                member = guild.get_member(int(target_user_id))
                if member is None:
                    try:
                        member = await guild.fetch_member(int(target_user_id))
                    except (discord.NotFound, discord.Forbidden):
                        member = None
            if member is not None:
                display_name = member.display_name

            # Generate the roast
            roast_text, provider = await self.engine.generate_roast(
                user_name=display_name,
                user_id=target_user_id,
                guild_id=guild_id,
                style="savage",
            )

            # Build and send the embed
            embed = discord.Embed(
                title="🔥 Roast of the Day",
                description=roast_text,
                color=discord.Color.red(),
            )
            if member is not None:
                embed.set_author(
                    name=display_name,
                    icon_url=member.display_avatar.url,
                )
            else:
                embed.set_author(name=display_name)
            embed.set_footer(text=f"Provider: {provider} • Style: savage")

            await channel.send(embed=embed)  # type: ignore[union-attr]

            logger.info(
                "Scheduled roast fired: guild=%s target=%s provider=%s",
                guild_id, target_user_id, provider,
            )
        except Exception:
            logger.exception(
                "Failed to fire scheduled roast for guild %s.", guild_id,
            )
