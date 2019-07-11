import discord, utils, sqlite3, copy

from discord.ext import commands

class Tags(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(invoke_without_command=True, usage="tag <name>")
    @utils.guild_only()
    async def tag(self, ctx, name):
        """Allows you to tag text for use later."""

        name = name.lower()

        try:
            tag = await utils.fetch_tag(ctx, name)

        except:
            return await utils.embed(ctx, discord.Embed(title="Tag Not Found", description=f"Sorry, the tag `{name}` doesn't appear to be in the database. Why not claim it by using `{ctx.bot.config.prefix}tag add {name} <content>`?"), error=True)

        await ctx.send(tag.content)

    @tag.command(name="add", aliases=["create", "new"], usage="tag create <name> <content>")
    @utils.guild_only()
    async def create_tag(self, ctx, name, *, content: commands.clean_content):
        """Creates a new tag and assigns ownership to you."""

        name = name.lower()

        try:
            tag = await utils.fetch_tag(ctx, name)

            return await utils.embed(ctx, discord.Embed(title="Tag Already Exists", description=f"Sorry, the tag `{name}` is already owned by {tag.owner.mention}. Why not check it out by using `{ctx.bot.config.prefix}tag {name}`?"), error=True)

        except:
            pass

        with sqlite3.connect(ctx.bot.config.database) as db:
            db.cursor().execute("INSERT INTO Tags VALUES (?, ?, ?)", (ctx.author.id, name, content))
            db.commit()

        self.bot.cache.tags[name] = [ctx.author.id, name, content]

        await utils.embed(ctx, discord.Embed(title="Tag Created", description=f"Congratulations, you are now the proud owner of the `{name}` tag. You can retrieve it by using `{ctx.bot.config.prefix}tag {name}`!"))

    @tag.command(name="rename", usage="tag rename <name> <new name>")
    @utils.guild_only()
    async def rename_tag(self, ctx, name, new_name):
        """Renames a tag that you own or moderate."""

        name = name.lower()
        new_name = new_name.lower()

        try:
            tag = await utils.fetch_tag(ctx, name)

        except:
            return await utils.embed(ctx, discord.Embed(title="Tag Doesn't Exists", description=f"Sorry, the tag `{name}` doesn't appear to be in the database. Why not claim it by using `{ctx.bot.config.prefix}tag add {new_name} <content>`?"), error=True)

        if name == new_name:
            return await utils.embed(ctx, discord.Embed(title="Cannot Rename", description=f"Sorry, you can't rename a tag to the same name."), error=True)

        if tag.owner.id != ctx.author.id and not utils.mod(self.bot, ctx):
            mod = ctx.guild.get_role(self.bot.config.roles.mod)

            if mod is None:
                raise utils.InvalidConfig("Roles", "int", "Mod")

            return await utils.embed(ctx, discord.Embed(title="Unauthorized", description=f"Sorry, only {tag.owner.mention} and those with the {mod.mention} role can rename the `{name}` tag."), error=True)

        with sqlite3.connect(ctx.bot.config.database) as db:
            db.cursor().execute("UPDATE Tags SET Name=? WHERE Name=?", (new_name, name))
            db.commit()

        self.bot.cache.tags.pop(name)
        self.bot.cache.tags[new_name] = [tag.owner.id, new_name, tag.content]

        await utils.embed(ctx, discord.Embed(title="Tag Renamed", description=f"You have successfully renamed the tag `{name}` to `{new_name}`. You can retrieve it by using `{ctx.bot.config.prefix}tag {new_name}`!"))

    @tag.command(name="delete", aliases=["remove"], usage="tag delete <name>")
    @utils.guild_only()
    async def delete_tag(self, ctx, name):
        """Deletes a tag that you own or moderate."""

        name = name.lower()

        try:
            tag = await utils.fetch_tag(ctx, name)

        except:
            return await utils.embed(ctx, discord.Embed(title="Tag Doesn't Exists", description=f"Sorry, the tag `{name}` doesn't appear to be in the database. Why not claim it by using `{ctx.bot.config.prefix}tag add {name} <content>`?"), error=True)

        if tag.owner.id != ctx.author.id and not utils.mod(self.bot, ctx):
            mod = ctx.guild.get_role(self.bot.config.roles.mod)

            if mod is None:
                raise utils.InvalidConfig("Roles", "int", "Mod")

            return await utils.embed(ctx, discord.Embed(title="Unauthorized", description=f"Sorry, only {tag.owner.mention} and those with the {mod.mention} role can delete the `{name}` tag."), error=True)

        with sqlite3.connect(ctx.bot.config.database) as db:
            db.cursor().execute("DELETE FROM Tags WHERE Name=?", (name,))
            db.commit()

        self.bot.cache.tags.pop(name)

        await utils.embed(ctx, discord.Embed(title="Tag Deleted", description=f"You have successfully deleted the tag `{name}`."))

    @tag.command(name="edit", usage="tag edit <name> <new content>")
    @utils.guild_only()
    async def edit_tag(self, ctx, name, *, new_content: commands.clean_content):
        """Edits a tag that you own or moderate."""

        name = name.lower()

        try:
            tag = await utils.fetch_tag(ctx, name)

        except:
            return await utils.embed(ctx, discord.Embed(title="Tag Doesn't Exists", description=f"Sorry, the tag `{name}` doesn't appear to be in the database. Why not claim it by using `{ctx.bot.config.prefix}tag add {name} <content>`?"), error=True)

        if tag.owner.id != ctx.author.id and not utils.mod(self.bot, ctx):
            mod = ctx.guild.get_role(self.bot.config.roles.mod)

            if mod is None:
                raise utils.InvalidConfig("Roles", "int", "Mod")

            return await utils.embed(ctx, discord.Embed(title="Unauthorized", description=f"Sorry, only {tag.owner.mention} and those with the {mod.mention} role can edit the `{name}` tag."), error=True)

        with sqlite3.connect(ctx.bot.config.database) as db:
            db.cursor().execute("UPDATE Tags SET Content=? WHERE Name=?", (new_content, name))
            db.commit()

        self.bot.cache.tags[name][2] = new_content

        await utils.embed(ctx, discord.Embed(title="Tag Renamed", description=f"You have successfully edited the content for the tag `{name}`. You can retrieve it by using `{ctx.bot.config.prefix}tag {name}`!"))

    @tag.command(name="transfer", usage="tag transfer <name> <@user>")
    @utils.guild_only()
    async def transfer_tag(self, ctx, name, new_owner: discord.Member):
        """Transfers a tag that you own to another user."""

        name = name.lower()

        try:
            tag = await utils.fetch_tag(ctx, name)

        except:
            return await utils.embed(ctx, discord.Embed(title="Tag Doesn't Exists", description=f"Sorry, the tag `{name}` doesn't appear to be in the database. Why not claim it by using `{ctx.bot.config.prefix}tag add {name} <content>`?"), error=True)

        if tag.owner.id == new_owner.id:
            return await utils.embed(ctx, discord.Embed(title="Cannot Transfer", description=f"Sorry, you can't transfer a tag that you own to yourself."), error=True)

        if tag.owner.id != ctx.author.id:
            return await utils.embed(ctx, discord.Embed(title="Unauthorized", description=f"Sorry, only {tag.owner.mention} can transfer the `{name}` tag."), error=True)

        with sqlite3.connect(ctx.bot.config.database) as db:
            db.cursor().execute("UPDATE Tags SET Owner_ID=? WHERE Name=?", (new_owner.id, name))
            db.commit()

        self.bot.cache.tags[name][0] = new_owner.id

        await utils.embed(ctx, discord.Embed(title="Tag Transferred", description=f"You have successfully transferred ownership of the tag `{name}` to {new_owner.mention}. You can retrieve it by using `{ctx.bot.config.prefix}tag {name}`!"))

    @tag.command(name="list", usage="tag list [@user]")
    @utils.guild_only()
    async def list_tags(self, ctx, user: discord.Member=None):
        """Shows a list of tags owned by you or the provided user."""

        if not user:
            user = ctx.author

        with sqlite3.connect(ctx.bot.config.database) as db:
            tags = db.cursor().execute("SELECT * FROM Tags WHERE Owner_ID=?", (user.id,)).fetchall()

            if not tags:
                return await utils.embed(ctx, discord.Embed(title=f"{user}'s Tags (0)", description=f"{user.mention} has no tags."))

            text = []
            i = 0
            for tag in tags:
                i += 1
                if i < 11:
                    text.append(f"{i}. {tag[1]}")

                else:
                    text[-1] = f"{text[-1]}..."
                    break

            await utils.embed(ctx, discord.Embed(title=f"{user}'s Tags ({len(tags)})", description="\n".join(text)).set_footer(text="Up to 10 tags are listed here."))

    @tag.command(name="claim", usage="tag claim <name>")
    @utils.guild_only()
    async def claim_tags(self, ctx, name):
        """Claims a tag of a user that left the server."""

        name = name.lower()

        try:
            tag = await utils.fetch_tag(ctx, name)

        except:
            return await utils.embed(ctx, discord.Embed(title="Tag Doesn't Exists", description=f"Sorry, the tag `{name}` doesn't appear to be in the database. Why not claim it by using `{ctx.bot.config.prefix}tag add {name} <content>`?"), error=True)

        if ctx.author.id == tag.owner.id:
            return await utils.embed(ctx, discord.Embed(title="Cannot Claim", description=f"Sorry, you can't claim your own tag."), error=True)

        if ctx.guild.get_member(tag.owner.id) is not None:
            return await utils.embed(ctx, discord.Embed(title="Cannot Claim", description=f"Sorry, the `{name}` tag's owner ({tag.owner.mention}) is still in the server."), error=True)

        with sqlite3.connect(ctx.bot.config.database) as db:
            db.cursor().execute("UPDATE Tags SET Owner_ID=? WHERE Name=?", (ctx.author.id, name))
            db.commit()

        self.bot.cache.tags[name][0] = ctx.author.id

        await utils.embed(ctx, discord.Embed(title="Tag Claimed", description=f"You have successfully claimed ownership of the tag `{name}`. You can retrieve it by using `{ctx.bot.config.prefix}tag {name}`!"))

    @commands.command(usage="tags [@user]")
    @utils.guild_only()
    async def tags(self, ctx, user: discord.Member=None):
        """Acts as an alias for tag list."""

        if not user:
            user = ctx.author

        msg = copy.copy(ctx.message)
        msg.author = user
        msg.content = ctx.prefix + "tag list"
        new_ctx = await self.bot.get_context(msg, cls=type(ctx))
        await self.bot.invoke(new_ctx)

def setup(bot):
    bot.add_cog(Tags(bot))