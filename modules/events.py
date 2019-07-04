import discord, re, utils, sqlite3

from discord.ext import commands
from datetime import datetime

try:
    from pyfiglet import print_figlet

except ImportError:
    utils.error("PyFiglet is not installed, run pip3 install pyfiglet.", "Events", terminate=True)

SLUR_REGEX = r"nigg(er|a)|faggot|tranny|crack(er|a)"
INVITE_REGEX = r"(https?:\/\/)?(www\.)?((discord|invite)\.(gg|io|me|li)|discordapp\.com\/invite)\/.+[a-z]"
NSFW_REGEX = r"(https?:\/\/)?(www\.)?(pornhub|redtube|youporn|tube8|pornmd|thumbzilla|modelhub)\.com"
LINK_REGEX = r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\), ]|(?:%[0-9a-fA-F][0-9a-fA-F]))+"
INV_VALID_REGEX = r"(https?:\/\/)?(www\.)?(discord\.gg|discordapp\.com\/invite)\/(.[^\s]+)"

class BasicEvents(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def perm_cleanup(self, perm):
        return perm.replace("_", " ").title()

    @commands.Cog.listener()
    async def on_ready(self):
        print_figlet(self.bot.config.figlet)

        display = self.bot.config.presence
        await self.bot.change_presence(activity=display.activity, status=display.status)

        with sqlite3.connect(self.bot.config.database) as db:
            for table, columns in (("Settings", "Case_ID TEXT"), ("Cases", "Mod_ID TEXT, User_ID TEXT, Case_ID TEXT, Msg_ID TEXT, Punishment TEXT, Reason TEXT"), ("Mute_Evaders", "User_ID TEXT"), ("Duty", "User_ID TEXT, Admin TEXT, Mod TEXT, Staff TEXT, Support TEXT")):
                db.cursor().execute(f"CREATE TABLE IF NOT EXISTS {table} ({columns})")
            
            if db.cursor().execute("SELECT * FROM Settings").fetchone() is None:
                db.cursor().execute("INSERT INTO Settings VALUES ('0')")
            
            db.commit()

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandNotFound):
            return

        if isinstance(error, commands.CommandOnCooldown):
            hours, remainder = divmod(error.retry_after, 3600)
            minutes, seconds = divmod(remainder, 60)
            days, hours = divmod(hours, 24)

            text = []
            
            if days > 0:
                text.append(f"{days} days")

            if hours > 0:
                text.append(f"{hours} hours")

            if minutes > 0:
                text.append(f"{minutes} minutes")

            if seconds > 0:
                text.append(f"{seconds} seconds")

            return await utils.embed(ctx, discord.Embed(title="Cooldown Active", description=f"Sorry, the command `{ctx.bot.config.prefix}{ctx.command.name}` is on cooldown. Try again in {', '.join(text)}"), error=True)

        if isinstance(error, commands.MissingRequiredArgument):
            return await utils.embed(ctx, discord.Embed(title="Missing Arguments", description=f"Sorry, it seems you haven't provided the `{error.param}` argument. Please check the usage instructions via `{ctx.bot.config.prefix}help {ctx.command.name}` and try again."), error=True)

        if isinstance(error, commands.BadArgument):
            return await utils.embed(ctx, discord.Embed(title="Invalid Arguments", description=f"Sorry, it seems you have provided an incorrect argument argument. Please check the usage instructions via `{ctx.bot.config.prefix}help {ctx.command.name}` and try again."), error=True)

        if isinstance(error, commands.BotMissingPermissions):
            return await utils.embed(ctx, discord.Embed(title="Missing Permission", description=f"Sorry, it seems I am missing the {', '.join(f'**{self.perm_cleanup(perm)}**' for perm in error.missing_perms)} {'permissions' if len(error.missing_perms) > 1 else 'permission'}."), error=True)

        if isinstance(error, commands.CheckFailure):
            if "guild_predicate" in [check.__name__ for check in ctx.command.checks]:
                server = self.bot.get_guild(self.bot.config.server)

                if ctx.guild is None:
                    return await utils.embed(ctx, discord.Embed(title="Server Only", description=f"Sorry, that command may only be used in **{server}**."), error=True)

                if ctx.guild.id != server.id:
                    return await utils.embed(ctx, discord.Embed(title="Server Only", description=f"Sorry, that command may only be used in **{server}**."), error=True)

            if "mod_predicate" in [check.__name__ for check in ctx.command.checks]:
                server = self.bot.get_guild(self.bot.config.server)
                role = server.get_role(self.bot.config.roles.mod)

                if role is None:
                    raise utils.InvalidConfig("Roles", "int", "Mod")

                return await utils.embed(ctx, discord.Embed(title="Missing Permission", description=f"Sorry, it seems you are missing the {role.mention} role."), error=True)

            if "admin_predicate" in [check.__name__ for check in ctx.command.checks]:
                server = self.bot.get_guild(self.bot.config.server)
                role = server.get_role(self.bot.config.roles.admin)

                if role is None:
                    raise utils.InvalidConfig("Roles", "int", "Admin")

                return await utils.embed(ctx, discord.Embed(title="Missing Permission", description=f"Sorry, it seems you are missing the {role.mention} role."), error=True)

        return await utils.embed(ctx, discord.Embed(title="Unknown Error", description=f"Sorry, it seems I've encountered an unknown error: {error.__cause__}"), error=True)

    @commands.Cog.listener()
    async def on_member_join(self, user):
        try:
            if user is None:
                return

            if user.guild.id != self.bot.config.server:
                return

            await utils.user_log(self, user)

            with sqlite3.connect(self.bot.config.database) as db:
                evader = db.cursor().execute("SELECT User_ID FROM Mute_Evaders WHERE User_ID=?", (user.id,)).fetchone()

                if evader is None:
                    return

                self.bot.log_interceptors.add(f"{user.id}:{user.guild.id}:Mute")
                await utils.mute(self.bot, user, f"[ Auto Mod ] >> Mute evasion detected")
                await utils.mod_log(self, user, "mute", self.bot.user, f"[ Auto Mod ] >> Mute evasion detected")

                db.cursor().execute("DELETE FROM Mute_Evaders WHERE User_ID=?", (user.id,))
                db.commit()

        except utils.InvalidConfig as error:
            await utils.handle_invalid_config(self, error)

    @commands.Cog.listener()
    async def on_member_remove(self, user):
        try:
            if user is None:
                return

            if user.guild.id != self.bot.config.server or user.id == self.bot.user.id:
                return

            await utils.user_log(self, user, stance="leave")

        except utils.InvalidConfig as error:
            await utils.handle_invalid_config(self, error)

class ModEvents(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.add_listener(self.anti_spam, "on_message")

        self.spam_ignore = set()

    @commands.Cog.listener()
    async def on_message(self, m):
        try:
            if m.guild is None:
                return

            if m.guild.id != self.bot.config.server:
                return

            if m.author.guild_permissions.manage_messages or utils.mod(self.bot, m):
                return

            if re.search(LINK_REGEX, m.content, re.IGNORECASE):
                module = utils.auto_mod(self.bot, "link")

                if module is False:
                    return

                if not module.enabled or m.channel.id in module.bypassed_channels:
                    return

                bypassed = []
                for link in module.bypassed_links:
                    if link.lower() in m.content.lower():
                        bypassed.append(link)

                if len(bypassed) > 0:
                    msg = m.content
                    for link in bypassed:
                        msg = msg.replace(link, "")

                    if not re.search(LINK_REGEX, msg, re.IGNORECASE):
                        return

                await utils.auto_punish(self, m.author, m.channel, "Link detected")

                return await m.delete()

            if re.search(SLUR_REGEX, m.content, re.IGNORECASE):
                module = utils.auto_mod(self.bot, "slur")

                if module is False:
                    return

                if not module.enabled or m.channel.id in module.bypassed_channels:
                    return

                await utils.auto_punish(self, m.author, m.channel, "Slur detected")

                return await m.delete()

            if re.search(INVITE_REGEX, m.content, re.IGNORECASE):
                module = utils.auto_mod(self.bot, "invite")

                if module is False:
                    return

                if not module.enabled or m.channel.id in module.bypassed_channels:
                    return

                try:
                    inv_code = re.search(INV_VALID_REGEX, m.content, re.IGNORECASE)

                    if inv_code is not None:
                        inv = await self.bot.fetch_invite(inv_code.groups()[-1])
                    
                        if inv.guild.id == m.guild.id:
                            return

                        if module.bypass_verified:
                            for feature in ("VERIFIED", "PARTNERED"):
                                if feature in inv.guild.features:
                                    return

                except discord.NotFound:
                    return

                await utils.auto_punish(self, m.author, m.channel, "Invite detected")

                return await m.delete()

            module = utils.auto_mod(self.bot, "nsfw")
            
            if module is False:
                return

            if not module.enabled or m.channel.id in module.bypassed_channels:
                return

            if re.search(NSFW_REGEX, m.content, re.IGNORECASE) or len([link for link in module.extra_links if link.lower() in m.content.lower()]) > 0:
                await utils.auto_punish(self, m.author, m.channel, "NSFW detected")

                return await m.delete()
            
        except utils.InvalidConfig as error:
            await utils.handle_invalid_config(self, error)

    @commands.Cog.listener()
    async def anti_spam(self, message):
        try:
            if message.guild is None:
                return

            if message.guild.id != self.bot.config.server:
                return

            if message.author.guild_permissions.manage_messages or utils.mod(self.bot, message):
                return

            def is_author(m):
                return m.author == message.author and m.channel == message.channel
            
            module = utils.auto_mod(self.bot, "spam")

            if module is False:
                return

            if not module.enabled or message.channel.id in module.bypassed_channels or f"{message.author.id}:{message.channel.id}" in self.spam_ignore:
                return

            timeout = module.threshold_seconds

            try:
                self.spam_ignore.add(f"{message.author.id}:{message.channel.id}")

                m1 = await self.bot.wait_for("message", check=is_author, timeout=timeout)
                time_gap = m1.created_at.second + timeout

                m2 = await self.bot.wait_for("message", check=is_author, timeout=timeout)
                if m2.created_at.second > time_gap:
                    return

                m3 = await self.bot.wait_for("message", check=is_author, timeout=timeout)
                if m3.created_at.second > time_gap:
                    return
                    
                m4 = await self.bot.wait_for("message", check=is_author, timeout=timeout)
                if m4.created_at.second > time_gap:
                    return

                def is_spam(m):
                    return m.content in (message.content, m1.content, m2.content, m3.content, m4.content)

                await utils.auto_punish(self, message.author, message.channel, "Spam detected")

                await message.channel.purge(check=is_spam)

            except:
                try:
                    return self.spam_ignore.remove(f"{message.author.id}:{message.channel.id}")
                
                except:
                    return

        except utils.InvalidConfig as error:
            await utils.handle_invalid_config(self, error)

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        try:
            if after.guild.id != self.bot.config.server:
                return

            role = after.guild.get_role(self.bot.config.roles.muted)

            if role in after.roles and not role in before.roles:
                if f"{after.id}:{after.guild.id}:Mute" in self.bot.log_interceptors:
                    return self.bot.log_interceptors.remove(f"{after.id}:{after.guild.id}:Mute")

                await utils.mod_log(self, after, "mute", "???")

            if role in before.roles and not role in after.roles:
                if f"{after.id}:{after.guild.id}:Unmute" in self.bot.log_interceptors:
                    return self.bot.log_interceptors.remove(f"{after.id}:{after.guild.id}:Unmute")

                await utils.mod_log(self, after, "unmute", "???")

        except utils.InvalidConfig as error:
            await utils.handle_invalid_config(self, error)

    @commands.Cog.listener()
    async def on_member_unban(self, guild, user):
        try:
            if user is None:
                return

            if user.guild.id != self.bot.config.server or user.id == self.bot.user.id:
                return

            if f"{user.id}:{guild.id}:Unban" in self.bot.log_interceptors:
                return self.bot.log_interceptors.remove(f"{user.id}:{guild.id}:Unban")

            await utils.mod_log(self, user, "unban", "???")
        
        except utils.InvalidConfig as error:
            await utils.handle_invalid_config(self, error)

    @commands.Cog.listener()
    async def on_member_remove(self, user):
        try:
            if user is None:
                return

            if user.guild.id != self.bot.config.server or user.id == self.bot.user.id:
                return
        
            if not user.guild.me.guild_permissions.view_audit_log:
                return

            role = user.guild.get_role(self.bot.config.roles.muted)

            if f"{user.id}:{user.guild.id}:Kick" in self.bot.log_interceptors:
                return self.bot.log_interceptors.remove(f"{user.id}:{user.guild.id}:Kick")

            async for log in user.guild.audit_logs(limit=1, action=discord.AuditLogAction.kick, after=datetime.utcnow()):
                now = datetime.utcnow().second
                if log.target is not None and log.target.id == user.id and log.action == discord.AuditLogAction.kick and log.created_at.second in (now, now - 1, now - 2):
                    return await utils.mod_log(self, user, "kick", log.user)

            if role in user.roles:
                with sqlite3.connect(self.bot.config.database) as db:
                    db.cursor().execute("INSERT INTO Mute_Evaders VALUES (?)", (user.id,))
                    db.commit()

        except utils.InvalidConfig as error:
            await utils.handle_invalid_config(self, error)

    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):
        try:
            if user is None:
                return

            if user.guild.id != self.bot.config.server or user.id == self.bot.user.id:
                return

            if f"{user.id}:{guild.id}:Ban" in self.bot.log_interceptors:
                return self.bot.log_interceptors.remove(f"{user.id}:{guild.id}:Ban")

            try:
                reason = await guild.fetch_ban(user).reason

            except:
                reason = None

            await utils.mod_log(self, user, "ban", "???", reason=reason)

        except utils.InvalidConfig as error:
            await utils.handle_invalid_config(self, error)

def setup(bot):
    bot.add_cog(BasicEvents(bot))
    bot.add_cog(ModEvents(bot))