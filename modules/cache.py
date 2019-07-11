import discord

from discord.ext import commands
from collections import namedtuple
from datetime import datetime

Storage = namedtuple("Storage", "spam, tags, logs, pings, boot")
default_values = {"spam": set(), "tags": {}, "logs": [], "pings": [], "boot": datetime.utcnow()}

class Cache(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.bot.cache = Storage._make(value for value in default_values.values())

def setup(bot):
    bot.add_cog(Cache(bot))