import discord
from discord.ext import commands
import json, os, random, string
from discord.ui import View, Button
from discord import Interaction
import asyncio
import shutil
import aiohttp

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="?", intents=intents, help_command=None)

def generate_backup_id(length=15):
    return ''.join(random.choices(string.digits, k=length))


def save_backup(data, backup_id):
    os.makedirs("backups", exist_ok=True)
    with open(f"backups/{backup_id}.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

def load_backup(backup_id):
    try:
        with open(f"backups/{backup_id}.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return None

def count_channels(data):
    return sum(len(cat["channels"]) for cat in data["categories"])

def count_roles(data):
    return len(data["roles"])

@bot.event
async def on_ready():
    activity = discord.Streaming(name="?help pour les commandes", url="https://www.twitch.tv/discord")
    await bot.change_presence(activity=activity)
    print(f"Connecté en tant que {bot.user.name}")

@bot.command(name="backup-create")
@commands.has_permissions(administrator=True)
async def backup_create(ctx):
    guild = ctx.guild
    backup_id = generate_backup_id()
    icon_url = guild.icon.url if guild.icon else None
    banner_url = guild.banner.url if guild.banner else None

    data = {
        "id": backup_id,
        "server_name": guild.name,
        "roles": [],
        "categories": [],
        "icon_url": icon_url,
        "banner_url": banner_url,
        "bans": [],
        "emojis": []
    }

    for role in reversed(guild.roles):
        if role.is_default(): continue
        data["roles"].append({
            "name": role.name,
            "permissions": role.permissions.value,
            "color": role.color.value,
            "mentionable": role.mentionable,
            "hoist": role.hoist,
            "position": role.position
        })
    for category in guild.categories:
        cat_data = {
            "name": category.name,
            "channels": []
        }
        for channel in category.channels:
            overwrites = {}
            for target, perms in channel.overwrites.items():
                overwrites[str(target.id)] = {
                    "type": "role" if isinstance(target, discord.Role) else "member",
                    "allow": perms.pair()[0].value,
                    "deny": perms.pair()[1].value
                }

            if isinstance(channel, discord.TextChannel):
                cat_data["channels"].append({
                    "name": channel.name,
                    "type": "text",
                    "topic": channel.topic,
                    "nsfw": channel.nsfw,
                    "position": channel.position,
                    "overwrites": overwrites
                })
            elif isinstance(channel, discord.VoiceChannel):
                cat_data["channels"].append({
                    "name": channel.name,
                    "type": "voice",
                    "bitrate": channel.bitrate,
                    "user_limit": channel.user_limit,
                    "position": channel.position,
                    "overwrites": overwrites
                })

        data["categories"].append(cat_data)

    try:
        async for ban_entry in guild.bans():
            data["bans"].append(str(ban_entry.user.id))
    except:
        data["bans"] = []

    for emoji in guild.emojis:
        data["emojis"].append({
            "name": emoji.name,
            "url": str(emoji.url)
        })

    save_backup(data, backup_id)

  
    embed = discord.Embed(
        title="📦 - Backup en cours de chargement",
        color=0x5865F2
    )
    embed.add_field(name=" ", value="> *Chargement de la backup...*", inline=False)
    
    embed.set_footer(text=f"{ctx.author.name}", icon_url=ctx.author.avatar.url if ctx.author.avatar else None)
    msg = await ctx.reply(embed=embed, mention_author=False)
    await ctx.message.delete()
    await asyncio.sleep(3)

    embed = discord.Embed(
        title="✅ - Backup créée avec succès",
        color=0x5865F2
    )
    embed.add_field(name=" ", value=f"> **Id de la backup créée :** `{backup_id}`", inline=False)
    embed.set_footer(text=f"{ctx.author.name}", icon_url=ctx.author.avatar.url if ctx.author.avatar else None)
    await msg.edit(content=f"{ctx.author.mention}", embed=embed)


@bot.command(name="backup-load")
@commands.has_permissions(administrator=True)
async def backup_load(ctx, backup_id):
    data = load_backup(backup_id)
    if not data:
        embed = discord.Embed(
            title="❌ Échec de la restauration",
            description=f"Aucune backup trouvée avec l'ID : `{backup_id}`",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
        return

    guild = ctx.guild

    loading_channel = discord.utils.get(guild.text_channels, name="backup-en-cours")
    if loading_channel is None:
        loading_channel = await guild.create_text_channel("backup-en-cours")

    embed = discord.Embed(
        title="🔄 Restauration en cours...",
        description="Début de la restauration du serveur, veuillez patienter...",
        color=0x5865F2
    )
    embed.set_footer(text=f"{ctx.author.name}", icon_url=ctx.author.avatar.url if ctx.author.avatar else None)
    invite = await loading_channel.create_invite(max_uses=100, unique=False)
    embed.set_author(name=guild.name, icon_url=guild.icon.url if guild.icon else None, url=invite)
    msg = await loading_channel.send(embed=embed)

    async def update_status(status):
        embed.description = status
        await msg.edit(embed=embed)

    await update_status("*Suppression des salons...*")
    for channel in guild.channels:
        if channel.id != loading_channel.id:
            try:
                await channel.delete()
            except:
                pass

    await update_status("*Suppression des rôles...*")
    for role in guild.roles:
        if not role.is_default():
            try:
                await role.delete()
            except:
                pass

    await update_status("*Suppression des emojis...*")
    for emoji in guild.emojis:
        try:
            await emoji.delete()
        except:
            pass

    await update_status("*Déban des membres...*")
    try:
        async for ban_entry in guild.bans():
            try:
                await guild.unban(ban_entry.user)
            except:
                pass
    except:
        pass

    await update_status("*Création des rôles...*")
    role_map = {}
    for role_data in data.get("roles", []):
        try:
            new_role = await guild.create_role(
                name=role_data["name"],
                permissions=discord.Permissions(role_data["permissions"]),
                color=discord.Color(role_data["color"]),
                mentionable=role_data["mentionable"],
                hoist=role_data["hoist"]
            )
            role_map[role_data["name"]] = new_role
            await asyncio.sleep(1.5)  
        except Exception as e:
            print(f"Erreur création rôle: {e}")
            continue

    await update_status("*Création des catégories et salons...*")
    for cat_data in data.get("categories", []):
        try:
            new_cat = await guild.create_category(cat_data["name"])
            for chan in cat_data.get("channels", []):
                overwrites = {}
                for role_id, perms in chan.get("overwrites", {}).items():
                    role_name = perms.get("name")
                    role_obj = role_map.get(role_name)
                    if role_obj:
                        allow = discord.Permissions(perms.get("allow", 0))
                        deny = discord.Permissions(perms.get("deny", 0))
                        ow = discord.PermissionOverwrite.from_pair(allow, deny)
                        overwrites[role_obj] = ow

                if chan["type"] == "text":
                    await guild.create_text_channel(
                        name=chan["name"],
                        topic=chan.get("topic"),
                        nsfw=chan.get("nsfw", False),
                        category=new_cat,
                        position=chan.get("position", 0),
                        overwrites=overwrites
                    )
                elif chan["type"] == "voice":
                    await guild.create_voice_channel(
                        name=chan["name"],
                        bitrate=chan.get("bitrate", 64000),
                        user_limit=chan.get("user_limit", 0),
                        category=new_cat,
                        position=chan.get("position", 0),
                        overwrites=overwrites
                    )
        except Exception as e:
            print(f"Erreur cat/salon: {e}")
            continue

    await update_status("*Restauration des emojis...*")
    for emoji in data.get("emojis", []):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(emoji["url"]) as resp:
                    if resp.status == 200:
                        img = await resp.read()
                        await guild.create_custom_emoji(name=emoji["name"], image=img)
                        await asyncio.sleep(1.0)
        except Exception as e:
            print(f"Erreur emoji: {e}")
            continue
            

    await update_status("*Réapplication des bans...*")
    for banned_id in data.get("bans", []):
        try:
            user = await bot.fetch_user(int(banned_id))
            await guild.ban(user, reason="Restoration backup")
        except Exception as e:
            print(f"Erreur ban: {e}")
            continue

    await update_status("**Backup restaurée avec succès !**")



@bot.command(name="backup-list")
@commands.has_permissions(administrator=True)
async def backup_list(ctx):
    folder = "backups"
    if not os.path.exists(folder):
        await ctx.send("📁 Aucun dossier de backups trouvé.")
        return

    files = [f[:-5] for f in os.listdir(folder) if f.endswith(".json") and f[:-5].isdigit()]
    if not files:
        await ctx.send("📦 Aucune backup trouvée.")
        return

    files.sort(reverse=True)
    per_page = 7
    total_pages = (len(files) - 1) // per_page + 1
    current_page = 0

    def get_embed(page):
        start = page * per_page
        end = start + per_page
        page_files = files[start:end]
        desc = ""
        for i, fid in enumerate(page_files, start=start + 1):
            data = load_backup(fid)
            name = data.get("server_name", "GUILD") if data else "Invalide"
            desc += f"**{i}.)** `{name}` - `{fid}`\n"
        embed = discord.Embed(title="📦 - All Backups Servers", description=desc or "*Aucune backup sur cette page.*", color=0x5865F2)
        embed.set_footer(text=f"{ctx.author.name}", icon_url=ctx.author.avatar.url if ctx.author.avatar else None)
        return embed

    async def update_message(interaction, direction):
        nonlocal current_page
        if interaction.user != ctx.author:
            return await interaction.response.send_message("❌ Ce menu ne t'appartient pas.", ephemeral=True)

        current_page += direction
        current_page = max(0, min(current_page, total_pages - 1))

        new_embed = get_embed(current_page)
        await interaction.response.edit_message(embed=new_embed, view=create_view())


    def create_view():
        view = View(timeout=60)

        btn_prev = Button(emoji="◀️", style=discord.ButtonStyle.secondary, disabled=current_page == 0)
        btn_page = Button(label=f"{current_page + 1}/{total_pages}", style=discord.ButtonStyle.gray, disabled=True)
        btn_next = Button(emoji="▶️", style=discord.ButtonStyle.secondary, disabled=current_page >= total_pages - 1)

        async def prev_callback(interaction: Interaction): await update_message(interaction, -1)
        async def next_callback(interaction: Interaction): await update_message(interaction, 1)

        btn_prev.callback = prev_callback
        btn_next.callback = next_callback

        view.add_item(btn_prev)
        view.add_item(btn_page)
        view.add_item(btn_next)
        return view


    await ctx.send(embed=get_embed(current_page), view=create_view())

@bot.command(name="backup-delete")
@commands.has_permissions(administrator=True)
async def backup_delete(ctx, backup_id):
    path = f"backups/{backup_id}.json"
    if not os.path.exists(path):
        await ctx.send(f"❌ La backup avec l'ID `{backup_id}` n'existe pas.")
        return

    os.remove(path)
    await ctx.send(f"🗑️ La backup `{backup_id}` a été supprimée avec succès.")

@bot.command(name="backup-info")
@commands.has_permissions(administrator=True)
async def backup_info(ctx, backup_id):
    data = load_backup(backup_id)

    if not data:
        embed = discord.Embed(
            title="❌ Backup introuvable",
            description=f"Aucune backup trouvée avec l'ID `{backup_id}`.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
        return

    roles = data.get("roles", [])
    emojis = data.get("emojis", [])
    bans = data.get("bans", [])
    categories = data.get("categories", [])

    total_text = 0
    total_voice = 0
    for cat in categories:
        for chan in cat.get("channels", []):
            if chan["type"] == "text":
                    total_text += 1
            elif chan["type"] == "voice":
                    total_voice += 1
    
        embed = discord.Embed(
            title="📦 Informations de la Backup",
            color=discord.Color.blurple()
        )

        embed.add_field(name=" ", value=f"""
    > **Nom du serveur :** {data.get("server_name", "Inconnu")}
    > **ID de la backup :** `{backup_id}`
    > **Catégories :** {len(categories)}
    > **Salons textuels :** {total_text}
    > **Salons vocaux :** {total_voice}
    > **Rôles :** {len(roles)}
    > **Emojis :** {len(emojis)}
    > **Membres bannis :** {len(bans)}
        """, inline=False)
        if data.get("icon_url"):
            embed.set_thumbnail(url=data["icon_url"])
        embed.set_footer(text=f"Demandé par {ctx.author}", icon_url=ctx.author.display_avatar.url)
        

        await ctx.send(embed=embed)

@bot.command(name="help")
async def help_command(ctx):
    embed = discord.Embed(
        title="📦 - Commandes de Backup",
        color=0x5865F2
    )
    embed.add_field(
        name=" ",
        value="""
> **`?backup-create`** - Créer une backup du serveur.
> **`?backup-load <id>`** - Restaurer une backup.
> **`?backup-list`** - Lister toutes les backups.
> **`?backup-delete <id>`** - Supprimer une backup.
> **`?backup-info <id>`** - Informations sur une backup.
> **`?help`** - Afficher ce message.
""",
        inline=False
    )
    embed.set_footer(
        text=f"{ctx.author.name}",
        icon_url=ctx.author.avatar.url if ctx.author.avatar else None
    )
    await ctx.reply(embed=embed, mention_author=False)

bot.run("TON_TOKEN")
