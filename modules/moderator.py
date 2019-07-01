import discord, utils, re, asyncio, sqlite3

from discord.ext import commands
from datetime import datetime

class ModeratorCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.bot.log_interceptors = set()

    @commands.command()
    @commands.guild_only()
    @commands.bot_has_permissions(ban_members=True)
    @utils.is_mod()
    async def bans(self, ctx):
        """Lists the server's ban list."""

        bans = await ctx.guild.bans()
        await utils.embed(ctx, discord.Embed(title=f"Server Banlist ({len(bans)})", description="\n".join([str(ban.user) for ban in bans[:20]]) if len(bans) > 0 else "*No one has been banned yet...*").set_footer(text="No more than 20 bans are shown here."))

    @commands.command()
    @commands.guild_only()
    async def case(self, ctx, case_id):
        """Shows info on a case."""

        case = await utils.get_case(self.bot, case_id)

        if case is None:
            return await utils.embed(ctx, discord.Embed(timestamp=datetime.utcnow(), title="Lookup Failed", description=f"Sorry, I could not find a case with the ID {case_id}."), error=True)

        send = await utils.embed(ctx, discord.Embed(colour=utils.case_colour(self.bot, case.punishment), timestamp=datetime.utcnow(), title=f"{case.punishment.title()} | Case #{case_id}").add_field(name="User" if not case.user.bot else "Bot", value=f"{case.user} ({case.user.mention})").add_field(name="Moderator", value=case.mod if hasattr(case.mod, "id") else f"??? (Moderator: do `{ctx.bot.config.prefix}reason {case_id}`)").add_field(name="Reason", value=case.reason if case.reason else f"Moderator: please do `{ctx.bot.config.prefix}reason {case_id} <reason>`", inline=False).set_footer(text=f"ID: {case.user.id}"), override_colour=True)
        await ctx.send(embed=send)

    @commands.command()
    @commands.guild_only()
    @utils.is_mod()
    async def reason(self, ctx, case_id, *, reason):
        """Edits the reason on a mod case."""

        if ctx.channel.id != self.bot.config.channels.mod_log:
            return await utils.embed(ctx, discord.Embed(timestamp=datetime.utcnow(), title="Edit Failed", description=f"Sorry, that command can only be used in <#{self.bot.config.channels.mod_log}>."), error=True)

        case = await utils.get_case(self.bot, case_id)

        if case is None:
            await utils.embed(ctx, discord.Embed(timestamp=datetime.utcnow(), title="Lookup Failed", description=f"Sorry, I could not find a case with the ID {case_id}."), error=True, delete_after=15)
            await asyncio.sleep(15)
            return await ctx.message.delete()

        await ctx.message.delete()

        send = await utils.embed(ctx, discord.Embed(colour=utils.case_colour(self.bot, case.punishment), timestamp=case.message.created_at, title=f"{case.punishment.title()} | Case #{case_id}").add_field(name="User" if not case.user.bot else "Bot", value=f"{case.user} ({case.user.mention})").add_field(name="Moderator", value=ctx.author if not hasattr(case.mod, "id") else case.mod).add_field(name="Reason", value=reason, inline=False).set_footer(text=f"ID: {case.user.id}"), override_colour=True, send=False)
        await case.message.edit(embed=send, content=None)

    @commands.command(aliases=["prune", "nuke"])
    @commands.guild_only()
    @commands.bot_has_permissions(manage_messages=True)
    @utils.is_mod()
    async def purge(self, ctx, limit, users: commands.Greedy[discord.Member]):
        """Purges up to 200 messages."""

        if int(limit) > 200:
            return await utils.embed(ctx, discord.Embed(timestamp=datetime.utcnow(), title="Purge Failed", description=f"Sorry, I can only purge up to 200 messages."), error=True)

        await ctx.message.delete()

        if not users:
            purged = await ctx.channel.purge(limit=int(limit))

        if users:
            def is_user(m):
                return m.author.id in [user.id for user in users]
            
            purged = await ctx.channel.purge(limit=int(limit), check=is_user)

        await utils.embed(ctx, discord.Embed(title="Purge Successful", description=f"**{len(purged)}/{limit}** messages were successfully purged by **{ctx.author}**."), delete_after=5)

    @commands.command()
    @commands.guild_only()
    @commands.bot_has_permissions(manage_roles=True)
    @utils.is_mod()
    async def mute(self, ctx, users: commands.Greedy[discord.Member], *, reason="No reason provided."):
        """Mutes up to 5 users at once."""

        failed_mutes = []
        successful_mutes = []
        role = ctx.guild.get_role(self.bot.config.roles.muted)

        for user in users[:5]:
            if not utils.is_higher_or_equal(ctx.bot, ctx.author, user) or role in user.roles:
                failed_mutes.append(user)

            else:
                self.bot.log_interceptors.add(f"{user.id}:{ctx.guild.id}:Mute")
                await utils.mute(self.bot, user, reason)
                await utils.mod_log(ctx, user, "mute", ctx.author, reason)
                successful_mutes.append(user)

        if len(failed_mutes) < 1 and len(successful_mutes) < 1:
            return await utils.embed(ctx, discord.Embed(timestamp=datetime.utcnow(), title="Punishment Failed", description="Sorry, it appears you haven't provided any users to mute."), error=True)

        await utils.embed(ctx, discord.Embed(timestamp=datetime.utcnow(), title="Punishment Executed", description=(f"{', '.join(f'**{str(user)}**' for user in successful_mutes)} {'were' if len(successful_mutes) > 1 else 'was'} successfully **muted** because:\n\n{reason}" if len(successful_mutes) > 0 else "") + (f"\n\nI could not **mute** {', '.join(f'**{str(user)}**' for user in failed_mutes)}. Please ensure the following:\n• The users don't have a higher or equal role to you.\n• You are not trying to mute me.\n• The user isn't already muted." if len(failed_mutes) > 0 else "")))

    @commands.command()
    @commands.guild_only()
    @commands.bot_has_permissions(manage_roles=True)
    @utils.is_mod()
    async def unmute(self, ctx, users: commands.Greedy[discord.Member], *, reason="No reason provided."):
        """Unmutes up to 5 users at once."""

        failed_unmutes = []
        successful_unmutes = []
        role = ctx.guild.get_role(self.bot.config.roles.muted)

        for user in users[:5]:
            if not utils.is_higher_or_equal(ctx.bot, ctx.author, user) or role not in user.roles:
                failed_unmutes.append(user)

            else:
                self.bot.log_interceptors.add(f"{user.id}:{ctx.guild.id}:Unmute")
                await utils.unmute(self.bot, user, reason)
                await utils.mod_log(ctx, user, "unmute", ctx.author, reason)
                successful_unmutes.append(user)

        if len(failed_unmutes) < 1 and len(successful_unmutes) < 1:
            return await utils.embed(ctx, discord.Embed(timestamp=datetime.utcnow(), title="Punishment Failed", description="Sorry, it appears you haven't provided any users to unmute."), error=True)

        await utils.embed(ctx, discord.Embed(timestamp=datetime.utcnow(), title="Punishment Executed", description=(f"{', '.join(f'**{str(user)}**' for user in successful_unmutes)} {'were' if len(successful_unmutes) > 1 else 'was'} successfully **unmuted** because:\n\n{reason}" if len(successful_unmutes) > 0 else "") + (f"\n\nI could not **unmute** {', '.join(f'**{str(user)}**' for user in failed_unmutes)}. Please ensure the following:\n• The users don't have a higher or equal role to you.\n• You are not trying to unmute me.\n• The user is already muted." if len(failed_unmutes) > 0 else "")))

    @commands.command(aliases=["idban"])
    @commands.guild_only()
    @commands.bot_has_permissions(ban_members=True)
    @utils.is_mod()
    async def hackban(self, ctx, users: commands.Greedy[int], *, reason="No reason provided."):
        """Hackbans up to 5 users at once."""

        failed_bans = []
        successful_bans = []

        for user in users[:5]:
            try:
                user = await self.bot.fetch_user(user)

                if ctx.guild.get_member(user.id) is not None:
                    failed_bans.append(user)

                else:
                    try:
                        await ctx.guild.fetch_ban(user)
                        failed_bans.append(user)

                    except discord.NotFound:
                        self.bot.log_interceptors.add(f"{user.id}:{ctx.guild.id}:Ban")
                        await self.bot.http.ban(user.id, ctx.guild.id, reason=reason)
                        await utils.mod_log(ctx, user, "ban", ctx.author, reason)
                        successful_bans.append(user)

            except discord.NotFound:
                failed_bans.append(user)

        if len(failed_bans) < 1 and len(successful_bans) < 1:
            return await utils.embed(ctx, discord.Embed(timestamp=datetime.utcnow(), title="Punishment Failed", description="Sorry, it appears you haven't provided any users to ban."), error=True)

        await utils.embed(ctx, discord.Embed(timestamp=datetime.utcnow(), title="Punishment Executed", description=(f"{', '.join(f'**{str(user)}**' for user in successful_bans)} {'were' if len(successful_bans) > 1 else 'was'} successfully **banned** because:\n\n{reason}" if len(successful_bans) > 0 else "") + (f"\n\nI could not **ban** {', '.join(f'**{str(user)}**' for user in failed_bans)}. Please ensure the following:\n• The users are not in the server, use `{ctx.bot.config.prefix}ban` for that.\n• The users are not already banned.\n• The provided IDs match a user." if len(failed_bans) > 0 else "")))

    @commands.command()
    @commands.guild_only()
    @commands.bot_has_permissions(ban_members=True)
    @utils.is_mod()
    async def ban(self, ctx, users: commands.Greedy[discord.Member], *, reason="No reason provided."):
        """Bans up to 5 users at once."""

        failed_bans = []
        successful_bans = []

        for user in users[:5]:
            if not utils.is_higher_or_equal(ctx.bot, ctx.author, user):
                failed_bans.append(user)

            else:
                self.bot.log_interceptors.add(f"{user.id}:{ctx.guild.id}:Ban")
                await user.ban(reason=reason)
                await utils.mod_log(ctx, user, "ban", ctx.author, reason)
                successful_bans.append(user)

        if len(failed_bans) < 1 and len(successful_bans) < 1:
            return await utils.embed(ctx, discord.Embed(timestamp=datetime.utcnow(), title="Punishment Failed", description=f"Sorry, it appears you haven't provided any users to ban. If you are banning via ID, please use `{ctx.bot.config.prefix}hackban` instead."), error=True)

        await utils.embed(ctx, discord.Embed(timestamp=datetime.utcnow(), title="Punishment Executed", description=(f"{', '.join(f'**{str(user)}**' for user in successful_bans)} {'were' if len(successful_bans) > 1 else 'was'} successfully **banned** because:\n\n{reason}" if len(successful_bans) > 0 else "") + (f"\n\nI could not **ban** {', '.join(f'**{str(user)}**' for user in failed_bans)}. Please ensure the following:\n• The users don't have a higher or equal role to you.\n• You are not trying to ban me." if len(failed_bans) > 0 else "")))

    @commands.command()
    @commands.guild_only()
    @commands.bot_has_permissions(ban_members=True)
    @utils.is_mod()
    async def unban(self, ctx, users: commands.Greedy[int], *, reason="No reason provided."):
        """Unbans up to 5 users at once."""

        failed_unbans = []
        successful_unbans = []

        for user in users[:5]:
            try:
                user = await self.bot.fetch_user(user)

                if ctx.guild.get_member(user.id) is not None:
                    failed_unbans.append(user)

                else:
                    try:
                        await ctx.guild.fetch_ban(user)
                        self.bot.log_interceptors.add(f"{user.id}:{ctx.guild.id}:Unban")
                        await self.bot.http.unban(user.id, ctx.guild.id, reason=reason)
                        await utils.mod_log(ctx, user, "unban", ctx.author, reason)
                        successful_unbans.append(user)

                    except discord.NotFound:
                        failed_unbans.append(user)

            except discord.NotFound:
                failed_unbans.append(user)

        if len(failed_unbans) < 1 and len(successful_unbans) < 1:
            return await utils.embed(ctx, discord.Embed(timestamp=datetime.utcnow(), title="Punishment Failed", description="Sorry, it appears you haven't provided any users to unban."), error=True)

        await utils.embed(ctx, discord.Embed(timestamp=datetime.utcnow(), title="Punishment Executed", description=(f"{', '.join(f'**{str(user)}**' for user in successful_unbans)} {'were' if len(successful_unbans) > 1 else 'was'} successfully **unbanned** because:\n\n{reason}" if len(successful_unbans) > 0 else "") + (f"\n\nI could not **unban** {', '.join(f'**{str(user)}**' for user in failed_unbans)}. Please ensure the following:\n• The users are already banned.\n• The provided IDs match a user." if len(failed_unbans) > 0 else "")))

    @commands.command()
    @commands.guild_only()
    @commands.bot_has_permissions(kick_members=True)
    @utils.is_mod()
    async def kick(self, ctx, users: commands.Greedy[discord.Member], *, reason="No reason provided."):
        """Kicks up to 5 users at once."""

        failed_kicks = []
        successful_kicks = []

        for user in users[:5]:
            if not utils.is_higher_or_equal(ctx.bot, ctx.author, user):
                failed_kicks.append(user)

            else:
                self.bot.log_interceptors.add(f"{user.id}:{ctx.guild.id}:Kick")
                await user.kick(reason=reason)
                await utils.mod_log(ctx, user, "kick", ctx.author, reason)
                successful_kicks.append(user)

        if len(failed_kicks) < 1 and len(successful_kicks) < 1:
            return await utils.embed(ctx, discord.Embed(timestamp=datetime.utcnow(), title="Punishment Failed", description="Sorry, it appears you haven't provided any users to kick."), error=True)

        await utils.embed(ctx, discord.Embed(timestamp=datetime.utcnow(), title="Punishment Executed", description=(f"{', '.join(f'**{str(user)}**' for user in successful_kicks)} {'were' if len(successful_kicks) > 1 else 'was'} successfully **kicked** because:\n\n{reason}" if len(successful_kicks) > 0 else "") + (f"\n\nI could not **kick** {', '.join(f'**{str(user)}**' for user in failed_kicks)}. Please ensure the following:\n• The users don't have a higher or equal role to you.\n• You are not trying to kick me." if len(failed_kicks) > 0 else "")))

def setup(bot):
    bot.add_cog(ModeratorCommands(bot))