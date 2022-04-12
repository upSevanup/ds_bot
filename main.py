import discord
from discord.ext import commands, tasks
from discord import utils
import random, logging
from config import *
from func import *
import datetime

logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

intents = discord.Intents.default()
intents.members = True

async def open_acc(user):
    users = await get_bank()
    if user.bot is True:
        return
    if str(user.id) in users:
        return False
    else:
        users[str(user.id)] = {}
        users[str(user.id)]['wallet'] = 100
    write_json('jsons/bank', users)
    return True

async def get_bank():
    users = load_json('jsons/bank')
    return users


class MarciBot(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @tasks.loop()
    async def check_mutes(self):
        current = datetime.datetime.now()
        mutes = load_json("jsons/mutes")
        users, times = list(mutes.keys()), list(mutes.values())
        for i in range(len(times)):
            time = times[i]
            unmute = datetime.datetime.strptime(str(time), "%c")
            if unmute < current:
                user_id = users[times.index(time)]
                try:
                    member = await self.guild.fetch_member(int(user_id))
                    await member.remove_roles(self.mutedrole)
                    mutes.pop(str(member.id))
                except discord.NotFound:
                    pass
                write_json("jsons/mutes", mutes)

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

    @commands.command()
    @commands.has_any_role(958272824634654730)
    async def mute(self, ctx, member: discord.Member = None, time: str = None, *, reason="не указана"):
        if member is None:
            return await ctx.send("Укажите пользователя")
        if member.bot is True:
            return await ctx.send("Вы не можете замутить бота")
        if member == ctx.author:
            return await ctx.send("Вы не можете замутить себя")
        if len(reason) > 150:
            return await ctx.send("Причина слишком длинная")
        if member and member.top_role.position >= ctx.author.top_role.position:
            return await ctx.send("Вы не можете замутить человека с ролью выше вашей")
        if time is None:
            return await ctx.send("Вы не указали время")
        else:
            try:
                seconds = int(time[:-1])
                duration = time[-1]
                if duration == "s":
                    pass
                if duration == "m":
                    seconds *= 60
                if duration == "h":
                    seconds *= 3600
                if duration == "d":
                    seconds *= 86400
            except:
                return await ctx.send("Указана неправильная продолжительность")
            mute_expiration = (datetime.datetime.now() + datetime.timedelta(seconds=int(seconds))).strftime("%c")
            role = self.mutedrole
            if not role:
                return await ctx.send("Я не могу найти роль мута")
            mutes = load_json("jsons/mutes")
            try:
                member_mute = mutes[str(member.id)]
                return await ctx.send("Пользователь ужe в муте")
            except:
                mutes[str(member.id)] = str(mute_expiration)
                write_json("jsons/mutes", mutes)
                await member.add_roles(role)
                await member.move_to(channel=None)
                await ctx.send(f"{ctx.author.mention} замутил(а) {member.mention}"
                               f" до {mute_expiration} по причине: {reason}")

    @commands.command()
    @commands.has_any_role(958272824634654730)
    async def unmute(self, ctx, member: discord.Member):
        await member.remove_roles(self.mutedrole)
        await ctx.send(f"{ctx.author.mention} размутил(а) {member.mention}")
        mutes = load_json("jsons/mutes")
        mutes.pop(str(member.id))
        write_json("jsons/mutes", mutes)

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

    @commands.Cog.listener()
    async def on_ready(self):
        self.guild = await self.bot.fetch_guild(958272741449039902)  # You server id
        self.mutedrole = utils.get(self.guild.roles, id=959376510509269032)  # Mute role id
        self.check_mutes.start()

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return
        if "пив" in message.content.lower():
            await message.channel.send("по пивку?)")
        elif "марси" in message.content.lower() or "marci" in message.content.lower():
            await message.channel.send("А!? Да, я тут")

    @commands.Cog.listener()
    async def on_member_join(self, member):
        channel = self.bot.get_channel(960902344164392970)
        await channel.send(f'Привет, {member.name}!')

class Eco(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def balance(self, ctx, member: discord.Member = None):
        if member is None:
            member = ctx.author
        await open_acc(member)
        users = await get_bank()
        member_bank = users[str(member.id)]['wallet']
        await ctx.send(f'Баланс {member.mention}: {member_bank} MarsiCoin')

    @commands.command()
    async def pay(self, ctx, num: int, member: discord.Member = None):
        if member is None:
            return await ctx.send('Вы не указали пользователя!', delete_after=3)
        if num < 0:
            return await ctx.send('Перевод должен быть положительным', delete_after=3)
        await open_acc(ctx.author)
        await open_acc(member)
        users = await get_bank()
        member_bank = users[str(member.id)]['wallet']
        author_bank = users[str(ctx.author.id)]['wallet']
        if author_bank < num:
            return await ctx.send('У вас недостаточно средств', delete_after=3)
        users[str(member.id)]['wallet'] += num
        users[str(ctx.author.id)]['wallet'] -= num
        write_json('jsons/bank', users)
        await ctx.send(f'{ctx.author.mention} перевел(а) {member.mention}: {num} MarsiCoin')

    @commands.command()
    @commands.has_any_role(958272824634654730)
    async def dup(self, ctx, num: int):
        await open_acc(ctx.author)
        users = await get_bank()
        author_bank = users[str(ctx.author.id)]['wallet']
        if num < 0:
            users[str(ctx.author.id)]['wallet'] += num
            write_json('jsons/bank', users)
            await ctx.send(f'Вы забрали у себя: {num * -1} MarsiCoin')
        else:
            users[str(ctx.author.id)]['wallet'] += num
            write_json('jsons/bank', users)
            await ctx.send(f'Вы выдали себе: {num} MarsiCoin')


bot = commands.Bot(command_prefix='//', intents=intents)
bot.add_cog(MarciBot(bot))
bot.add_cog(Eco(bot))

bot.run(TOKEN)
