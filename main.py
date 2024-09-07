import discord
from discord.ext import commands
import os
import webserver
import logging

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
KEYWORDS = ['Code', 'CODE', 'code', 'CodeRp','[CodeRp]']
ALLOWED_GUILD_ID = 1249889579041820823

# dev e Gaucheira
AUTHORIZED_USERS = [757934740308361247, 691679550140055573]
TARGET_CHANNEL_ID = 1257959837866786868

logging.basicConfig(filename='bot.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('discord')

bot = commands.Bot(command_prefix='$', intents=intents)

@bot.event
async def on_guild_join(guild):
    if guild.id != ALLOWED_GUILD_ID:
        await guild.leave()  # Faz o bot sair de outros servidores
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
    # Verifica se a mensagem foi enviada em um DM e se o autor não é um bot
    if isinstance(message.channel, discord.DMChannel) and not message.author.bot:
        # Verifica se o autor está na lista de usuários autorizados
        if message.author.id in AUTHORIZED_USERS:
            target_channel = bot.get_channel(TARGET_CHANNEL_ID)
            if target_channel:
                await target_channel.send(f"{message.content}")
                logger.info(f'Redirecionou mensagem privada de {message.author} para o canal {target_channel.name}.')
            else:
                logger.error(f'Canal com ID {TARGET_CHANNEL_ID} não encontrado.')
        else:
            logger.warning(f'{message.author} tentou enviar uma mensagem, mas não está autorizado.')
    
    # Permite que outros comandos sejam processados
    await bot.process_commands(message)

@bot.command(name='teste')
async def teste(ctx):
    logger.info(f'Comando "teste" chamado por {ctx.author.id}.')
    if ctx.author.id in AUTHORIZED_USERS:
        logger.info(f'{ctx.author.display_name} está autorizado a usar o comando teste.')
        await ctx.send(f"{ctx.author.display_name} está ao vivo! Assista em https://www.youtube.com/watch?v=KYimxdQlogg")
    else:
        await ctx.send("Você não tem permissão para usar este comando.")


# Função para dar cargo a streamer quando tiverem ao vivo e no CodeRP
@bot.event
async def on_presence_update(before, after):
    guild = after.guild
    
    # Verifica se o usuário começou ou parou de fazer live
    if before.activities != after.activities:
        role = discord.utils.get(guild.roles, name=ROLE_NAME)
        streamer_role = discord.utils.get(guild.roles, name=STREAMER_ROLE_NAME)

        # Checa se o usuário tem o cargo "Streamer" e está transmitindo ao vivo
        if role and streamer_role and streamer_role in after.roles:
            # Verifica se a atividade é um streaming e contém qualquer palavra-chave
            if any(activity.type == discord.ActivityType.streaming and contains_keyword(activity.name) for activity in after.activities):
                # Atribui o cargo se estiver em live com a palavra-chave no nome
                if role not in after.roles:
                    try:
                        await after.add_roles(role)

                        print(f'Cargo "{ROLE_NAME}" atribuído a {after.display_name}')
                        
                        # Envia a mensagem para o canal específico
                        target_channel = bot.get_channel(TARGET_CHANNEL_ID)
                        if target_channel:
                            # Encontre a atividade de streaming com URL
                            activity = next((a for a in after.activities if a.type == discord.ActivityType.streaming), None)
                            if activity and activity.url:
                                message = f"{after.display_name} está ao vivo! Assista em {activity.url}"
                            else:
                                message = f"{after.display_name} está ao vivo! Link não disponível"
                            await target_channel.send(message)
                            logger.info(f'Mensagem enviada para o canal {target_channel.name}: {message}')
                        else:
                            logger.error(f'Canal com ID {TARGET_CHANNEL_ID} não encontrado.')
                        
                    except discord.Forbidden:
                        print(f'Permissões insuficientes para atribuir o cargo "{ROLE_NAME}" a {after.display_name}.')
                    except discord.HTTPException as e:
                        print(f'Ocorreu um erro ao atribuir o cargo: {e}')
            else:
                # Remove o cargo se não estiver mais em live ou se a atividade não contém a palavra-chave
                if any(activity.type == discord.ActivityType.streaming for activity in before.activities) and not any(activity.type == discord.ActivityType.streaming and contains_keyword(activity.name) for activity in after.activities):
                    if role in after.roles:
                        try:
                            await after.remove_roles(role)
                            print(f'Cargo "{ROLE_NAME}" removido de {after.display_name}')
                        except discord.Forbidden:
                            print(f'Permissões insuficientes para remover o cargo "{ROLE_NAME}" de {after.display_name}.')
                        except discord.HTTPException as e:
                            print(f'Ocorreu um erro ao remover o cargo: {e}')
        else:
            print('checando atividade...')

#  mantem ele ativo
webserver.keep_alive()
# Inicializa o bot
bot.run(TOKEN)


