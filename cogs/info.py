import time
import discord
import psutil
import os
import asyncio
import dhooks

from collections import Counter
from dhooks import Webhook, Embed
from discord.ext import commands
from datetime import datetime
from utils import repo, default, permissions


class Information:
    def __init__(self, bot):
        self.bot = bot
        self.config = default.get("config.json")
        self.process = psutil.Process(os.getpid())
        self.counter = Counter()

    async def getserverstuff(self, ctx):
        query = "SELECT * FROM adminpanel WHERE serverid = $1;"
        row = await self.bot.db.fetchrow(query, ctx.guild.id)
        if row is None:
            query = "INSERT INTO adminpanel VALUES ($1, $2, $3, $4, $5, $6, $7);"
            await self.bot.db.execute(query, ctx.guild.id, 0, 0, 1, 0, 0, 0)
            query = "SELECT * FROM adminpanel WHERE serverid = $1;"
            row = await self.bot.db.fetchrow(query, ctx.guild.id)
        return row

    def get_bot_uptime(self, *, brief=False):
        now = datetime.utcnow()
        delta = now - self.bot.uptime
        hours, remainder = divmod(int(delta.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        days, hours = divmod(hours, 24)

        if not brief:
            if days:
                fmt = '{d} days, {h} hours, {m} minutes, and {s} seconds'
            else:
                fmt = '{h} hours, {m} minutes, and {s} seconds'
        else:
            fmt = '{h}h {m}m {s}s'
            if days:
                fmt = '{d}d ' + fmt

        return fmt.format(d=days, h=hours, m=minutes, s=seconds)

    @commands.command(aliases=["?"])
    async def help(self, ctx, option: str=None, *, command_or_module: str=None):
        """ Gives my commands! """
        bot = self.bot
        server = self.bot.get_emoji(513831608265080852)
        bottag = self.bot.get_emoji(513831608265080852)
        public_modules = ["adminpanel", "info", "encryption", "mod", "nsfw", "fun"]
        paws = self.bot.get_emoji(513831608265080852)
        user = ctx.author
        avy = user.avatar_url

        if not option:
            mods = "• " + "\n• ".join(public_modules)
            embed = discord.Embed(title=f"{paws} Hewwo {ctx.author.name}, I'm owopup! {paws}", description=f"`The fluffiest Discord Bot Around~`\nUse `{ctx.prefix}help m <module>` to get help on a set of commands or `{ctx.prefix}help c <cmd>` to get help on a specific command.\n\nAll of my modules are listed below:\n\n{mods}", color=ctx.me.colour)
            embed.set_thumbnail(url=self.bot.user.avatar_url_as(format="png"))
            embed.add_field(name="Important Links", value=f"{bottag} [Bot Invite](https://discordapp.com/oauth2/authorize?client_id=365255872181567489&scope=bot&permissions=470150214)\n{server} [Support Guild Invite](https://discord.gg/c4vWDdd)", inline=True)
            embed.set_footer(text=f"Requested by {ctx.author}", icon_url=avy)
            try:
                await ctx.send(embed=embed)
            except discord.Forbidden:
                await ctx.send(";w; i can't send embeds")

        if option == "c" or option == "command" or option == "Command" or option == "cmd":
            if not command_or_module:
                return await ctx.send("You gotta specify a command to get help for y'know. :P")
            try:
                cmd = bot.get_command(command_or_module)
                if cmd.cog_name == "Admin" and ctx.author.id not in repo.owners:
                    return await ctx.send("Woah there, this command is for my owners only.")
                try:
                    one = "\n```fix\nSubcommands\n" + "\n".join([f"│├{x.name} - {x.help}" for x in bot.all_commands[command_or_module].commands]) + "```"
                except AttributeError:
                    one = ""

                uwu = " ".join(cmd.clean_params)
                uwu = uwu

                one = one
                if cmd.root_parent:
                    cmd_name = str(cmd.root_parent) + " " + str(cmd.name)
                else:
                    cmd_name = cmd.name
                if not cmd.aliases == []:
                    aliases = f"Aliases: ``" + ", ".join(cmd.aliases) + "``"
                else:
                    aliases = ""

                info = discord.Embed(color=ctx.me.colour)
                info.title = f"{paws} Help for {cmd} {paws}"
                info.description = f"Usage: `{ctx.prefix}{cmd_name} {uwu}`\nCommand Description: `{cmd.help}`\n{aliases}{one}".replace(bot.user.mention, f"@{bot.user.name}")
                info.set_thumbnail(url=self.bot.user.avatar_url_as(format="png"))
                info.set_footer(text=f"Requested by {ctx.author}", icon_url=avy)
                await ctx.send(embed=info)
            except ValueError:
                await ctx.send("uhhhh ``{}`` is not a valid command.".format(command_or_module))
        elif option == "m" or option == "module" or option == "Module":
            if command_or_module.lower() == "fun":
                cogname = "Fun"
                embedcommandname = "Fun"
                extra = ""
            elif command_or_module.lower() == "info":
                cogname = "Information"
                embedcommandname = "Info"
                extra = ""
            elif command_or_module.lower() == "mod":
                cogname = "Moderation"
                embedcommandname = "Mod"
                extra = "**These Commands Require Perms**\n\n"
            elif command_or_module.lower() == "encryption":
                cogname = "Encryption"
                embedcommandname = "Encryption"
                extra = ""
            elif command_or_module.lower() == "nsfw":
                cogname = "NSFW"
                embedcommandname = "NSFW"
                extra = "**These can only be used in an NSFW channel**\n\n"
            elif command_or_module.lower() == "adminpanel":
                cogname = "AdminPanel"
                embedcommandname = "Admin Panel"
                extra = "**Server admins only**\n\n"
            else:
                return await ctx.send("Uhhh, i couldn't find a module called `{}`".format(command_or_module))

            cogname = "\n".join([f"`{cmd.name}` - {cmd.help}" for cmd in bot.get_cog_commands(cogname)])
            embed = discord.Embed(title=f"{paws} {embedcommandname} {paws}", description=extra + cogname, color=ctx.me.colour)
            embed.set_thumbnail(url=self.bot.user.avatar_url_as(format="png"))
            embed.set_footer(text=f"Requested by {ctx.author}", icon_url=avy)
            try:
                await ctx.send(embed=embed)
            except discord.Forbidden:
                await ctx.send(";w; i can't send embeds")
        elif not option:
            pass
        else:
            await ctx.send("The valid options are\nCommand: `owo help command|c|Command|cmd`\nModule: `owo help m|module|Module`")

    @commands.command()
    async def ping(self, ctx):
        """ Pong! """
        before = time.monotonic()
        message = await ctx.send("Did you just ping me?!")
        ping = (time.monotonic() - before) * 1000
        await message.edit(content=f"`MSG :: {int(ping)}ms\nAPI :: {round(self.bot.latency * 1000)}ms`")

    @commands.command(aliases=['joinme', 'join', 'botinvite'])
    async def invite(self, ctx):
        """ Invite me to your server """
        await ctx.send(f"**{ctx.author.name}**, use this URL to invite me\n<https://discordapp.com/oauth2/authorize?client_id=460383314973556756&scope=bot&permissions=469888118>")

    @commands.command(aliases=['supportserver', 'feedbackserver'])
    async def botserver(self, ctx):
        """ Get an invite to our support server! """
        if isinstance(ctx.channel, discord.DMChannel) or ctx.guild.id != 508396955660189715:
            return await ctx.send(f"**{ctx.author.name}**, you can join here! 🍻\n<{repo.invite}>")

        await ctx.send(f"**{ctx.author.name}**, this is my home.")

    @commands.command(aliases=['info', 'stats', 'status'])
    @commands.guild_only()
    async def about(self, ctx):
        """ About the bot """
        rowcheck = await self.getserverstuff(ctx)
        ramUsage = self.process.memory_full_info().rss / 1024**2
        avgmembers = round(len(self.bot.users) / len(self.bot.guilds))

        if rowcheck['embeds'] is 0 or not permissions.can_embed(ctx):
            return await ctx.send(f"```\nAbout {ctx.bot.user.name} | {repo.version}\nUptime: {self.get_bot_uptime()}\nDev: Paws#0001\nLibrary: discord.py\nCommands Loaded: {len([x.name for x in self.bot.commands])}\nGuilds: {len(ctx.bot.guilds)} (avg: {avgmembers} users/server )\nRAM: {ramUsage:.2f} MB\n```")

        embed = discord.Embed(title=f"About **{ctx.bot.user.name}** | **{repo.version}**", colour=ctx.me.colour, url="https://discordapp.com/oauth2/authorize?client_id=460383314973556756&scope=bot&permissions=469888118",)
        embed.set_thumbnail(url=ctx.bot.user.avatar_url)
        embed.add_field(name="Uptime", value=self.get_bot_uptime(), inline=False)
        embed.add_field(name="Dev", value="Paws#0001", inline=True)
        embed.add_field(name="Library", value="discord.py", inline=True)
        embed.add_field(name="Commands loaded", value=len([x.name for x in self.bot.commands]), inline=True)
        embed.add_field(name="Guilds", value=f"{len(ctx.bot.guilds)} (avg: {avgmembers} users/server )", inline=True)
        embed.add_field(name="RAM", value=f"{ramUsage:.2f} MB", inline=True)
        embed.add_field(name="Support", value=f"[Here]({repo.invite})", inline=True)

        await ctx.send(embed=embed)

    @commands.command()
    async def avatar(self, ctx, user: discord.Member = None):
        """ Get the avatar of you or someone else """
        rowcheck = await self.getserverstuff(ctx)

        if user is None:
            user = ctx.author

        if rowcheck['embeds'] is 0 or not permissions.can_embed(ctx):
            return await ctx.send(user.avatar_url)

        embed = discord.Embed(colour=249742)
        embed.set_image(url=user.avatar_url)
        await ctx.send(embed=embed)

    @commands.command()
    @commands.guild_only()
    async def joinedat(self, ctx, user: discord.Member = None):
        """ Check when a user joined the current server """
        rowcheck = await self.getserverstuff(ctx)

        if user is None:
            user = ctx.author

        if rowcheck['embeds'] is 0 or not permissions.can_embed(ctx):
            return await ctx.send(f"**{user}** joined **{ctx.guild.name}**\n{default.date(user.joined_at)}")

        embed = discord.Embed(colour=249742)
        embed.set_thumbnail(url=user.avatar_url)
        embed.description = f'**{user}** joined **{ctx.guild.name}**\n{default.date(user.joined_at)}'
        await ctx.send(embed=embed)

    @commands.command()
    @commands.guild_only()
    async def server(self, ctx):
        """ Check info about current server """
        if ctx.invoked_subcommand is None:

            rowcheck = await self.getserverstuff(ctx)
            
            findbots = sum(1 for member in ctx.guild.members if member.bot)

            emojilist = "​"
            for Emoji in ctx.guild.emojis:
                emojilist += f"{Emoji} "
            if len(emojilist) > 1024:
                emojilist = "Too long!"

            if rowcheck['embeds'] is 0 or not permissions.can_embed(ctx):
                return await ctx.send(f"```\nServer Name: {ctx.guild.name}\nServer ID: {ctx.guild.id}\nMembers: {ctx.guild.member_count}\nBots: {findbots}\nOwner: {ctx.guild.owner}\nRegion: {ctx.guild.region}\nCreated At: {default.date(ctx.guild.created_at)}\n```\nEmojis: {emojilist}")

            embed = discord.Embed(colour=249742)
            embed.set_thumbnail(url=ctx.guild.icon_url)
            embed.add_field(name="Server Name", value=ctx.guild.name, inline=True)
            embed.add_field(name="Server ID", value=ctx.guild.id, inline=True)
            embed.add_field(name="Members", value=ctx.guild.member_count, inline=True)
            embed.add_field(name="Bots", value=findbots, inline=True)
            embed.add_field(name="Owner", value=ctx.guild.owner, inline=True)
            embed.add_field(name="Region", value=ctx.guild.region, inline=True)
            embed.add_field(name='Emojis', value=emojilist, inline=False)
            embed.add_field(name="Created", value=default.date(ctx.guild.created_at), inline=False)
            await ctx.send(content=f"ℹ information about **{ctx.guild.name}**", embed=embed)

    @commands.command()
    async def user(self, ctx, user: discord.Member = None):
        """ Get user information """
        rowcheck = await self.getserverstuff(ctx)

        if user is None:
            user = ctx.author

        embed = discord.Embed(colour=249742)

        usrstatus = user.status

        if usrstatus == "online" or usrstatus == discord.Status.online:
            usrstatus = "<:online:514203909363859459> Online"
        elif usrstatus == "idle" or usrstatus == discord.Status.idle:
            usrstatus = "<:away:514203859057639444> Away"
        elif usrstatus == "dnd" or usrstatus == discord.Status.dnd:
            usrstatus = "<:dnd:514203823888138240> DnD"
        elif usrstatus == "offline" or usrstatus == discord.Status.offline:
            usrstatus = "<:offline:514203770452836359> Offline"
        else:
            usrstatus = "Broken"

        if user.nick:
            nick = user.nick
        else:
            nick = "No Nickname"

        if user.activity:
            usrgame = f"{user.activity.name}"
        else:
            usrgame = "No current game"

        usrroles = ""

        for Role in user.roles:
            if "@everyone" in Role.name:
                usrroles += "| @everyone | "
            else:
                usrroles += f"{Role.name} | "

        if len(usrroles) > 1024:
            usrroles = "Too many to count!"
        
        if rowcheck['embeds'] is 0 or not permissions.can_embed(ctx):
            return await ctx.send(f"Name: `{user.name}#{user.discriminator}`\nNick: `{nick}`\nUID: `{user.id}`\nStatus: {usrstatus}\nGame: `{usrgame}`\nCreated On: `{default.date(user.created_at)}`\nRoles:\n```\n{usrroles}\n```")

        embed.set_thumbnail(url=user.avatar_url)
        embed.add_field(name="Name", value=f"{user.name}#{user.discriminator}\n{nick}\n({user.id})", inline=True)
        embed.add_field(name="Status", value=usrstatus, inline=True)
        embed.add_field(name="Game", value=usrgame, inline=False)
        embed.add_field(name="Roles", value=usrroles, inline=False)
        embed.add_field(name="Created On", value=default.date(user.created_at), inline=True)
        if hasattr(user, "joined_at"):
            embed.add_field(name="Joined this server", value=default.date(user.joined_at), inline=True)
        await ctx.send(content=f"ℹ About **{user.name}**", embed=embed)

    @commands.command()
    @commands.guild_only()
    async def poll(self, ctx, time, *, question):
        """
        Creates a poll
        """
        await ctx.message.delete()
        time = int(time)
        pollmsg = await ctx.send(f"{ctx.message.author.mention} created a poll that will end after {time} seconds!\n**{question}**\n\nReact with :thumbsup: or :thumbsdown: to vote!")
        await pollmsg.add_reaction('👍')
        await pollmsg.add_reaction('👎')
        await asyncio.sleep(time)
        reactiongrab = await ctx.channel.get_message(pollmsg.id)
        for reaction in reactiongrab.reactions:
            if reaction.emoji == str('👍'):
                upvote_count = reaction.count
            else:
                if reaction.emoji == str('👎'):
                    downvote_count = reaction.count
                else:
                    pass
        await pollmsg.edit(content=f"{ctx.message.author.mention} created a poll that will end after {time} seconds!\n**{question}**\n\nTime's up!\n👍 = {upvote_count-1}\n\n👎 = {downvote_count-1}")

    @commands.command()
    async def suggest(self, ctx, *, suggestion_txt: str):
        """ Send a suggestion to my owner or just tell him shes doing a bad job """
        webhook = Webhook(self.config.suggwebhook, is_async=True)
        suggestion = suggestion_txt
        if ctx.guild:
            color = ctx.author.color
            footer = f"Sent from {ctx.guild.name}"
            guild_pic = ctx.guild.icon_url
        else:
            color = 0x254d16
            footer = "Sent from DMs"
            guild_pic = ""
        if len(suggestion) > 1500:
            await ctx.send(f"{ctx.author.mention} thats a bit too long for me to send. Shorten it and try again. (1500 character limit)")
        else:
            suggestionem = dhooks.Embed(description=f"{suggestion}", colour=color, timestamp=True)
            suggestionem.set_author(name=f"From {ctx.author}", icon_url=ctx.author.avatar_url)
            suggestionem.set_footer(text=footer, icon_url=guild_pic)
            try:
                await ctx.send("Alright, I sent your suggestion!!")
                await webhook.send(embeds=suggestionem)
                await webhook.close()
            except ValueError as e:
                await ctx.send("uhm.. something went wrong, try again later..")
                logchannel = self.bot.get_channel(508420200815656966)
                return await logchannel.send(f"`ERROR`\n```py\n{e}\n```\nRoot server: {ctx.guild.name} ({ctx.guild.id})\nRoot user: {ctx.author.name}#{ctx.author.discriminator} ({ctx.author.id})")

    @commands.command()
    async def customlink(self, ctx, invsuffix: str, invlink: str):
        """ Request a custom discord invite """
        webhook = Webhook(self.config.customlinkwebhook, is_async=True)
        color = ctx.author.color
        footer = f"Sent from {ctx.guild.name}"
        guild_pic = ctx.guild.icon_url
        embed = dhooks.Embed(description=f"Requested suffix: {invsuffix}\nInvite link: {invlink}", colour=color, timestamp=True)
        embed.set_author(name=f"From {ctx.author}", icon_url=ctx.author.avatar_url)
        embed.set_footer(text=footer, icon_url=guild_pic)
        try:
            await ctx.send("Alright, I sent your request!!")
            await webhook.send(embeds=embed)
            await webhook.close()
        except ValueError as e:
            await ctx.send("uhm.. something went wrong, try again later..")
            logchannel = self.bot.get_channel(508420200815656966)
            return await logchannel.send(f"`ERROR`\n```py\n{e}\n```\nRoot server: {ctx.guild.name} ({ctx.guild.id})\nRoot user: {ctx.author.name}#{ctx.author.discriminator} ({ctx.author.id})")

    @commands.command()
    async def args(self, ctx, *args):
        """Returns the number of args"""
        await ctx.send('{} arguments: {}'.format(len(args), ', '.join(args)))

    @commands.command()
    async def compare(self, ctx, str1: str = None, str2: str = None):
        """ Compare 2 strings, put in "" for multiple words per string """
        if str1 == str2:
            await ctx.send("The two strings are the same!")
        else:
            await ctx.send("The two strings are different...")

    @commands.command()
    @commands.guild_only()
    async def remindme(self, ctx, time: int, *, reminder):
        """ Pings you with the reminder after an amount of minutes """
        if self.counter[f"{ctx.author.id}.reminder"] is 1:
            return await ctx.send("You already have a current reminder!")
        if len(reminder) > 1500:
            return ctx.send("That reminder is too big!")
        timetowait = int(time*60)
        if timetowait > 604800:
            return await ctx.send("That's too long! I can wait up to 7 days (10080 mins).")
        timetowait = int(timetowait)
        await ctx.send(f"Ok! I'll remind you in `{time}` minute(s) about `{reminder}`")
        self.counter[f"{ctx.author.id}.reminder"] += 1
        await asyncio.sleep(timetowait)
        await ctx.send(f"{ctx.author.mention} your reminder: `{reminder}` is complete!")
        self.counter[f"{ctx.author.id}.reminder"] -= 1


def setup(bot):
    bot.add_cog(Information(bot))
