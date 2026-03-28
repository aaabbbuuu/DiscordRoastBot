"""BattleCog — head-to-head roast battle with reaction voting.

Provides the ``/battle`` slash command that pits two users against each other
with AI-generated roasts and lets the server vote via reactions.
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

# Reaction emojis used for voting
_VOTE_EMOJI_1 = "1️⃣"
_VOTE_EMOJI_2 = "2️⃣"


class BattleCog(commands.Cog):
    """Slash command for a two-user roast battle with reaction-based voting."""

    def __init__(self, bot: commands.Bot, db: Database, engine: AIEngine) -> None:
        self.bot = bot
        self.db = db
        self.engine = engine

    # ------------------------------------------------------------------
    # /battle
    # ------------------------------------------------------------------

    @app_commands.command(name="battle", description="Start a roast battle between two users")
    @app_commands.describe(
        member1="First contestant",
        member2="Second contestant",
    )
    async def battle(
        self,
        interaction: discord.Interaction,
        member1: discord.Member,
        member2: discord.Member,
    ) -> None:
        """Generate roasts for two members and let the server vote on the best one."""
        # Validation: must be two different, non-bot users
        if member1.id == member2.id:
            await interaction.response.send_message(
                "❌ You can't battle someone against themselves! Pick two different users.",
                ephemeral=True,
            )
            return

        if member1.bot or member2.bot:
            await interaction.response.send_message(
                "❌ Bots can't participate in roast battles. Pick real humans!",
                ephemeral=True,
            )
            return

        await interaction.response.defer()

        guild_id = str(interaction.guild_id)

        try:
            roast1_text, provider1 = await self.engine.generate_roast(
                user_name=member1.display_name,
                user_id=str(member1.id),
                guild_id=guild_id,
                style="savage",
            )
            roast2_text, provider2 = await self.engine.generate_roast(
                user_name=member2.display_name,
                user_id=str(member2.id),
                guild_id=guild_id,
                style="savage",
            )

            logger.info(
                "/battle member1=%s member2=%s providers=%s/%s guild=%s",
                member1.id, member2.id, provider1, provider2, guild_id,
            )

            embed = discord.Embed(
                title="⚔️ Roast Battle",
                description=(
                    f"**{member1.display_name}** vs **{member2.display_name}**"
                ),
                color=discord.Color.orange(),
            )
            embed.add_field(
                name=f"{_VOTE_EMOJI_1} {member1.display_name}",
                value=roast1_text,
                inline=False,
            )
            embed.add_field(
                name=f"{_VOTE_EMOJI_2} {member2.display_name}",
                value=roast2_text,
                inline=False,
            )
            embed.set_footer(text="React to vote for the better roast!")

            message = await interaction.followup.send(embed=embed, wait=True)
            await message.add_reaction(_VOTE_EMOJI_1)
            await message.add_reaction(_VOTE_EMOJI_2)

        except Exception:
            logger.exception(
                "Error generating battle roasts for %s vs %s",
                member1.id, member2.id,
            )
            await interaction.followup.send(
                "❌ Something went wrong generating the battle. Try again later."
            )
