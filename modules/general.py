import discord, utils, time

from discord.ext import commands

class GeneralCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def ping(self, ctx):
        """Displays DisBot's connection latency"""

        rt_1 = time.perf_counter()
        
        msg = await utils.embed(ctx, discord.Embed(title="Connection Latency", description="Pinging..."))
        
        rt_2 = time.perf_counter()

        roundtrip = round((rt_2-rt_1) * 1000)
        websocket = round(self.bot.latency * 1000)

        fmt = await utils.embed(ctx, discord.Embed(title="Connection Latency", description=f"Roundtrip: `{roundtrip} ms`\nWebSocket: `{websocket} ms`"), send=False)

        await msg.edit(content=None, embed=fmt)

    @commands.command(aliaes=["commands"])
    async def help(self, ctx, command=None):
        """Shows a list of every DisBot command"""

        if not command:
            return await utils.embed(ctx, discord.Embed(title="Command List", description="Here's a list of every command DisBot has:\n%s" % "\n\n".join(f"• `{ctx.bot.config.prefix}{cmd.name}`\n- {cmd.short_doc}" for cmd in self.bot.commands)).set_footer(text=f"To view a command's help profile, use {ctx.bot.config.prefix}help [command]"))

        if command.startswith(ctx.bot.config.prefix):
            command = command[3:]

        cmd = self.bot.get_command(command)
        
        if cmd is None:
            return await utils.embed(ctx, discord.Embed(description=f"Sorry, I couldn't find the `{ctx.bot.config.prefix}{command}` command."), override_author=True)

        await utils.embed(ctx, discord.Embed(title="Command Help", description=f"Here's the help profile for the `{ctx.bot.config.prefix}{cmd.name}` command:\n\n**Name:** `{ctx.bot.config.prefix}{cmd.name}`\n**Usage:** `{utils.command_usage(ctx, cmd)}`\n**Aliases:** {' | '.join('`%s%s`' % (ctx.bot.config.prefix, [alias for alias in cmd.aliases])) if len(cmd.aliases) > 0 else 'None'}\n**Description:** {cmd.short_doc}"))

    @commands.command(aliases=["developers"])
    async def devs(self, ctx):
        """Shows a list of every DisBot developer"""

        await utils.embed(ctx, discord.Embed(title="DisBot Developers", description="Here are the people who made DisBot:\n%s" % "\n".join(f"• **{self.bot.get_user(dev)}**" for dev in (269758783557730314, 263396882762563584))))

def setup(bot):
    bot.add_cog(GeneralCommands(bot))