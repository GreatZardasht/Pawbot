import random
import discord
import json

from discord.ext import commands
from utils import http, default, sfapi, eapi

bannedtags = ["loli", "shota"]

processapi = eapi.processapi
processshowapi = eapi.processshowapi
search = sfapi.search


class ResultNotFound(Exception):
    """Used if ResultNotFound is triggered by e* API."""
    pass


class InvalidHTTPResponse(Exception):
    """Used if non-200 HTTP Response got from server."""
    pass


class NSFW:
    def __init__(self, bot):
        self.bot = bot
        self.config = default.get("config.json")

    async def randomimageapi(self, ctx, url, endpoint):
        try:
            r = await http.get(url, res_method="json", no_cache=True)
        except json.JSONDecodeError:
            return await ctx.send("Couldn't find anything from the API")

        embed = discord.Embed(colour=249742)
        embed.set_image(url=r[endpoint])
        await ctx.send(embed=embed)

    @commands.command()
    @commands.is_nsfw()
    @commands.cooldown(rate=1, per=5.0, type=commands.BucketType.user)
    async def lewdneko(self, ctx):
        """ Posts a lewd neko """
        await self.randomimageapi(ctx, 'https://nekos.life/api/v2/img/lewd', 'url')

    @commands.command()
    @commands.is_nsfw()
    @commands.cooldown(rate=1, per=5.0, type=commands.BucketType.user)
    async def lewdfeet(self, ctx):
        """ Posts a lewd foot image or gif """
        randomfoot = ["feet", "feetg"]
        await self.randomimageapi(ctx, f'https://nekos.life/api/v2/img/{random.choice(randomfoot)}', 'url')

    @commands.command()
    @commands.is_nsfw()
    @commands.cooldown(rate=1, per=5.0, type=commands.BucketType.user)
    async def lewdkemo(self, ctx):
        """ Posts a lewd kemonomimi character """
        randomfox = ["holoero", "erokemo", "hololewd"]
        await self.randomimageapi(ctx, f'https://nekos.life/api/v2/img/{random.choice(randomfox)}', 'url')

    @commands.command()
    @commands.is_nsfw()
    @commands.cooldown(rate=1, per=5.0, type=commands.BucketType.user)
    async def lewdanal(self, ctx):
        """ Posts a lewd anal gif/picture """
        await self.randomimageapi(ctx, f'https://nekos.life/api/v2/img/anal', 'url')

    @commands.command()
    @commands.is_nsfw()
    async def e621(self, ctx, *args):
        """Searches e621 with given queries."""
        if bannedtags in args:
            return ctx.send("Pls no")
        msgtoedit = await ctx.send("Searching...")
        args = ' '.join(args)
        args = str(args)
        netloc = "e621"
        print("------")
        print("Got command with args: " + args)
        if "order:score_asc" in args:
            await ctx.send("I'm not going to fall into that one, silly~")
            return
        if "score:" in args:
            apilink = 'https://e621.net/post/index.json?tags=' + args + '&limit=320'
        else:
            apilink = 'https://e621.net/post/index.json?tags=' + args + ' score:>25&limit=320'
        try:
            await processapi(apilink)
        except ResultNotFound:
            await ctx.send("Result not found!")
            return
        except InvalidHTTPResponse:
            await ctx.send("We're getting invalid response from the API, please try again later!")
            return
        msgtoedit = await ctx.channel.get_message(msgtoedit.id)
        msgtosend = """Post link: `https://""" + netloc + """.net/post/show/""" + processapi.imgid + """/`\r\nArtist: `""" + processapi.imgartist + """`\r\nSource: `""" + processapi.imgsource + """`\r\nRating: """ + processapi.imgrating + """\r\nTags: `""" + processapi.imgtags + """` ...and more\r\nImage link: """ + processapi.file_link
        await msgtoedit.edit(content=msgtosend)

    @commands.command()
    @commands.is_nsfw()
    async def show(self, ctx, arg):
        """Show a post from e621/e926 with given post ID"""
        msgtoedit = await ctx.send("Searching...")
        print("------")
        arg = str(arg)
        print("Got command with arg: " + arg)
        apilink = 'https://e621.net/post/show.json?id=' + arg
        try:
            await processshowapi(apilink)
        except ResultNotFound:
            await ctx.send("Result not found!")
            return
        except InvalidHTTPResponse:
            await ctx.send("We're getting invalid response from the API, please try again later!")
            return
        msgtoedit = await ctx.channel.get_message(msgtoedit.id)
        msgtosend = """Artist: """ + processshowapi.imgartist + """\r\nSource: `""" + processshowapi.imgsource + """`\r\nRating: """ + processshowapi.imgrating + """\r\nTags: `""" + processshowapi.imgtags + """` ...and more\r\nImage link: """ + processshowapi.file_link
        await msgtoedit.edit(content=msgtosend)

    @commands.command()
    @commands.is_nsfw()
    async def sofurry(self, ctx, *args):
        """Searches SoFurry with given queries."""
        maxlevel = "2"
        if bannedtags in args:
            return ctx.send("Pls no")
        msgtoedit = await ctx.send("Searching...")
        args = ' '.join(args)
        args = str(args)
        print("------")
        print("Got command with args: " + args)
        try:
            await search(args, maxlevel)
        except ResultNotFound:
            await ctx.send("Result not found!")
            return
        except InvalidHTTPResponse:
            await ctx.send("We're getting invalid response from the API, please try again later!")
            return
        msgtoedit = await ctx.channel.get_message(msgtoedit.id)
        msgtosend = """Title: {}\r\nArtist: {}\r\nTags: `{}`\r\nRating: {}\r\nImage link: {}""".format(search.title, search.artistName, search.tags, search.contentRating, search.full)
        await msgtoedit.edit(content=msgtosend)


def setup(bot):
    bot.add_cog(NSFW(bot))
