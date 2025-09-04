# cogs/utility.py
import discord
from discord import app_commands
from discord.ext import commands

class Utility(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="ping", description="Verifica a latência do bot.")
    async def ping(self, interaction: discord.Interaction):
        """ Responde com o ping do bot. """
        latency = round(self.bot.latency * 1000)
        await interaction.response.send_message(f"Pong! 🏓 Latência: `{latency}ms`", ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(Utility(bot))