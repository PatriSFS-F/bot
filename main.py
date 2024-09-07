import discord
from discord.ext import commands
import os
import webserver
import logging
import asyncio
from discord.errors import HTTPException

# Configuração do bot com intents ativados
intents = discord.Intents.default()
intents.presences = True
intents.messages = True
intents.guilds = True
intents.message_content = True
intents.members = True
intents.dm_messages = True

# Configurações do bot
TOKEN = os.environ.get('discordkey')
ROLE_NAME = '📺⠂Ao vivo'
STREAMER_ROLE_NAME = 'Streamer'
KEYWORDS = ['Code', 'CODE', 'code', 'CodeRp', '[CodeRp]']
ALLOWED_GUILD_ID = 1249889579041820823

# dev e Gaucheira
AUTHORIZED_USERS = [757934740308361247, 691679550140055573]
TARGET_CHANNEL_ID = 1257959837866786868

logging.basicConfig(filename='bot.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('discord')

bot = commands.Bot(command_prefix='$', intents=intents)

# Função para lidar com rate limits
async def handle_rate_limit(retry_after):
    logger.warning(f'Rate limited! Aguardando {retry_after:.2f} segundos.')
    await asyncio.sleep(retry_after)

@bot.event
async def on_guild_join(guild):
    if guild.id != ALLOWED_GUILD_ID:
        await guild.leave()  # Faz o bot sair de outros servidores não autorizados
        logger.info(f'Saiu do servidor não autorizado: {guild.name} (ID: {guild.id})')

# Função de inicialização
@bot.event
async def on_ready():
    print(f'Bot {bot.user} está online!')

def contains_keyword(activity_name):
    """Verifica se a atividade contém qualquer palavra-chave da lista."""
    return any(keyword in (activity_name or '') for keyword in KEYWORDS)

# permite mandar mensagem em um canal especifico
@bot.event
async def on_message(message):
    if isinstance(message.channel, discord.DMChannel) and not message.author.bot:
        if message.author.id in AUTHORIZED_USERS:
            target_channel = bot.get_channel(TARGET_CHANNEL_ID)
            if target_channel:
                try:
                    await target_channel.send(f"{message.content}")
                    logger.info(f'Redirecionou mensagem privada de {message.author} para o canal {target_channel.name}.')
                except HTTPException as e:
                    if e.code == 429:  # Rate limit
                        await handle_rate_limit(e.retry_after)
                    else:
                        logger.error(f'Erro ao enviar mensagem: {e}')
            else:
                logger.error(f'Canal com ID {TARGET_CHANNEL_ID} não encontrado.')
        else:
            logger.warning(f'{message.author} tentou enviar uma mensagem, mas não está autorizado.')

    await bot.process_commands(message)

@bot.command(name='teste')
async def teste(ctx):
    logger.info(f'Comando "teste" chamado por {ctx.author.id}.')
    if ctx.author.id in AUTHORIZED_USERS:
        await ctx.send(f"{ctx.author.display_name} está ao vivo! Assista em https://www.youtube.com/watch?v=KYimxdQlogg")
    else:
        await ctx.send("Você não tem permissão para usar este comando.")

# Função para gerenciar cargos de streaming ao vivo
@bot.event
async def on_presence_update(before, after):
    guild = after.guild

    if before.activities == after.activities:  # Sem mudança nas atividades
        return

    role = discord.utils.get(guild.roles, name=ROLE_NAME)
    streamer_role = discord.utils.get(guild.roles, name=STREAMER_ROLE_NAME)

    if role and streamer_role and streamer_role in after.roles:
        streaming_activity = next((activity for activity in after.activities if activity.type == discord.ActivityType.streaming and contains_keyword(activity.name)), None)

        if streaming_activity and role not in after.roles:
            try:
                await after.add_roles(role)
                print(f'Cargo "{ROLE_NAME}" atribuído a {after.display_name}')
                target_channel = bot.get_channel(TARGET_CHANNEL_ID)
                if target_channel:
                    message = f"{after.display_name} está ao vivo! Assista em {streaming_activity.url}" if streaming_activity.url else f"{after.display_name} está ao vivo! Link não disponível"
                    try:
                        await target_channel.send(message)
                        logger.info(f'Mensagem enviada: {message}')
                    except HTTPException as e:
                        if e.code == 429:  # Rate limit
                            await handle_rate_limit(e.retry_after)
                        else:
                            logger.error(f'Erro ao enviar mensagem ao canal: {e}')
                else:
                    logger.error(f'Canal com ID {TARGET_CHANNEL_ID} não encontrado.')
            except discord.Forbidden:
                logger.error(f'Permissões insuficientes para atribuir o cargo "{ROLE_NAME}" a {after.display_name}.')
            except discord.HTTPException as e:
                logger.error(f'Erro ao atribuir o cargo: {e}')
        elif not streaming_activity and role in after.roles:
            try:
                await after.remove_roles(role)
                print(f'Cargo "{ROLE_NAME}" removido de {after.display_name}')
            except discord.Forbidden:
                logger.error(f'Permissões insuficientes para remover o cargo "{ROLE_NAME}" de {after.display_name}.')
            except discord.HTTPException as e:
                logger.error(f'Erro ao remover o cargo: {e}')
    else:
        print('Nenhuma ação necessária.')

# Mantém o bot ativo
webserver.keep_alive()

# Inicializa o bot
bot.run(TOKEN)
