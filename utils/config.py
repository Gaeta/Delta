import json, discord, os

from .namedtuples import Presence, AutoMod, Roles, Channels, Colours, Emojis
from .exceptions import InvalidConfig

class Config:
    def __init__(self):
        self.config = json.load(open("config.json"))

    @property
    def prefix(self):
        return self.config["prefix"]

    @property
    def token(self):
        return self.config["token"]

    @property
    def server(self):
        try:
            return int(self.config["server"])

        except:
            raise InvalidConfig("Server", "int")

    @property
    def roles(self):
        roles = self.config["roles"]

        try:
            member = roles["member"]

            if not isinstance(member, int):
                if member.lower() in ("@everyone", "everyone", "default"):
                    member = "default"
            
            else:
                member = int(member)

            return Roles(int(roles["admin"]), int(roles["mod"]), int(roles["muted"]), member, int(roles["offduty"]), int(roles["staff"]), int(roles["support"]))
        
        except:
            raise InvalidConfig("Roles", "list of int")

    @property
    def channels(self):
        channels = self.config["channels"]

        try:
            return Channels(int(channels["user_log"]), int(channels["mod_log"]), int(channels["announcements"]))
        
        except:
            raise InvalidConfig("Channels", "list of int")

    @property
    def emojis(self):
        emojis = self.config["emojis"]

        try:
            return Emojis(int(emojis["online"]), int(emojis["idle"]), int(emojis["dnd"]), int(emojis["offline"]))
    
        except:
            raise InvalidConfig("Emojis", "list of int")

    @property
    def colours(self):
        colours = self.config["colours"]

        return Colours(colours["embed"], colours["error"], colours["ban"], colours["unban"], colours["mute"], colours["unmute"], colours["kick"])

    @property
    def presence(self):
        presence = self.config["presence"]

        if presence["type"].upper() not in ("WATCHING", "PLAYING", "STREAMING", "LISTENING"):
            raise ValueError("'type' should be one of 'watching', 'playing', 'streaming' or 'listening', not %s" % presence["type"])

        if presence["status"].upper() not in ("ONLINE", "IDLE", "DND", "OFFLINE", "INVISIBLE"):
            raise ValueError("'status' should be one of 'online', 'idle', 'dnd', 'offline' or 'invisible', not %s" % presence["status"])

        status = {
            "ONLINE": discord.Status.online,
            "IDLE": discord.Status.idle,
            "DND": discord.Status.dnd,
            "OFFLINE": discord.Status.offline,
            "INVISIBLE": discord.Status.offline
        }[presence["status"].upper()]

        return Presence({
            "WATCHING": discord.Activity(type=discord.ActivityType.watching, name=presence["name"]),
            "STREAMING": discord.Streaming(name=presence["name"], url=presence["url"]),
            "PLAYING": discord.Game(name=presence["name"]),
            "LISTENING": discord.Activity(type=discord.ActivityType.listening, name=presence["name"])
        }[presence["type"].upper()], status)

    @property
    def figlet(self):
        return self.config["figlet"]

    @property
    def directories(self):
        return self.config["directories"]

    @property
    def cogs(self):
        return [f"{self.directories['cogs']}.{file[:-3]}" for file in os.listdir(self.directories["cogs"]) if file.endswith(".py")]

    @property
    def database(self):
        return f"{self.directories['database']}.db"

    @property
    def stderr(self):
        return f"{self.directories['stderr']}.log"

    @property
    def case_insensitive(self):
        return bool(self.config["case_insensitive"])

    def anti(self, setting="invite"):
        auto_mod = self.config["auto_moderator"]["enabled"]
        config = self.config["auto_moderator"]["modules"][f"anti_{setting}"]

        if not auto_mod or not config["enabled"]:
            return False

        return config

    @property
    def auto_mod(self):
        config = self.config["auto_moderator"]

        if config["punishment"] not in ("kick", "ban", "mute"):
            raise InvalidConfig("Auto Mod", "one of kick ban or mute", "Punishment")

        return AutoMod(bool(config["enabled"]), config["punishment"])