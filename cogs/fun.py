import random
import discord
import json
import requests

from random import randint
from discord.ext import commands
from utils import lists, http, default, eapi, sfapi, permissions

processapi = eapi.processapi
processshowapi = eapi.processshowapi
search = sfapi.search


class ResultNotFound(Exception):
    """Used if ResultNotFound is triggered by e* API."""

    pass


class InvalidHTTPResponse(Exception):
    """Used if non-200 HTTP Response got from server."""

    pass


class Fun:
    def __init__(self, bot):
        self.bot = bot
        self.config = default.get("config.json")

    async def getserverstuff(self, ctx):
        query = "SELECT * FROM adminpanel WHERE serverid = $1;"
        row = await self.bot.db.fetchrow(query, ctx.guild.id)
        if row is None:
            query = "INSERT INTO adminpanel VALUES ($1, $2, $3, $4, $5, $6, $7);"
            await self.bot.db.execute(query, ctx.guild.id, 0, 0, 1, 0, 0, 0)
            query = "SELECT * FROM adminpanel WHERE serverid = $1;"
            row = await self.bot.db.fetchrow(query, ctx.guild.id)
        return row

    @commands.command(aliases=["8ball"])
    async def eightball(self, ctx, *, question: commands.clean_content):
        """ Consult 8ball to receive an answer """
        answer = random.choice(lists.ballresponse)
        await ctx.send(f"🎱 **Question:** {question}\n**Answer:** {answer}")

    async def randomimageapi(self, ctx, url, endpoint):
        rowcheck = await self.getserverstuff(ctx)
        try:
            urltouse = url.replace("webp", "png")
            r = await http.get(urltouse, res_method="json", no_cache=True)
        except json.JSONDecodeError:
            return await ctx.send("Couldn't find anything from the API")
        if rowcheck["embeds"] is 0 or not permissions.can_embed(ctx):
            return await ctx.send(r[endpoint])
        embed = discord.Embed(colour=249_742)
        embed.set_image(url=r[endpoint])
        await ctx.send(embed=embed)

    async def textapi(self, ctx, url, endpoint):
        try:
            r = await http.get(url, res_method="json", no_cache=True)
        except json.JSONDecodeError:
            return await ctx.send("Couldn't find anything from the API")

        await ctx.send(f"{r[endpoint]}")

    async def factapi(self, ctx, url, endpoint):
        try:
            r = await http.get(url, res_method="json", no_cache=True)
        except json.JSONDecodeError:
            return await ctx.send("Couldn't find anything from the API")

        await ctx.send(f"**Did you know?** 🤔\n\n{r[endpoint]}")

    async def asciitext(self, ctx, url):
        try:
            with requests.get(url) as f:
                html = f.text
                await ctx.send(f"```\n{html}\n```")
        except InvalidHTTPResponse as e:
            print(e)

    @commands.command()
    @commands.cooldown(rate=1, per=5.0, type=commands.BucketType.user)
    async def cat(self, ctx):
        """ Posts a random cat """
        await self.randomimageapi(ctx, "https://nekos.life/api/v2/img/meow", "url")

    @commands.command()
    @commands.cooldown(rate=1, per=5.0, type=commands.BucketType.user)
    async def dog(self, ctx):
        """ Posts a random dog """
        await self.randomimageapi(ctx, "https://random.dog/woof.json", "url")

    @commands.command()
    @commands.cooldown(rate=1, per=5.0, type=commands.BucketType.user)
    async def doggo(self, ctx):
        """ Posts a random dog """
        await self.randomimageapi(
            ctx, "https://dog.ceo/api/breeds/image/random", "message"
        )

    @commands.command()
    @commands.cooldown(rate=1, per=5.0, type=commands.BucketType.user)
    async def neko(self, ctx):
        """ Posts a random neko """
        await self.randomimageapi(ctx, "https://nekos.life/api/v2/img/neko", "url")

    @commands.command()
    @commands.cooldown(rate=1, per=5.0, type=commands.BucketType.user)
    async def duck(self, ctx):
        """ Posts a random duck """
        await self.randomimageapi(ctx, "https://random-d.uk/api/v1/random", "url")

    @commands.command()
    @commands.cooldown(rate=1, per=5.0, type=commands.BucketType.user)
    async def fox(self, ctx):
        """ Posts a random fox girl """
        await self.randomimageapi(ctx, "https://nekos.life/api/v2/img/fox_girl", "url")

    @commands.command()
    @commands.cooldown(rate=1, per=5.0, type=commands.BucketType.user)
    async def rabbit(self, ctx):
        """ Posts a random rabbit """
        await self.randomimageapi(
            ctx,
            f"https://api.chewey-bot.ga/rabbit?auth={self.config.cheweyauth}",
            "data",
        )

    @commands.command()
    @commands.cooldown(rate=1, per=5.0, type=commands.BucketType.user)
    async def snek(self, ctx):
        """ Does a heckin snek image """
        await self.randomimageapi(
            ctx,
            f"https://api.chewey-bot.ga/snake?auth={self.config.cheweyauth}",
            "data",
        )

    @commands.command()
    @commands.cooldown(rate=1, per=5.0, type=commands.BucketType.user)
    async def otter(self, ctx):
        """ Posts a random otter """
        await self.randomimageapi(
            ctx,
            f"https://api.chewey-bot.ga/otter?auth={self.config.cheweyauth}",
            "data",
        )

    @commands.command()
    @commands.cooldown(rate=1, per=5.0, type=commands.BucketType.user)
    async def birb(self, ctx):
        """ Posts a random birb """
        await self.randomimageapi(
            ctx, f"https://api.chewey-bot.ga/birb?auth={self.config.cheweyauth}", "data"
        )

    @commands.command(aliases=["flip", "coin"])
    async def coinflip(self, ctx):
        """ Coinflip! """
        coinsides = ["Heads", "Tails"]
        await ctx.send(
            f"**{ctx.author.name}** flipped a coin and got **{random.choice(coinsides)}**!"
        )

    @commands.command()
    async def reverse(self, ctx, *, text: str):
        """ !poow ,ffuts esreveR """
        t_rev = text[::-1].replace("@", "@\u200B").replace("&", "&\u200B")
        await ctx.send(f"🔁 {t_rev}")

    @commands.command()
    async def rate(self, ctx, *, thing: commands.clean_content):
        """ Rates what you desire """
        numbers = random.randint(0, 100)
        decimals = random.randint(0, 9)

        if numbers == 100:
            decimals = 0

        await ctx.send(f"I'd rate {thing} a **{numbers}.{decimals} / 100**")

    @commands.command(aliases=["howhot", "hot"])
    async def hotcalc(self, ctx, user: discord.Member = None):
        """ Returns a random percent for how hot is a discord user """
        if user is None:
            user = ctx.author

        random.seed(user.id)
        r = random.randint(1, 100)
        hot = r / 1.17

        emoji = "💔"
        if hot > 25:
            emoji = "❤"
        if hot > 50:
            emoji = "💖"
        if hot > 75:
            emoji = "💞"

        await ctx.send(f"**{user.name}** is **{hot:.2f}%** hot {emoji}")

    @commands.command()
    async def e926(self, ctx, *args):
        """ Searches e926 with given tags. """
        msgtoedit = await ctx.send("Searching...")
        args = " ".join(args)
        args = str(args)
        print("------")
        print("Got command with args: " + args)
        if "order:score_asc" in args:
            await ctx.send("I'm not going to fall into that one, silly~")
            return
        if "score:" in args:
            apilink = f"https://e926.net/post/index.json?tags={args}&limit=320"
        else:
            apilink = (
                f"https://e926.net/post/index.json?tags={args}&score:>25&limit=320"
            )
        try:
            await eapi.processapi(apilink)
        except ResultNotFound:
            await ctx.send("Result not found!")
            return
        except InvalidHTTPResponse:
            await ctx.send(
                "We're getting invalid response from the API, please try again later!"
            )
            return
        msgtoedit = await ctx.channel.get_message(msgtoedit.id)
        msgtosend = "Post link: `https://{netloc}.net/post/show/{eapi.processapi.imgid}/`\r\nArtist: `{eapi.processapi.imgartist}`\r\nSource: `{eapi.processapi.imgsource}`\r\nRating: {eapi.processapi.imgrating}\r\nTags: `{eapi.processapi.imgtags}` ...and more\r\nImage link: {eapi.processapi.file_link}"
        await msgtoedit.edit(content=msgtosend)

    @commands.command()
    async def yell(self, ctx, *, text: str):
        """ AAAAAAAAA! """
        t_upper = text.upper().replace("@", "@\u200B").replace("&", "&\u200B")
        await ctx.send(f"⬆️ {t_upper}")

    @commands.command()
    async def whisper(self, ctx, *, text: str):
        """ Shh Be quiet.. """
        t_lower = text.lower().replace("@", "@\u200B").replace("&", "&\u200B")
        await ctx.send(f"⬇️ {t_lower}")

    @commands.command()
    @commands.cooldown(rate=1, per=5.0, type=commands.BucketType.user)
    async def fact(self, ctx):
        """ sends a random fact """
        await self.factapi(ctx, "https://nekos.life/api/v2/fact", "fact")

    @commands.command()
    async def bamboozle(self, ctx):
        """ You just got bamboozled! """
        await ctx.send(f"**{ctx.author.name}** just got heckin' bamboozled!")

    @commands.command()
    @commands.guild_only()
    async def ship(self, ctx, user: discord.User, *, user2: discord.User = None):
        """Checks the shiprate for 2 users"""
        rowcheck = await self.getserverstuff(ctx)
        author = ctx.message.author
        if not user2:
            user2 = author
        if not user:
            await ctx.send("can't ship nothing y'know..")
        elif user.id == user2.id:
            await ctx.send("i-i can't ship the same person..")
        elif user.id == author.id and user2.id == author.id:
            await ctx.send(f"wow, you're in love with yourself, huh {ctx.author.name}?")
        elif (
            user == self.bot.user
            and user2 == author
            or user2 == self.bot.user
            and user == author
        ):
            blushes = ["m-me..? 0////0", "m-me..? >////<"]
            return await ctx.send(random.choice(blushes))

        else:
            n = randint(1, 100)
            if n == 100:
                bar = "██████████"
                heart = "💞"
            elif n >= 90:
                bar = "█████████."
                heart = "💕"
            elif n >= 80:
                bar = "████████.."
                heart = "😍"
            elif n >= 70:
                bar = "███████..."
                heart = "💗"
            elif n >= 60:
                bar = "██████...."
                heart = "❤"
            elif n >= 50:
                bar = "█████....."
                heart = "❤"
            elif n >= 40:
                bar = "████......"
                heart = "💔"
            elif n >= 30:
                bar = "███......."
                heart = "💔"
            elif n >= 20:
                bar = "██........"
                heart = "💔"
            elif n >= 10:
                bar = "█........."
                heart = "💔"
            elif n < 10:
                bar = ".........."
                heart = "🖤"
            else:
                bar = ".........."
                heart = "🖤"
            name1 = user.name.replace(" ", "")
            name1 = name1[: int(len(name1) / 2) :]
            name2 = user2.name.replace(" ", "")
            name2 = name2[int(len(name2) / 2) : :]
            if rowcheck["embeds"] is 0 or not permissions.can_embed(ctx):
                return await ctx.send(
                    f"```\n{user.name} x {user2.name}\n\n{n}% {bar} {heart}\n\nShipname: {str(name1 + name2).lower()}\n```"
                )
            ship = discord.Embed(
                description=f"**{n}%** **`{bar}`** {heart}", color=ctx.me.colour
            )
            ship.title = f"{user.name} x {user2.name}"
            ship.set_footer(text=f"Shipname: {str(name1 + name2).lower()}")
            await ctx.send(embed=ship)

    @commands.command(aliases=["👏"])
    @commands.guild_only()
    async def emojify(self, ctx, emote, *, text_to_clap: str):
        """ 👏bottom👏text👏 """
        clapped_text = (
            text_to_clap.replace("@everyone", f"{emote}everyone")
            .replace("@here", f"{emote}here")
            .replace(" ", f"{emote}")
        )
        clapped_text = f"{emote}{clapped_text}{emote}"
        await ctx.send(clapped_text)

    @commands.command()
    @commands.guild_only()
    async def owo(self, ctx):
        """Sends a random owo face"""
        owo = random.choice(lists.owos)
        await ctx.send(f"{owo} whats this~?")

    @commands.command()
    @commands.guild_only()
    async def choose(self, ctx, *args):
        """Choose one of a lot (Split with |) """
        args = " ".join(args)
        args = str(args)
        choices = args.split("|")
        if len(choices) < 2:
            return await ctx.send("You need to send at least 2 choices!")
        await ctx.send(random.choice(choices))

    @commands.command()
    @commands.guild_only()
    async def jpeg(self, ctx, urltojpeg: str):
        """ Does what it says on the can """
        if "http" not in urltojpeg:
            return await ctx.send("Include a url you donk!")
        await self.randomimageapi(
            ctx,
            f"https://nekobot.xyz/api/imagegen?type=jpeg&url={urltojpeg}",
            "message",
        )

    @commands.command()
    @commands.guild_only()
    async def deepfry(self, ctx, urltojpeg: str):
        """ Deepfries an image """
        if "http" not in urltojpeg:
            return await ctx.send("Include a url you donk!")
        await self.randomimageapi(
            ctx,
            f"https://nekobot.xyz/api/imagegen?type=deepfry&image={urltojpeg}",
            "message",
        )

    @commands.command()
    @commands.guild_only()
    async def clyde(self, ctx, clydetext: str):
        """ Makes Clyde say something """
        if clydetext is None:
            return await ctx.send("Include some text you donk!")
        await self.randomimageapi(
            ctx,
            f"https://nekobot.xyz/api/imagegen?type=clyde&text={clydetext}",
            "message",
        )

    @commands.command()
    @commands.guild_only()
    async def magik(self, ctx, intensity: str, imgtomagik: str):
        """ why don'T WE JUST RELAX AND TURn on THe rADIO? """
        if imgtomagik is None:
            return await ctx.send("Include some text you donk!")
        if intensity not in ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"]:
            return await ctx.send("Include an intensity to magik (1-10)")
        await self.randomimageapi(
            ctx,
            f"https://nekobot.xyz/api/imagegen?type=magik&image={imgtomagik}&intensity={intensity}",
            "message",
        )

    @commands.command(aliases=["ascii"])
    @commands.guild_only()
    async def asciify(self, ctx, *, text: str):
        """ Turns any text given into ascii """
        texttoascii = text.replace(" ", "%20")
        await self.asciitext(ctx, f"http://artii.herokuapp.com/make?text={texttoascii}")

    @commands.command(aliases=["say"])
    @commands.guild_only()
    async def echo(self, ctx, *, text: str):
        """ Says what you want """
        text = text.replace("@everyone", "@​everyone").replace("@here", "@​here")
        await ctx.send(text)

    @commands.command()
    @commands.guild_only()
    async def snipe(self, ctx, channel: discord.TextChannel = None, index: int = 0):
        """ Snipe deleted messages o3o """
        rowcheck = await self.getserverstuff(ctx)
        channel = channel or ctx.channel

        if index != 0:
            index = index - 1

        try:
            sniped = self.bot.snipes[channel.id][index]
        except KeyError:
            return await ctx.send(
                ":warning: | **No message to snipe or index must not be greater than 5 or lower than 1**",
                delete_after=10,
            )
        if rowcheck["embeds"] is 0 or not permissions.can_embed(ctx):
            return await ctx.send(
                f"```\n{sniped.author}: {sniped.clean_content}\n\nSniped by: {ctx.author}\n```"
            )

        embed = discord.Embed(
            color=randint(0x000000, 0xFFFFFF),
            timestamp=sniped.created_at,
            title=f"{sniped.author} said",
            description=sniped.clean_content,
        )
        embed.set_footer(
            text=f"Sniped by {ctx.author} | Message created",
            icon_url=ctx.author.avatar_url,
        )
        embed.set_thumbnail(url=sniped.author.avatar_url)
        await ctx.send(embed=embed)

    @commands.command()
    @commands.guild_only()
    async def markov(self, ctx):
        """Generates a Markov Chain"""
        await ctx.send(
            " ".join(
                random.sample(
                    [
                        m.clean_content
                        for m in await ctx.channel.history(limit=150).flatten()
                        if not m.author.bot
                    ],
                    10,
                )
            )
        )

    @commands.command()
    async def hug(self, ctx, user: discord.Member = None):
        """ Hug a user! """
        rowcheck = await self.getserverstuff(ctx)
        endpoint = "url"
        if user is None:
            user = "themself"
        try:
            await ctx.message.delete()
        except discord.Forbidden:
            pass
        try:
            r = await http.get("https://nekos.life/api/v2/img/hug", res_method="json", no_cache=True)
        except json.JSONDecodeError:
            return await ctx.send("Couldn't find anything from the API")
        if rowcheck["embeds"] is 0 or not permissions.can_embed(ctx):
            return await ctx.send(f"💖 | **{ctx.author.name}** hugs **{user.name}**")
        embed = discord.Embed(colour=249_742, description=f"**{ctx.author.name}** hugs **{user.name}**")
        embed.set_image(url=r[endpoint])
        await ctx.send(embed=embed)

    @commands.command()
    async def kiss(self, ctx, user: discord.Member = None):
        """ Kiss a user! """
        rowcheck = await self.getserverstuff(ctx)
        endpoint = "url"
        if user is None:
            user = "themself"
        try:
            await ctx.message.delete()
        except discord.Forbidden:
            pass
        try:
            r = await http.get("https://nekos.life/api/v2/img/kiss", res_method="json", no_cache=True)
        except json.JSONDecodeError:
            return await ctx.send("Couldn't find anything from the API")
        if rowcheck["embeds"] is 0 or not permissions.can_embed(ctx):
            return await ctx.send(f"💗 | **{ctx.author.name}** gives **{user.name}** a kiss~!")
        embed = discord.Embed(colour=249_742, description=f"**{ctx.author.name}** gives **{user.name}** a kiss~!")
        embed.set_image(url=r[endpoint])
        await ctx.send(embed=embed)

    @commands.command()
    async def pat(self, ctx, user: discord.Member = None):
        """ Pat a user! """
        rowcheck = await self.getserverstuff(ctx)
        endpoint = "url"
        if user is None:
            user = "themself"
        try:
            await ctx.message.delete()
        except discord.Forbidden:
            pass
        try:
            r = await http.get("https://nekos.life/api/v2/img/pat", res_method="json", no_cache=True)
        except json.JSONDecodeError:
            return await ctx.send("Couldn't find anything from the API")
        if rowcheck["embeds"] is 0 or not permissions.can_embed(ctx):
            return await ctx.send(f"💗 | **{ctx.author.name}** pats **{user.name}** on the head")
        embed = discord.Embed(colour=249_742, description=f"**{ctx.author.name}** pats **{user.name}** on the head")
        embed.set_image(url=r[endpoint])
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Fun(bot))

# feed <@user>
# cuddle <@user>
# poke <@user>
# slap <@user>
# tickle <@user>
