"""RoastCog — core roasting and compliment slash commands.

Provides ``/roast``, ``/roastme``, ``/embarrass``, and ``/compliment``
application commands with style selection, cooldowns, and embed responses.
"""

from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING

import discord
from discord import app_commands
from discord.ext import commands

if TYPE_CHECKING:
    from roast_master.ai.engine import AIEngine
    from roast_master.database import Database

logger = logging.getLogger(__name__)

# Keywords used by /embarrass to find cringe-worthy messages
_EMBARRASSING_KEYWORDS: list[str] = [
    "oops",
    "sorry",
    "my bad",
    "accidentally",
    "drunk",
    "cringe",
    "regret",
]

# Cooldown duration in seconds per target user
_ROAST_COOLDOWN_SECONDS: float = 30.0


class RoastCog(commands.Cog):
    """Slash commands for roasting, self-roasting, embarrassing, and complimenting users."""

    def __init__(self, bot: commands.Bot, db: Database, engine: AIEngine) -> None:
        self.bot = bot
        self.db = db
        self.engine = engine
        self._cooldowns: dict[str, float] = {}

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _check_cooldown(self, target_id: str) -> float | None:
        """Return remaining cooldown seconds, or ``None`` if ready.

        Args:
            target_id: The Discord user ID of the roast target.

        Returns:
            Seconds remaining if on cooldown, otherwise ``None``.
        """
        now = time.time()
        last = self._cooldowns.get(target_id)
        if last is not None:
            remaining = _ROAST_COOLDOWN_SECONDS - (now - last)
            if remaining > 0:
                return remaining
        return None

    def _set_cooldown(self, target_id: str) -> None:
        """Record the current timestamp as the last roast time for *target_id*."""
        self._cooldowns[target_id] = time.time()

    @staticmethod
    def _roast_embed(target: discord.Member, text: str, provider: str, style: str) -> discord.Embed:
        """Build a Discord embed for a roast response."""
        embed = discord.Embed(
            description=text,
            color=discord.Color.red(),
        )
        embed.set_author(name=f"🔥 Roast — {target.display_name}", icon_url=target.display_avatar.url)
        embed.set_footer(text=f"Style: {style} • Provider: {provider}")
        return embed

    @staticmethod
    def _compliment_embed(target: discord.Member, text: str, provider: str) -> discord.Embed:
        """Build a Discord embed for a compliment response."""
        embed = discord.Embed(
            description=text,
            color=discord.Color.green(),
        )
        embed.set_author(name=f"💚 Compliment — {target.display_name}", icon_url=target.display_avatar.url)
        embed.set_footer(text=f"Provider: {provider}")
        return embed

    # ------------------------------------------------------------------
    # /roast
    # ------------------------------------------------------------------

    @app_commands.command(name="roast", description="Roast someone based on their chat history")
    @app_commands.describe(
        member="Who to roast (leave empty to roast yourself)",
        style="Roast style",
    )
    @app_commands.choices(style=[
        app_commands.Choice(name="Savage", value="savage"),
        app_commands.Choice(name="Mild", value="mild"),
        app_commands.Choice(name="Shakespearean", value="shakespearean"),
        app_commands.Choice(name="Corporate", value="corporate"),
        app_commands.Choice(name="Gen-Z", value="gen-z"),
    ])
    async def roast(
        self,
        interaction: discord.Interaction,
        member: discord.Member | None = None,
        style: str = "savage",
    ) -> None:
        """Generate an AI roast for the target member."""
        target = member or interaction.user  # type: ignore[assignment]
        target_id = str(target.id)
        guild_id = str(interaction.guild_id)

        # Cooldown check
        remaining = self._check_cooldown(target_id)
        if remaining is not None:
            await interaction.response.send_message(
                f"⏳ {target.display_name} was just roasted. Try again in {remaining:.0f}s.",
                ephemeral=True,
            )
            return

        await interaction.response.defer()

        try:
            roast_text, provider = await self.engine.generate_roast(
                user_name=target.display_name,
                user_id=target_id,
                guild_id=guild_id,
                style=style,
            )
            self._set_cooldown(target_id)
            logger.info(
                "/roast target=%s style=%s provider=%s guild=%s",
                target_id, style, provider, guild_id,
            )
            embed = self._roast_embed(target, roast_text, provider, style)
            await interaction.followup.send(embed=embed)
        except Exception:
            logger.exception("Error generating roast for %s", target_id)
            await interaction.followup.send("❌ Something went wrong generating the roast. Try again later.")

    # ------------------------------------------------------------------
    # /roastme
    # ------------------------------------------------------------------

    @app_commands.command(name="roastme", description="Roast yourself — no mercy")
    async def roastme(self, interaction: discord.Interaction) -> None:
        """Roast the command invoker using the savage style."""
        target = interaction.user
        target_id = str(target.id)
        guild_id = str(interaction.guild_id)

        remaining = self._check_cooldown(target_id)
        if remaining is not None:
            await interaction.response.send_message(
                f"⏳ You were just roasted. Try again in {remaining:.0f}s.",
                ephemeral=True,
            )
            return

        await interaction.response.defer()

        try:
            roast_text, provider = await self.engine.generate_roast(
                user_name=target.display_name,
                user_id=target_id,
                guild_id=guild_id,
                style="savage",
            )
            self._set_cooldown(target_id)
            logger.info(
                "/roastme target=%s provider=%s guild=%s",
                target_id, provider, guild_id,
            )
            embed = self._roast_embed(target, roast_text, provider, "savage")
            await interaction.followup.send(embed=embed)
        except Exception:
            logger.exception("Error generating self-roast for %s", target_id)
            await interaction.followup.send("❌ Something went wrong generating the roast. Try again later.")

    # ------------------------------------------------------------------
    # /embarrass
    # ------------------------------------------------------------------

    @app_commands.command(name="embarrass", description="Find someone's embarrassing moments and roast them")
    @app_commands.describe(member="Who to embarrass")
    async def embarrass(self, interaction: discord.Interaction, member: discord.Member) -> None:
        """Search the target's messages for embarrassing keywords and roast them."""
        target_id = str(member.id)
        guild_id = str(interaction.guild_id)

        await interaction.response.defer()

        try:
            # Collect embarrassing messages across all keywords
            embarrassing_messages: list[str] = []
            for keyword in _EMBARRASSING_KEYWORDS:
                results = await self.db.search_messages(target_id, guild_id, keyword)
                for row in results:
                    content = row.get("content", "")
                    if content and content not in embarrassing_messages:
                        embarrassing_messages.append(content)

            if not embarrassing_messages:
                await interaction.followup.send(
                    f"😇 {member.display_name} has a squeaky-clean history. No embarrassing moments found!"
                )
                return

            roast_text, provider = await self.engine.generate_roast(
                user_name=member.display_name,
                user_id=target_id,
                guild_id=guild_id,
                style="savage",
                embarrassing=embarrassing_messages,
            )
            logger.info(
                "/embarrass target=%s found=%d provider=%s guild=%s",
                target_id, len(embarrassing_messages), provider, guild_id,
            )
            embed = self._roast_embed(member, roast_text, provider, "savage")
            embed.set_author(
                name=f"😳 Embarrassing Roast — {member.display_name}",
                icon_url=member.display_avatar.url,
            )
            await interaction.followup.send(embed=embed)
        except Exception:
            logger.exception("Error generating embarrass roast for %s", target_id)
            await interaction.followup.send("❌ Something went wrong. Try again later.")

    # ------------------------------------------------------------------
    # /compliment
    # ------------------------------------------------------------------

    @app_commands.command(name="compliment", description="Give someone a genuine AI-powered compliment")
    @app_commands.describe(member="Who to compliment (leave empty to compliment yourself)")
    async def compliment(
        self,
        interaction: discord.Interaction,
        member: discord.Member | None = None,
    ) -> None:
        """Generate a genuine compliment for the target member."""
        target = member or interaction.user  # type: ignore[assignment]
        target_id = str(target.id)
        guild_id = str(interaction.guild_id)

        await interaction.response.defer()

        try:
            compliment_text, provider = await self.engine.generate_compliment(
                user_name=target.display_name,
                user_id=target_id,
                guild_id=guild_id,
            )
            logger.info(
                "/compliment target=%s provider=%s guild=%s",
                target_id, provider, guild_id,
            )
            embed = self._compliment_embed(target, compliment_text, provider)
            await interaction.followup.send(embed=embed)
        except Exception:
            logger.exception("Error generating compliment for %s", target_id)
            await interaction.followup.send("❌ Something went wrong generating the compliment. Try again later.")
