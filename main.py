import discord
import os
from dotenv import load_dotenv
import asyncio
from datetime import timedelta, datetime
import logging

# Charger les variables d'environnement
load_dotenv()

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    filename='/home/discord/discord-bot.log',  # Chemin où le log sera enregistré
    filemode='a',  # 'a' pour ajouter, 'w' pour écraser
    format='%(asctime)s - %(levelname)s - %(message)s'
    )

# Créer un bot sans commande manuelle
intents = discord.Intents.default()
client = discord.Client(intents=intents)

# ID des canaux (récupérés depuis les variables d'environnement)
CHANNEL_ID_DP = os.getenv('CHANNEL_ID_DP')  # ID du canal donjon-party pour le sondage et le message
CHANNEL_ID_BOSS = os.getenv('CHANNEL_ID_BOSS')  # ID du canal pour le message canal boss-event
CHANNEL_ID_SIEGE = os.getenv('CHANNEL_ID_SIEGE')  # ID du canal siege-raid pour le message du dimanche à 14:30

# Variables globales pour stocker les messages
poll_message = None
text_message = None
weekend_event_messages = []  # Liste pour garder une trace des messages envoyés pour les événements du week-end

# Fonction pour créer un sondage avec la nouvelle API Poll Resource
async def create_poll():
    global poll_message, text_message

    channel = client.get_channel(int(CHANNEL_ID_DP))

    if not channel:
        logging.error("Impossible de trouver le canal.")
        return

    poll = discord.Poll(
        question="Présence pour le 👥Donjon Party👥 du soir à 21h (heure de Paris) - 15h (heure du Québec).",  # Question du sondage
        duration=timedelta(hours=8)  # Durée de 8 heures
    )

    poll.add_answer(text="Oui", emoji="✅")
    poll.add_answer(text="Non", emoji="❌")

    poll_message = await channel.send(poll=poll)
    logging.info("Sondage créé avec succès !")

    text_message = await channel.send("⬆️⬆️⬆️⬆️⬆️⬆️⬆️⬆️⬆️@everyone⬆️⬆️⬆️⬆️⬆️⬆️⬆️⬆️⬆️")
    logging.info("Message texte créé avec succès !")

# Fonction générique pour gérer les événements (boss et siege)
async def send_event_message(channel_id, message_list, event_message):
    # ID du canal
    channel = client.get_channel(channel_id)
    if channel:
        try:
            # Supprimer les messages précédents de l'événement
            await delete_messages(message_list)
            # Envoyer un nouveau message
            message = await channel.send(event_message)
            message_list.append(message)  # Ajouter ce message à la liste
            logging.info(f"Message de l'événement envoyé avec succès dans le canal {channel_id} !")
        except discord.DiscordException as e:
            logging.error(f"Erreur lors de l'envoi du message de l'événement : {e}")

# Fonction pour supprimer les messages (sondage, texte, ou événement)
async def delete_messages(message_list):
    for msg in message_list:
        try:
            await msg.delete()
            logging.info(f"Message supprimé : {msg.id}")
        except discord.DiscordException as e:
            logging.error(f"Erreur lors de la suppression du message {msg.id} : {e}")

# Tâche pour envoyer un message tous les samedis et dimanches à 20:30 (événement boss)
async def send_boss_message():
    while True:
        now = datetime.now()

        if now.weekday() in [5, 6] and now.hour == 20 and now.minute == 30:
            await send_event_message(int(CHANNEL_ID_BOSS), weekend_event_messages, "⬆️⬆️⬆️⬆️⬆️⬆️⬆️⬆️@everyone⬆️⬆️⬆️⬆️⬆️⬆️⬆️⬆️")

        await asyncio.sleep(60)

# Tâche pour envoyer un message tous les dimanches à 14:30 (événement siege)
async def send_siege_message():
    while True:
        now = datetime.now()

        if now.weekday() == 6 and now.hour == 14 and now.minute == 30:
            await send_event_message(int(CHANNEL_ID_SIEGE), weekend_event_messages, "⬆️⬆️⬆️⬆️⬆️⬆️⬆️⬆️@everyone⬆️⬆️⬆️⬆️⬆️⬆️⬆️⬆️")

        await asyncio.sleep(60)

# Tâche qui crée le sondage et le message texte tous les jours à 18:00
async def poll_cycle():
    while True:
        now = datetime.now()

        if now.hour == 18 and now.minute == 0:
            await create_poll()  # Créer un nouveau sondage et message texte
            logging.info("Sondage et message texte créés à 18:00 !")

        await asyncio.sleep(60)

# Tâche pour supprimer le sondage et le message texte tous les jours à 00:00
async def delete_poll_messages():
    global poll_message, text_message
    while True:
        now = datetime.now()

        if now.hour == 0 and now.minute == 0:
            # Supprimer les messages du sondage et texte
            if poll_message or text_message:
                await delete_messages([poll_message, text_message])
                poll_message = None
                text_message = None

        await asyncio.sleep(60)

# Lorsque le bot est prêt, démarre les tâches nécessaires
@client.event
async def on_ready():
    logging.info(f"Bot connecté en tant que {client.user}")

    # Démarrer les tâches
    client.loop.create_task(send_boss_message())
    client.loop.create_task(send_siege_message())
    client.loop.create_task(poll_cycle())
    client.loop.create_task(delete_poll_messages())

# Lancer le bot avec le token
client.run(os.getenv('TOKEN_DISCORD'))  # Utilise la variable d'environnement TOKEN_DISCORD
