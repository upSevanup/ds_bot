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

    @commands.command(name='mute')
    @commands.has_any_role(959376510509269032)
    async def mute(self, ctx, member: discord.Member, time: int):
        emb = discord.Embed(title="Участник Был Замучен!", colour=discord.Color.blue())
        await ctx.channel.purge(limit=1)

        emb.set_author(name=member.name, icon_url=member.avatar_url)
        emb.set_footer(text="Его замутил {}".format(ctx.author.name), icon_url=ctx.author.avatar_url)

        await ctx.send(embed=emb)
        muted_role = discord.utils.get(ctx.message.guild.roles, name="Muted")
        await member.add_roles(muted_role)

        await asyncio.sleep(time)
        await member.remove_roles(muted_role)

    @commands.command(name='kick')
    async def kick(self, ctx, member: discord.Member, *, reason=None, amount=1):
        await ctx.channel.purge(limit=int(amount))
        await member.kcik(reason=reason)
        await ctx.send(f'kick user {member.mention}')




bot = commands.Bot(command_prefix='//', intents=intents)
bot.add_cog(RandomThings(bot))

TOKEN = "***"

bot.run(TOKEN)
