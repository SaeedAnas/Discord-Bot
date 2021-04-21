import os

import discord
from discord.ext import tasks, commands
from dotenv import load_dotenv

import spreadsheet
from spreadsheet import StrikeSheet

import cards
from cards import Tasks

load_dotenv('.env')

TOKEN = os.getenv('TOKEN')

command_prefix = '$'
intents = discord.Intents.all()
help_command = commands.DefaultHelpCommand(no_category='Commands')

bot = commands.Bot(command_prefix=command_prefix,
                   intents=intents,
                   help_command=help_command)

main_guild = 'Inspire Speaker Series'


# Utility Functions
async def is_admin(ctx):
    roles = list(filter(lambda role: role.name == 'Leader', ctx.author.roles))
    return len(roles) > 0


def get_user(ctx, uid):
    members = ctx.guild.members
    user = list(filter(lambda m: f'<@!{m.id}>' == uid, members))

    if len(user) == 0:
        user = list(
            filter(
                lambda m: m.display_name.split(' ')[0].lower() == uid.lower(),
                members))

    if len(user) == 0:
        return None

    return user[0]


def get_roles(user):
    return [role.name for role in user.roles][1:]


def find_role(name, guild):
    return list(filter(lambda r: r.name.lower() == name.lower(),
                       guild.roles))[0]


def get_guild(name):
    return list(filter(lambda g: g.name == name, bot.guilds))[0]


def get_channel(name, guild):
    return list(
        filter(lambda c: c.name.lower() == name.replace(' ', '-').lower(),
               guild.channels))[0]


# General
@bot.command(name='profile', help='show user profile')
async def profile(ctx, user=None):
    if user is None:
        user = ctx.author
    else:
        user = get_user(ctx, user)
        if user is None:
            await ctx.send('Please enter a valid user id')

    roles = get_roles(user)

    connection = spreadsheet.connect(ctx)
    t = Tasks()

    task_dict = t.get_tasks(user.display_name)

    embed = discord.Embed(title=f'{user.display_name}',
                          description=', '.join(roles),
                          colour=user.colour)

    task_dict = await task_dict
    s = await connection

    user_cell = s.find_user(user.id, has_wrapper=False)

    try:
        embed.add_field(name='Strikes', value=s.get_strikes(user_cell))
    except Exception:
        print('no strikes available')

    for task_list in task_dict:
        task = task_dict[task_list]
        if len(task) > 0:
            embed.add_field(name=f'{task_list}:\n',
                            value=cards.format_tasks(task),
                            inline=False)

    embed.set_thumbnail(url=user.avatar_url)
    await ctx.send(embed=embed)


@bot.command(name='drive', help='gives link to google drive folder')
async def drive(ctx):
    await ctx.send(
        'https://drive.google.com/drive/u/0/folders/1bZdKIoGCg5gn_tvByUMOpmIWyYrXE94R'
    )


@bot.command(name='notify', help='manually call notify function')
async def notify():
    guild = get_guild(main_guild)
    t = Tasks()
    important = await t.get_important()
    for branch in important:
        role = find_role(branch, guild)
        channel = get_channel(branch, guild)
        await t.notify_channel(role, channel, important[branch])


# Strikesheet
@bot.command(name='registerall', help='registers all members onto strikesheet')
@commands.check(is_admin)
async def init_sheet(ctx):
    members = ctx.guild.members
    s = StrikeSheet(ctx)
    await s.register_members(members)


@bot.command(name='register', help='register new member')
@commands.check(is_admin)
async def register(ctx, uid):
    user = get_user(ctx, uid)
    s = StrikeSheet(ctx)
    try:
        await s.register_member(user)
    except Exception:
        await ctx.send('Please enter a valid user id')


@bot.command(name='strike', help='strikes a user')
@commands.check(is_admin)
async def strike(ctx, *args):
    user = args[0]
    reason = ' '.join(args[1:])
    s = StrikeSheet(ctx)
    try:
        await s.strike_user(user, reason)
    except Exception:
        await ctx.send('Please enter a valid user id')


@bot.command(name='unstrike', help='unstrikes a user')
@commands.check(is_admin)
async def unstrike(ctx, uid):
    s = StrikeSheet(ctx)
    try:
        await s.remove_strike(uid)
    except Exception:
        await ctx.send('Please enter a valid user id')


@bot.command(name='spreadsheet', help='gives link to spreadsheet')
async def sheet(ctx):
    s = StrikeSheet(ctx)
    await s.spreadsheet()


# Tasks
@tasks.loop(hours=1)
async def notify_tasks():
    if cards.isMidnight():
        await notify()


# All bot event handlers and commands
@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')
    notify_tasks.start()


bot.run(TOKEN)
