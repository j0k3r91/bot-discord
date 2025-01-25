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
   python main.py
   ```

2. Le bot se connectera à votre serveur Discord et commencera à faire des sondages et à envoyer des messages aux heures spécifiées.


# Créer un Service pour le Bot Discord


Pour exécuter le bot en tant que service sur un système Linux, suivez ces étapes :

### 1. Créer un fichier de config systemd

Créez un fichier dans `/etc/systemd/system/` avec l'extension `.service`. Par exemple, vous pouvez le nommer `discord-bot.service`.

Exécutez la commande suivante dans un terminal :

```
sudo nano /etc/systemd/system/discord-bot.service
```

### 2. Ajouter le contenu suivant au fichier

Ajoutez le code suivant dans le fichier que vous venez d'ouvrir :

```
[Unit]
Description=Discord Bot
After=network.target

[Service]
User=votre_nom_utilisateur
WorkingDirectory=/chemin/vers/votre/bot-discord
ExecStart=/usr/bin/python3 /chemin/vers/votre/bot-discord/votre_script.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Assurez-vous de remplacer :
- `votre_nom_utilisateur` : par votre nom d'utilisateur Linux.
- `/chemin/vers/votre/bot-discord` : par le chemin absolu vers le répertoire de votre projet.
- `/chemin/vers/votre/bot-discord/votre_script.py` : par le chemin vers le script Python que vous exécutez.

### 3. Enregistrer et fermer l'éditeur

Sauvegardez le fichier dans l'éditeur (`Ctrl + O`, puis `Enter` pour enregistrer et `Ctrl + X` pour quitter si vous utilisez `nano`).

### 4. Recharger systemd

Pour prendre en compte le nouveau service, exécutez la commande suivante :

```
sudo systemctl daemon-reload
```

### 5. Activer le service

Activez le service pour qu'il se lance au démarrage :

```
sudo systemctl enable discord_bot.service
```

### 6. Démarrer le service

Démarrez le service avec la commande suivante :

```
sudo systemctl start discord_bot.service
```

### 7. Vérifier l'état du service

Pour vérifier que le service fonctionne correctement, utilisez la commande suivante :

```
sudo systemctl status discord_bot.service
```

### 8. Afficher les logs du service

Pour voir les logs du service en temps réel, exécutez :

```
journalctl -u discord_bot.service -f
```

---

Cela vous permettra de garder votre bot en fonctionnement en arrière-plan, même après le redémarrage de votre système.

### N'oubliez pas

- Assurez-vous que votre script Python fonctionne comme prévu avant de le configurer en tant que service.
- Les chemins indiqués doivent correspondre à la structure de votre système.
- Vérifiez les permissions du fichier du service pour qu'il soit accessible par `systemd`.



## Contribuer

Les contributions sont les bienvenues ! N'hésitez pas à soumettre une demande de pull request ou à signaler des problèmes sur le dépôt GitHub.

## License

Ce projet est sous licence MIT. Voir le fichier [LICENSE](LICENSE) pour plus de détails.

## Aide et Ressources

- [Documentation de discord.py](https://discordpy.readthedocs.io/en/stable/)
- [Guide pour créer un bot Discord](https://discord.com/developers/docs/intro)
