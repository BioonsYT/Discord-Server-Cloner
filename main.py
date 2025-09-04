# main.py
import os
import asyncio
import discord
from discord.ext import commands
from dotenv import load_dotenv

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# Define as intenções (Intents) do bot.
# Precisamos de permissões amplas para ler e escrever a estrutura do servidor.
intents = discord.Intents.all()

# Cria a classe principal do Bot
class ClonadorBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="/", intents=intents)

    async def setup_hook(self):
        """ Carrega os cogs (módulos de comandos) automaticamente. """
        print("Carregando módulos (cogs)...")
        for filename in os.listdir('./cogs'):
            if filename.endswith('.py') and not filename.startswith('__'):
                try:
                    await self.load_extension(f'cogs.{filename[:-3]}')
                    print(f"  -> Módulo '{filename}' carregado com sucesso.")
                except Exception as e:
                    print(f"  -> Falha ao carregar o módulo '{filename}': {e}")
        
        # Sincroniza os comandos de barra com o Discord.
        # Pode levar alguns minutos para os comandos aparecerem pela primeira vez.
        await self.tree.sync()
        print("Comandos de barra sincronizados.")

    async def on_ready(self):
        print(f'Bot conectado como {self.user.name} (ID: {self.user.id})')
        print(f'Pronto para clonar servidores!')
        print('------')

async def main():
    bot = ClonadorBot()
    await bot.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())