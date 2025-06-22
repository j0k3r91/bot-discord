import discord
import os
from dotenv import load_dotenv
import asyncio
from datetime import timedelta, datetime
from discord.ext import commands, tasks
import logging
from zoneinfo import ZoneInfo  # Python 3.9+ (ou utilisez pytz pour versions antérieures)

# Charger les variables d'environnement
load_dotenv()

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    filename='/home/discord/discord-bot.log',
    filemode='a',
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Constantes
POLL_CREATION_HOUR = 18
POLL_CREATION_MINUTE = 0
POLL_DELETION_HOUR = 0
POLL_DELETION_MINUTE = 0
BOSS_EVENT_HOUR = 20
BOSS_EVENT_MINUTE = 30
SIEGE_EVENT_HOUR = 14
SIEGE_EVENT_MINUTE = 30
TIMEZONE = "Europe/Paris"

class BotState:
    """Classe pour encapsuler l'état du bot"""
    def __init__(self):
        self.poll_message = None
        self.text_message = None
        self.weekend_event_messages = []

# Créer le bot avec les intents nécessaires
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Instance de l'état du bot
bot_state = BotState()

# Vérification et récupération des variables d'environnement
def get_env_variables():
    """Récupère et valide les variables d'environnement"""
    required_vars = {
        'TOKEN_DISCORD': os.getenv('TOKEN_DISCORD'),
        'CHANNEL_ID_DP': os.getenv('CHANNEL_ID_DP'),
        'CHANNEL_ID_BOSS': os.getenv('CHANNEL_ID_BOSS'),
        'CHANNEL_ID_SIEGE': os.getenv('CHANNEL_ID_SIEGE')
    }
    
    for var_name, var_value in required_vars.items():
        if not var_value:
            logging.error(f"Variable d'environnement {var_name} non définie dans .env")
            raise ValueError(f"Variable d'environnement manquante: {var_name}")
    
    return required_vars

# Récupérer les variables d'environnement
try:
    env_vars = get_env_variables()
    CHANNEL_ID_DP = int(env_vars['CHANNEL_ID_DP'])
    CHANNEL_ID_BOSS = int(env_vars['CHANNEL_ID_BOSS'])
    CHANNEL_ID_SIEGE = int(env_vars['CHANNEL_ID_SIEGE'])
    TOKEN_DISCORD = env_vars['TOKEN_DISCORD']
except (ValueError, TypeError) as e:
    logging.error(f"Erreur de configuration: {e}")
    exit(1)

def get_current_time():
    """Retourne l'heure actuelle dans le timezone configuré"""
    return datetime.now(ZoneInfo(TIMEZONE))

async def create_poll():
    """Créer un sondage avec la nouvelle API Poll Resource"""
    global bot_state

    channel = bot.get_channel(CHANNEL_ID_DP)
    if not channel:
        logging.error(f"Impossible de trouver le canal {CHANNEL_ID_DP}.")
        return

    try:
        # Supprimer les anciens messages s'ils existent
        await delete_poll_messages()

        poll = discord.Poll(
            question="Présence pour le 👥Donjon Party👥 du soir à 21h (heure de Paris) - 15h (heure du Québec).",
            duration=timedelta(hours=8)
        )

        poll.add_answer(text="Oui", emoji="✅")
        poll.add_answer(text="Non", emoji="❌")

        bot_state.poll_message = await channel.send(poll=poll)
        logging.info("Sondage créé avec succès !")

        bot_state.text_message = await channel.send("⬆️⬆️⬆️⬆️⬆️⬆️⬆️⬆️⬆️@everyone⬆️⬆️⬆️⬆️⬆️⬆️⬆️⬆️⬆️")
        logging.info("Message texte créé avec succès !")

    except discord.DiscordException as e:
        logging.error(f"Erreur lors de la création du sondage : {e}")

async def send_event_message(channel_id, message_list, event_message):
    """Fonction générique pour gérer les événements (boss et siege)"""
    channel = bot.get_channel(channel_id)
    if not channel:
        logging.error(f"Impossible de trouver le canal {channel_id}.")
        return

    try:
        # Supprimer les messages précédents de l'événement
        await delete_messages(message_list)
        
        # Envoyer un nouveau message
        message = await channel.send(event_message)
        message_list.append(message)
        logging.info(f"Message de l'événement envoyé avec succès dans le canal {channel_id} !")
        
    except discord.DiscordException as e:
        logging.error(f"Erreur lors de l'envoi du message de l'événement : {e}")

async def delete_messages(message_list):
    """Supprimer une liste de messages"""
    for msg in message_list[:]:  # Copie pour éviter les modifications durant l'itération
        if msg:
            try:
                await msg.delete()
                message_list.remove(msg)
                logging.info(f"Message supprimé : {msg.id}")
            except discord.DiscordException as e:
                logging.error(f"Erreur lors de la suppression du message {msg.id if msg else 'None'} : {e}")

async def delete_poll_messages():
    """Supprimer les messages de sondage et texte"""
    global bot_state
    
    messages_to_delete = []
    if bot_state.poll_message:
        messages_to_delete.append(bot_state.poll_message)
    if bot_state.text_message:
        messages_to_delete.append(bot_state.text_message)
    
    if messages_to_delete:
        await delete_messages(messages_to_delete)
        bot_state.poll_message = None
        bot_state.text_message = None

@tasks.loop(minutes=1)
async def schedule_checker():
    """Vérificateur de planning principal"""
    now = get_current_time()
    
    # Création du sondage quotidien à 18:00
    if now.hour == POLL_CREATION_HOUR and now.minute == POLL_CREATION_MINUTE:
        await create_poll()
        logging.info("Sondage et message texte créés à 18:00 !")
    
    # Suppression du sondage quotidien à 00:00
    elif now.hour == POLL_DELETION_HOUR and now.minute == POLL_DELETION_MINUTE:
        await delete_poll_messages()
        logging.info("Messages de sondage supprimés à 00:00 !")
    
    # Événement boss les samedis et dimanches à 20:30
    elif (now.weekday() in [5, 6] and 
          now.hour == BOSS_EVENT_HOUR and 
          now.minute == BOSS_EVENT_MINUTE):
        await send_event_message(
            CHANNEL_ID_BOSS, 
            bot_state.weekend_event_messages, 
            "⬆️⬆️⬆️⬆️⬆️⬆️⬆️⬆️@everyone⬆️⬆️⬆️⬆️⬆️⬆️⬆️⬆️"
        )
        logging.info("Message boss envoyé pour le week-end !")
    
    # Événement siege les dimanches à 14:30
    elif (now.weekday() == 6 and 
          now.hour == SIEGE_EVENT_HOUR and 
          now.minute == SIEGE_EVENT_MINUTE):
        await send_event_message(
            CHANNEL_ID_SIEGE, 
            bot_state.weekend_event_messages, 
            "⬆️⬆️⬆️⬆️⬆️⬆️⬆️⬆️@everyone⬆️⬆️⬆️⬆️⬆️⬆️⬆️⬆️"
        )
        logging.info("Message siege envoyé pour le dimanche !")

@schedule_checker.before_loop
async def before_schedule_checker():
    """Attendre que le bot soit prêt avant de démarrer les tâches"""
    await bot.wait_until_ready()

@bot.event
async def on_ready():
    """Événement déclenché quand le bot est prêt"""
    logging.info(f"Bot connecté en tant que {bot.user}")
    
    # Démarrer le vérificateur de planning
    if not schedule_checker.is_running():
        schedule_checker.start()
        logging.info("Tâches de planning démarrées !")

@bot.event
async def on_error(event, *args, **kwargs):
    """Gestionnaire d'erreurs global"""
    logging.error(f"Erreur dans l'événement {event}: {args}, {kwargs}")

# Commande de test (optionnelle)
@bot.command(name='test')
@commands.has_permissions(administrator=True)
async def test_command(ctx):
    """Commande de test pour les administrateurs"""
    await ctx.send("Bot fonctionnel ! ✅")

@bot.command(name='status')
@commands.has_permissions(administrator=True)
async def status_command(ctx):
    """Affiche le statut du bot"""
    now = get_current_time()
    status_msg = f"""
**Statut du Bot** 🤖
Heure actuelle: {now.strftime('%H:%M:%S')}
Sondage actif: {'Oui' if bot_state.poll_message else 'Non'}
Messages d'événements: {len(bot_state.weekend_event_messages)}
Tâches actives: {'Oui' if schedule_checker.is_running() else 'Non'}
    """
    await ctx.send(status_msg)

# Gestionnaire d'erreur pour les commandes
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ Vous n'avez pas les permissions nécessaires.")
    else:
        logging.error(f"Erreur de commande: {error}")

if __name__ == "__main__":
    try:
        bot.run(TOKEN_DISCORD)
    except Exception as e:
        logging.error(f"Erreur critique lors du démarrage du bot: {e}")
