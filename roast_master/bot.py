"""Bot setup, event handlers, and cog loading.

Provides :func:`create_bot` which wires up a hybrid :class:`commands.Bot`
with intent configuration, database-backed message logging, error handling,
and automatic cog loading via ``setup_hook``.
"""

from __future__ import annotations

import logging
from datetime import timezone
from typing import TYPE_CHECKING

import discord
from discord.ext import commands

if TYPE_CHECKING:
    from roast_master.ai.engine import AIEngine
    from roast_master.config import Config
    from roast_master.database import Database

logger = logging.getLogger(__name__)


def create_bot(config: Config, db: Database, engine: AIEngine) -> commands.Bot:
    """Create and configure the hybrid Discord bot.

    The returned bot stores *db* and *engine* as instance attributes so that
    cogs can access them via ``bot.db`` and ``bot.engine``.
    """
    intents = discord.Intents.default()
    intents.message_content = True
    intents.members = True

    bot = commands.Bot(command_prefix=config.command_prefix, intents=intents)

    # Attach shared resources so cogs can reach them
    bot.db = db  # type: ignore[attr-defined]
    bot.engine = engine  # type: ignore[attr-defined]

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------

    @bot.event
    async def on_ready() -> None:
        logger.info("Logged in as %s (ID: %s)", bot.user, bot.user.id if bot.user else "?")
        logger.info("Connected to %d guild(s)", len(bot.guilds))
        synced = bot.tree.get_commands()
        logger.info("Synced %d app command(s)", len(synced))

    @bot.event
    async def on_message(message: discord.Message) -> None:
        # Ignore bots and DMs
        if message.author.bot:
            return
        if message.guild is None:
            return

        # Store non-command messages in the database
        if not message.content.startswith(config.command_prefix):
            try:
                await db.add_message(
                    user_id=str(message.author.id),
                    guild_id=str(message.guild.id),
                    channel_id=str(message.channel.id),
                    content=message.content,
                    created_at=message.created_at.replace(tzinfo=timezone.utc).isoformat(),
                )
            except Exception:
                logger.exception("Failed to store message from %s", message.author.id)

        await bot.process_commands(message)

    @bot.event
    async def on_command_error(ctx: commands.Context, error: commands.CommandError) -> None:
        if isinstance(error, commands.CommandNotFound):
            # Silently ignore unknown commands
            return
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ You don't have permission to use this command.")
            return
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send(
                f"⏳ This command is on cooldown. Try again in {error.retry_after:.0f}s."
            )
            return
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"❌ Missing required argument: {error.param.name}")
            return

        logger.exception("Unhandled error in command '%s': %s", ctx.command, error)
        await ctx.send("❌ Something went wrong. Please try again later.")

    # ------------------------------------------------------------------
    # Cog loading
    # ------------------------------------------------------------------

    @bot.event
    async def setup_hook() -> None:
        """Load all cogs and sync app commands."""
        from roast_master.cogs.roast import RoastCog
        from roast_master.cogs.battle import BattleCog
        from roast_master.cogs.stats import StatsCog
        from roast_master.cogs.history import HistoryCog
        from roast_master.cogs.receipts import ReceiptsCog
        from roast_master.cogs.hallofshame import HallOfShameCog
        from roast_master.cogs.scheduler import SchedulerCog

        cogs: list[commands.Cog] = [
            RoastCog(bot, db, engine),
            BattleCog(bot, db, engine),
            StatsCog(bot, db),
            HistoryCog(bot, db),
            ReceiptsCog(bot, db, engine),
            HallOfShameCog(bot, db),
            SchedulerCog(bot, db, engine),
        ]

        for cog in cogs:
            await bot.add_cog(cog)
            logger.info("Loaded cog: %s", type(cog).__name__)

        synced = await bot.tree.sync()
        logger.info("Synced %d app command(s) to Discord", len(synced))

    return bot
