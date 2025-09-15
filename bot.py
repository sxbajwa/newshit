import os
import re
import json
import random
import logging
from pathlib import Path
from datetime import timedelta

import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv

from keep_alive import keep_alive
keep_alive()  # keeps the bot alive (Replit/Heroku/etc.)

# ===================== LOAD ENV =====================
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID", "0"))  # server ID from .env
if not TOKEN:
    raise RuntimeError("DISCORD_TOKEN not set in .env")

# ===================== CONFIG =====================
COMMAND_PREFIX = "!"
ALLOWED_NUKE_CHANNEL = os.getenv("NUKE_CHANNEL_NAME", "bot-commands")
MAX_NUKE = int(os.getenv("MAX_NUKE", "30"))
FUN_COOLDOWN_SECONDS = int(os.getenv("FUN_COOLDOWN", "5"))
CATEGORY_NAME = "ModMail"   # for ModMail tickets

# ===================== LOGGING =====================
logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s:%(name)s: %(message)s")
log = logging.getLogger("bot")

# ===================== BOT SETUP =====================
intents = discord.Intents.all()
bot = commands.Bot(command_prefix=COMMAND_PREFIX, intents=intents)

# ===================== UTILITIES =====================
def parse_duration(duration_str: str):
    match = re.match(r"^\s*(\d+)\s*([smhd])\s*$", duration_str.lower())
    if not match:
        return None
    amount, unit = match.groups()
    amount = int(amount)
    delta = {
        "s": timedelta(seconds=amount),
        "m": timedelta(minutes=amount),
        "h": timedelta(hours=amount),
        "d": timedelta(days=amount),
    }[unit]
    return discord.utils.utcnow() + delta

def can_act(ctx: commands.Context, target: discord.Member):
    if target == ctx.author:
        return False, "You cannot act on yourself."
    if target == ctx.guild.owner:
        return False, "You cannot act on the server owner."
    if target == ctx.me:
        return False, "I cannot act on myself."
    if target.guild_permissions.administrator:
        return False, "You cannot act on an Administrator."
    if ctx.author.top_role <= target.top_role and ctx.author != ctx.guild.owner:
        return False, "You cannot act on a higher or equal role."
    if ctx.me.top_role <= target.top_role:
        return False, "I cannot act on a higher or equal role."
    return True, None

# ===================== EVENTS =====================
@bot.event
async def on_ready():
    await bot.change_presence(
        status=discord.Status.online,
        activity=discord.Activity(type=discord.ActivityType.watching, name="the server")
    )
    await bot.tree.sync()
    log.info(f"✅ Logged in as {bot.user} (ID: {bot.user.id})")

# ===================== ERROR HANDLER =====================
@bot.event
async def on_command_error(ctx: commands.Context, error):
    if isinstance(error, commands.CommandNotFound):
        return
    if isinstance(error, commands.MissingRequiredArgument):
        return await ctx.send("❌ Missing argument. Check your command usage.")
    if isinstance(error, commands.MissingPermissions):
        return await ctx.send("❌ You don’t have permission for that.")
    if isinstance(error, commands.CommandOnCooldown):
        return await ctx.send(f"⏳ Slow down! Try again in {error.retry_after:.1f}s.")
    await ctx.send("⚠️ An error occurred.")
    log.exception("Unhandled error: %s", error)

# ===================== FUN COMMANDS =====================
fun_commands = {
    "hug": "🤗",
    "kiss": "😘",
    "slap": "🤚",
    "hit": "👊",
    "kickfun": "🦵",
    "kill": "💀",
    "punch": "👊💥",
    "blowkiss": "💋",
    "tickle": "😂",
    "sex": "🔞",
    "esex": "💻🔞",
}

def register_fun_command(name: str, emoji: str):
    # Prefix
    @bot.command(name=name, aliases=["fuck"] if name == "sex" else [])
    @commands.cooldown(1, FUN_COOLDOWN_SECONDS, commands.BucketType.user)
    async def fun_prefix(ctx, user: discord.Member = None):
        if not user:
            return await ctx.send(f"You must mention someone to {name}.")
        await ctx.send(f"{ctx.author.mention} {name}s {user.mention} {emoji}")

    # Slash
    @bot.tree.command(name=name, description=f"{name.capitalize()} someone {emoji}")
    @app_commands.describe(user="Who do you want to target?")
    async def fun_slash(interaction: discord.Interaction, user: discord.Member):
        await interaction.response.send_message(f"{interaction.user.mention} {name}s {user.mention} {emoji}")

for n, e in fun_commands.items():
    register_fun_command(n, e)

# Ship
@bot.command()
async def ship(ctx, user1: discord.Member, user2: discord.Member):
    percentage = random.randint(1, 100)
    heart = "❤️" if percentage > 50 else "💔"
    await ctx.send(f"💘 {user1.mention} {heart} {user2.mention} → **{percentage}%**")

@bot.tree.command(name="ship", description="Ship two users together ❤️")
async def ship_slash(interaction: discord.Interaction, user1: discord.Member, user2: discord.Member):
    percentage = random.randint(1, 100)
    heart = "❤️" if percentage > 50 else "💔"
    await interaction.response.send_message(f"💘 {user1.mention} {heart} {user2.mention} → **{percentage}%**")

# ===================== MODERATION COMMANDS =====================
@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason="No reason"):
    can, msg = can_act(ctx, member)
    if not can: return await ctx.send(f"❌ {msg}")
    await member.ban(reason=reason)
    await ctx.send(f"✅ {member} was banned. Reason: {reason}")

@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason="No reason"):
    can, msg = can_act(ctx, member)
    if not can: return await ctx.send(f"❌ {msg}")
    await member.kick(reason=reason)
    await ctx.send(f"✅ {member} was kicked. Reason: {reason}")

@bot.command()
@commands.has_permissions(manage_roles=True)
async def mute(ctx, member: discord.Member, duration: str = "10m", *, reason="No reason"):
    until = parse_duration(duration)
    if not until: return await ctx.send("❌ Invalid duration (use 10s/10m/2h/1d).")
    can, msg = can_act(ctx, member)
    if not can: return await ctx.send(f"❌ {msg}")
    await member.timeout(until, reason=reason)
    await ctx.send(f"✅ {member.mention} muted until {until}.")

@bot.command()
@commands.has_permissions(manage_roles=True)
async def unmute(ctx, member: discord.Member):
    await member.timeout(None)
    await ctx.send(f"✅ {member.mention} has been unmuted.")

@bot.command()
@commands.has_permissions(manage_channels=True)
async def nuke(ctx):
    if ctx.channel.name != ALLOWED_NUKE_CHANNEL:
        return await ctx.send(f"❌ Nukes only allowed in #{ALLOWED_NUKE_CHANNEL}")
    if len(ctx.channel.members) > MAX_NUKE:
        return await ctx.send(f"❌ Too many members in channel.")
    new = await ctx.channel.clone()
    await ctx.channel.delete()
    await new.send("💥 Channel has been nuked!")

# ===================== MODMAIL =====================
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    # User DM → forward to server
    if isinstance(message.channel, discord.DMChannel):
        log.info(f"📩 DM from {message.author}: {message.content}")
        guild = bot.get_guild(GUILD_ID)
        if not guild:
            log.warning("⚠️ Guild not found! Check GUILD_ID in .env")
            return
        category = discord.utils.get(guild.categories, name=CATEGORY_NAME) or await guild.create_category(CATEGORY_NAME)
        channel = discord.utils.get(category.channels, name=str(message.author.id))
        if channel is None:
            channel = await guild.create_text_channel(name=str(message.author.id), category=category)
            await channel.send(f"📩 New ModMail opened by {message.author.mention}")
        await channel.send(f"**{message.author}**: {message.content}")

    # Staff reply → send back to user
    elif message.guild and message.channel.category and message.channel.category.name == CATEGORY_NAME:
        try:
            user = await bot.fetch_user(int(message.channel.name))
            await user.send(f"**Staff**: {message.content}")
        except:
            pass

    await bot.process_commands(message)

@bot.tree.command(name="close", description="Close a ModMail ticket")
async def close_ticket(interaction: discord.Interaction):
    if isinstance(interaction.channel, discord.DMChannel):
        return await interaction.response.send_message("❌ You can’t close tickets in DM.", ephemeral=True)
    if interaction.channel.category and interaction.channel.category.name == CATEGORY_NAME:
        await interaction.response.send_message("✅ Ticket closed.", ephemeral=True)
        await interaction.channel.delete()
    else:
        await interaction.response.send_message("❌ Not a ModMail ticket.", ephemeral=True)

# ===================== AUTO-REPLY CONFIG =====================
auto_replies = {
    "hi": "Hey there! 👋",
    "hello": "Hello! 😊",
    "hey": "Hey! How are you?",
    "good morning": "☀️ Good morning! Hope you have a great day!",
    "good night": "🌙 Good night! Sweet dreams!",
    "bye": "👋 See you later!",
    "thanks": "You're welcome! 🙏",
    "help": "Need help? Use `/help` or DM me!",
}

# ===================== EVENTS (update on_message) =====================
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    # -------------------- AUTO-REPLY --------------------
    content = message.content.lower().strip()
    if content in auto_replies:
        await message.channel.send(auto_replies[content])

    # -------------------- MODMAIL: User DM → Server --------------------
    if isinstance(message.channel, discord.DMChannel):
        log.info(f"📩 DM from {message.author}: {message.content}")
        guild = bot.get_guild(GUILD_ID)
        if not guild:
            log.warning("⚠️ Guild not found! Check GUILD_ID in .env")
            return
        category = discord.utils.get(guild.categories, name=CATEGORY_NAME) or await guild.create_category(CATEGORY_NAME)
        channel = discord.utils.get(category.channels, name=str(message.author.id))
        if channel is None:
            channel = await guild.create_text_channel(name=str(message.author.id), category=category)
            await channel.send(f"📩 New ModMail opened by {message.author.mention}")
        await channel.send(f"**{message.author}**: {message.content}")

    # -------------------- MODMAIL: Staff → User --------------------
    elif message.guild and message.channel.category and message.channel.category.name == CATEGORY_NAME:
        try:
            user = await bot.fetch_user(int(message.channel.name))
            await user.send(f"**Staff**: {message.content}")
        except:
            pass

    await bot.process_commands(message)


# ===================== RUN =====================
if __name__ == "__main__":
    bot.run("MTQxMDE1MTE2NDYxMTI2NDU2NA.GyThRp.EbVnjeDf_bfmLYK0iOjlV_5JXPEbNZ1z1Ree5s")
