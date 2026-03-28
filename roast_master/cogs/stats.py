"""StatsCog — read-only statistics slash commands.

Provides ``/stats``, ``/leaderboard``, and ``/memory`` application commands
that query the database for user and guild statistics.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import discord
from discord import app_commands
from discord.ext import commands

if TYPE_CHECKING:
    from roast_master.database import Database

logger = logging.getLogger(__name__)


class StatsCog(commands.Cog):
    """Slash commands for viewing user stats, leaderboards, and memory usage."""

    def __init__(self, bot: commands.Bot, db: Database) -> None:
        self.bot = bot
        self.db = db

    # ------------------------------------------------------------------
    # /stats
    # ------------------------------------------------------------------

    @app_commands.command(name="stats", description="View message stats for a user")
    @app_commands.describe(member="Who to check (leave empty for yourself)")
    async def stats(
        self,
        interaction: discord.Interaction,
        member: discord.Member | None = None,
    ) -> None:
        """Display message count, average length, first seen, and last seen for a user."""
        target = member or interaction.user  # type: ignore[assignment]
        target_id = str(target.id)
        guild_id = str(interaction.guild_id)

        await interaction.response.defer()

        try:
            user_data = await self.db.get_or_create_user(target_id, guild_id)
            message_count = await self.db.get_message_count(target_id, guild_id)
            messages = await self.db.get_user_messages(target_id, guild_id)

            # Compute average message length
            if messages:
                total_len = sum(len(m.get("content", "")) for m in messages)
                avg_length = total_len / len(messages)
            else:
                avg_length = 0.0

            first_seen = user_data.get("first_seen", "Unknown")
            last_seen = user_data.get("last_seen", "Unknown")

            embed = discord.Embed(
                title=f"📊 Stats — {target.display_name}",
                color=discord.Color.blue(),
            )
            embed.set_thumbnail(url=target.display_avatar.url)
            embed.add_field(name="Messages", value=str(message_count), inline=True)
            embed.add_field(name="Avg Length", value=f"{avg_length:.1f} chars", inline=True)
            embed.add_field(name="First Seen", value=first_seen, inline=True)
            embed.add_field(name="Last Seen", value=last_seen, inline=True)

            logger.info("/stats target=%s guild=%s", target_id, guild_id)
            await interaction.followup.send(embed=embed)
        except Exception:
            logger.exception("Error fetching stats for %s", target_id)
            await interaction.followup.send("❌ Something went wrong fetching stats. Try again later.")

    # ------------------------------------------------------------------
    # /leaderboard
    # ------------------------------------------------------------------

    @app_commands.command(name="leaderboard", description="Top 10 most active users in this server")
    async def leaderboard(self, interaction: discord.Interaction) -> None:
        """Display the top 10 users by message count in the current guild."""
        guild_id = str(interaction.guild_id)

        await interaction.response.defer()

        try:
            rows = await self.db.get_leaderboard(guild_id, limit=10)

            if not rows:
                await interaction.followup.send("📭 No data yet — start chatting!")
                return

            lines: list[str] = []
            for rank, row in enumerate(rows, start=1):
                user_id = row["user_id"]
                total = row["total_messages"]

                # Try to resolve display name
                display_name = f"User {user_id}"
                user = self.bot.get_user(int(user_id))
                if user is None:
                    try:
                        user = await self.bot.fetch_user(int(user_id))
                    except discord.NotFound:
                        user = None
                if user is not None:
                    display_name = user.display_name

                lines.append(f"**{rank}.** {display_name} — {total} messages")

            embed = discord.Embed(
                title="🏆 Leaderboard — Top 10",
                description="\n".join(lines),
                color=discord.Color.gold(),
            )

            logger.info("/leaderboard guild=%s entries=%d", guild_id, len(rows))
            await interaction.followup.send(embed=embed)
        except Exception:
            logger.exception("Error fetching leaderboard for guild %s", guild_id)
            await interaction.followup.send("❌ Something went wrong fetching the leaderboard. Try again later.")

    # ------------------------------------------------------------------
    # /memory
    # ------------------------------------------------------------------

    @app_commands.command(name="memory", description="Check how many messages are stored for a user")
    @app_commands.describe(member="Who to check (leave empty for yourself)")
    async def memory(
        self,
        interaction: discord.Interaction,
        member: discord.Member | None = None,
    ) -> None:
        """Show stored message count vs total tracked messages for a user."""
        target = member or interaction.user  # type: ignore[assignment]
        target_id = str(target.id)
        guild_id = str(interaction.guild_id)

        await interaction.response.defer()

        try:
            user_data = await self.db.get_or_create_user(target_id, guild_id)
            stored_count = await self.db.get_message_count(target_id, guild_id)
            total_tracked = user_data.get("total_messages", 0)
            first_seen = user_data.get("first_seen", "Unknown")

            embed = discord.Embed(
                title=f"🧠 Memory — {target.display_name}",
                color=discord.Color.blue(),
            )
            embed.set_thumbnail(url=target.display_avatar.url)
            embed.add_field(name="Stored Messages", value=str(stored_count), inline=True)
            embed.add_field(name="Total Tracked", value=str(total_tracked), inline=True)
            embed.add_field(name="First Seen", value=first_seen, inline=False)

            logger.info("/memory target=%s guild=%s", target_id, guild_id)
            await interaction.followup.send(embed=embed)
        except Exception:
            logger.exception("Error fetching memory info for %s", target_id)
            await interaction.followup.send("❌ Something went wrong fetching memory info. Try again later.")
