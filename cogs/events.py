import dhooks
import discord
import traceback
import psutil
import os
import random
import datetime

from dhooks import Webhook
from datetime import datetime
from discord.ext.commands import errors
from utils import default, lists


async def send_cmd_help(ctx):
    if ctx.invoked_subcommand:
        _help = await ctx.bot.formatter.format_help_for(ctx, ctx.invoked_subcommand)
    else:
        _help = await ctx.bot.formatter.format_help_for(ctx, ctx.command)

    for page in _help:
        await ctx.send(page)


class Events:
    def __init__(self, bot):
        self.bot = bot
        self.config = default.get("config.json")
        self.process = psutil.Process(os.getpid())

    async def on_command_error(self, ctx, err):
        if isinstance(err, (errors.BadArgument, errors.MissingRequiredArgument)):
            await send_cmd_help(ctx)

        elif isinstance(err, errors.CommandInvokeError):
            err = err.original

            _traceback = traceback.format_tb(err.__traceback__)
            _traceback = ''.join(_traceback)
            error = '```py\n{2}{0}: {3}\n```'.format(type(err).__name__, ctx.message.content, _traceback, err)
            logchannel = self.bot.get_channel(508420200815656966)
            await ctx.send("There was an error in processing the command, our staff team have been notified, and will be in contact soon.")
            await logchannel.send(f"`ERROR`\n{error}\nRoot Server: {ctx.guild.name} ({ctx.guild.id})\nRoot Channel: {ctx.channel.name} ({ctx.channel.id})\nRoot User: {ctx.author.name}#{ctx.author.discriminator} ({ctx.author.id})")

        elif isinstance(err, errors.CheckFailure):
            pass

        elif isinstance(err, errors.CommandOnCooldown):
            await ctx.send(f"This command is on cooldown... try again in {err.retry_after:.0f} seconds.")

        elif isinstance(err, errors.CommandNotFound):
            pass

    async def on_ready(self):
        if not hasattr(self.bot, 'uptime'):
            self.bot.uptime = datetime.utcnow()
        webhook = Webhook(self.config.readywebhook, is_async=True)
        embed = dhooks.Embed(title=f'Reconnected, Online and Operational!', description='Ready Info', color=5810826, timestamp=True)
        embed.set_author(name=f'PawBot', url='https://discordapp.com/oauth2/authorize?client_id=460383314973556756&scope=bot&permissions=469888118', icon_url='https://cdn.discordapp.com/avatars/460383314973556756/d96ff7682f89483c4864f7af4b3a096c.png?size=2048')
        embed.add_field(name='Guilds', value=f'**{len(self.bot.guilds)}**', inline=True)
        embed.add_field(name='Users', value=f'**{len(self.bot.users)}**', inline=True)
        await webhook.execute(embeds=embed)
        await webhook.close()
        await self.bot.change_presence(activity=discord.Game(type=0, name=random.choice(lists.randomPlayings)), status=discord.Status.online)

    async def on_guild_join(self, guild):
        if not guild.icon_url:
            guildicon = "https://cdn.discordapp.com/attachments/443347566231289856/513380120451350541/2mt196.jpg"
        else:
            guildicon = guild.icon_url
        findbots = sum(1 for member in guild.members if member.bot)
        findusers = sum(1 for member in guild.members if not member.bot)
        webhook = Webhook(self.config.guildjoinwebhook, is_async=True)
        embed = dhooks.Embed(description=f'I\'ve joined {guild.name}!', color=5810826, timestamp=True)
        embed.set_author(name=f'{guild.name}', url='https://discordapp.com/oauth2/authorize?client_id=460383314973556756&scope=bot&permissions=469888118', icon_url=guildicon)
        embed.set_thumbnail(url=guildicon)
        embed.add_field(name='Info', value=f'New guild count: **{len(self.bot.guilds)}**\nOwner: **{guild.owner}**\nUsers/Bot Ratio: **{findusers}/{findbots}**')
        await webhook.execute(embeds=embed, username=guild.name, avatar_url=guildicon)
        await webhook.close()

    async def on_guild_remove(self, guild):
        if not guild.icon_url:
            guildicon = "https://cdn.discordapp.com/attachments/443347566231289856/513380120451350541/2mt196.jpg"
        else:
            guildicon = guild.icon_url
        findbots = sum(1 for member in guild.members if member.bot)
        findusers = sum(1 for member in guild.members if not member.bot)
        webhook = Webhook(self.config.guildleavewebhook, is_async=True)
        embed = dhooks.Embed(description=f'I\'ve left {guild.name}...', color=5810826, timestamp=True)
        embed.set_author(name=f'{guild.name}', url='https://discordapp.com/oauth2/authorize?client_id=460383314973556756&scope=bot&permissions=469888118', icon_url=guildicon)
        embed.set_thumbnail(url=guildicon)
        embed.add_field(name='Info', value=f'New guild count: **{len(self.bot.guilds)}**\nOwner: **{guild.owner}**\nUsers/Bot Ratio: **{findusers}/{findbots}**')
        await webhook.execute(embeds=embed, username=guild.name, avatar_url=guildicon)
        await webhook.close()


def setup(bot):
    bot.add_cog(Events(bot))
