import discord
from discord.ext import commands
import random, logging

logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

intents = discord.Intents.default()
intents.members = True


class RandomThings(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='ban')
    async def ban(self, ctx, member: discord.Member, *, reason=None, amount=1):
        await ctx.channel.purge(limit=int(amount))
        await member.ban(reason=reason)
        await ctx.send(f'ban user {member.mention}')

    @commands.command(name='roll')
    async def roll(self, ctx, min_int, max_int):
        num = random.randint(int(min_int), int(max_int))
        await ctx.send(num)


bot = commands.Bot(command_prefix='//', intents=intents)
bot.add_cog(RandomThings(bot))

TOKEN = "OTU4NjI5NjkxNjk3Mjc5MDA2.YkQHeA.yYrUUZj92IZVYs-_YQeRiPAsG8o"

bot.run(TOKEN)
