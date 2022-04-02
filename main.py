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
    @commands.has_permissions(administrator=True)
    async def ban(self, ctx, member: discord.Member, *, reason=None, amount=1):
        await ctx.channel.purge(limit=int(amount))
        await member.ban(reason=reason)
        await ctx.send(f'О мой бог этот парень реально пререшел черту { member.mention }')

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def unban(self, ctx, *, member):
        await ctx.channel.purge(limit=1)
        banned_users = await ctx.guild.bans()
        for ban_entry in banned_users:
            user = ban_entry.user
            await ctx.guild.unban(user)
            await ctx.send(f'{ctx.author.name} сегодня добрый , он простил {user.mention}')
            return

    @commands.command(name='roll')
    async def roll(self, ctx, min_int, max_int):
        num = random.randint(int(min_int), int(max_int))
        await ctx.send(num)

    @commands.command()
    async def mute(self, ctx, member: discord.Member, *, reason=None):
        mute = discord.utils.get(ctx.guild.roles, name='лох в муте')
        await member.move_to(channel=None)
        await member.add_roles(mute)
        await ctx.send(f'{ctx.author.name} замутил(а) {member.mention} по причине {reason}.')

    @commands.command()
    async def unmute(self, ctx, member: discord.Member):
        mute = discord.utils.get(ctx.guild.roles, name='лох в муте')
        await member.remove_roles(mute)
        await ctx.send(f'{ctx.author.name} раззамутил(а) {member.mention}.')

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def kick(self, ctx, member: discord.Member, *, reason='Гнев Бога'):
        await ctx.channel.purge(limit=1)

        await member.kick(reason=reason)
        await ctx.send(f'{ctx.author.name} в гневе и выкинул с олимпа {member.mention}')


bot = commands.Bot(command_prefix='//', intents=intents)
bot.add_cog(RandomThings(bot))

TOKEN = "OTU4NjI5NjkxNjk3Mjc5MDA2.YkQHeA.Q7k6cGWJIYbMr_ypA5cAq4ZrRk4"

bot.run(TOKEN)
