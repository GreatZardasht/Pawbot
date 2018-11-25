import asyncio

from collections import Counter
from utils import permissions, default
from discord.ext.commands import AutoShardedBot

config = default.get("config.json")


class Bot(AutoShardedBot):
    def __init__(self, *args, prefix=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.db = kwargs.pop("db")
        self.counter = Counter()

    async def on_message(self, msg):
        blacklist = default.get("blacklist.json")
        uplink = default.get("uplink.json")

        if msg.guild is None:
            if not self.is_ready() or msg.author.bot or not permissions.can_send(msg) or msg.author.id in blacklist.blacklist:
                return
            return await self.process_commands(msg)
        if not self.is_ready() or msg.author.bot or not permissions.can_send(msg) or msg.author.id in blacklist.blacklist or msg.guild.id in blacklist.blacklist:
            return
        if msg.channel.id == uplink.uplinkchan:
            downlinkchannel = self.get_channel(uplink.downlinkchan)
            await downlinkchannel.send(f"{msg.author.name}#{msg.author.discriminator}: {msg.content}")
        if msg.channel.id == uplink.downlinkchan:
            uplinkchannel = self.get_channel(uplink.uplinkchan)
            await uplinkchannel.send(f"{msg.author.name}#{msg.author.discriminator}: {msg.content}")
        await self.process_commands(msg)
        self.counter[f"{msg.author.id}.{msg.guild.id}.msgs"] += 1
        await asyncio.sleep(5)
        self.counter[f"{msg.author.id}.{msg.guild.id}.msgs"] -= 1
