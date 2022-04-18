import discord
from discord.ext import commands, tasks
from discord import utils
import random, logging
from config import *
from func import *
import datetime
import os

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
    @commands.has_any_role(ACCESS_ROLE)
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
    @commands.has_any_role(ACCESS_ROLE)
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
        self.guild = await self.bot.fetch_guild(SERVER_ID)  # You server id
        self.mutedrole = utils.get(self.guild.roles, id=MUTE_ROLE)  # Mute role id
        self.check_mutes.start()

    @commands.Cog.listener()
    async def on_message(self, message):
        marsi_pivo = os.listdir('foto/marsi/pivko')
        marsi_yatut = os.listdir('foto/marsi/yatut')
        if message.author == self.bot.user:
            return
        if 'посоветуй' in message.content.lower() and 'пив' in message.content.lower():
            x = random.randint(1, 25)
            if x == 1:
                await message.channel.send('''Guinness
Guinness – легендарный пивной бренд, прочно ассоциирующийся с Ирландией.
Вкус: сладкий, с преобладанием вкуса шоколада над привкусом кофе.
Обладает легким послевкусием со средне сладким ощущением.
Содержание спирта: 6%''',
                                           file=discord.File(f'foto/pivo/Guinness.jpg'))
            elif x == 2:
                await message.channel.send('''Kronenbourg 1664
Kronenbourg 1664 – светлый фильтрованный европейский лагер крепостью 4,5%
Это самый продаваемый сорт во Франции, он пользуется неизменной популярностью у поклонников во многих странах мира.
Пиво золотисто-желтого цвета с обильной белоснежной пеной обладает необычным легким ароматом, 
в котором преобладают кориандр, хмелевые, солодовые и цитрусовые оттенки.''',
                                           file=discord.File(f'foto/pivo/Kronenbourg.jpeg'))
            elif x == 3:
                await message.channel.send('''Redd’s
Слабоалкогольный напиток «Реддс» не пиво, в традиционном понимании — в нём нет хмеля, основной пивной составляющей,
и не остаётся характерного горьковатого послевкусия.
Фруктовое пиво — напиток самостоятельный, не требующий закуски, сопровождения фруктами или сладостями.''',
                                           file=discord.File(f'foto/pivo/Redd’s.png'))
            elif x == 4:
                await message.channel.send('''Heineken
Heineken – монобренд, который принадлежит одноименной нидерландской компании, 
занимающей первое место среди европейских – и вторую позицию в списке мировых – пивоваренных гигантов.
Во вкусе выделяются оттенки жареных каштанов, банана и карамели на фоне сбалансированной горьковатой ноты.''',
                                           file=discord.File(f'foto/pivo/Heineken.jpg'))
            elif x == 5:
                await message.channel.send('''Bud
Напиток, провозглашенный «королем пива», впервые был представлен Адольфусом Бушем в 1876 году. 
До сегодняшнего дня каждая партия Budweiser варится в соответствии со старым семейным рецептом, 
которого придерживались пять поколений пивоваренной династии.
Во вкусе сконцентрировано все то, чем славятся светлые лагеры: насыщенное солодовое тело с нотами карамели и бисквита,
уравновешенными благородной горчинкой.''',
                                           file=discord.File(f'foto/pivo/Bud.jpg'))
            elif x == 6:
                await message.channel.send('''Grolsch
Пиво Grolsch производят в Нидерландах. Компания на рынке уже давно и успела завоевать верных поклонников.
Привлекательный дизайн бутылки и мягкий напиток в лучших голландских традициях — в целом, 
это и есть секрет успеха компании.''',
                                           file=discord.File(f'foto/pivo/Grolsch.jpg'))
            elif x == 7:
                await message.channel.send('''Krombacher
В ассортименте немецкого производителя несколько разновидностей пенного алкоголя на любой вкус. 
Различаясь по крепости и технологии изготовления, все они обрели популярность у потребителя.''',
                                           file=discord.File(f'foto/pivo/Krombacher.jpeg'))
            elif x == 8:
                await message.channel.send('''Белый Волк
Увы... Но по данному запросу не нашлось ничего, можем вам посоветовать только...
Ге́ральт из Ри́вии  — главный герой литературной саги и протагонист последующих игр, 
Ведьмак, профессиональный охотник на монстров, один из лучших фехтовальщиков Севера.''',
                                           file=discord.File(f'foto/pivo/pashalka.png'))
            elif x == 9:
                await message.channel.send('''Stella Artois
Самое распространенное в мире бельгийское пиво,
неоднократно признававшееся лучшим в категории Lager/Pilsner на международных конкурсах.
Вкус чистый, сухой, со сдержанной горчинкой, сохраняющейся и в послевкусии.
Питкое столовое пиво одинаково хорошо сочетается с легкими закусками и сытными мясными блюдами.''',
                                           file=discord.File(f'foto/pivo/Stella.jpg'))
            elif x == 10:
                await message.channel.send('''Spaten
Светло-золотистый напиток дает высокую шапку снежно-белой пены, оставляющей заметные кружевные следы на стенках бокала.
В медовом аромате едва слышна слабая цитрусовая кислинка, дополненная тонами травянистого хмеля и сена.
Тело пива округлое и плотное, выраженный солодовый вкус переходит
в терпкую горечь черного хлеба с ненавязчивым хмелем. ''',
                                           file=discord.File(f'foto/pivo/Spaten.jpg'))
            elif x == 11:
                await message.channel.send('''Amstel
Пиво золотистого цвета, крепостью 5%. Пахнет солодом, во вкусе чувствуется хмелевая горчинка.
Имеет очень много разных вкусов''',
                                           file=discord.File(f'foto/pivo/Amstel.jpg'))
            elif x == 12:
                await message.channel.send('''Faxe
европейский лагер светло-янтарного цвета крепостью 5% и плотностью 11%, пена стойкая. 
Напиток благоухает солодом и хмелем, хмелевая горчинка во вкусе гармонирует с травяными нотами,
послевкусие – мягкое, с легкой сладостью свежего хлеба.''',
                                           file=discord.File(f'foto/pivo/Faxe.jpg'))
            elif x == 13:
                await message.channel.send('''Garage
Бренд Garage — один из лидеров в сегменте ароматизированного пива,
Напитки представлены во многих магазинах, уже хорошо раскручены и давно имеют свою армию поклонников.
Повнимательнее присмотримся к пиву Гараж.
Во всех вкусах пива Гараж доминируют фруктовые и ягодные ноты.
Только на финише проступают легкие солодовые и хмельные мотивы.''',
                                           file=discord.File(f'foto/pivo/Garage.jpg'))
            elif x == 14:
                await message.channel.send('''Tuborg
Tuborg сварили первый датский пилснер и разлили его в бутылки с яркой зеленой этикеткой.
Напиток быстро приобрел популярность у датчан,
а сегодня он является настоящим «космополитом» и представлен в более чем 70 странах.
Варится с использованием бережно обжаренного солода лагерного типа,
что наделяет букет гаммой зерновых, карамельных и цветочных тонов.''',
                                           file=discord.File(f'foto/pivo/Tuborg.jpg'))
            elif x == 15:
                await message.channel.send('''Miller
По стилю это – американский лагер янтарно-золотистого цвета, с жемчужной шапкой пены.
Основные составляющие аромата – хлебные и травянистые ноты.
Во вкусе выражена солодовая сладость, ноты хмеля и фруктов. ''',
                                           file=discord.File(f'foto/pivo/Miller.jpg'))
            elif x == 16:
                await message.channel.send('''Edelweiss
Пиво Edelweiss получило свое название благодаря горному альпийскому цветку,
который растет лишь в экологически чистых условиях первозданной природы. 
Австрийский пенный напиток полностью соответствует своему названию. 
Он состоит исключительно из натуральных ингредиентов: пшеничного и ячменного солода, хмеля и чистой альпийской воды.''',
                                           file=discord.File(f'foto/pivo/Edelweiss.jpg'))
            elif x == 17:
                await message.channel.send('''Essa
Essa нельзя назвать «настоящим» пивом из-за состава напитка.
В нем, помимо классического пивного сырья, присутствуют и другие ингредиенты, которые придают продукту фруктовый вкус.
Это, скорее, походит на газированный фруктовый коктейль с легким пивным ароматом.''',
                                           file=discord.File(f'foto/pivo/Essa.jpg'))
            elif x == 18:
                await message.channel.send('''Gosser
Пиво соломенно-золотистого цвета крепостью 5,2% и плотностью 11,9%. Сварено по старинным монастырским рецептам.
Напиток обладает солодово-цветочным ароматом,
в насыщенном вкусе деликатная сладость солода уравновешена хмелевой горчинкой.''',
                                           file=discord.File(f'foto/pivo/Gosser.jpg'))
            elif x == 19:
                await message.channel.send('''Franziskaner
Franziskaner – марка пшеничного пива, производимого в Мюнхене.
В ассортименте компании внушительная линейка пенного.
И каждое наименование имеет целую армию поклонников, предпочитающих освежающий вкус настоящего немецкого пива.''',
                                           file=discord.File(f'foto/pivo/Franziskaner.jpg'))
            elif x == 20:
                await message.channel.send('''Velkopopovicky Kozel
Карамелизованный солод придает напитку коричнево-рубиновый оттенок и сладковатый аромат.
В ярком фруктовом букете чувствуются ноты черной смородины и вишни,
а также карамели, шоколада и орехов кешью, приправленных пряным карри с щепоткой имбиря.
Во вкусе проявляется деликатная сладость и приятная горечь, которые отлично сбалансированы.''',
                                           file=discord.File(f'foto/pivo/Kozel.jpg'))
            elif x == 21:
                await message.channel.send('''Corona
Напиток относят к категории премиум-лагеров в американском стиле.
Для него характерны сладковатое солодовое тело с карамельными тонами и нюансами сухофруктов и специй.
Принято подавать к столу хорошо охлажденным, с кусочком лайма в горлышке бутылки.''',
                                           file=discord.File(f'foto/pivo/Corona.jpg'))
            elif x == 22:
                await message.channel.send('''Хамовники
Классический немецкий пилс золотистого цвета, абсолютно прозрачный, с белоснежной мелкозернистой пеной.
Букет точно соответствует стилю: даже в ароматике чувствуется присущая пильзнерам сухость,
травянистый хмель, сено, легкая сернистость.
Тело плотное, с зерновой основой, хмелевая горечь во вкусе не подавляет, а гармонично дополняет сладость солода.''',
                                           file=discord.File(f'foto/pivo/Хамовники.jpg'))
            elif x == 23:
                await message.channel.send('''Юзберг
Пшеничное нефильтрованное пиво верхового брожения (светлое, мутное, пастеризованное),
крепость – 4,9% плотность – 13,1%, пеностойкость – 6 минут.
Бананово-гвоздичные ноты во вкусе эффектно подчеркивают пикантность хмелевой горчинки.''',
                                           file=discord.File(f'foto/pivo/Юзберг-.jpg'))
            elif x == 24:
                await message.channel.send('''Zatecky Gus
Второй по времени появления сорт в линейке бренда, сваренный на основе микса светлого и карамельного солодов.
Цвет пива в кружке темно-коричневый с красными проблесками,
бежевая пена с плотной структурой долго не оседает и оставляет кружевные узоры на стенках.
В ароматике ощущаются обжаренный солод, сухофрукты, корочка ржаного хлеба, холодный кофе.
Тело легкое, со средней карбонизацией. Характер вкуса главным образом карамельный,
дополненный тонами коричневого сахара, темного шоколада, чернослива, кваса с низким содержанием углекислого газа.
В сухом послевкусии проступает неяркая хмелевая горчинка.
Хорошо сочетается с куриными крылышками гриль, сырными профитролями, пивным кексом с орехами пекан.''',
                                           file=discord.File(f'foto/pivo/Gus.jpg'))
            elif x == 25:
                await message.channel.send('''Жигули
Крепость– 4,9 % оборотов. Это значение на пиво Жигули производитель разместил на этикетке.
Вкус содержит солодово-лимонные нотки и лёгкую горчинку.
Считается мягким, но насыщенным. Цвет – золотисто-пшеничный, светлый элегантно янтарный.
Аромат характерный для пива: чувствуются оттенки хмеля, солода, фруктово-цветочные нотки.''',
                                           file=discord.File(f'foto/pivo/Жигули.jpg'))
        elif "пив" in message.content.lower():
            await message.channel.send("по пивку?)",
                                       file=discord.File(f'foto/marsi/pivko/{random.choice(marsi_pivo)}'))
        elif "марси" in message.content.lower() or "marci" in message.content.lower():
            await message.channel.send("А!? Да, я тут",
                                       file=discord.File(f'foto/marsi/yatut/{random.choice(marsi_yatut)}'))

    @commands.Cog.listener()
    async def on_member_join(self, member):
        channel = self.bot.get_channel(GREETINGS_CHAT)
        await channel.send(f'''Привет, {member.mention}!
напиши //help_me если хочешь ознакомиться с командами сервера''')

    @commands.command(name='poker')
    async def poker(self, ctx, num: int, member: discord.Member = None):
        await open_acc(ctx.author)
        await open_acc(member)
        users = await get_bank()
        member_bank = users[str(member.id)]['wallet']
        author_bank = users[str(ctx.author.id)]['wallet']
        if author_bank < num:
            await ctx.send('У вас не достаточно денег')
            return
        elif member_bank < num:
            await ctx.send(f'У {member.mention} не достаточно денег')
            return

        combos = ['ничего', 'пара', 'две пары', 'сет', 'фулл хаус', 'каре', 'покер']
        edges = ['\u2680', '\u2681', '\u2682', '\u2683', '\u2684', '\u2685']

        player_1, pl_1_score, combo_1 = poker()
        player_2, pl_2_score, combo_2 = poker()

        winner = ''
        looser = ''
        if player_1 == player_2:
            if pl_1_score > pl_2_score:
                winner = ctx.author
                looser = member
            elif pl_1_score < pl_2_score:
                winner = member
                looser = ctx.author
        elif combos.index(player_1) > combos.index(player_2):
            winner = ctx.author
            looser = member
        else:
            winner = member
            looser = ctx.author

        await ctx.send(f'''{ctx.author.mention}: 
{edges[combo_1[0] - 1]} {edges[combo_1[1] - 1]} {edges[combo_1[2] - 1]} {edges[combo_1[3] - 1]} {edges[combo_1[4] - 1]} 
комбинация: {player_1} 
счёт: {pl_1_score} \n
{member.mention}: 
{edges[combo_2[0] - 1]} {edges[combo_2[1] - 1]} {edges[combo_2[2] - 1]} {edges[combo_2[3] - 1]} {edges[combo_2[4] - 1]} 
комбинация: {player_2} 
счёт: {pl_2_score} \n
Победил {winner.mention}!''')

        await open_acc(winner)
        users = await get_bank()
        users[str(winner.id)]['wallet'] += num
        write_json('jsons/bank', users)

        await open_acc(looser)
        users = await get_bank()
        users[str(looser.id)]['wallet'] += num * -1
        write_json('jsons/bank', users)

    @commands.command(name='poker_rules')
    async def poker_rules(self, ctx):
        await ctx.send(f'''Для каждого игрока бросается по 5 игральных кубиков,
игрок с большей комбиеацией побеждает и получает выйгрыш (у проигравшего MarciСoins забираются)
Комбинации (по возрастанию):
1 - ничего
2 - пара
3 - две пары
4 - сет
5 - фулл хаус
6 - каре
8 - покер
Если у игроков одинаковые комбинации то выигрывает тот, у кого больше счёт в комбинации''')

    @commands.command(name='help_me')
    async def help_me(self, ctx):
        await ctx.send(f'''Список команд и возможностей:
//ban member - бан выбранного пользователя
//mute member time s/m/h/d - мут пользователя на время
//kick member - кикнуть выбранного пользователя
//clear number - удалить определённое число сообщений
в чате greetings можно получить роль кликнув на реакцию
//balance - посмотреть свой баланс (MarciCoins)
//poker bet member - покер костями с другим участником
//roll mum_1 num_2 - случайное число от num_1 до num_2
бот може посоветовать пиво (просто попросите его об этом)''')


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
    @commands.has_any_role(ACCESS_ROLE)
    async def dupe(self, ctx, num: int):
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
