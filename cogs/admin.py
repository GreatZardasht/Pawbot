import time
import aiohttp
import traceback
import discord
import textwrap
import io
import json
import requests

from io import BytesIO
from bs4 import BeautifulSoup
from dhooks import Webhook
from utils.chat_formatting import pagify
from utils.formats import TabularData, Plural
from contextlib import redirect_stdout
from copy import copy
from typing import Union
from utils import repo, default, http, dataIO
from discord.ext import commands


class Admin:
    def __init__(self, bot):
        self.bot = bot
        self.config = default.get("config.json")
        self._last_result = None
        self.sessions = set()

    @staticmethod
    def cleanup_code(content):
        """Automatically removes code blocks from the code."""
        # remove ```py\n```
        if content.startswith("```") and content.endswith("```"):
            return "\n".join(content.split("\n")[1:-1])

        # remove `foo`
        return content.strip("` \n")

    @staticmethod
    def get_syntax_error(e):
        if e.text is None:
            return f"```py\n{e.__class__.__name__}: {e}\n```"
        return f'```py\n{e.text}{"^":>{e.offset}}\n{e.__class__.__name__}: {e}```'

    @commands.command()
    async def amiadmin(self, ctx):
        """ Are you admin? """
        if ctx.author.id in self.config.owners:
            await ctx.send(f"Yes **{ctx.author.name}** you are admin! ✅")
        elif ctx.author.id in self.config.contributors:
            await ctx.send(f"No, but you're a contributor **{ctx.author.name}** 💙")
        elif ctx.author.id in self.config.friends:
            await ctx.send(f"No, but you're a friend of Paws **{ctx.author.name}** 💜")
        else:
            await ctx.send(f"No, heck off **{ctx.author.name}**.")

    @commands.command(aliases=["re"])
    @commands.check(repo.is_owner)
    async def reload(self, ctx, name: str):
        """ Reloads an extension. """
        try:
            self.bot.unload_extension(f"cogs.{name}")
            self.bot.load_extension(f"cogs.{name}")
        except FileNotFoundError as e:
            return await ctx.send(f"```\n{e}```")
        await ctx.send(f"Reloaded extension **{name}.py**")

    @commands.command()
    @commands.check(repo.is_owner)
    async def reboot(self, ctx):
        """ Reboot the bot """
        await ctx.send("Rebooting now...")
        time.sleep(1)
        await self.bot.logout()

    @commands.command()
    @commands.check(repo.is_owner)
    async def load(self, ctx, name: str):
        """ Loads an extension. """
        try:
            self.bot.load_extension(f"cogs.{name}")
        except FileNotFoundError as e:
            await ctx.send(f"```diff\n- {e}```")
            return
        await ctx.send(f"Loaded extension **{name}.py**")

    @commands.command()
    @commands.check(repo.is_owner)
    async def unload(self, ctx, name: str):
        """ Unloads an extension. """
        try:
            self.bot.unload_extension(f"cogs.{name}")
        except FileNotFoundError as e:
            await ctx.send(f"```diff\n- {e}```")
            return
        await ctx.send(f"Unloaded extension **{name}.py**")

    @commands.group()
    @commands.check(repo.is_owner)
    async def change(self, ctx):
        if ctx.invoked_subcommand is None:
            _help = await ctx.bot.formatter.format_help_for(ctx, ctx.command)

            for page in _help:
                await ctx.send(page)

    @change.command(name="playing")
    @commands.check(repo.is_owner)
    async def change_playing(self, ctx, *, playing: str):
        """ Change playing status. """
        try:
            await self.bot.change_presence(
                activity=discord.Game(type=0, name=playing),
                status=discord.Status.online,
            )
            dataIO.change_value("config.json", "playing", playing)
            await ctx.send(f"Successfully changed playing status to **{playing}**")
        except discord.InvalidArgument as err:
            await ctx.send(err)
        except Exception as e:
            await ctx.send(e)

    @change.command(name="username")
    @commands.check(repo.is_owner)
    async def change_username(self, ctx, *, name: str):
        """ Change username. """
        try:
            await self.bot.user.edit(username=name)
            await ctx.send(f"Successfully changed username to **{name}**")
        except discord.HTTPException as err:
            await ctx.send(err)

    @change.command(name="nickname")
    @commands.check(repo.is_owner)
    async def change_nickname(self, ctx, *, name: str = None):
        """ Change nickname. """
        try:
            await ctx.guild.me.edit(nick=name)
            if name:
                await ctx.send(f"Successfully changed nickname to **{name}**")
            else:
                await ctx.send("Successfully removed nickname")
        except Exception as err:
            await ctx.send(err)

    @change.command(name="avatar")
    @commands.check(repo.is_owner)
    async def change_avatar(self, ctx, url: str = None):
        """ Change avatar. """
        if url is None and len(ctx.message.attachments) == 1:
            url = ctx.message.attachments[0].url
        else:
            url = url.strip("<>")

        try:
            bio = await http.get(url, res_method="read")
            await self.bot.user.edit(avatar=bio)
            await ctx.send(f"Successfully changed the avatar. Currently using:\n{url}")
        except aiohttp.InvalidURL:
            await ctx.send("The URL is invalid...")
        except discord.InvalidArgument:
            await ctx.send("This URL does not contain a usable image")
        except discord.HTTPException as err:
            await ctx.send(err)

    @commands.command()
    @commands.check(repo.is_owner)
    async def steal(self, ctx, emojiname, url: str = None):
        """Steals emojis"""
        if emojiname is None or "http" in emojiname:
            return await ctx.send("No emoji name provided")
        if url is None and len(ctx.message.attachments) == 1:
            url = ctx.message.attachments[0].url
        else:
            url = url.strip("<>")

        try:
            botguild = self.bot.get_guild(423_879_867_457_863_680)
            bio = await http.get(url, res_method="read")
            await botguild.create_custom_emoji(name=emojiname, image=bio)
            await ctx.message.delete()
            await ctx.send(f"Successfully stolen emoji.")
        except aiohttp.InvalidURL:
            await ctx.send("The URL is invalid...")
        except discord.InvalidArgument:
            await ctx.send("This URL does not contain a usable image")
        except discord.HTTPException as err:
            await ctx.send(err)

    @commands.command(pass_context=True, name="eval")
    @commands.check(repo.is_owner)
    async def _eval(self, ctx, *, body: str):
        """Evaluates a code"""
        env = {
            "bot": self.bot,
            "ctx": ctx,
            "channel": ctx.channel,
            "author": ctx.author,
            "guild": ctx.guild,
            "message": ctx.message,
            "_": self._last_result,
        }

        if "bot.http.token" in body:
            return await ctx.send(f"You can't take my token {ctx.author.name}")
        env.update(globals())

        body = self.cleanup_code(body)
        stdout = io.StringIO()

        to_compile = f'async def func():\n{textwrap.indent(body, "  ")}'

        try:
            start = time.perf_counter()
            exec(to_compile, env)
        except EnvironmentError as e:
            return await ctx.send(f"```py\n{e.__class__.__name__}: {e}\n```")

        func = env["func"]
        try:
            with redirect_stdout(stdout):
                ret = await func()
        except Exception:
            value = stdout.getvalue()
            await ctx.send(f"```py\n{value}{traceback.format_exc()}\n```")
        else:
            try:
                value = stdout.getvalue()
                reactiontosend = self.bot.get_emoji(508_388_437_661_843_483)
                await ctx.message.add_reaction(reactiontosend)
                dt = (time.perf_counter() - start) * 1000.0
            except discord.Forbidden:
                return await ctx.send("I couldn't react...")

            if ret is None:
                if value:
                    await ctx.send(f"```py\n{value}\n```")
            else:
                if self.config.token in ret:
                    ret = self.config.realtoken
                self._last_result = ret
                await ctx.send(
                    f"Inputted code:\n```py\n{body}\n```\n\nOutputted Code:\n```py\n{value}{ret}\n```\n*Evalled in {dt:.2f}ms*"
                )

    @commands.group(aliases=["as"])
    @commands.check(repo.is_owner)
    async def sudo(self, ctx):
        """ Run a cmd under an altered context """
        if ctx.invoked_subcommand is None:
            await ctx.send("...")

    @sudo.command(aliases=["user"])
    @commands.check(repo.is_owner)
    async def sudo_user(
        self, ctx, who: Union[discord.Member, discord.User], *, command: str
    ):
        """ Run a cmd under someone else's name """
        msg = copy(ctx.message)
        msg.author = who
        msg.content = ctx.prefix + command
        new_ctx = await self.bot.get_context(msg)
        await self.bot.invoke(new_ctx)

    @sudo.command(aliases=["channel"])
    @commands.check(repo.is_owner)
    async def sudo_channel(self, ctx, chid: int, *, command: str):
        """ Run a command in a different channel. """
        cmd = copy(ctx.message)
        cmd.channel = self.bot.get_channel(chid)
        cmd.content = ctx.prefix + command
        new_ctx = await self.bot.get_context(cmd)
        await self.bot.invoke(new_ctx)

    @commands.command()
    @commands.check(repo.is_owner)
    async def cogs(self, ctx):
        """ Gives all loaded cogs """
        mod = ", ".join(list(self.bot.cogs))
        await ctx.send(f"The current modules are:\n```\n{mod}\n```")

    @commands.command(aliases=["gsi"])
    @commands.check(repo.is_owner)
    async def getserverinfo(self, ctx, *, guild_id: int):
        """ Makes me get the information from a guild id """
        guild = self.bot.get_guild(guild_id)
        if guild is None:
            return await ctx.send("Hmph.. I got nothing..")
        members = set(guild.members)
        bots = filter(lambda m: m.bot, members)
        bots = set(bots)
        members = len(members) - len(bots)
        if guild == ctx.guild:
            roles = " ".join([x.mention for x in guild.roles != "@everyone"])
        else:
            roles = ", ".join([x.name for x in guild.roles if x.name != "@everyone"])

        info = discord.Embed(
            title="Guild info",
            description=f"» Name: {guild.name}\n» Members/Bots: `{members}:{len(bots)}`"
            f"\n» Owner: {guild.owner}\n» Created at: {guild.created_at}"
            f"\n» Roles: {roles}",
            color=discord.Color.blue(),
        )
        info.set_thumbnail(url=guild.icon_url)
        await ctx.send(embed=info)

    @commands.command(alisases=["bsl"])
    @commands.check(repo.is_owner)
    async def botservers(self, ctx):
        """ Lists servers """
        guilds = sorted(list(self.bot.guilds), key=lambda s: s.name.lower())
        msg = ""
        for i, guild in enumerate(guilds, 1):
            members = set(guild.members)
            bots = filter(lambda m: m.bot, members)
            bots = set(bots)
            members = len(members) - len(bots)
            msg += "`{}:` {}, `{}` `{} members, {} bots` \n".format(
                i, guild.name, guild.id, members, len(bots)
            )

        for page in pagify(msg, ["\n"]):
            await ctx.send(page)

    @commands.command(aliases=["webhooktest"])
    @commands.check(repo.is_owner)
    async def whtest(self, ctx, whlink: str, *, texttosend):
        """ Messages a webhook """
        try:
            await ctx.message.delete()
            hook = Webhook(whlink, is_async=True)
            await hook.send(texttosend)
            await hook.close()
        except ValueError:
            return await ctx.send("I couldn't send the message..")

    @commands.command()
    @commands.check(repo.is_owner)
    async def sql(self, ctx, *, query: str):
        """Run some SQL."""

        query = self.cleanup_code(query)

        is_multistatement = query.count(";") > 1
        if is_multistatement:
            strategy = self.bot.db.execute
        else:
            strategy = self.bot.db.fetch

        try:
            start = time.perf_counter()
            results = await strategy(query)
            dt = (time.perf_counter() - start) * 1000.0
        except Exception:
            return await ctx.send(f"```py\n{traceback.format_exc()}\n```")

        rows = len(results)
        if is_multistatement or rows == 0:
            return await ctx.send(f"`{dt:.2f}ms: {results}`")

        headers = list(results[0].keys())
        table = TabularData()
        table.set_columns(headers)
        table.add_rows(list(r.values()) for r in results)
        render = table.render()

        fmt = f"```\n{render}\n```\n*Returned {Plural(row=rows)} in {dt:.2f}ms*"
        if len(fmt) > 2000:
            fp = io.BytesIO(fmt.encode("utf-8"))
            await ctx.send("Too many results...", file=discord.File(fp, "results.txt"))
        else:
            await ctx.send(fmt)

    @commands.group(aliases=["ul"])
    @commands.check(repo.is_owner)
    async def uplink(self, ctx):
        """ Relay messages between current and target channel """
        if ctx.invoked_subcommand is None:
            _help = await ctx.bot.formatter.format_help_for(ctx, ctx.command)

            for page in _help:
                await ctx.send(page)

    @uplink.command(name="-o")
    @commands.check(repo.is_owner)
    async def uplink_open(self, ctx, uplinkchannelid: int):
        """ Open the connection """
        msguplinkchan = self.bot.get_channel(uplinkchannelid)
        with open("uplink.json", "r+") as file:
            content = json.load(file)
            content["uplinkchan"] = uplinkchannelid
            content["downlinkchan"] = ctx.channel.id
            file.seek(0)
            json.dump(content, file)
            file.truncate()
            await msguplinkchan.send(
                "A support staff member has connected to the channel."
            )
            await ctx.send("Connected.")

    @uplink.command(name="-c")
    @commands.check(repo.is_owner)
    async def uplink_close(self, ctx):
        """ Close the connection """
        with open("uplink.json", "r+") as file:
            content = json.load(file)
            msguplinkchan = self.bot.get_channel(content["uplinkchan"])
            content["uplinkchan"] = 0
            content["downlinkchan"] = 0
            file.seek(0)
            json.dump(content, file)
            file.truncate()
            await msguplinkchan.send("The connection was closed.")
            await ctx.send("Disconnected")

    @commands.group()
    @commands.check(repo.is_owner)
    async def blacklist(self, ctx):
        await ctx.send("Arguments: `BADD` / `BREMOVE` / `BDISCARD` / `BSHOW`")

    @blacklist.command()
    @commands.check(repo.is_owner)
    async def badd(self, ctx, userid: int, *, reason: str):
        self.bot.blacklist.append(userid)
        user = self.bot.find_user(userid)
        try:
            await user.send(
                f"**{ctx.author.name}#{ctx.author.discriminator}** blocked you from using the bot for: **{reason}**"
            )
        except discord.forbidden:
            await ctx.send(":warning: | **Unable to send DMs to specified user.**")
        await ctx.send(":ok_hand:")

    @blacklist.command()
    @commands.check(repo.is_owner)
    async def bremove(self, ctx, *, userid: int):
        self.bot.blacklist.remove(userid)
        user = self.bot.find_user(userid)
        try:
            await user.send(
                f"**{user.name}#{user.discriminator}**, **{ctx.author.name}#{ctx.author.discriminator}** unblocked you from using the bot. Don't abuse the bot again or you will get blocked **permanently**."
            )
        except discord.forbidden:
            await ctx.send(":warning: | **Unable to send DMs to specified user.**")
        await ctx.send(":ok_hand:")

    @blacklist.command()
    @commands.check(repo.is_owner)
    async def bdiscard(self, ctx):
        self.bot.blacklist = []
        await ctx.send(":ok_hand:")

    @blacklist.command()
    @commands.check(repo.is_owner)
    async def bshow(self, ctx):
        await ctx.send(f"``{self.bot.blacklist}``")

    @commands.command()
    @commands.check(repo.is_owner)
    async def parsehtml(self, ctx, url: str):
        r = requests.get(f"{url}")
        data = r.text
        soup = BeautifulSoup(data, 'html.parser')
        msgtosend = f"```html\n{soup.prettify()}\n```"
        if len(msgtosend) > 1900:
            file = BytesIO(msgtosend.encode('utf-8'))
            return await ctx.send(content=f"Too big to send, here is the file!", file=discord.File(file, filename="parsedhtml.html"))
        await ctx.send(msgtosend)


def setup(bot):
    bot.add_cog(Admin(bot))
