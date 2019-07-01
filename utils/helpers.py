import discord, sys, os, asyncio, sqlite3

from discord.ext import commands
from datetime import datetime
from .namedtuples import AntiSpam, AntiSlur, AntiInvite, AntiNSFW, AntiLink, Case
from .exceptions import InvalidConfig

async def handle_invalid_config(ctx, error):
    if error.subsetting is not None:
        print(f"[ {time_fmt()} ] >> [ Config ] >> [ {error.setting} ]: {error.subsetting} is improperly configured, type '{error.expected_type}' was expected.", file=sys.stderr)

    else:
        print(f"[ {time_fmt()} ] >> [ Config ]: {error.setting} is improperly configured, type '{error.expected_type}' was expected.", file=sys.stderr)

    for task in asyncio.Task.all_tasks():
        try:
            task.cancel()
        
        except:
            continue

    try:
        await self.bot.logout()
        self.bot.loop.stop()
        self.bot.loop.close()
    
    except:
        pass
    
    os._exit(2)

def is_higher_or_equal(bot, author, user):
    return author.top_role.position > user.top_role.position and user.guild.owner_id != user.id and user.id != bot.user.id

def time_fmt():
    return datetime.utcnow().strftime('%d/%m/%y %I:%M %p')

def cleanup_dir_name(name, directories, directory):
    length = len(directories[directory]) + 1

    return name[length:]

def get_ext_err(error, config):
    name = cleanup_dir_name(error.name, config.directories, "cogs")
    prefab = f"Extension '{name}'"

    # 'setup' function doesn't exist
    if isinstance(error, commands.NoEntryPointError):
        return f"{prefab} has no 'setup' function."

    # extension is already loaded
    if isinstance(error, commands.ExtensionAlreadyLoaded):
        return f"{prefab} is already loaded."

    # extension has yet to be loaded
    if isinstance(error, commands.ExtensionNotLoaded):
        return f"{prefab} is not yet loaded."

    # extension contains an error
    if isinstance(error, commands.ExtensionFailed):
        return f"{prefab} encountered an error: {error.original}"

    # extension doesn't exist
    if isinstance(error, commands.ExtensionNotFound):
        return f"{prefab} was not found."

async def embed(ctx, embed: discord.Embed, send=True, error=False, delete_after=None, override_colour=False, override_author=False):
    if not override_colour:
        if not error:
            embed.colour = int(ctx.bot.config.colours.embed, 16) # base 16 converts a string-hex to a hexadecimal

        if error:
            embed.colour = int(ctx.bot.config.colours.error, 16)
    
    if not override_author:
        embed.set_author(name=ctx.bot.user.name, icon_url=ctx.bot.user.avatar_url)

    if send:
        if delete_after:
            return await ctx.send(embed=embed, delete_after=delete_after)

        return await ctx.send(embed=embed)

    return embed

def command_usage(ctx, command):
    sig = command.signature
    call = sig.split(" ")[0]
    options = ""

    if call != "":
        options = sig.split(call)[1]

    return f"`{ctx.bot.config.prefix}{f'{command.parent} ' if command.parent else ''}{command.name} {call + options}`"

def auto_mod(bot, setting="invite"):
    config = bot.config.anti(setting.lower())

    if not config:
        return False

    if setting.lower() == "invite":
        return AntiInvite(config["enabled"], config["bypass_verified"], config["bypassed_channels"], config["bypassed_invites"])

    if setting.lower() == "nsfw":
        return AntiNSFW(config["enabled"], config["bypassed_channels"], config["extra_links"])

    if setting.lower() == "slur":
        return AntiSlur(config["enabled"], config["bypassed_channels"])

    if setting.lower() == "spam":
        try:
            return AntiSpam(config["enabled"], config["bypassed_channels"], int(config["threshold_seconds"]))
        
        except ValueError:
            raise InvalidConfig("Auto Mod", "int", "Anti Link >> Threshold Seconds")

    if setting.lower() == "link":
        return AntiLink(config["enabled"], config["bypassed_channels"], config["bypassed_links"])

async def mute(bot, user, reason=None):
    server_id = bot.config.server
    role_id = bot.config.roles.muted

    server = bot.get_guild(server_id)
    role = server.get_role(role_id)

    if role is None:
        raise InvalidConfig("Roles", "int", "Muted")

    await user.add_roles(role, reason=reason)

async def unmute(bot, user, reason=None):
    server_id = bot.config.server
    role_id = bot.config.roles.muted

    server = bot.get_guild(server_id)
    role = server.get_role(role_id)

    if role is None:
        raise InvalidConfig("Roles", "int", "Muted")

    await user.remove_roles(role, reason=reason)

async def auto_punish(ctx, user, channel, reason):
    reason = f"[ Auto Mod ] >> {reason}"
    punishment = ctx.bot.config.auto_mod.action

    if punishment.lower() in ("kick", "ban"):
        func = {
            "ban": user.ban,
            "kick": user.kick
        }[punishment.lower()]
        await func(reason=reason)

        send = await embed(ctx, discord.Embed(title="Auto Moderator", description=f"**{user}** ({user.id}) was **{{'kick': 'kicked', 'ban': 'banned'}}** because:\n\n{reason}"), send=False)
        await channel.send(embed=send, delete_after=30)

    if punishment.lower() == "mute":
        await mute(ctx.bot, user, reason=reason)
        send = await embed(ctx, discord.Embed(title="Auto Moderator", description=f"**{user}** ({user.id}) was **muted** because:\n\n{reason}"), send=False)
        await channel.send(embed=send, delete_after=30)

async def user_log(ctx, user, stance="join"):
    channel = ctx.bot.get_channel(ctx.bot.config.channels.user_log)

    if channel is None:
        raise InvalidConfig("Channels", "int", "User Log")

    prefabs = {
        "join": [
            "Member Joined",
            "joined"
        ],
        "leave": [
            "Member Left",
            "left"
        ]
    }[stance.lower()]

    send = await embed(ctx, discord.Embed(timestamp=datetime.utcnow(), title=prefabs[0], description=f"**{user}** ({user.id}) has **{prefabs[1]}** {user.guild}").set_footer(text=f"ID: {user.id}"), send=False)
    await channel.send(embed=send)

async def mod_log(ctx, user, punishment, moderator, reason=None):
    channel = ctx.bot.get_channel(ctx.bot.config.channels.mod_log)

    if channel is None:
        raise InvalidConfig("Channels", "int", "Mod Log")

    with sqlite3.connect(ctx.bot.config.database) as db:
        current_case_id = int(db.cursor().execute("SELECT Case_ID FROM Settings").fetchone()[0]) + 1
        
        send = await embed(ctx, discord.Embed(colour=case_colour(ctx.bot, punishment), timestamp=datetime.utcnow(), title=f"{punishment.title()} | Case #{current_case_id}").add_field(name="User" if not user.bot else "Bot", value=f"{user} ({user.mention})").add_field(name="Moderator", value=moderator if hasattr(moderator, "id") else f"??? (Moderator: do `{ctx.bot.config.prefix}reason {current_case_id}`)").add_field(name="Reason", value=reason if reason else f"Moderator: please do `{ctx.bot.config.prefix}reason {current_case_id} <reason>`", inline=False).set_footer(text=f"ID: {user.id}"), override_colour=True, send=False)
        msg = await channel.send(embed=send)

        db.cursor().execute("INSERT INTO Cases VALUES (?, ?, ?, ?, ?, ?)", (moderator.id if hasattr(moderator, "id") else "???", user.id, current_case_id, msg.id, punishment, reason if reason else f"Moderator: please do `{ctx.bot.config.prefix}reason {current_case_id} <reason>`"))
        db.cursor().execute("UPDATE Settings SET Case_ID=?", (current_case_id,))
        db.commit()

def case_colour(bot, punishment):
    return int({
        "ban": bot.config.colours.ban,
        "unban": bot.config.colours.unban,
        "mute": bot.config.colours.mute,
        "unmute": bot.config.colours.unmute,
        "kick": bot.config.colours.kick,
    }[punishment.lower()], 16)

def get_member_role(ctx):
    role = ctx.bot.config.roles.member

    if role == "default":
        return ctx.guild.default_role

    role = ctx.guild.get_role(role)

    if role is None:
        raise InvalidConfig("Roles", "int or @everyone", "Member")

    return role

async def get_case(bot, case_id):
    with sqlite3.connect(bot.config.database) as db:
        case = db.cursor().execute("SELECT * FROM Cases WHERE Case_ID=?", (case_id,)).fetchone()

        if case is None:
            return None

        mod = case[0]
        user = await bot.fetch_user(int(case[1]))
        case_id = int(case[2])
        
        channel = bot.get_channel(bot.config.channels.mod_log)

        if channel is None:
            raise InvalidConfig("Channels", "int", "Mod Log")

        message = await channel.fetch_message(int(case[3]))
        punishment = case[4]
        reason = case[5]

        if not case[0].startswith("???"):
            mod = await bot.fetch_user(int(case[0]))

        return Case(mod, user, case_id, message, punishment, reason)