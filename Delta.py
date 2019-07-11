import discord, utils, sys, sqlite3

from discord.ext import commands
from datetime import datetime

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

        with sqlite3.connect(self.config.database) as db:
            try:
                all_tags = db.cursor().execute("SELECT * FROM Tags").fetchall()

                for tag in all_tags:
                    self.cache.tags[tag[1]] = tag

            except:
                pass
        
        sys.stderr = open(self.config.stderr, "w")

        super().run(self.config.token)

if __name__ == "__main__":
    Delta().boot()