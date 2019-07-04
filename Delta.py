import discord, utils, sys

from discord.ext import commands

class Delta(commands.AutoShardedBot):
    def __init__(self):
        self.config = utils.Config()

        super().__init__(command_prefix=self.config.prefix,
                         description="A bot that does simple yet marvellous things!",
                         case_insensitive=self.config.case_insensitive)

        self.remove_command("help")

    def boot(self):
        for cog in self.config.cogs:
            try:
                self.load_extension(cog)

            except commands.ExtensionError as error:
                utils.cog_error(error, self.config)
        
        sys.stderr = open(self.config.stderr, "w")

        super().run(self.config.token)

if __name__ == "__main__":
    Delta().boot()