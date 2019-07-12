import discord, sys, os, asyncio, sqlite3, ast

from discord.ext import commands
from datetime import datetime
from .namedtuples import AntiSpam, AntiSlur, AntiInvite, AntiNSFW, AntiLink, Case, Tag
from .exceptions import InvalidConfig, TagNotFound

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
    if command.usage is None:
        sig = command.signature
        call = sig.split(" ")[0]
        options = ""

        if call != "":
            options = sig.split(call)[1]

        return f"`{ctx.bot.config.prefix}{f'{command.parent} ' if command.parent else ''}{command.name} {call + options}`"

    return f"`{ctx.bot.config.prefix}{command.usage}`"

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

def get_ping_role(ctx):
    role = ctx.bot.config.roles.pings

    if role == "default":
        return ctx.guild.default_role

    role = ctx.guild.get_role(role)

    if role is None:
        raise InvalidConfig("Roles", "int or @everyone", "Pings")

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

def mod(bot, ctx):
    return ctx.author.guild_permissions.manage_guild or bot.config.roles.mod in (role.id for role in ctx.author.roles) or bot.config.roles.admin in (role.id for role in ctx.author.roles)

def staff(ctx):
    return [staff for staff in ctx.guild.members if not staff.bot and (staff.guild_permissions.manage_guild or ctx.bot.config.roles.mod in (role.id for role in staff.roles) or ctx.bot.config.roles.admin in (role.id for role in staff.roles) or ctx.bot.config.roles.staff in (role.id for role in staff.roles))]

def is_streaming(user):
    return isinstance(user.activity, discord.Streaming)

def activity_info(user):
    return {
        "ActivityType.playing": f"Playing **{user.activity.name}**",
        "ActivityType.listening": f"Listening to **{user.activity.name}**",
        "ActivityType.watching": f"Watching **{user.activity.name}**",
        "ActivityType.streaming": f"Streaming [**{user.activity.name}**]({user.activity.url if hasattr(user.activity, 'url') else 'https://twitch.tv/discordapp'})",
        "-1": f"**{user.activity.name}**",
        "4": f"{user.activity.state if hasattr(user.activity, 'state') else user.activity.name}"
    }[str(user.activity.type)]

def hoist_role(user):
    if len(user.roles) <= 1:
        return None
    
    for role in reversed(user.roles):
        if role.hoist:
            return role

    return None

def colour_role(user):
    if len(user.roles) <= 1:
        return None
    
    for role in reversed(user.roles):
        if role.colour.value != 0:
            return role

    return None

def tick(ctx, e_type):
    emoji_list = ctx.bot.config.emojis

    if e_type is True:
        return f"<:greenTick:{emoji_list.green_tick}>"

    if e_type is None:
        return f"<:grayTick:{emoji_list.gray_tick}>"

    if e_type is False:
        return f"<:redTick:{emoji_list.red_tick}>"

async def fetch_tag(ctx, name):
    if name in ctx.bot.cache.tags.keys():
        tag = ctx.bot.cache.tags[name]

        owner = await ctx.bot.fetch_user(int(tag[0]))

        return Tag(owner, tag[1], tag[2])

    with sqlite3.connect(ctx.bot.config.database) as db:
        query = db.cursor().execute("SELECT Owner_ID, Name, Content FROM Tags WHERE Name=?", (name,)).fetchone()

        if query is None:
            raise TagNotFound(name)

        owner = await ctx.bot.fetch_user(int(query[0]))

        return Tag(owner, query[1], query[2])

def display_time(seconds, granularity=2):
    result = []

    for name, count in (("weeks", 60 * 60 * 24 * 7), ("days", 60 * 60 * 24), ("hours", 60 * 60), ("minutes", 60), ("seconds", 1)):
        value = seconds // count
        if value:
            seconds -= value * count

            if value == 1:
                name = name.rstrip("s")
            
            result.append(f"{value} {name}")

    return ", ".join(result[:granularity])

def get_user_prefixes(bot, user):
    if user.id in bot.cache.prefixes.keys():
        return bot.cache.prefixes[user.id]

    with sqlite3.connect(bot.config.database) as db:
        ensure_prefix(bot, user, db)

        query = db.cursor().execute("SELECT Prefixes FROM Prefixes WHERE Used_ID=?", (user.id,)).fetchone()

        return ast.literal_eval(query[0])

def ensure_prefix(bot, user, db):
    if db.cursor().execute("SELECT * FROM Prefixes WHERE Used_ID=?", (user.id,)).fetchone() is None:
        value = [bot.config.prefix]

        db.cursor().execute("INSERT INTO Prefixes VALUES (?, ?)", (user.id, str(value)))
        db.commit()

        bot.cache.prefixes[user.id] = value