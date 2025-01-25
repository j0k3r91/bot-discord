import discord
import os
from dotenv import load_dotenv
import asyncio
from datetime import timedelta, datetime

# Charger les variables d'environnement
load_dotenv()

# Créer un bot sans commande manuelle
intents = discord.Intents.default()
client = discord.Client(intents=intents)

# ID des canaux (récupérés depuis les variables d'environnement)
CHANNEL_ID_DP = os.getenv('CHANNEL_ID_DP')  # ID du canal donjon-party pour le sondage et le message
CHANNEL_ID_BOSS = os.getenv('CHANNEL_ID_BOSS')  # ID du canal pour le message canal boss-event
CHANNEL_ID_SIEGE = os.getenv('CHANNEL_ID_SIEGE')  # ID du canal siege-raid pour le message du dimanche à 14:30

# Variables globales pour stocker le message du sondage et le message texte
poll_message = None
text_message = None

# Fonction pour créer un sondage avec la nouvelle API Poll Resource
async def create_poll():
    global poll_message, text_message

    # ID du canal où tu veux envoyer le sondage
    channel = client.get_channel(int(CHANNEL_ID_DP))

    if not channel:
        print("Impossible de trouver le canal.")
        return

    # Créer un sondage
    poll = discord.Poll(
        question="Présence pour le 👥Donjon Party👥 du soir à 21h (heure de Paris) - 15h (heure du Québec).",  # Question du sondage
        duration=timedelta(hours=8)  # Durée de 8 heures
    )

    # Ajouter les réponses possibles
    poll.add_answer(text="Oui", emoji="✅")
    poll.add_answer(text="Non", emoji="❌")

    # Envoyer le sondage dans le canal
    poll_message = await channel.send(poll=poll)
    print("Sondage créé avec succès !")

    # Envoyer le message texte
    text_message = await channel.send("⬆️⬆️⬆️⬆️⬆️⬆️⬆️⬆️⬆️@everyone⬆️⬆️⬆️⬆️⬆️⬆️⬆️⬆️⬆️")
    print("Message texte créé avec succès !")

# Fonction pour supprimer le sondage et le message texte à 00:00
async def delete_poll_messages():
    global poll_message, text_message
    while True:
        now = datetime.now()

        # Vérifier si c'est 00:00
        if now.hour == 0 and now.minute == 0:
            # Supprimer le sondage si existant
            if poll_message:
                try:
                    await poll_message.delete()
                    print("Sondage supprimé avec succès à 00:00 !")
                except discord.DiscordException as e:
                    print(f"Erreur lors de la suppression du sondage : {e}")

            # Supprimer le message texte si existant
            if text_message:
                try:
                    await text_message.delete()
                    print("Message texte supprimé avec succès à 00:00 !")
                except discord.DiscordException as e:
                    print(f"Erreur lors de la suppression du message texte : {e}")

        # Attendre 60 secondes avant de vérifier à nouveau l'heure
        await asyncio.sleep(60)

# Fonction pour envoyer un message tous les samedis et dimanches à 20:30
async def send_boss_message():
    while True:
        now = datetime.now()

        # Vérifier si c'est samedi ou dimanche à 20:30
        if now.weekday() in [5, 6] and now.hour == 20 and now.minute == 30:
            # ID du canal BOSS
            channel_boss = client.get_channel(int(CHANNEL_ID_BOSS))
            if channel_boss:
                try:
                    await channel_boss.send("⬆️⬆️⬆️⬆️⬆️⬆️⬆️⬆️@everyone⬆️⬆️⬆️⬆️⬆️⬆️⬆️⬆️")
                    print("Message envoyé avec succès !")
                except discord.DiscordException as e:
                    print(f"Erreur lors de l'envoi du message : {e}")

        # Attendre 60 secondes avant de vérifier à nouveau l'heure
        await asyncio.sleep(60)

# Fonction pour envoyer un message tous les dimanches à 14:30
async def send_siege_message():
    while True:
        now = datetime.now()

        # Vérifier si c'est dimanche à 14:30
        if now.weekday() == 6 and now.hour == 14 and now.minute == 30:
            # ID du canal SIEGE
            channel_siege = client.get_channel(int(CHANNEL_ID_SIEGE))
            if channel_siege:
                try:
                    await channel_siege.send("⬆️⬆️⬆️⬆️⬆️⬆️⬆️⬆️@everyone⬆️⬆️⬆️⬆️⬆️⬆️⬆️⬆️")
                    print("Message envoyé avec succès !")
                except discord.DiscordException as e:
                    print(f"Erreur lors de l'envoi du message : {e}")

        # Attendre 60 secondes avant de vérifier à nouveau l'heure
        await asyncio.sleep(60)

# Tâche qui recrée le sondage et le message texte tous les jours à 18:00
async def poll_cycle():
    while True:
        now = datetime.now()

        # Vérifier si c'est tous les jours à 18:00
        if now.hour == 18 and now.minute == 0:
            await create_poll()  # Créer un nouveau sondage et message texte
            print("Sondage et message texte créés à 18:00 !")

        # Attendre 60 secondes avant de vérifier à nouveau l'heure
        await asyncio.sleep(60)

# Lorsque le bot est prêt, démarre le cycle de création du sondage et du message texte
@client.event
async def on_ready():
    print(f"Bot connecté en tant que {client.user}")

    # Démarrer la tâche qui recrée le sondage et le message texte tous les jours à 18:00
    client.loop.create_task(poll_cycle())

    # Démarrer la tâche qui envoie le message tous les samedis et dimanches à 20:30
    client.loop.create_task(send_boss_message())

    # Démarrer la tâche qui envoie le message tous les dimanches à 14:30
    client.loop.create_task(send_siege_message())

    # Démarrer la tâche qui supprime les messages à 00:00
    client.loop.create_task(delete_poll_messages())

# Lancer le bot avec le token
client.run(os.getenv('TOKEN_DISCORD'))  # Utilise la variable d'environnement TOKEN_DISCORD
