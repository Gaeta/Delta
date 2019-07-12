import discord, utils, sqlite3

from discord.ext import commands

class Prefix(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(usage="prefix", invoke_without_command=True)
    async def prefix(self, ctx, user: discord.Member=None):
        """Lists every prefix that you or the user have."""

        if user is None:
            user = ctx.author

        all_prefixes = utils.get_user_prefixes(self.bot, user)

        prefixes = []
        i = 0
        for prefix in all_prefixes:
            i += 1
            prefixes.append(f"{i}. {prefix}")

        await utils.embed(ctx, discord.Embed(title=f"{user}'s Prefixes ({len(all_prefixes)})", description=f"**{self.bot.user.mention} will always be an available prefix.**\n\n" + "\n".join(prefixes)).set_footer(text=f"{10-len(all_prefixes)}/10 prefix slots remaining."))

    @prefix.command(name="add", usage="prefix add <prefix>", aliases=["new", "create"])
    async def create_prefix(self, ctx, prefix):
        """Adds a prefix if you have a slot available."""

        all_prefixes = utils.get_user_prefixes(self.bot, ctx.author)

        if len(all_prefixes) >= 10:
            return await utils.embed(ctx, discord.Embed(title="Cannot Add", description=f"Sorry, you can only have up to 10 prefixes at once. To remove a prefix, please do **{self.bot.prefix}prefix remove <prefix>**."), error=True)

        if prefix in all_prefixes:
            return await utils.embed(ctx, discord.Embed(title="Cannot Add", description=f"Sorry, **{prefix}** is already in your list of prefixes."), error=True)

        all_prefixes.append(prefix)

        with sqlite3.connect(self.bot.config.database) as db:
            utils.ensure_prefix(self.bot, ctx.author, db)

            db.cursor().execute("UPDATE Prefixes SET Prefixes=? WHERE Used_ID=?", (str(all_prefixes), ctx.author.id))
            db.commit()

        self.bot.cache.prefixes[ctx.author.id] = all_prefixes

        await utils.embed(ctx, discord.Embed(title="Prefix Added", description=f"The prefix **{prefix}** has been added to your list of prefix. You currently have **{10-len(all_prefixes)}** prefix slots remaining, use **{ctx.bot.config.prefix}prefix** to view your list of prefixes."))

    @prefix.command(name="delete", usage="prefix delete <prefix>", aliases=["remove"])
    async def delete_prefix(self, ctx, prefix):
        """Deletes the provided prefix."""

        all_prefixes = utils.get_user_prefixes(self.bot, ctx.author)

        if len(all_prefixes) <= 1:
            return await utils.embed(ctx, discord.Embed(title="Cannot Delete", description=f"Sorry, you must have at least 1 prefix."), error=True)

        if prefix not in all_prefixes:
            return await utils.embed(ctx, discord.Embed(title="Cannot Delete", description=f"Sorry, **{prefix}** is not in your list of prefixes."), error=True)

        all_prefixes.remove(prefix)

        with sqlite3.connect(self.bot.config.database) as db:
            utils.ensure_prefix(self.bot, ctx.author, db)

            db.cursor().execute("UPDATE Prefixes SET Prefixes=? WHERE Used_ID=?", (str(all_prefixes), ctx.author.id))
            db.commit()

        self.bot.cache.prefixes[ctx.author.id] = all_prefixes

        await utils.embed(ctx, discord.Embed(title="Prefix Deleted", description=f"The prefix **{prefix}** has been removed from your list of prefix. You currently have **{10-len(all_prefixes)}** prefix slots remaining, use **{ctx.bot.config.prefix}prefix** to view your list of prefixes."))

def setup(bot):
    bot.add_cog(Prefix(bot))