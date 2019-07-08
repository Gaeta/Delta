import discord, utils, time, random

from discord.ext import commands
from datetime import datetime

class GeneralCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def ping(self, ctx):
        """Displays Delta's connection latency."""

        rt_1 = time.perf_counter()
        
        msg = await utils.embed(ctx, discord.Embed(title="Connection Latency", description="Pinging..."))
        
        rt_2 = time.perf_counter()

        roundtrip = round((rt_2-rt_1) * 1000)
        websocket = round(self.bot.latency * 1000)

        fmt = await utils.embed(ctx, discord.Embed(title="Connection Latency", description=f"Roundtrip: `{roundtrip} ms`\nWebSocket: `{websocket} ms`"), send=False)

        await msg.edit(content=None, embed=fmt)

    @commands.command(aliaes=["commands"])
    async def help(self, ctx, command=None):
        """Shows a list of every Delta command."""

        if not command:
            return await utils.embed(ctx, discord.Embed(title="Command List", description="Here's a list of every command Delta has:\n%s" % "\n\n".join(f"• `{ctx.bot.config.prefix}{cmd.name}`\n- {cmd.short_doc}" for cmd in self.bot.commands)).set_footer(text=f"To view a command's help profile, use {ctx.bot.config.prefix}help [command]"))

        if command.startswith(ctx.bot.config.prefix):
            command = command[3:]

        cmd = self.bot.get_command(command)
        
        if cmd is None:
            return await utils.embed(ctx, discord.Embed(description=f"Sorry, I couldn't find the `{ctx.bot.config.prefix}{command}` command."), override_author=True)

        await utils.embed(ctx, discord.Embed(title="Command Help", description=f"Here's the help profile for the `{ctx.bot.config.prefix}{cmd.name}` command:\n\n**Name:** `{ctx.bot.config.prefix}{cmd.name}`\n**Usage:** `{utils.command_usage(ctx, cmd)}`\n**Aliases:** {' | '.join(f'`{ctx.bot.config.prefix}{alias}`' for alias in cmd.aliases) if len(cmd.aliases) > 0 else 'None'}\n**Description:** {cmd.short_doc}"))

    @commands.command(aliases=["developers"])
    async def devs(self, ctx):
        """Shows a list of every Delta developer."""

        await utils.embed(ctx, discord.Embed(title="Delta Developers", description="Here are the people who made Delta:\n%s" % "\n".join(f"• **{self.bot.get_user(dev)}**" for dev in (269758783557730314, 263396882762563584))))

    @commands.command(aliases=["mods", "admins"])
    @utils.guild_only()
    async def staff(self, ctx):
        """Shows a detailed list of the server's staff."""

        staff_list = utils.staff(ctx)
        emoji_list = self.bot.config.emojis

        staff = {
            "online": [staff for staff in staff_list if staff.status is discord.Status.online],
            "idle": [staff for staff in staff_list if staff.status is discord.Status.idle],
            "dnd": [staff for staff in staff_list if staff.status is discord.Status.dnd],
            "offline": [staff for staff in staff_list if staff.status is discord.Status.offline]
        }
        emojis = {
            "online": emoji_list.online,
            "idle": emoji_list.idle,
            "dnd": emoji_list.dnd,
            "offline": emoji_list.offline
        }

        display = "\n\n".join(f"<:{status}:{emojis[status]}> __**{status.capitalize()}**__\n" + ("\n".join(f"> {staff}" for staff in staff[status]) if len(staff[status]) > 0 else f"*No staff are {status}*") for status in ("online", "idle", "dnd", "offline"))

        await utils.embed(ctx, discord.Embed(title=f"{ctx.guild} Staff", description=f"Below is a list of every Moderator & Administrator in **{ctx.guild}**:\n\n{display}"))

    @commands.command(aliases=["pingadmin", "pingmod"])
    @utils.guild_only()
    @commands.cooldown(1, 60 * 5, commands.BucketType.member)
    async def pingstaff(self, ctx, *, message):
        """Picks an on-duty staff member at random and pings them."""

        staff = [staff for staff in utils.staff(ctx) if staff.status not in (discord.Status.idle, discord.Status.offline)]

        if not staff:
            return await utils.embed(ctx, discord.Embed(title="Autoping Failed", description="Sorry, there are no Moderators available."), error=True)

        staff = random.choice(staff)

        try:
            await staff.send(f"__**Mod Autoping:**__\n\n{message}\n\n{staff.mention} (by **{ctx.author}**)")
            await utils.embed(ctx, discord.Embed(timestamp=datetime.utcnow(), title="Moderator Autoping", description=f"**{ctx.author}** requested help from a Moderator.\n\n__**Sent message:**__\n\n{message}\n\n__**Pinged Moderator:**__\n\n{staff.mention}\nA Direct Message was successfully sent."))

        except:
            await ctx.send(f"__**Mod Autoping:**__\n\n{message}\n\n{staff.mention} (by **{ctx.author}**)")
            await utils.embed(ctx, discord.Embed(timestamp=datetime.utcnow(), title="Moderator Autoping", description=f"**{ctx.author}** requested help from a Moderator.\n\n__**Sent message:**__\n\n{message}\n\n__**Pinged Moderator:**__\n\n{staff.mention}\nSend a Direct Message failed, so a message was posted in this channel."))

    @commands.command(aliases=["getnews", "togglenews", "polls", "getpolls", "togglepolls"])
    @utils.guild_only()
    @commands.cooldown(3, 60, commands.BucketType.member)
    async def news(self, ctx):
        """Toggles the poll/announcement ping role."""

        ping_role = utils.get_ping_role(ctx)

        if ping_role is None:
            return await utils.embed(ctx, discord.Embed(title="Toggle Failed", description=f"Sorry, the `pings` role hasn't been configured."), error=True)

        if ping_role == ctx.guild.default_role:
            return await utils.embed(ctx, discord.Embed(title="Toggle Failed", description=f"Sorry, the `pings` role is currently set to @everyone."), error=True)

        try:
            if not ping_role in ctx.author.roles:
                await ctx.author.add_roles(ping_role)

                change = "added"

            else:
                await ctx.author.remove_roles(ping_role)

                change = "removed"

            await utils.embed(ctx, discord.Embed(title="Toggle Successful", description=f"I have successfully **{change}** {ping_role.mention}."))

        except discord.Forbidden:
            return await utils.embed(ctx, discord.Embed(title="Toggle Failed", description=f"I do not have permission to **add** {ping_role.mention}."), error=True)

    @commands.command(aliases=["userinfo"])
    @utils.guild_only()
    async def user(self, ctx, user: discord.Member=None):
        """Shows info on a user."""

        if user is None:
            user = ctx.author

        emoji_list = self.bot.config.emojis

        emoji = {
            "online": f"<:online:{emoji_list.online}>",
            "idle": f"<:idle:{emoji_list.idle}>",
            "dnd": f"<:dnd:{emoji_list.dnd}>",
            "offline": f"<:offline:{emoji_list.offline}>",
            "streaming": f"<:streaming:{emoji_list.streaming}>",
        }[str(user.status) if not utils.is_streaming(user) else "streaming"]

        hoist_role = utils.hoist_role(user)
        colour_role = utils.colour_role(user)
        user.roles.remove(ctx.guild.default_role)

        await utils.embed(ctx, discord.Embed(timestamp=user.created_at, colour=user.colour, title="User Info", description=f"{emoji} {user.mention} (`{user.nick if user.nick else user.name}`)" + ("\n" + "\u2000"*4 + f"{utils.activity_info(user)}" if user.activity is not None else "")).add_field(name="User ID", value=user.id).add_field(name="Highest Role", value=f"{user.top_role.mention} ({user.top_role.name})" if user.top_role.id != ctx.guild.id else "None").add_field(name="Hoist Role", value=f"{hoist_role.mention} ({hoist_role.name})" if hoist_role is not None else "None").add_field(name="Colour Role", value=f"{colour_role.mention} ({colour_role.name})" if colour_role is not None else "None").add_field(name=f"Roles ({len(user.roles)-1})", value=", ".join(role.name for role in user.roles[::-1][0:10])  + ("..." if len(user.roles) > 10 else "") if len(user.roles) > 1 else "None").set_footer(text="Created at:").set_thumbnail(url=user.avatar_url), override_colour=user.colour.value != 0)

def setup(bot):
    bot.add_cog(GeneralCommands(bot))