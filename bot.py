import discord
from discord.ext import commands
from flask import Flask, request, jsonify
import threading
import random

intents = discord.Intents.default()
intents.presences = True
intents.members = True

bot = commands.Bot(command_prefix="/", intents=intents)

user_links = {}
spotify_status = {}

@bot.slash_command(name="setuser", description="Vincula tu avatar de SL con el bot")
async def setuser(ctx, avatar: str):
    hud_id = random.randint(10000, 99999)
    user_links[str(hud_id)] = {
        "discord_id": str(ctx.author.id),
        "discord_name": ctx.author.name,
        "avatar": avatar
    }
    await ctx.respond(f"✅ Tu HUD ID es: {hud_id}. Guárdalo en tu HUD de SL.")

@bot.event
async def on_presence_update(before, after):
    user_id = str(after.id)
    if after.activities:
        for activity in after.activities:
            if isinstance(activity, discord.Spotify):
                spotify_status[user_id] = {
                    "username": after.name,
                    "track": activity.title,
                    "artist": activity.artist,
                    "album": activity.album
                }
                break
        else:
            if user_id in spotify_status:
                del spotify_status[user_id]

app = Flask(__name__)

@app.route("/nowplaying")
def nowplaying():
    hud_id = request.args.get("hud")
    if hud_id in user_links:
        discord_id = user_links[hud_id]["discord_id"]
        if discord_id in spotify_status:
            return jsonify(spotify_status[discord_id])
        else:
            return jsonify({"error": "Usuario no está escuchando Spotify"})
    return jsonify({"error": "HUD ID no vinculado"})

def run_flask():
    app.run(host="0.0.0.0", port=3000)

threading.Thread(target=run_flask).start()

import os
bot.run(os.getenv("DISCORD_TOKEN"))

