# Bot Discord for Event Management

Ce bot Discord, est conçu pour gérer des événements au sein d'un serveur Discord, 
notamment des sondages pour des événements de jeu tels que des "Donjons Parties" et des notifications pour des événements spéciaux tels que des raids ou des boss.
Il utilise la bibliothèque `discord.py` pour interagir avec l'API de Discord.

## Fonctionnalités

- Création automatique de sondages pour les événements de jeu.
- Envoi de rappels pour des événements récurrents, comme les boss-events le week-end.
- Suppression automatique des sondages et des messages associés à minuit.
- Support de messages envoyés dans différents canaux selon les événements.

## Prérequis

- Python : Version 3.6 ou plus.
- Dépendances :
  - `discord.py`
  - `python-dotenv` (pour gérer les variables d'environnement)

## Installation

1. Clonez le dépôt :
   ```
   git clone https://github.com/j0k3r91/bot-discord.git
   cd bot-discord
   ```

2. Créez un environnement virtuel (optionnel) :
   ```
   python -m venv venv
   source venv/bin/activate  # sur Linux/Mac
   venv\Scripts\activate  # sur Windows
   ```

3. Installez les dépendances :
   ```
   pip install discord.py python-dotenv
   ```

4. Créez un fichier `.env` :
   Ce fichier doit contenir vos variables d'environnement. Exemple :
   ```
   TOKEN_DISCORD=VotreTokenIci
   CHANNEL_ID_DP=VotreChannelIDDonjonParty
   CHANNEL_ID_BOSS=VotreChannelIDBoss
   CHANNEL_ID_SIEGE=VotreChannelIDSiege
   ```

   - `TOKEN_DISCORD` : Le token de votre bot Discord, que vous pouvez obtenir depuis le [portail des développeurs Discord](https://discord.com/developers/applications).
   - `CHANNEL_ID_DP` : L'ID du canal dans lequel le bot enverra les sondages.
   - `CHANNEL_ID_BOSS` : L'ID du canal où le bot enverra les messages pour les événements de boss.
   - `CHANNEL_ID_SIEGE` : L'ID du canal pour les messages de siège.

## Utilisation

1. Démarrez le bot avec la commande suivante :
   ```
   python votre_script.py
   ```

2. Le bot se connectera à votre serveur Discord et commencera à faire des sondages et à envoyer des messages aux heures spécifiées.

## Contribuer

Les contributions sont les bienvenues ! N'hésitez pas à soumettre une demande de pull request ou à signaler des problèmes sur le dépôt GitHub.

## License

Ce projet est sous licence MIT. Voir le fichier [LICENSE](LICENSE) pour plus de détails.

## Aide et Ressources

- [Documentation de discord.py](https://discordpy.readthedocs.io/en/stable/)
- [Guide pour créer un bot Discord](https://discord.com/developers/docs/intro)
