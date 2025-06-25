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
    """Classe pour encapsuler l'état du bot avec améliorations"""
    def __init__(self):
        self.poll_message = None
        self.text_message = None
        # Séparer les messages d'événements
        self.boss_event_messages = []
        self.siege_event_messages = []
        # Tracking des dernières exécutions pour éviter les doublons
        self.last_poll_creation = None
        self.last_poll_deletion = None
        self.last_boss_event = None
        self.last_siege_event = None
        # Nouveau: stockage des liens d'événements
        self.cached_event_links = {}

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

# ======================== FONCTIONS POUR LES ÉVÉNEMENTS (CORRIGÉES) ========================

async def get_server_events():
    """Récupère tous les événements programmés du serveur"""
    try:
        guild = bot.guilds[0] if bot.guilds else None  # Premier serveur du bot
        if not guild:
            logging.error("Aucun serveur trouvé pour le bot")
            return []

        events = await guild.fetch_scheduled_events()
        logging.info(f"Trouvé {len(events)} événement(s) sur le serveur {guild.name}")
        return events
    
    except discord.DiscordException as e:
        logging.error(f"Erreur lors de la récupération des événements: {e}")
        return []

def construct_event_link(guild_id, event_id):
    """Construit le lien Discord pour un événement"""
    return f"https://discord.com/events/{guild_id}/{event_id}"

async def get_all_events():
    """Récupère TOUS les événements du serveur sans filtrage"""
    events = await get_server_events()
    if not events:
        return {}

    guild_id = events[0].guild.id if events else None
    all_events = {}

    for event in events:
        try:
            event_link = construct_event_link(guild_id, event.id)
            all_events[event.name] = {
                'id': event.id,
                'name': event.name,
                'link': event_link,
                'start_time': event.start_time,
                'description': event.description,
                'status': event.status.name
            }
            logging.info(f"Événement trouvé: {event.name} -> {event_link}")
        except Exception as e:
            logging.error(f"Erreur lors du traitement de l'événement {event.name}: {e}")
            continue

    return all_events

async def update_event_links_cache():
    """Met à jour le cache des liens d'événements"""
    try:
        events = await get_all_events()
        bot_state.cached_event_links = events
        logging.info(f"Cache des événements mis à jour: {len(events)} événement(s)")
        return events
    except Exception as e:
        logging.error(f"Erreur lors de la mise à jour du cache: {e}")
        return {}

async def get_event_links_formatted():
    """Retourne les liens d'événements dans un format lisible"""
    events = await update_event_links_cache()
    
    if not events:
        return "Aucun événement trouvé."
    
    formatted_links = "**🎮 Liens des Événements 🎮**\n\n"
    
    for event_name, event_data in events.items():
        start_time = event_data['start_time']
        start_str = start_time.strftime('%d/%m à %H:%M') if start_time else 'Date non définie'
        
        formatted_links += f"**{event_name}**\n"
        formatted_links += f"📅 {start_str}\n"
        formatted_links += f"🔗 {event_data['link']}\n\n"
    
    return formatted_links

# ======================== ANCIENNES FONCTIONS (inchangées) ========================

async def recover_existing_messages():
    """Récupère les messages existants au redémarrage du bot"""
    try:
        # Récupérer les sondages existants
        dp_channel = bot.get_channel(CHANNEL_ID_DP)
        if dp_channel:
            async for message in dp_channel.history(limit=50):
                if message.author == bot.user:
                    if message.poll and not bot_state.poll_message:
                        bot_state.poll_message = message
                        logging.info(f"Sondage récupéré: {message.id}")
                    elif "⬆️⬆️⬆️" in message.content and not bot_state.text_message:
                        bot_state.text_message = message
                        logging.info(f"Message texte récupéré: {message.id}")
        
        # Récupérer les messages d'événements boss
        boss_channel = bot.get_channel(CHANNEL_ID_BOSS)
        if boss_channel:
            async for message in boss_channel.history(limit=10):
                if message.author == bot.user and "⬆️⬆️⬆️" in message.content:
                    bot_state.boss_event_messages.append(message)
                    logging.info(f"Message boss récupéré: {message.id}")
        
        # Récupérer les messages d'événements siege
        siege_channel = bot.get_channel(CHANNEL_ID_SIEGE)
        if siege_channel:
            async for message in siege_channel.history(limit=10):
                if message.author == bot.user and "⬆️⬆️⬆️" in message.content:
                    bot_state.siege_event_messages.append(message)
                    logging.info(f"Message siege récupéré: {message.id}")
                    
        logging.info("Récupération des messages terminée")
        
    except Exception as e:
        logging.error(f"Erreur lors de la récupération des messages: {e}")

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

async def send_boss_event():
    """Gérer spécifiquement les événements boss"""
    await send_event_message(
        CHANNEL_ID_BOSS, 
        bot_state.boss_event_messages, 
        "⬆️⬆️⬆️⬆️⬆️⬆️⬆️⬆️@everyone⬆️⬆️⬆️⬆️⬆️⬆️⬆️⬆️"
    )

async def send_siege_event():
    """Gérer spécifiquement les événements siege"""
    await send_event_message(
        CHANNEL_ID_SIEGE, 
        bot_state.siege_event_messages, 
        "⬆️⬆️⬆️⬆️⬆️⬆️⬆️⬆️@everyone⬆️⬆️⬆️⬆️⬆️⬆️⬆️⬆️"
    )

async def send_event_message(channel_id, message_list, event_message):
    """Fonction générique pour gérer les événements"""
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
    """Vérificateur de planning principal avec protection contre les doublons"""
    now = get_current_time()
    current_date = now.date()
    current_datetime = now.replace(second=0, microsecond=0)  # Pour comparaison précise
    
    # Création du sondage quotidien à 18:00 (avec protection doublon)
    if (now.hour == POLL_CREATION_HOUR and now.minute == POLL_CREATION_MINUTE 
        and bot_state.last_poll_creation != current_date):
        await create_poll()
        bot_state.last_poll_creation = current_date
        logging.info("Sondage et message texte créés à 18:00 !")
    
    # Suppression du sondage quotidien à 00:00 (avec protection doublon)
    elif (now.hour == POLL_DELETION_HOUR and now.minute == POLL_DELETION_MINUTE
          and bot_state.last_poll_deletion != current_date):
        await delete_poll_messages()
        bot_state.last_poll_deletion = current_date
        logging.info("Messages de sondage supprimés à 00:00 !")
    
    # Événement boss les samedis et dimanches à 20:30 (avec protection doublon)
    elif (now.weekday() in [5, 6] and 
          now.hour == BOSS_EVENT_HOUR and 
          now.minute == BOSS_EVENT_MINUTE and
          bot_state.last_boss_event != current_datetime):
        await send_boss_event()
        bot_state.last_boss_event = current_datetime
        logging.info("Message boss envoyé pour le week-end !")
    
    # Événement siege les dimanches à 14:30 (avec protection doublon)
    elif (now.weekday() == 6 and 
          now.hour == SIEGE_EVENT_HOUR and 
          now.minute == SIEGE_EVENT_MINUTE and
          bot_state.last_siege_event != current_datetime):
        await send_siege_event()
        bot_state.last_siege_event = current_datetime
        logging.info("Message siege envoyé pour le dimanche !")

@schedule_checker.before_loop
async def before_schedule_checker():
    """Attendre que le bot soit prêt avant de démarrer les tâches"""
    await bot.wait_until_ready()

@bot.event
async def on_ready():
    """Événement déclenché quand le bot est prêt"""
    logging.info(f"Bot connecté en tant que {bot.user}")
    
    # Récupérer les messages existants
    await recover_existing_messages()
    
    # Mettre à jour le cache des événements au démarrage
    await update_event_links_cache()
    
    # Démarrer le vérificateur de planning
    if not schedule_checker.is_running():
        schedule_checker.start()
        logging.info("Tâches de planning démarrées !")

@bot.event
async def on_error(event, *args, **kwargs):
    """Gestionnaire d'erreurs global"""
    logging.error(f"Erreur dans l'événement {event}: {args}, {kwargs}")

# ======================== COMMANDES POUR LES ÉVÉNEMENTS (CORRIGÉES) ========================

@bot.command(name='events')
@commands.has_permissions(administrator=True)
async def list_events(ctx):
    """Affiche tous les événements du serveur avec leurs liens"""
    formatted_links = await get_event_links_formatted()
    
    # Discord a une limite de 2000 caractères par message
    if len(formatted_links) > 1900:
        # Diviser en plusieurs messages si nécessaire
        chunks = [formatted_links[i:i+1900] for i in range(0, len(formatted_links), 1900)]
        for chunk in chunks:
            await ctx.send(chunk)
    else:
        await ctx.send(formatted_links)

@bot.command(name='update_events')
@commands.has_permissions(administrator=True)
async def update_events_cache(ctx):
    """Force la mise à jour du cache des événements"""
    events = await update_event_links_cache()
    await ctx.send(f"✅ Cache mis à jour ! {len(events)} événement(s) trouvé(s).")
    logging.info(f"Cache des événements mis à jour manuellement par {ctx.author}")

@bot.command(name='event_link')
@commands.has_permissions(administrator=True)
async def get_specific_event_link(ctx, *, event_name):
    """Récupère le lien d'un événement spécifique par son nom"""
    events = bot_state.cached_event_links
    
    # Recherche exacte d'abord
    if event_name in events:
        event_data = events[event_name]
        await ctx.send(f"**{event_name}**\n🔗 {event_data['link']}")
        return
    
    # Recherche partielle
    matching_events = []
    for name, data in events.items():
        if event_name.lower() in name.lower():
            matching_events.append((name, data))
    
    if matching_events:
        if len(matching_events) == 1:
            name, data = matching_events[0]
            await ctx.send(f"**{name}**\n🔗 {data['link']}")
        else:
            result = "**Plusieurs événements trouvés:**\n"
            for name, data in matching_events[:5]:  # Limiter à 5 résultats
                result += f"• **{name}**: {data['link']}\n"
            await ctx.send(result)
    else:
        await ctx.send(f"❌ Aucun événement trouvé contenant '{event_name}'")

# ======================== COMMANDES EXISTANTES (inchangées) ========================

@bot.command(name='test')
@commands.has_permissions(administrator=True)
async def test_command(ctx):
    """Commande de test pour les administrateurs"""
    await ctx.send("Bot fonctionnel ! ✅")

@bot.command(name='status')
@commands.has_permissions(administrator=True)
async def status_command(ctx):
    """Affiche le statut complet du bot"""
    now = get_current_time()
    status_msg = f"""
**Statut du Bot** 🤖
**Heure actuelle:** {now.strftime('%H:%M:%S (%d/%m/%Y)')}
**Sondage actif:** {'Oui' if bot_state.poll_message else 'Non'}
**Messages boss:** {len(bot_state.boss_event_messages)}
**Messages siege:** {len(bot_state.siege_event_messages)}
**Événements en cache:** {len(bot_state.cached_event_links)}
**Tâches actives:** {'Oui' if schedule_checker.is_running() else 'Non'}

**Dernières exécutions:**
• Sondage créé: {bot_state.last_poll_creation or 'Jamais'}
• Sondage supprimé: {bot_state.last_poll_deletion or 'Jamais'}
• Boss event: {bot_state.last_boss_event or 'Jamais'}
• Siege event: {bot_state.last_siege_event or 'Jamais'}
    """
    await ctx.send(status_msg)

@bot.command(name='force_poll')
@commands.has_permissions(administrator=True)
async def force_poll(ctx):
    """Force la création d'un sondage manuellement"""
    await create_poll()
    await ctx.send("✅ Sondage créé manuellement !")
    logging.info(f"Sondage créé manuellement par {ctx.author}")

@bot.command(name='force_boss')
@commands.has_permissions(administrator=True)
async def force_boss(ctx):
    """Force l'envoi d'un message boss"""
    await send_boss_event()
    await ctx.send("✅ Message boss envoyé manuellement !")
    logging.info(f"Message boss créé manuellement par {ctx.author}")

@bot.command(name='force_siege')
@commands.has_permissions(administrator=True)
async def force_siege(ctx):
    """Force l'envoi d'un message siege"""
    await send_siege_event()
    await ctx.send("✅ Message siege envoyé manuellement !")
    logging.info(f"Message siege créé manuellement par {ctx.author}")

@bot.command(name='clean_poll')
@commands.has_permissions(administrator=True)
async def clean_poll(ctx):
    """Nettoie les messages de sondage"""
    await delete_poll_messages()
    await ctx.send("✅ Messages de sondage nettoyés !")
    logging.info(f"Messages de sondage nettoyés par {ctx.author}")

@bot.command(name='clean_events')
@commands.has_permissions(administrator=True)
async def clean_events(ctx):
    """Nettoie tous les messages d'événements"""
    await delete_messages(bot_state.boss_event_messages)
    await delete_messages(bot_state.siege_event_messages)
    await ctx.send("✅ Messages d'événements nettoyés !")
    logging.info(f"Messages d'événements nettoyés par {ctx.author}")

@bot.command(name='clean_all')
@commands.has_permissions(administrator=True)
async def clean_all(ctx):
    """Nettoie tous les messages du bot"""
    await delete_poll_messages()
    await delete_messages(bot_state.boss_event_messages)
    await delete_messages(bot_state.siege_event_messages)
    await ctx.send("✅ Tous les messages nettoyés !")
    logging.info(f"Tous les messages nettoyés par {ctx.author}")

@bot.command(name='recover')
@commands.has_permissions(administrator=True)
async def recover_command(ctx):
    """Récupère les messages existants manuellement"""
    await recover_existing_messages()
    await ctx.send("✅ Récupération des messages terminée !")
    logging.info(f"Récupération manuelle lancée par {ctx.author}")

@bot.command(name='help_admin')
@commands.has_permissions(administrator=True)
async def help_admin(ctx):
    """Affiche l'aide pour les commandes administrateur"""
    help_msg = """
**Commandes Administrateur** 🔧

**Gestion des sondages:**
• `!force_poll` - Créer un sondage manuellement
• `!clean_poll` - Supprimer les messages de sondage

**Gestion des événements:**
• `!force_boss` - Envoyer un message boss
• `!force_siege` - Envoyer un message siege
• `!clean_events` - Supprimer tous les messages d'événements

**Gestion des liens d'événements:**
• `!events` - Afficher tous les événements avec liens
• `!update_events` - Mettre à jour le cache des événements
• `!event_link <nom>` - Récupérer le lien d'un événement spécifique

**Utilitaires:**
• `!status` - Voir le statut du bot
• `!recover` - Récupérer les messages existants
• `!clean_all` - Nettoyer tous les messages
• `!test` - Test de fonctionnement
    """
    await ctx.send(help_msg)

# Gestionnaire d'erreur pour les commandes
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ Vous n'avez pas les permissions nécessaires.")
    elif isinstance(error, commands.CommandNotFound):
        # Ignorer les commandes inconnues pour éviter le spam
        pass
    else:
        logging.error(f"Erreur de commande: {error}")
        await ctx.send("❌ Une erreur s'est produite lors de l'exécution de la commande.")

if __name__ == "__main__":
    try:
        bot.run(TOKEN_DISCORD)
    except Exception as e:
        logging.error(f"Erreur critique lors du démarrage du bot: {e}")
