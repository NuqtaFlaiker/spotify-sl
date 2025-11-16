import os
import random
import threading
import discord
from discord.ext import commands
from discord import app_commands
from flask import Flask, request, jsonify

intents = discord.Intents.default()
intents.presences = True
intents.members = True

bot = commands.Bot(command_prefix="/", intents=intents)

# Almacenes en memoria
user_links = {}     # hud_id -> {discord_id, discord_name, avatar}
spotify_status = {} # discord_id -> {username, track, artist, album}

# ---- Slash command con app_commands ----
@bot.tree.command(name="setuser", description="Vincula tu avatar de SL con el bot")
@app_commands.describe(avatar="Nombre de tu avatar en Second Life")
async def setuser(interaction: discord.Interaction, avatar: str):
    hud_id = random.randint(10000, 99999)
    user_links[str(hud_id)] = {
        "discord_id": str(interaction.user.id),
        "discord_name": interaction.user.name,
        "avatar": avatar
    }
    await interaction.response.send_message(
        f"✅ Tu HUD ID es: {hud_id}. Guárdalo en tu HUD de SL.",
        ephemeral=True
    )

# ---- Presencias para Spotify ----
@bot.event
async def on_presence_update(before: discord.Member, after: discord.Member):
    user_id = str(after.id)
    found_spotify = False
    if after.activities:
        for activity in after.activities:
            if isinstance(activity, discord.Spotify):
                spotify_status[user_id] = {
                    "username": after.name,
                    "track": activity.title,
                    "artist": activity.artist,
                    "album": activity.album
                }
                found_spotify = True
                break
    if not found_spotify and user_id in spotify_status:
        del spotify_status[user_id]

# ---- Flask para endpoint público ----
app = Flask(__name__)

@app.route("/nowplaying")
def nowplaying():
    hud_id = request.args.get("hud")
    if not hud_id:
        return jsonify({"error": "Falta parámetro 'hud'"}), 400
    if hud_id in user_links:
        discord_id = user_links[hud_id]["discord_id"]
        data = spotify_status.get(discord_id)
        if data:
            return jsonify(data)
        return jsonify({"error": "Usuario no está escuchando Spotify"})
    return jsonify({"error": "HUD ID no vinculado"})

def run_flask():
    app.run(host="0.0.0.0", port=3000)

# ---- Sincroniza los slash commands al iniciar ----
@bot.event
async def on_ready():
    try:
        await bot.tree.sync()  # sincroniza globalmente (tarda unos minutos la primera vez)
        print(f"Synced slash commands como {bot.user}")
    except Exception as e:
        print(f"Error al sincronizar comandos: {e}")

# ---- Arranque ----
threading.Thread(target=run_flask, daemon=True).start()

token = os.getenv("DISCORD_TOKEN")
if not token:
    raise RuntimeError("DISCORD_TOKEN no está configurado en variables de entorno")
bot.run(token)
