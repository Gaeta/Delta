import discord, utils, sys, sqlite3, ast

from discord.ext import commands
from datetime import datetime

def get_prefix(bot, m):
    return commands.when_mentioned_or(*utils.get_user_prefixes(bot, m.author))(bot, m)

class Delta(commands.AutoShardedBot):
    def __init__(self):
        self.config = utils.Config()

        super().__init__(command_prefix=get_prefix,
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
                
                all_prefixes = db.cursor().execute("SELECT * FROM Prefixes").fetchall()

                for prefix in all_prefixes:
                    self.cache.prefixes[prefix[0]] = ast.literal_eval(prefix[1])

            except:
                pass
        
        sys.stderr = open(self.config.stderr, "w")

        super().run(self.config.token)

if __name__ == "__main__":
    Delta().boot()