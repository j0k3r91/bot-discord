"""
Discord Event Management Bot
============================

Bot Discord professionnel pour la gestion automatisée d'événements,
sondages quotidiens et notifications de communauté gaming.

Author: j0k3r91
Version: 2.0
License: MIT
"""

import asyncio
import logging
import os
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Union
from dataclasses import dataclass

import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv
from zoneinfo import ZoneInfo

# ======================== CONFIGURATION ET CONSTANTES ========================

class EventType(Enum):
    """Types d'événements supportés"""
    BOSS = "boss"
    SIEGE = "siege"
    POLL = "poll"

class TimeSlot(Enum):
    """Créneaux horaires configurés"""
    POLL_CREATION = (18, 0)
    POLL_DELETION = (0, 0)
    BOSS_NOTIFICATION = (20, 30)
    SIEGE_NOTIFICATION = (14, 30)
    WEEKLY_UPDATE = (0, 0)

@dataclass
class BotConfiguration:
    """Configuration centralisée du bot"""
    # Tokens et IDs
    discord_token: str
    channel_dp: int
    channel_boss: int
    channel_siege: int
    
    # Configuration temporelle
    timezone: str = "Europe/Paris"
    weekly_update_day: int = 0  # Lundi
    
    # Templates de messages
    boss_template: str = """Présence pour l'événement Boss du weekend (samedi et dimanche) à 21h00 (heure de Paris) - 15h00 (heure du Québec).
Merci de venir 15 minutes avant l'événement.
{boss_links}"""
    
    siege_template: str = """Présence pour le siège du donjon de la Grotte de Cristal le dimanche à 15h00 (heure de Paris) - 9h00 (heure du Québec).
Merci de venir 15 minutes avant l'événement.
{siege_links}"""
    
    poll_question: str = "Présence pour le 👥Donjon Party👥 du soir à 21h (heure de Paris) - 15h (heure du Québec)."
    notification_message: str = "⬆️⬆️⬆️⬆️⬆️⬆️⬆️⬆️@everyone⬆️⬆️⬆️⬆️⬆️⬆️⬆️⬆️"
    
    # Filtres d'événements
    boss_keywords: List[str] = None
    siege_keywords: List[str] = None
    
    def __post_init__(self):
        if self.boss_keywords is None:
            self.boss_keywords = ["boss", "samedi", "dimanche"]
        if self.siege_keywords is None:
            self.siege_keywords = ["siège", "grotte", "cristal"]

class LoggerManager:
    """Gestionnaire de logging centralisé"""
    
    @staticmethod
    def setup_logging(log_file: str = '/home/discord/discord-bot.log') -> logging.Logger:
        """Configure le système de logging"""
        logging.basicConfig(
            level=logging.INFO,
            filename=log_file,
            filemode='a',
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            encoding='utf-8'
        )
        
        # Ajout d'un handler console pour le développement
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(formatter)
        
        logger = logging.getLogger(__name__)
        logger.addHandler(console_handler)
        
        return logger

# ======================== CLASSES DE GESTION ========================

@dataclass
class MessageState:
    """État des messages par type"""
    event_messages: List[discord.Message]
    notification_messages: List[discord.Message]
    
    def __post_init__(self):
        if not hasattr(self, 'event_messages'):
            self.event_messages = []
        if not hasattr(self, 'notification_messages'):
            self.notification_messages = []

class BotState:
    """Gestionnaire d'état centralisé du bot"""
    
    def __init__(self):
        # Messages de sondages
        self.poll_message: Optional[discord.Message] = None
        self.text_message: Optional[discord.Message] = None
        
        # Messages par type d'événement
        self.boss_state = MessageState([], [])
        self.siege_state = MessageState([], [])
        
        # Tracking des exécutions
        self.last_executions: Dict[str, Optional[Union[datetime, datetime.date]]] = {
            'poll_creation': None,
            'poll_deletion': None,
            'boss_event': None,
            'siege_event': None,
            'weekly_update': None
        }
        
        # Cache des événements
        self.cached_events: Dict[str, Dict] = {}
    
    def update_last_execution(self, action: str, timestamp: Union[datetime, datetime.date]) -> None:
        """Met à jour le timestamp d'une action"""
        self.last_executions[action] = timestamp
    
    def get_last_execution(self, action: str) -> Optional[Union[datetime, datetime.date]]:
        """Récupère le timestamp d'une action"""
        return self.last_executions.get(action)

class EventManager:
    """Gestionnaire d'événements Discord"""
    
    def __init__(self, bot: commands.Bot, config: BotConfiguration, logger: logging.Logger):
        self.bot = bot
        self.config = config
        self.logger = logger
    
    async def fetch_server_events(self) -> List[discord.ScheduledEvent]:
        """Récupère tous les événements du serveur"""
        try:
            guild = self.bot.guilds[0] if self.bot.guilds else None
            if not guild:
                self.logger.error("Aucun serveur trouvé pour le bot")
                return []

            events = await guild.fetch_scheduled_events()
            self.logger.info(f"Récupération de {len(events)} événement(s) sur {guild.name}")
            return events
            
        except discord.DiscordException as e:
            self.logger.error(f"Erreur lors de la récupération des événements: {e}")
            return []
    
    def construct_event_link(self, guild_id: int, event_id: int) -> str:
        """Construit le lien direct vers un événement"""
        return f"https://discord.com/events/{guild_id}/{event_id}"
    
    async def get_all_events(self) -> Dict[str, Dict]:
        """Récupère et formate tous les événements"""
        events = await self.fetch_server_events()
        if not events:
            return {}

        guild_id = events[0].guild.id
        formatted_events = {}

        for event in events:
            try:
                event_link = self.construct_event_link(guild_id, event.id)
                formatted_events[event.name] = {
                    'id': event.id,
                    'name': event.name,
                    'link': event_link,
                    'start_time': event.start_time,
                    'description': event.description,
                    'status': event.status.name
                }
                self.logger.debug(f"Événement traité: {event.name}")
                
            except Exception as e:
                self.logger.error(f"Erreur lors du traitement de l'événement {event.name}: {e}")
                continue

        return formatted_events
    
    def filter_events_by_criteria(self, events: Dict[str, Dict], 
                                 weekdays: List[int], keywords: List[str]) -> List[Dict]:
        """Filtre les événements selon des critères"""
        filtered = []
        
        for event_name, event_data in events.items():
            start_time = event_data.get('start_time')
            if not start_time:
                continue
                
            # Filtre par jour de la semaine
            if start_time.weekday() not in weekdays:
                continue
                
            # Filtre par mots-clés
            name_lower = event_name.lower()
            if any(keyword.lower() in name_lower for keyword in keywords):
                filtered.append(event_data)
                self.logger.info(f"Événement filtré: {event_name} (jour {start_time.weekday()})")
        
        return filtered

class MessageManager:
    """Gestionnaire de messages Discord"""
    
    def __init__(self, bot: commands.Bot, logger: logging.Logger):
        self.bot = bot
        self.logger = logger
    
    async def delete_messages(self, messages: List[discord.Message]) -> None:
        """Supprime une liste de messages"""
        for msg in messages[:]:
            if msg:
                try:
                    await msg.delete()
                    messages.remove(msg)
                    self.logger.info(f"Message supprimé: {msg.id}")
                except discord.DiscordException as e:
                    self.logger.error(f"Erreur suppression message {msg.id}: {e}")
    
    async def send_message(self, channel_id: int, content: str) -> Optional[discord.Message]:
        """Envoie un message dans un canal"""
        channel = self.bot.get_channel(channel_id)
        if not channel:
            self.logger.error(f"Canal {channel_id} introuvable")
            return None
        
        try:
            message = await channel.send(content)
            self.logger.info(f"Message envoyé dans le canal {channel_id}")
            return message
        except discord.DiscordException as e:
            self.logger.error(f"Erreur envoi message: {e}")
            return None
    
    async def send_poll(self, channel_id: int, question: str, 
                       duration: timedelta) -> Optional[discord.Message]:
        """Crée et envoie un sondage"""
        channel = self.bot.get_channel(channel_id)
        if not channel:
            self.logger.error(f"Canal {channel_id} introuvable")
            return None
        
        try:
            poll = discord.Poll(question=question, duration=duration)
            poll.add_answer(text="Oui", emoji="✅")
            poll.add_answer(text="Non", emoji="❌")
            
            message = await channel.send(poll=poll)
            self.logger.info(f"Sondage créé dans le canal {channel_id}")
            return message
        except discord.DiscordException as e:
            self.logger.error(f"Erreur création sondage: {e}")
            return None

class EventBot(commands.Bot):
    """Bot Discord principal avec logique métier"""
    
    def __init__(self):
        # Chargement de la configuration
        load_dotenv()
        self.config = self._load_configuration()
        self.logger = LoggerManager.setup_logging()
        
        # Initialisation du bot
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix='!', intents=intents)
        
        # Gestionnaires
        self.state = BotState()
        self.event_manager = EventManager(self, self.config, self.logger)
        self.message_manager = MessageManager(self, self.logger)
        
        self.logger.info("Bot initialisé avec succès")
    
    def _load_configuration(self) -> BotConfiguration:
        """Charge la configuration depuis les variables d'environnement"""
        required_vars = ['TOKEN_DISCORD', 'CHANNEL_ID_DP', 'CHANNEL_ID_BOSS', 'CHANNEL_ID_SIEGE']
        
        for var in required_vars:
            if not os.getenv(var):
                raise ValueError(f"Variable d'environnement manquante: {var}")
        
        return BotConfiguration(
            discord_token=os.getenv('TOKEN_DISCORD'),
            channel_dp=int(os.getenv('CHANNEL_ID_DP')),
            channel_boss=int(os.getenv('CHANNEL_ID_BOSS')),
            channel_siege=int(os.getenv('CHANNEL_ID_SIEGE'))
        )
    
    def get_current_time(self) -> datetime:
        """Retourne l'heure actuelle dans le timezone configuré"""
        return datetime.now(ZoneInfo(self.config.timezone))
    
    async def setup_hook(self) -> None:
        """Configuration initiale du bot"""
        self.logger.info("Configuration du bot...")
        await self.recover_existing_messages()
        await self.update_events_cache()
        
        # Démarrage des tâches automatiques
        if not self.schedule_checker.is_running():
            self.schedule_checker.start()
            self.logger.info("Planificateur démarré")
    
    # ======================== GESTION DES SONDAGES ========================
    
    async def create_daily_poll(self) -> None:
        """Crée le sondage quotidien"""
        try:
            # Suppression des anciens sondages
            await self.delete_poll_messages()
            
            # Création du nouveau sondage
            poll_msg = await self.message_manager.send_poll(
                self.config.channel_dp, 
                self.config.poll_question,
                timedelta(hours=8)
            )
            
            # Message d'accompagnement
            text_msg = await self.message_manager.send_message(
                self.config.channel_dp,
                self.config.notification_message
            )
            
            self.state.poll_message = poll_msg
            self.state.text_message = text_msg
            self.logger.info("Sondage quotidien créé avec succès")
            
        except Exception as e:
            self.logger.error(f"Erreur création sondage: {e}")
    
    async def delete_poll_messages(self) -> None:
        """Supprime les messages de sondage"""
        messages_to_delete = [
            msg for msg in [self.state.poll_message, self.state.text_message] 
            if msg is not None
        ]
        
        if messages_to_delete:
            await self.message_manager.delete_messages(messages_to_delete)
            self.state.poll_message = None
            self.state.text_message = None
    
    # ======================== GESTION DES ÉVÉNEMENTS ========================
    
    async def update_events_cache(self) -> Dict[str, Dict]:
        """Met à jour le cache des événements"""
        try:
            events = await self.event_manager.get_all_events()
            self.state.cached_events = events
            self.logger.info(f"Cache mis à jour: {len(events)} événement(s)")
            return events
        except Exception as e:
            self.logger.error(f"Erreur mise à jour cache: {e}")
            return {}
    
    async def update_boss_messages(self) -> None:
        """Met à jour les messages d'événements boss"""
        try:
            events = await self.event_manager.get_all_events()
            if not events:
                self.logger.info("Aucun événement pour mise à jour boss")
                return
            
            # Filtrage des événements boss
            boss_events = self.event_manager.filter_events_by_criteria(
                events, [5, 6], self.config.boss_keywords
            )
            
            if not boss_events:
                self.logger.info("Aucun événement boss trouvé")
                return
            
            # Nettoyage des anciens messages
            await self.message_manager.delete_messages(self.state.boss_state.event_messages)
            await self.message_manager.delete_messages(self.state.boss_state.notification_messages)
            
            # Séparation par jour
            saturday_events = [e for e in boss_events if e['start_time'].weekday() == 5]
            sunday_events = [e for e in boss_events if e['start_time'].weekday() == 6]
            
            # Création des nouveaux messages
            if saturday_events:
                saturday_links = "\n".join(e['link'] for e in saturday_events)
                content = self.config.boss_template.format(boss_links=saturday_links)
                
                msg = await self.message_manager.send_message(self.config.channel_boss, content)
                if msg:
                    self.state.boss_state.event_messages.append(msg)
                    self.logger.info(f"Message boss samedi créé")
            
            if sunday_events:
                sunday_links = "\n".join(e['link'] for e in sunday_events)
                msg = await self.message_manager.send_message(self.config.channel_boss, sunday_links)
                if msg:
                    self.state.boss_state.event_messages.append(msg)
                    self.logger.info(f"Message boss dimanche créé")
            
            self.logger.info("Mise à jour boss terminée avec succès")
            
        except Exception as e:
            self.logger.error(f"Erreur mise à jour boss: {e}")
    
    async def update_siege_messages(self) -> None:
        """Met à jour les messages d'événements siege"""
        try:
            events = await self.event_manager.get_all_events()
            if not events:
                self.logger.info("Aucun événement pour mise à jour siege")
                return
            
            # Filtrage des événements siege
            siege_events = self.event_manager.filter_events_by_criteria(
                events, [6], self.config.siege_keywords
            )
            
            if not siege_events:
                self.logger.info("Aucun événement siege trouvé")
                return
            
            # Nettoyage des anciens messages
            await self.message_manager.delete_messages(self.state.siege_state.event_messages)
            await self.message_manager.delete_messages(self.state.siege_state.notification_messages)
            
            # Création des nouveaux messages
            for event_data in siege_events:
                content = self.config.siege_template.format(siege_links=event_data['link'])
                msg = await self.message_manager.send_message(self.config.channel_siege, content)
                if msg:
                    self.state.siege_state.event_messages.append(msg)
                    self.logger.info(f"Message siege créé pour: {event_data['name']}")
            
            self.logger.info("Mise à jour siege terminée avec succès")
            
        except Exception as e:
            self.logger.error(f"Erreur mise à jour siege: {e}")
    
    async def send_notification(self, event_type: EventType) -> None:
        """Envoie une notification pour un type d'événement"""
        try:
            if event_type == EventType.BOSS:
                channel_id = self.config.channel_boss
                message_list = self.state.boss_state.notification_messages
            elif event_type == EventType.SIEGE:
                channel_id = self.config.channel_siege
                message_list = self.state.siege_state.notification_messages
            else:
                self.logger.error(f"Type d'événement non supporté: {event_type}")
                return
            
            # Suppression des anciennes notifications
            await self.message_manager.delete_messages(message_list)
            
            # Envoi de la nouvelle notification
            msg = await self.message_manager.send_message(channel_id, self.config.notification_message)
            if msg:
                message_list.append(msg)
                self.logger.info(f"Notification {event_type.value} envoyée")
                
        except Exception as e:
            self.logger.error(f"Erreur notification {event_type.value}: {e}")
    
    # ======================== PLANIFICATEUR ========================
    
    @tasks.loop(minutes=1)
    async def schedule_checker(self) -> None:
        """Vérificateur de planning principal"""
        now = self.get_current_time()
        current_date = now.date()
        current_datetime = now.replace(second=0, microsecond=0)
        
        try:
            # Création du sondage quotidien à 18:00
            if (now.hour, now.minute) == TimeSlot.POLL_CREATION.value:
                if self.state.get_last_execution('poll_creation') != current_date:
                    await self.create_daily_poll()
                    self.state.update_last_execution('poll_creation', current_date)
            
            # Suppression du sondage à 00:00
            if (now.hour, now.minute) == TimeSlot.POLL_DELETION.value:
                if self.state.get_last_execution('poll_deletion') != current_date:
                    await self.delete_poll_messages()
                    self.state.update_last_execution('poll_deletion', current_date)
            
            # Mise à jour hebdomadaire (lundi 00:00)
            if (now.weekday() == self.config.weekly_update_day and 
                (now.hour, now.minute) == TimeSlot.WEEKLY_UPDATE.value):
                if self.state.get_last_execution('weekly_update') != current_date:
                    await self.weekly_update()
                    self.state.update_last_execution('weekly_update', current_date)
            
            # Notifications boss (samedi/dimanche 20:30)
            elif (now.weekday() in [5, 6] and 
                  (now.hour, now.minute) == TimeSlot.BOSS_NOTIFICATION.value):
                if self.state.get_last_execution('boss_event') != current_datetime:
                    await self.send_notification(EventType.BOSS)
                    self.state.update_last_execution('boss_event', current_datetime)
            
            # Notification siege (dimanche 14:30)
            elif (now.weekday() == 6 and 
                  (now.hour, now.minute) == TimeSlot.SIEGE_NOTIFICATION.value):
                if self.state.get_last_execution('siege_event') != current_datetime:
                    await self.send_notification(EventType.SIEGE)
                    self.state.update_last_execution('siege_event', current_datetime)
                    
        except Exception as e:
            self.logger.error(f"Erreur dans le planificateur: {e}")
    
    @schedule_checker.before_loop
    async def before_schedule_checker(self) -> None:
        """Attendre que le bot soit prêt"""
        await self.wait_until_ready()
    
    async def weekly_update(self) -> None:
        """Mise à jour hebdomadaire complète"""
        self.logger.info("=== DÉBUT MISE À JOUR HEBDOMADAIRE ===")
        try:
            await self.update_events_cache()
            await self.update_boss_messages()
            await self.update_siege_messages()
            self.logger.info("=== MISE À JOUR HEBDOMADAIRE TERMINÉE ===")
        except Exception as e:
            self.logger.error(f"Erreur mise à jour hebdomadaire: {e}")
    
    # ======================== RÉCUPÉRATION MESSAGES ========================
    
    async def recover_existing_messages(self) -> None:
        """Récupère les messages existants au redémarrage"""
        try:
            # Récupération messages DP
            await self._recover_dp_messages()
            # Récupération messages Boss
            await self._recover_boss_messages()
            # Récupération messages Siege
            await self._recover_siege_messages()
            
            self.logger.info("Récupération des messages terminée")
            
        except Exception as e:
            self.logger.error(f"Erreur récupération messages: {e}")
    
    async def _recover_dp_messages(self) -> None:
        """Récupère les messages du canal DP"""
        channel = self.get_channel(self.config.channel_dp)
        if not channel:
            return
        
        async for message in channel.history(limit=50):
            if message.author == self.user:
                if message.poll and not self.state.poll_message:
                    self.state.poll_message = message
                    self.logger.info(f"Sondage récupéré: {message.id}")
                elif "⬆️⬆️⬆️" in message.content and not self.state.text_message:
                    self.state.text_message = message
                    self.logger.info(f"Message texte récupéré: {message.id}")
    
    async def _recover_boss_messages(self) -> None:
        """Récupère les messages du canal Boss"""
        channel = self.get_channel(self.config.channel_boss)
        if not channel:
            return
        
        async for message in channel.history(limit=10):
            if message.author == self.user:
                if "Présence pour l'événement Boss" in message.content:
                    self.state.boss_state.event_messages.append(message)
                    self.logger.info(f"Message boss (lien) récupéré: {message.id}")
                elif "⬆️⬆️⬆️" in message.content:
                    self.state.boss_state.notification_messages.append(message)
                    self.logger.info(f"Message boss (notif) récupéré: {message.id}")
    
    async def _recover_siege_messages(self) -> None:
        """Récupère les messages du canal Siege"""
        channel = self.get_channel(self.config.channel_siege)
        if not channel:
            return
        
        async for message in channel.history(limit=10):
            if message.author == self.user:
                if "Présence pour le siège" in message.content:
                    self.state.siege_state.event_messages.append(message)
                    self.logger.info(f"Message siege (lien) récupéré: {message.id}")
                elif "⬆️⬆️⬆️" in message.content:
                    self.state.siege_state.notification_messages.append(message)
                    self.logger.info(f"Message siege (notif) récupéré: {message.id}")

# ======================== COMMANDES BOT ========================

@EventBot.command(name='events')
@commands.has_permissions(administrator=True)
async def list_events(bot: EventBot, ctx: commands.Context) -> None:
    """Affiche tous les événements avec leurs liens"""
    try:
        events = await bot.update_events_cache()
        if not events:
            await ctx.send("Aucun événement trouvé.")
            return
        
        formatted_links = "**🎮 Liens des Événements 🎮**\n\n"
        for name, data in events.items():
            start_time = data['start_time']
            start_str = start_time.strftime('%d/%m à %H:%M') if start_time else 'Date non définie'
            formatted_links += f"**{name}**\n📅 {start_str}\n🔗 {data['link']}\n\n"
        
        # Gestion de la limite Discord
        if len(formatted_links) > 1900:
            chunks = [formatted_links[i:i+1900] for i in range(0, len(formatted_links), 1900)]
            for chunk in chunks:
                await ctx.send(chunk)
        else:
            await ctx.send(formatted_links)
            
    except Exception as e:
        bot.logger.error(f"Erreur commande events: {e}")
        await ctx.send("❌ Erreur lors de la récupération des événements.")

@EventBot.command(name='status')
@commands.has_permissions(administrator=True)
async def bot_status(bot: EventBot, ctx: commands.Context) -> None:
    """Affiche le statut complet du bot"""
    now = bot.get_current_time()
    status_msg = f"""
**🤖 Statut du Bot**
**Heure:** {now.strftime('%H:%M:%S (%d/%m/%Y)')}
**Sondage actif:** {'✅' if bot.state.poll_message else '❌'}
**Boss (liens/notifs):** {len(bot.state.boss_state.event_messages)}/{len(bot.state.boss_state.notification_messages)}
**Siege (liens/notifs):** {len(bot.state.siege_state.event_messages)}/{len(bot.state.siege_state.notification_messages)}
**Événements en cache:** {len(bot.state.cached_events)}
**Planificateur:** {'✅' if bot.schedule_checker.is_running() else '❌'}

**📅 Dernières exécutions:**
• Sondage créé: {bot.state.get_last_execution('poll_creation') or 'Jamais'}
• Sondage supprimé: {bot.state.get_last_execution('poll_deletion') or 'Jamais'}
• Notification boss: {bot.state.get_last_execution('boss_event') or 'Jamais'}
• Notification siege: {bot.state.get_last_execution('siege_event') or 'Jamais'}
• Mise à jour hebdo: {bot.state.get_last_execution('weekly_update') or 'Jamais'}
"""
    await ctx.send(status_msg)

@EventBot.command(name='force_poll')
@commands.has_permissions(administrator=True)
async def force_poll(bot: EventBot, ctx: commands.Context) -> None:
    """Force la création d'un sondage"""
    try:
        await bot.create_daily_poll()
        await ctx.send("✅ Sondage créé manuellement !")
        bot.logger.info(f"Sondage forcé par {ctx.author}")
    except Exception as e:
        bot.logger.error(f"Erreur force_poll: {e}")
        await ctx.send("❌ Erreur lors de la création du sondage.")

@EventBot.command(name='force_boss')
@commands.has_permissions(administrator=True)
async def force_boss(bot: EventBot, ctx: commands.Context) -> None:
    """Force l'envoi d'une notification boss"""
    try:
        await bot.send_notification(EventType.BOSS)
        await ctx.send("✅ Notification boss envoyée !")
        bot.logger.info(f"Notification boss forcée par {ctx.author}")
    except Exception as e:
        bot.logger.error(f"Erreur force_boss: {e}")
        await ctx.send("❌ Erreur lors de l'envoi de la notification.")

@EventBot.command(name='force_siege')
@commands.has_permissions(administrator=True)
async def force_siege(bot: EventBot, ctx: commands.Context) -> None:
    """Force l'envoi d'une notification siege"""
    try:
        await bot.send_notification(EventType.SIEGE)
        await ctx.send("✅ Notification siege envoyée !")
        bot.logger.info(f"Notification siege forcée par {ctx.author}")
    except Exception as e:
        bot.logger.error(f"Erreur force_siege: {e}")
        await ctx.send("❌ Erreur lors de l'envoi de la notification.")

@EventBot.command(name='update_all_links')
@commands.has_permissions(administrator=True)
async def update_all_links(bot: EventBot, ctx: commands.Context) -> None:
    """Force la mise à jour de tous les liens"""
    try:
        await bot.weekly_update()
        await ctx.send("✅ Tous les liens mis à jour !")
        bot.logger.info(f"Mise à jour complète forcée par {ctx.author}")
    except Exception as e:
        bot.logger.error(f"Erreur update_all_links: {e}")
        await ctx.send("❌ Erreur lors de la mise à jour.")

@EventBot.command(name='help_admin')
@commands.has_permissions(administrator=True)
async def help_admin(bot: EventBot, ctx: commands.Context) -> None:
    """Affiche l'aide administrateur"""
    help_msg = """
**🔧 Commandes Administrateur**

**📊 Consultation:**
• `!events` - Afficher tous les événements
• `!status` - Statut du bot

**⚡ Actions forcées:**
• `!force_poll` - Créer un sondage
• `!force_boss` - Notification boss
• `!force_siege` - Notification siege
• `!update_all_links` - Mettre à jour tous les liens

**⏰ Automatisations:**
• Lundi 00:00 → Mise à jour hebdomadaire
• Quotidien 18:00 → Sondage / 00:00 → Suppression
• Sam/Dim 20:30 → Notif boss / Dim 14:30 → Notif siege
"""
    await ctx.send(help_msg)

# ======================== GESTIONNAIRE D'ERREURS ========================

@EventBot.event
async def on_command_error(bot: EventBot, ctx: commands.Context, error: Exception) -> None:
    """Gestionnaire d'erreurs global"""
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ Permissions insuffisantes.")
    elif isinstance(error, commands.CommandNotFound):
        pass  # Ignorer les commandes inconnues
    else:
        bot.logger.error(f"Erreur commande: {error}")
        await ctx.send("❌ Erreur lors de l'exécution.")

@EventBot.event
async def on_ready(bot: EventBot) -> None:
    """Événement de connexion du bot"""
    bot.logger.info(f"Bot connecté: {bot.user}")

# ======================== POINT D'ENTRÉE ========================

def main() -> None:
    """Point d'entrée principal"""
    try:
        bot = EventBot()
        bot.run(bot.config.discord_token)
    except Exception as e:
        print(f"Erreur critique: {e}")
        logging.error(f"Erreur critique: {e}")

if __name__ == "__main__":
    main()
