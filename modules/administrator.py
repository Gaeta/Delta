import discord, sqlite3, asyncio, utils, re

from discord.ext import commands
from datetime import datetime

intervals = (("weeks", 60 * 60 * 24 * 7), ("days", 60 * 60 * 24), ("hours", 60 * 60), ("minutes", 60), ("seconds", 1))

TIME_REGEX = re.compile("(?:(\d{1,5})\s?(h|hours|hrs|hour|hr|s|seconds|secs|sec|second|m|mins|minutes|minute|min|d|days|day))+?")
TIME_DICT = {"h": 3600, "s": 1, "m": 60, "d": 86400}

def display_time(seconds, granularity=2):
    result = []

    for name, count in intervals:
        value = seconds // count
        if value:
            seconds -= value * count

            if value == 1:
                name = name.rstrip("s")
            
            result.append("{} {}".format(value, name))

    return ", ".join(result[:granularity])

class TimeConverter(commands.Converter):
    async def convert(self, argument):
        if argument is None:
            return 0

        args = argument.lower()
        matches = re.findall(TIME_REGEX, args)
        time = 0

        for v, k in matches:
            try:
                for key in ("h", "s", "m", "d"):
                    if k.startswith(key):
                        k = key
                        break

                time += TIME_DICT[k]*float(v)
            
            except KeyError:
                raise commands.BadArgument("{} is an invalid time-key! h/m/s/d are valid!".format(k))
            
            except ValueError:
                raise commands.BadArgument("{} is not a number!".format(v))
        
        return time

class AdministratorCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.guild_only()
    @utils.is_admin()
    async def announce(self, ctx, *, announcement):
        """Creates an announcement."""

        channel_id = self.bot.config.channels.announcements
        channel = self.bot.get_channel(channel_id)

        try:
            await channel.send(announcement)

            await utils.embed(ctx, discord.Embed(title="Announcement Sent", description=f"Your announcement was successfully posted in {channel.mention}."), error=True)

        except:
            if channel.permissions_for(ctx.guild.me).send_messages is False:
                issue = f"I do not have permission to **send messages** in <#{channel.mention}>."

            await utils.embed(ctx, discord.Embed(title="Announcement Failed", description=issue), error=True)

    @commands.command(aliases=["resetcase"])
    @commands.guild_only()
    @utils.is_admin()
    async def resetid(self, ctx):
        """Resets the case ID."""

        with sqlite3.connect(self.bot.config.database) as db:
            db.cursor().execute("UPDATE Settings SET Case_ID='0'")
            db.cursor().execute("DELETE FROM Cases")
            db.commit()

        await utils.embed(ctx, discord.Embed(timestamp=datetime.utcnow(), title="Data Wiped", description="All case data has been successfully cleared."))

    @commands.command(aliases=["reloadconfig"])
    @commands.guild_only()
    @utils.is_admin()
    async def reload(self, ctx):
        """Reloads the config file."""

        del self.bot.config

        self.bot.config = utils.Config()

        await utils.embed(ctx, discord.Embed(timestamp=datetime.utcnow(), title="Config Reloaded", description="All config data has been successfully reloaded."))

    @commands.command()
    @commands.guild_only()
    @commands.bot_has_permissions(manage_channels=True)
    @utils.is_admin()
    async def lockdown(self, ctx, *, time=None):
        """Locks or unlocks a channel for a specified amount of time."""

        member_role = utils.get_member_role(ctx)
        ows = ctx.channel.overwrites_for(member_role)

        if ows.read_messages is False:
            return await utils.embed(ctx, discord.Embed(timestamp=datetime.utcnow(), title="Lockdown Failed", description=f"Sorry, I can only lock channels that can be seen by {member_role.mention if member_role != ctx.guild.default_role else member_role}."), error=True)

        if ows.send_messages is False:
            await ctx.channel.set_permissions(member_role, send_messages=None)
            await ctx.channel.set_permissions(ctx.guild.me, send_messages=None)
            return await utils.embed(ctx, discord.Embed(timestamp=datetime.utcnow(), title="Lockdown Deactivated", description=f"Lockdown has been lifted by **{ctx.author}**."))

        if ows.send_messages in (True, None):
            seconds = await TimeConverter().convert(time)

            await ctx.channel.set_permissions(member_role, send_messages=False)
            await ctx.channel.set_permissions(ctx.guild.me, send_messages=True)
            
            if seconds < 1:
                return await utils.embed(ctx, discord.Embed(timestamp=datetime.utcnow(), title="Lockdown Activated", description=f"Lockdown has been activated by **{ctx.author}**."))

            await utils.embed(ctx, discord.Embed(timestamp=datetime.utcnow(), title="Lockdown Activated", description=f"Lockdown has been activated by **{ctx.author}** for {display_time(round(seconds), 4)}."))
            await asyncio.sleep(seconds)

            ows = ctx.channel.overwrites_for(member_role)
            if ows.send_messages is False:
                await ctx.channel.set_permissions(member_role, send_messages=None)
                await ctx.channel.set_permissions(ctx.guild.me, send_messages=None)
                return await utils.embed(ctx, discord.Embed(timestamp=datetime.utcnow(), title="Lockdown Deactivated", description=f"Lockdown has been lifted."))

def setup(bot):
    bot.add_cog(AdministratorCommands(bot))