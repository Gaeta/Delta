import discord, utils

from discord.ext import commands

def parse_prefix(bot, m):
    config = bot.config

    if config.prefix.allow_mention:
        return commands.when_mentioned_or(prefix for prefix in config.prefixes)

    return (prefix for prefix in config.prefixes)

class Delta(commands.AutoShardedBot):
    def __init__(self):
        self.config = utils.Config()

        super().__init__(command_prefix=parse_prefix,
                         description="A bot that does simple yet marvellous things!",
                         case_insensitive=self.config.case_insensitive)

        self.remove_command("help")

    def boot(self):
        for cog in self.config.cogs:
            try:
                self.load_extension(cog)

            except commands.ExtensionError as error:
                utils.cog_error(error, self.config)
        
        super().run(self.config.token)

if __name__ == "__main__":
    Delta().boot()