
# 📦 Discord Backup Bot

Un bot Discord complet en Python pour créer, gérer et restaurer des sauvegardes de serveurs.  
Il inclut une interface avec embed et boutons pour gérer les backups facilement.

---

## 🚀 Fonctionnalités

- Sauvegarde complète du serveur (salons, rôles, catégories, emojis, bannissements, icône, bannière…)
- Interface de configuration interactive
- Système de backup avec identifiants aléatoires
- Restauration facile d'une backup
- Liste des backups avec pagination
- Suppression et affichage d'informations sur chaque backup
- Protection par permissions (`administrator` ou `owner`)

---

## 🛠️ Installation

### 1. Cloner le dépôt

```bash
git clone https://github.com/ton-utilisateur/discord-backup-bot.git
cd discord-backup-bot
````

### 2. Installer les dépendances

```bash
pip install -r requirements.txt
```

### 3. Lancer le bot

Remplis le token dans le fichier `config.json` ou directement dans le code.

```bash
python main.py
```

---

## 📚 Commandes disponibles

| Commande              | Description                                      |
| --------------------- | ------------------------------------------------ |
| `.backup-create`      | Créer une sauvegarde du serveur                  |
| `.backup-load <id>`   | Restaurer une sauvegarde                         |
| `.backup-list`        | Voir la liste de toutes les backups              |
| `.backup-info <id>`   | Voir les détails d’une backup                    |
| `.backup-delete <id>` | Supprimer une backup                             |
| `.help`               | Affiche l’embed avec la liste des commandes      |

---

## 🔐 Permissions requises

Pour que le bot fonctionne correctement, il a besoin des permissions suivantes :

* Gérer les salons
* Gérer les rôles
* Gérer les messages
* Gérer les emojis et stickers
* Voir les logs
* Administrateur (de préférence pour les backups complètes)

---

## 📁 Structure des Backups

Les backups sont enregistrées dans un dossier `/backups` sous forme de fichiers `.json`, contenant :

* Informations générales du serveur
* Rôles, emojis, bannissements
* Catégories, salons textuels/vocaux avec leurs permissions
* Sauvegarde des permissions (`overwrites`) sous forme de dictionnaire lisible

---

## 📸 Aperçu

![Interface backup Discord](./assets/screenshot_backup_embed.png)

---

## 🧑‍💻 Dépendances principales

* [`discord.py`](https://pypi.org/project/discord.py/) ou fork compatible (`pycord`, `nextcord`, etc.)
* `os`, `json`, `random`, `datetime`

---

## 📄 Licence

Ce projet est open-source. Utilisation libre avec crédits si possible.

---

## 🙋 Aide

En cas de problème, ouvre une issue ou contacte le développeur.

```
