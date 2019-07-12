import discord, sqlite3, asyncio, utils, re

from discord.ext import commands
from datetime import datetime

TIME_REGEX = re.compile("(?:(\d{1,5})\s?(h|hours|hrs|hour|hr|s|seconds|secs|sec|second|m|mins|minutes|minute|min|d|days|day))+?")
TIME_DICT = {"h": 3600, "s": 1, "m": 60, "d": 86400}

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

    @commands.command(usage="poll <ping> <question> | <answer 1> | <answer2...>")
    @utils.guild_only()
    @utils.is_admin()
    @commands.bot_has_permissions(manage_roles=True)
    @commands.cooldown(1, 60, commands.BucketType.guild)
    async def poll(self, ctx, ping_member, *, args):
        """Creates a poll with up to 5 answers."""

        ping = ping_member.lower()

        if ping not in ("yes", "no", "true", "false", "y", "n", "t", "f"):
            return await utils.embed(ctx, discord.Embed(title="Poll Failed", description=f"Sorry, the `ping_member` argument should be \"Yes\" or \"No\". Please use `{self.bot.config.prefix}help poll` for more information."), error=True)

        if ping in ("yes", "y", "true", "t"):
            ping = True

        if ping in ("no", "n", "no", "n"):
            ping = False

        ques_ans = args.split(" | ")
        
        if len(ques_ans) <= 2:
            return await utils.embed(ctx, discord.Embed(title="Poll Failed", description=f"Sorry, the `args` argument should be follow this syntax: `question | answer 1 | answer 2...`."), error=True)

        question = ques_ans[0]
        answers = ques_ans[1:6]

        channel_id = self.bot.config.channels.announcements
        channel = self.bot.get_channel(channel_id)

        if channel is None:
            return await utils.embed(ctx, discord.Embed(title="Poll Failed", description=f"Sorry, the `announcements` channel hasn't been configured."), error=True)

        reactions = []
        text = ""

        i = 1
        for answer in answers:
            react = {1: "1\u20e3", 2: "2\u20e3", 3: "3\u20e3", 4: "4\u20e3", 5: "5\u20e3"}[i]
            reactions.append(react)
            text += f"{react} {answers[i-1]}\n\n"
            i += 1

        embed = await utils.embed(ctx, discord.Embed(timestamp=datetime.utcnow(), title="Server Poll", description=f"**{question}**\n\n{text}").set_footer(text=f"Poll by {ctx.author}"), send=False)

        if ping:
            ping_role = utils.get_ping_role(ctx)

            if ping_role != ctx.guild.default_role:
                if not ping_role.mentionable:
                    edited = False
                    try:
                        await ping_role.edit(mentionable=True)
                        edited = True

                    except discord.Forbidden:
                        return await utils.embed(ctx, discord.Embed(title="Poll Failed", description=f"I do not have permission to **edit** {ping_role.mention}."), error=True)

                try:
                    message = await channel.send(ping_role.mention, embed=embed)
                    await utils.embed(ctx, discord.Embed(title="Poll Created", description=f"Your poll was successfully posted in {channel.mention}."), error=True)

                    for r in reactions:
                        await message.add_reaction(r)

                except:
                    if channel.permissions_for(ctx.guild.me).add_reactions is False:
                        issue = f"I do not have permission to **add reactions** in <#{channel.mention}>."

                    if channel.permissions_for(ctx.guild.me).send_messages is False:
                        issue = f"I do not have permission to **send messages** in <#{channel.mention}>."

                    return await utils.embed(ctx, discord.Embed(title="Poll Failed", description=issue), error=True)

                if edited:
                    await ping_role.edit(mentionable=False)

                return

        try:
            message = await channel.send(content="@everyone" if ping else None, embed=embed)
            await utils.embed(ctx, discord.Embed(title="Poll Created", description=f"Your poll was successfully posted in {channel.mention}."), error=True)

            for r in reactions:
                await message.add_reaction(r)

        except:
            if channel.permissions_for(ctx.guild.me).add_reactions is False:
                issue = f"I do not have permission to **add reactions** in <#{channel.mention}>."

            if channel.permissions_for(ctx.guild.me).send_messages is False:
                issue = f"I do not have permission to **send messages** in <#{channel.mention}>."

            await utils.embed(ctx, discord.Embed(title="Poll Failed", description=issue), error=True)

    @commands.command(usage="announce <ping> <announcement>")
    @utils.guild_only()
    @utils.is_admin()
    async def announce(self, ctx, ping_member, *, announcement):
        """Creates an announcement."""

        ping = ping_member.lower()

        if ping not in ("yes", "no", "true", "false", "y", "n", "t", "f"):
            return await utils.embed(ctx, discord.Embed(title="Announcement Failed", description=f"Sorry, the `ping_member` argument should be \"Yes\" or \"No\". Please use `{self.bot.config.prefix}help announce` for more information."), error=True)

        if ping in ("yes", "y", "true", "t"):
            ping = True

        if ping in ("no", "n", "no", "n"):
            ping = False

        channel_id = self.bot.config.channels.announcements
        channel = self.bot.get_channel(channel_id)

        if channel is None:
            return await utils.embed(ctx, discord.Embed(title="Announcement Failed", description=f"Sorry, the `announcements` channel hasn't been configured."), error=True)

        if ping:
            ping_role = utils.get_ping_role(ctx)

            if ping_role != ctx.guild.default_role:
                if not ping_role.mentionable:
                    edited = False
                    try:
                        await ping_role.edit(mentionable=True)
                        edited = True

                    except discord.Forbidden:
                        return await utils.embed(ctx, discord.Embed(title="Announcement Failed", description=f"I do not have permission to **edit** {ping_role.mention}."), error=True)

                try:
                    await channel.send(f"{ping_role.mention}\n{announcement}")
                    await utils.embed(ctx, discord.Embed(title="Announcement Sent", description=f"Your announcement was successfully posted in {channel.mention}."), error=True)

                except:
                    if channel.permissions_for(ctx.guild.me).send_messages is False:
                        issue = f"I do not have permission to **send messages** in <#{channel.mention}>."

                    return await utils.embed(ctx, discord.Embed(title="Announcement Failed", description=issue), error=True)

                if edited:
                    await ping_role.edit(mentionable=False)

                return

        try:
            await channel.send("@everyone\n" if ping else "" + announcement)
            await utils.embed(ctx, discord.Embed(title="Announcement Sent", description=f"Your announcement was successfully posted in {channel.mention}."), error=True)

        except:
            if channel.permissions_for(ctx.guild.me).send_messages is False:
                issue = f"I do not have permission to **send messages** in <#{channel.mention}>."

            await utils.embed(ctx, discord.Embed(title="Poll Failed", description=issue), error=True)

    @commands.command(aliases=["resetcase"], usage="resetid")
    @utils.guild_only()
    @utils.is_admin()
    async def resetid(self, ctx):
        """Resets the case ID."""

        with sqlite3.connect(self.bot.config.database) as db:
            db.cursor().execute("UPDATE Settings SET Case_ID='0'")
            db.cursor().execute("DELETE FROM Cases")
            db.commit()

        await utils.embed(ctx, discord.Embed(timestamp=datetime.utcnow(), title="Data Wiped", description="All case data has been successfully cleared."))

    @commands.command(aliases=["reloadconfig"], usage="reload")
    @utils.guild_only()
    @utils.is_admin()
    async def reload(self, ctx):
        """Reloads the config file."""

        del self.bot.config

        self.bot.config = utils.Config()

        await utils.embed(ctx, discord.Embed(timestamp=datetime.utcnow(), title="Config Reloaded", description="All config data has been successfully reloaded."))

    @commands.command(usage="lockdown [time]")
    @utils.guild_only()
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

            await utils.embed(ctx, discord.Embed(timestamp=datetime.utcnow(), title="Lockdown Activated", description=f"Lockdown has been activated by **{ctx.author}** for {utils.display_time(round(seconds), 4)}."))
            await asyncio.sleep(seconds)

            ows = ctx.channel.overwrites_for(member_role)
            if ows.send_messages is False:
                await ctx.channel.set_permissions(member_role, send_messages=None)
                await ctx.channel.set_permissions(ctx.guild.me, send_messages=None)
                return await utils.embed(ctx, discord.Embed(timestamp=datetime.utcnow(), title="Lockdown Deactivated", description=f"Lockdown has been lifted."))

def setup(bot):
    bot.add_cog(AdministratorCommands(bot))