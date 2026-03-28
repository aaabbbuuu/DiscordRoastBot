"""ReceiptsCog — search a user's message history for receipts.

Provides the ``/receipts`` slash command that searches a target user's
stored messages for a given claim/query and returns matching messages
with timestamps in a formatted embed.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import discord
from discord import app_commands
from discord.ext import commands

if TYPE_CHECKING:
    from roast_master.ai.engine import AIEngine
    from roast_master.database import Database

logger = logging.getLogger(__name__)

# Maximum number of matching messages to display
_MAX_RESULTS: int = 10


class ReceiptsCog(commands.Cog):
    """Slash command for pulling receipts from a user's chat history."""

    def __init__(self, bot: commands.Bot, db: Database, engine: AIEngine) -> None:
        self.bot = bot
        self.db = db
        self.engine = engine

    # ------------------------------------------------------------------
    # /receipts
    # ------------------------------------------------------------------

    @app_commands.command(
        name="receipts",
        description="Pull the receipts — search someone's messages for a claim",
    )
    @app_commands.describe(
        member="Whose messages to search",
        claim="The claim or keyword to search for",
    )
    async def receipts(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        claim: str,
    ) -> None:
        """Search *member*'s stored messages for *claim* and display matches."""
        target_id = str(member.id)
        guild_id = str(interaction.guild_id)

        await interaction.response.defer()

        try:
            matches = await self.db.search_messages(target_id, guild_id, claim)

            if not matches:
                await interaction.followup.send(
                    f"🔍 No receipts found for **{member.display_name}** matching \"{claim}\"."
                )
                return

            # Limit to top results
            matches = matches[:_MAX_RESULTS]

            embed = discord.Embed(
                title=f"🧾 Receipts for {member.display_name}",
                description=f"Search: \"{claim}\" — {len(matches)} match(es)",
                color=discord.Color.purple(),
            )
            embed.set_thumbnail(url=member.display_avatar.url)

            for match in matches:
                content = match.get("content", "")
                created_at = match.get("created_at", "unknown")
                embed.add_field(
                    name="\u200b",
                    value=f"📝 {content}\n🕐 {created_at}",
                    inline=False,
                )

            embed.set_footer(text=f"Showing top {len(matches)} result(s)")
            await interaction.followup.send(embed=embed)

            logger.info(
                "/receipts target=%s claim=%r matches=%d guild=%s",
                target_id,
                claim,
                len(matches),
                guild_id,
            )
        except Exception:
            logger.exception("Error searching receipts for %s", target_id)
            await interaction.followup.send(
                "❌ Something went wrong searching for receipts. Try again later."
            )
