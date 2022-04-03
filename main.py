import discord
from discord.ext import commands
from discord import utils
import random, logging
from config import *

logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

intents = discord.Intents.default()
intents.members = True


class MarciBot(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='ban')
    @commands.has_permissions(administrator=True)
    async def ban(self, ctx, member: discord.Member, *, reason=None, amount=1):
        await ctx.channel.purge(limit=int(amount))
        await member.ban(reason=reason)
        await ctx.send(f'О мой бог этот парень реально пререшел черту { member.mention }')

    @commands.command(name='unban')
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

    @commands.command(name='mute')
    async def mute(self, ctx, member: discord.Member, *, reason=None):
        mute = utils.get(ctx.guild.roles, id=959376510509269032)
        await member.move_to(channel=None)
        await member.add_roles(mute)
        await ctx.send(f'{ctx.author.name} замутил(а) {member.mention} по причине {reason}.')

    @commands.command(name='unmute')
    async def unmute(self, ctx, member: discord.Member):
        mute = utils.get(ctx.guild.roles, id=959376510509269032)
        await member.remove_roles(mute)
        await ctx.send(f'{ctx.author.name} раззамутил(а) {member.mention}.')

    @commands.command(name='kick')
    @commands.has_permissions(administrator=True)
    async def kick(self, ctx, member: discord.Member, *, reason='Гнев Бога'):
        await ctx.channel.purge(limit=1)

        await member.kick(reason=reason)
        await ctx.send(f'{ctx.author.name} в гневе и выкинул с олимпа {member.mention}')

    @commands.command(name='clear')
    async def clear(self, ctx, amount: int):
        await ctx.channel.purge(limit=amount + 1)
        await ctx.send(f'Удалено {amount} сообщений!', delete_after=3)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.message_id == ROLE_POST_ID:
            channel = self.bot.get_channel(payload.channel_id)
            message = await channel.fetch_message(payload.message_id)
            member = await (await self.bot.fetch_guild(payload.guild_id)).fetch_member(payload.user_id)

            emoji = str(payload.emoji)
            role = utils.get(message.guild.roles, id=ROLES[emoji])

            await member.add_roles(role)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        if payload.message_id == ROLE_POST_ID:
            channel = self.bot.get_channel(payload.channel_id)
            message = await channel.fetch_message(payload.message_id)
            member = await (await self.bot.fetch_guild(payload.guild_id)).fetch_member(payload.user_id)

            emoji = str(payload.emoji)
            role = utils.get(message.guild.roles, id=ROLES[emoji])

            await member.remove_roles(role)


bot = commands.Bot(command_prefix='//', intents=intents)
bot.add_cog(MarciBot(bot))

bot.run(TOKEN)