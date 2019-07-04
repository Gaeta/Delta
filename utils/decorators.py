import discord

from discord.ext import commands

def is_mod():
    async def mod_predicate(ctx):
        return ctx.author.guild_permissions.manage_guild or ctx.bot.config.roles.mod in (role.id for role in ctx.author.roles) or ctx.bot.config.roles.admin in (role.id for role in ctx.author.roles)

    return commands.check(mod_predicate)

def is_admin():
    async def admin_predicate(ctx):
        return ctx.author.guild_permissions.administrator or ctx.bot.config.roles.admin in (role.id for role in ctx.author.roles)

    return commands.check(admin_predicate)

def guild_only():
    async def guild_predicate(ctx):
        if ctx.guild is None:
            return False

        return ctx.guild.id == ctx.bot.config.server

    return commands.check(guild_predicate)