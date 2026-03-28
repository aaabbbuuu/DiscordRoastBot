"""HallOfShameCog — server-wide embarrassment leaderboard.

Provides the ``/hallofshame`` slash command that queries all stored messages
in the guild, scores each user by embarrassing-keyword density, and displays
the top 10 most embarrassing users with excerpts.
"""

from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING

import discord
from discord import app_commands
from discord.ext import commands

if TYPE_CHECKING:
    from roast_master.database import Database

logger = logging.getLogger(__name__)

# Keywords that count toward the embarrassment score.
_EMBARRASSING_KEYWORDS: list[str] = [
    "oops",
    "sorry",
    "my bad",
    "accidentally",
    "drunk",
    "cringe",
    "regret",
    "mistake",
    "fail",
    "stupid",
    "forgot",
    "confused",
    "help me",
]

# Pre-compiled pattern for efficient matching (case-insensitive).
_KEYWORD_PATTERN: re.Pattern[str] = re.compile(
    "|".join(re.escape(kw) for kw in _EMBARRASSING_KEYWORDS),
    re.IGNORECASE,
)

# Maximum excerpt length shown per user in the embed.
_MAX_EXCERPT_LENGTH: int = 80


class HallOfShameCog(commands.Cog):
    """Slash command for the server-wide Hall of Shame leaderboard."""

    def __init__(self, bot: commands.Bot, db: Database) -> None:
        self.bot = bot
        self.db = db

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _count_keywords(text: str) -> int:
        """Return the number of embarrassing keyword occurrences in *text*."""
        return len(_KEYWORD_PATTERN.findall(text))

    @staticmethod
    def _truncate(text: str, max_len: int = _MAX_EXCERPT_LENGTH) -> str:
        """Truncate *text* to *max_len* characters, adding ellipsis if needed."""
        if len(text) <= max_len:
            return text
        return text[: max_len - 1] + "…"

    # ------------------------------------------------------------------
    # /hallofshame
    # ------------------------------------------------------------------

    @app_commands.command(
        name="hallofshame",
        description="Top 10 most embarrassing users in this server",
    )
    async def hallofshame(self, interaction: discord.Interaction) -> None:
        """Score every user in the guild by embarrassing-keyword density and display the top 10."""
        guild_id = str(interaction.guild_id)

        await interaction.response.defer()

        try:
            # Fetch all messages for this guild directly from the DB.
            assert self.db._db is not None
            cursor = await self.db._db.execute(
                "SELECT user_id, content FROM messages WHERE guild_id = ?",
                (guild_id,),
            )
            rows = await cursor.fetchall()

            if not rows:
                await interaction.followup.send(
                    "📭 No messages stored for this server yet — start chatting!"
                )
                return

            # Accumulate per-user stats: total messages, keyword hits,
            # and the single most embarrassing message (highest hit count).
            user_stats: dict[str, dict] = {}
            for row in rows:
                uid: str = row["user_id"]
                content: str = row["content"]
                hits = self._count_keywords(content)

                if uid not in user_stats:
                    user_stats[uid] = {
                        "total": 0,
                        "hits": 0,
                        "worst_msg": "",
                        "worst_hits": 0,
                    }

                entry = user_stats[uid]
                entry["total"] += 1
                entry["hits"] += hits

                if hits > entry["worst_hits"]:
                    entry["worst_hits"] = hits
                    entry["worst_msg"] = content

            # Compute density (hits / total) and sort descending.
            scored: list[tuple[str, float, str]] = []
            for uid, data in user_stats.items():
                if data["hits"] == 0:
                    continue
                density = data["hits"] / data["total"]
                scored.append((uid, density, data["worst_msg"]))

            scored.sort(key=lambda t: t[1], reverse=True)
            top = scored[:10]

            if not top:
                await interaction.followup.send(
                    "😇 This server is squeaky clean — no embarrassing moments found!"
                )
                return

            # Build the embed.
            lines: list[str] = []
            for rank, (uid, density, worst) in enumerate(top, start=1):
                # Resolve display name
                display_name = f"User {uid}"
                user = self.bot.get_user(int(uid))
                if user is None:
                    try:
                        user = await self.bot.fetch_user(int(uid))
                    except discord.NotFound:
                        user = None
                if user is not None:
                    display_name = user.display_name

                excerpt = self._truncate(worst)
                lines.append(
                    f"**{rank}.** {display_name} — score: {density:.2f}\n"
                    f"  _\"{excerpt}\"_"
                )

            embed = discord.Embed(
                title="🏆 Hall of Shame",
                description="\n\n".join(lines),
                color=discord.Color.dark_red(),
            )
            embed.set_footer(
                text="Score = embarrassing keywords per message"
            )

            logger.info(
                "/hallofshame guild=%s ranked=%d",
                guild_id,
                len(top),
            )
            await interaction.followup.send(embed=embed)
        except Exception:
            logger.exception("Error generating hall of shame for guild %s", guild_id)
            await interaction.followup.send(
                "❌ Something went wrong building the Hall of Shame. Try again later."
            )
