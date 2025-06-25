\===============================================================================

           BOT DISCORD FOR EVENT MANAGEMENT

\===============================================================================

  

Ce bot Discord avancé est conçu pour gérer automatiquement des événements au 

sein d'un serveur Discord. Il gère les sondages quotidiens, les notifications 

d'événements récurrents, et maintient automatiquement les liens vers les 

événements Discord programmés. Parfait pour les communautés de jeu et les guildes.

  

\===============================================================================

              FONCTIONNALITÉS PRINCIPALES

\===============================================================================

  

Gestion Automatique des Sondages

\---------------------------------

\- Création automatique de sondages quotidiens à 18h00 (heure de Paris)

\- Suppression automatique des sondages à minuit

\- Protection anti-doublon pour éviter les créations multiples

  

Gestion des Événements Discord

\------------------------------

\- Récupération automatique des événements programmés sur le serveur

\- Mise à jour hebdomadaire des liens d'événements (chaque lundi à 00:00)

\- Filtrage intelligent des événements par mots-clés et jours de la semaine

\- Templates personnalisables pour les messages d'événements

  

Notifications Automatiques

\---------------------------

\- Boss Events : Notifications les samedis et dimanches à 20:30

\- Siege Events : Notifications les dimanches à 14:30

\- Messages @everyone pour alerter la communauté

  

Système de Cache

\----------------

\- Cache local des événements pour optimiser les performances

\- Mise à jour intelligente du cache lors des modifications

  

\===============================================================================

              NOUVELLES FONCTIONNALITÉS

\===============================================================================

  

Gestion Avancée des Liens d'Événements

\---------------------------------------

\- Récupération automatique de tous les événements Discord du serveur

\- Liens directs générés automatiquement vers les événements

\- Regroupement intelligent des événements boss du weekend dans un seul message

\- Filtrage par mots-clés : "boss", "raid", "siège", "grotte", "cristal"

  

Commandes Administrateur Complètes

\-----------------------------------

\- Consultation des événements en temps réel

\- Mise à jour manuelle des liens d'événements

\- Nettoyage sélectif des messages

\- Monitoring complet du statut du bot

  

\===============================================================================

                 PRÉREQUIS

\===============================================================================

  

\- Python : Version 3.9+ (pour zoneinfo)

\- Dépendances :

 \* discord.py (version récente avec support des Polls)

 \* python-dotenv

  

\===============================================================================

                INSTALLATION

\===============================================================================

  

1\. Clonez le dépôt :

  git clone https://github.com/j0k3r91/bot-discord.git

  cd bot-discord

  

2\. Créez un environnement virtuel (recommandé) :

  python -m venv venv

  source venv/bin/activate # Linux/Mac

  venv\\Scripts\\activate   # Windows

  

3\. Installez les dépendances :

  pip install discord.py python-dotenv

  

4\. Configurez les variables d'environnement :

  Créez un fichier .env dans le répertoire du projet :

  TOKEN\_DISCORD=VotreTokenDiscordIci

  CHANNEL\_ID\_DP=IDDuCanalDonjonParty

  CHANNEL\_ID\_BOSS=IDDuCanalBossEvents

  CHANNEL\_ID\_SIEGE=IDDuCanalSiegeEvents

  

  Comment obtenir les IDs :

  - Token Discord : Portail Développeurs Discord

   (https://discord.com/developers/applications)

  - IDs des canaux : Mode développeur Discord → Clic droit sur canal 

   → "Copier l'identifiant"

  

\===============================================================================

                UTILISATION

\===============================================================================

  

Démarrage du Bot

\----------------

python main.py

  

Automatisations Programmées

\----------------------------

HORAIRE     | ACTION          | DESCRIPTION

\----------------|---------------------------|----------------------------------

18:00      | Création sondage     | Sondage quotidien "Donjon Party"

00:00      | Suppression sondage   | Nettoyage automatique

Lundi 00:00   | Mise à jour événements  | Actualisation des liens hebdomadaires

Sam/Dim 20:30  | Notification boss    | Rappel événements boss

Dim 14:30    | Notification siège    | Rappel événements siège

  

\===============================================================================

              COMMANDES DISCORD

\===============================================================================

  

Consultation des Événements

\----------------------------

!events       - Affiche tous les événements avec leurs liens

!event\_link <nom>  - Recherche un événement spécifique

!update\_events    - Met à jour le cache des événements

  

Mise à Jour des Liens

\---------------------

!update\_boss\_links  - Met à jour les liens d'événements boss

!update\_siege\_links - Met à jour les liens d'événements siège

!update\_all\_links  - Met à jour tous les liens d'événements

  

Gestion des Sondages

\--------------------

!force\_poll     - Crée un sondage manuellement

!clean\_poll     - Supprime les messages de sondage

  

Gestion des Événements

\----------------------

!force\_boss     - Envoie une notification boss

!force\_siege     - Envoie une notification siège

!clean\_events    - Supprime tous les messages d'événements

  

Utilitaires

\-----------

!status       - Affiche le statut complet du bot

!test        - Vérifie le fonctionnement du bot

!recover       - Récupère les messages existants

!clean\_all      - Nettoie tous les messages du bot

!help\_admin     - Affiche l'aide complète

  

NOTE: Toutes les commandes nécessitent les permissions administrateur.

  

\===============================================================================

              CONFIGURATION AVANCÉE

\===============================================================================

  

Templates de Messages

\---------------------

Le bot utilise des templates personnalisables pour les messages d'événements :

  

Template Boss Events:

"Présence pour l'événement Boss du weekend (samedi et dimanche) à 21h00 

(heure de Paris) - 15h00 (heure du Québec).

Merci de venir 15 minutes avant l'événement.

{boss\_links}"

  

Template Siege Events:

"Présence pour le siège du donjon de la Grotte de Cristal le dimanche à 15h00 

(heure de Paris) - 9h00 (heure du Québec).

Merci de venir 15 minutes avant l'événement.

{siege\_links}"

  

Filtres d'Événements

\--------------------

Mots-clés pour les événements boss: \["boss", "samedi", "dimanche"\]

Mots-clés pour les événements siège: \["siège", "grotte", "cristal"\]

  

\===============================================================================

          INSTALLATION EN TANT QUE SERVICE LINUX

\===============================================================================

  

1\. Créer le fichier service

  sudo nano /etc/systemd/system/discord-bot.service

  

2\. Configuration du service

  \[Unit\]

  Description=Discord Event Management Bot

  After=network.target

  

  \[Service\]

  Type=simple

  User=votre\_utilisateur

  WorkingDirectory=/chemin/vers/bot-discord

  ExecStart=/usr/bin/python3 /chemin/vers/bot-discord/main.py

  Restart=always

  RestartSec=10

  

  \[Install\]

  WantedBy=multi-user.target

  

3\. Activation du service

  # Recharger systemd

  sudo systemctl daemon-reload

  

  # Activer au démarrage

  sudo systemctl enable discord-bot.service

  

  # Démarrer le service

  sudo systemctl start discord-bot.service

  

  # Vérifier le statut

  sudo systemctl status discord-bot.service

  

  # Voir les logs en temps réel

  journalctl -u discord-bot.service -f

  

\===============================================================================

              STRUCTURE DU PROJET

\===============================================================================

  

bot-discord/

├── main.py         # Script principal du bot

├── .env          # Variables d'environnement (à créer)

├── .env.example      # Exemple de configuration

├── requirements.txt    # Dépendances Python

├── README.md       # Documentation

└── logs/

  └── discord-bot.log  # Fichiers de logs

  

\===============================================================================

              MONITORING ET LOGS

\===============================================================================

  

Le bot génère des logs détaillés pour le monitoring :

  

\- Fichier de log : /home/discord/discord-bot.log

\- Niveaux : INFO, ERROR, WARNING

\- Contenu : Toutes les actions automatiques, erreurs, et commandes exécutées

  

Commandes de monitoring

\-----------------------

\# Logs en temps réel

tail -f /home/discord/discord-bot.log

  

\# Logs du service

journalctl -u discord-bot.service -f

  

\# Statut du service

systemctl status discord-bot.service

  

\===============================================================================

                SÉCURITÉ

\===============================================================================

  

\- Token Discord : Stocké dans .env, jamais dans le code

\- Permissions : Commandes réservées aux administrateurs

\- Validation : Vérification des variables d'environnement au démarrage

\- Gestion d'erreurs : Protection contre les crashes

  

\===============================================================================

               MISE À JOUR

\===============================================================================

  

Pour mettre à jour le bot :

  

1\. Arrêter le service :

  sudo systemctl stop discord-bot.service

  

2\. Mettre à jour le code :

  git pull origin main

  

3\. Redémarrer le service :

  sudo systemctl start discord-bot.service

  

\===============================================================================

                CONTRIBUER

\===============================================================================

  

Les contributions sont les bienvenues ! 

  

1\. Fork le projet

2\. Créez votre branche feature (git checkout -b feature/AmazingFeature)

3\. Commitez vos changements (git commit -m 'Add some AmazingFeature')

4\. Push vers la branche (git push origin feature/AmazingFeature)

5\. Ouvrez une Pull Request

  

\===============================================================================

                RESSOURCES

\===============================================================================

  

\- Documentation discord.py: https://discordpy.readthedocs.io/en/stable/

\- Guide Discord Bot: https://discord.com/developers/docs/intro

\- API Discord Events: https://discord.com/developers/docs/resources/guild-scheduled-event

\- Python dotenv: https://pypi.org/project/python-dotenv/

  

\===============================================================================

                LICENCE

\===============================================================================

  

Ce projet est sous licence MIT. Voir le fichier LICENSE pour plus de détails.

  

\===============================================================================

                SUPPORT

\===============================================================================

  

Pour obtenir de l'aide :

\- Issues GitHub : Créer une issue sur https://github.com/j0k3r91/bot-discord/issues

\- Discord : Utilisez !help\_admin pour voir toutes les commandes disponibles

  

\===============================================================================

               FIN DU DOCUMENT

\===============================================================================
