import discord
import random
import asyncio
import random
import string

from discord.ext import commands
from utils import permissions, default


class Economy:
    def __init__(self, bot):
        self.bot = bot
        self.config = default.get("config.json")

    @commands.command(aliases=["lb", "leaders"])
    @commands.guild_only()
    @commands.cooldown(rate=1, per=10.0, type=commands.BucketType.user)
    async def leaderboard(self, ctx):
        """Shows global leaderboard"""
        query = "SELECT * FROM userbal ORDER BY money DESC LIMIT 3;"
        row = await self.bot.db.fetch(query)
        embed = discord.Embed(
            title="The Richest People",
            color=random.randint(0x000000, 0xFFFFFF),
            timestamp=ctx.message.created_at,
        )
        embed.add_field(
            name="**:dizzy: Leaders**",
            value=f""":first_place: | {self.bot.get_user(row[0][0])}: **{row[0][1]}** <:coins:529700967097171969>\n:second_place: | {self.bot.get_user(row[1][0])}: **{row[1][1]}** <:coins:529700967097171969>\n:third_place: | {self.bot.get_user(row[2][0])}: **{row[2][1]}** <:coins:529700967097171969>""",
        )
        embed.set_footer(
            text=f"These stats are global, {ctx.author.name}",
            icon_url=ctx.author.avatar_url,
        )
        await ctx.send(embed=embed)

    @commands.group(hidden=True)
    @commands.guild_only()
    async def bank(self, ctx):
        """ Manage your money! """
        if ctx.invoked_subcommand is None:
            _help = await ctx.bot.formatter.format_help_for(ctx, ctx.command)

            for page in _help:
                await ctx.send(page)

    @bank.command()
    async def bal(self, ctx, user: discord.Member = None):
        """ Prints your balance """
        if user is None:
            user = ctx.author
        query = "SELECT * FROM userbal WHERE userid=$1;"
        row = await self.bot.db.fetchrow(query, user.id)
        if row is None:
            return await ctx.send(
                f"Hey! **{user.name}** doesn't have a bank account yet! Do `paw bank create` to create an account!"
            )
        await ctx.send(
            f"**{user.name}** has {row['money']} <:coins:529700967097171969>"
        )

    @bank.command()
    async def open(self, ctx):
        """ Opens an account """
        query = "SELECT * FROM userbal WHERE userid=$1;"
        row = await self.bot.db.fetchrow(query, ctx.author.id)
        if row:
            return await ctx.send("You already have an account!")
        query = "INSERT INTO userbal VALUES($1, $2);"
        row = await self.bot.db.fetchrow(query, ctx.author.id, 30)
        await ctx.send(
            "Thank you for registering with Pawbank! You have been given 30 <:coins:529700967097171969> as a gift."
        )

    @bank.command()
    @commands.cooldown(rate=1, per=86400.0, type=commands.BucketType.user)
    async def close(self, ctx):
        """ Closes an account """
        query = "SELECT * FROM userbal WHERE userid=$1;"
        row = await self.bot.db.fetchrow(query, ctx.author.id)
        if not row:
            return await ctx.send("You don't have an account!")
        N = 6
        delstring = ''.join(random.choices(string.ascii_uppercase + string.digits, k=N))
        def check(m):
            return m.content == delstring and m.channel == channel

        await ctx.message.delete()
        delmsg = await ctx.send(
            f"Are you sure you want to delete your account? If so, type: `{delstring}`"
        )
        channel = ctx.channel
        try:
            msg = await self.bot.wait_for(
                "message", timeout=60.0, check=check
            )
        except asyncio.TimeoutError:
            await delmsg.edit(content="Timed out..")
            await msg.delete()
        else:
            await msg.delete()
            query = "DELETE FROM userbal WHERE userid=$1;"
            row = await self.bot.db.fetchrow(query, ctx.author.id)
            await delmsg.edit(content="We're sorry to see you go ;w;")

    @bank.command()
    @commands.cooldown(rate=1, per=5.0, type=commands.BucketType.user)
    async def transfer(self, ctx, amount: int, user: discord.Member):
        """ Transfer coins """
        query = "SELECT * FROM userbal WHERE userid=$1;"
        altrow = await self.bot.db.fetchrow(query, user.id)
        if not altrow:
            return await ctx.send(
                "The person you are tranferring to doesn't have an account!"
            )
        query = "SELECT * FROM userbal WHERE userid=$1;"
        row = await self.bot.db.fetchrow(query, ctx.author.id)
        if not row:
            return await ctx.send("You don't have an account!")
        if row["money"] < amount:
            return await ctx.send("You don't have enough coins!")
        N = 6
        delstring = ''.join(random.choices(string.ascii_uppercase + string.digits, k=N))
        def check(m):
            return m.content == delstring and m.channel == channel
        try:
            await ctx.message.delete()
        except discord.Forbidden:
            pass
        delmsg = await ctx.send(
            f"Are you sure you want to transfer **{amount}** <:coins:529700967097171969> to **{user}**? If so, type: `{delstring}`"
        )
        channel = ctx.channel
        try:
            msg = await self.bot.wait_for(
                "message", timeout=60.0, check=check
            )
        except asyncio.TimeoutError:
            await delmsg.edit(content="Timed out..")
            try:
                await msg.delete()
            except discord.Forbidden:
                pass
        else:
            try:
                await msg.delete()
            except discord.Forbidden:
                pass
            transferfromamount = row["money"] - int(amount)
            transfertoamount = altrow["money"] + int(amount)
            query = "UPDATE userbal SET money = $1 WHERE userid = $2;"
            altrow = await self.bot.db.fetchrow(query, transfertoamount, user.id)
            query = "UPDATE userbal SET money = $1 WHERE userid = $2;"
            altrow = await self.bot.db.fetchrow(query, transferfromamount, ctx.author.id)
            await delmsg.edit(
                content=f"{ctx.author.mention}, you have successfully transferred {amount} <:coins:529700967097171969> to **{user.name}**"
            )

    @commands.command(aliases=["flip", "coin"])
    @commands.guild_only()
    @commands.cooldown(rate=1, per=5.0, type=commands.BucketType.user)
    async def coinflip(self, ctx, bet: int, side: str):
        query = "SELECT * FROM userbal WHERE userid=$1;"
        row = await self.bot.db.fetchrow(query, ctx.author.id)
        if not row:
            return await ctx.send("You don't have an account!")
        if bet > row["money"]:
            return await ctx.send("You're betting more than you own!")
        coinsides = ["heads", "tails"]
        if side not in coinsides:
            return await ctx.send("Please only use `heads` or `tails`!")
        result = random.choice(coinsides)
        if result == side:
            query = "SELECT * FROM userbal WHERE userid=$1;"
            row = await self.bot.db.fetchrow(query, ctx.author.id)
            betresult = int(bet * 2)
            betresult = row["money"] + betresult
            query = "UPDATE userbal SET money = $1 WHERE userid = $2;"
            altrow = await self.bot.db.fetchrow(query, betresult, ctx.author.id)
            msg = await ctx.send(f"The coin landed and...")
            await asyncio.sleep(2)
            return await msg.edit(content=f"{msg.content} You won!")
        query = "SELECT * FROM userbal WHERE userid=$1;"
        row = await self.bot.db.fetchrow(query, ctx.author.id)
        betresult = row["money"] - bet
        query = "UPDATE userbal SET money = $1 WHERE userid = $2;"
        altrow = await self.bot.db.fetchrow(query, betresult, ctx.author.id)
        msg = await ctx.send(f"The coin landed and...")
        await asyncio.sleep(2)
        await msg.edit(content=f"{msg.content} You lost!")


def setup(bot):
    bot.add_cog(Economy(bot))
