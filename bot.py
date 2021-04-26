import os

import discord
from discord.ext import tasks, commands
from dotenv import load_dotenv

import spreadsheet
from spreadsheet import StrikeSheet, MeetingSheet, Meeting

import cards
from cards import Tasks

import bot_utils

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
    roles = list(
        filter(lambda role: role.name.lower() == 'imperator',
               ctx.author.roles))
    if len(roles) > 0:
        await ctx.send("You do not have permission to run this command.")
        return True
    return False


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
    return list(
        filter(lambda r: r.name.lower() == name.replace('-', ' ').lower(),
               guild.roles))[0]


def get_guild(name):
    return list(filter(lambda g: g.name == name, bot.guilds))[0]


def get_channel(name, guild):
    return list(
        filter(lambda c: c.name.lower() == name.replace(' ', '-').lower(),
               guild.channels))[0]


async def alert(branch, time, humanize):
    guild = get_guild(main_guild)
    channel = get_channel(branch, guild)
    role = find_role(branch, guild)

    if humanize == 'right now':
        if time.place is None:
            await channel.send(f'<@&{role.id}>, you have a meeting right now!')
            return
        await channel.send(
            f'<@&{role.id}>, you have a meeting right now @ {time.place}')
        return

    if time.place is None:
        await channel.send(
            f'<@&{role.id}>, you have a meeting {humanize} at {bot_utils.format_meeting_time(time.time)}'
        )
        return

    await channel.send(
        f'<@&{role.id}>, you have a meeting {humanize} at {bot_utils.format_meeting_time(time.time)} @ {time.place}'
    )


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
    m = MeetingSheet(ctx)
    meeting_times = m.get_times()

    task_dict = t.get_tasks(user.display_name)

    embed = discord.Embed(title=f'{user.display_name}',
                          description=', '.join(roles),
                          colour=user.colour)

    task_dict = await task_dict
    s = await connection
    meeting_times = await meeting_times

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

    meeting_string = ''
    for meeting_time in meeting_times:
        name = meeting_time[0].replace('-', ' ').lower()
        if len(list(filter(lambda r: r.lower() == name, roles))) > 0:
            if len(meeting_time[1:]) > 0:
                try:
                    meets = m.to_meetings(meeting_time[1:])
                    meeting_string += bot_utils.format_dates(
                        meets, branch=meeting_time[0])
                except Exception:
                    continue
    if meeting_string != '':
        embed.add_field(name='Meeting Times:',
                        value=meeting_string,
                        inline=False)

    embed.set_thumbnail(url=user.avatar_url)
    await ctx.send(embed=embed)


@bot.command(name='meet', help='schedule meet times ($meet <date> <time>)')
async def meet(ctx, *args):
    channel = ctx.channel.name
    role = find_role(channel, ctx.guild)
    date = ' '.join(args)

    date = Meeting(date)

    if date.time is None:
        print('here')
        await ctx.send('Please enter a valid date and time')
        return
    if bot_utils.has_passed(date.time):
        await ctx.send('Date has already passed. Please enter a future date')
        return

    m = MeetingSheet(ctx)
    try:
        await m.add_time(channel, date)
    except Exception as e:
        if str(e) == channel:
            await ctx.send(f'branch not found: {e}')
            return
        await ctx.send(e)
        return
    await ctx.send(f'{role.name} Meeting Scheduled on: {date.format()}')


@bot.command(name='meetings', help='Shows all meetings for a channel')
async def meetings(ctx):
    channel = ctx.channel.name
    role = find_role(channel, ctx.guild)

    m = MeetingSheet(ctx)
    dates = m.get_sorted_times(channel)

    desc = bot_utils.format_dates(dates)
    embed = discord.Embed(title=f'{role.name} Meetings:',
                          description=desc,
                          colour=role.colour)
    await ctx.send(embed=embed)


@bot.command(name='reschedule', help='reschedule a meeting')
async def reschedule(ctx, *args):
    channel = ctx.channel.name
    role = find_role(channel, ctx.guild)
    date = ' '.join(args)

    dates = date.split(' to ')

    old = Meeting(dates[0])
    new = Meeting(dates[1])

    if old == new:
        await ctx.send('Dates are the same')

    m = MeetingSheet(ctx)
    row = m.get_branch(channel)
    dates = m.to_meetings(m.get_branch_times(channel)[1:], sort=False)
    for col, date in enumerate(dates):
        if date.time == old.time:
            time = date.format()
            length = list(filter(lambda t: t == time, dates))
            if len(length) > 0:
                ctx.send('Time already scheduled')
                return
            m.ws.update_cell(row, col + 2, new.format())
            await ctx.send(
                f'{role.name} Meeting Rescheduled to: {new.format()}')
            return

    await ctx.send(f'Date not found: {old.format()}')


@bot.command(name='drive', help='gives link to google drive folder')
async def drive(ctx):
    await ctx.send(
        'https://drive.google.com/drive/u/0/folders/1bZdKIoGCg5gn_tvByUMOpmIWyYrXE94R'
    )


@bot.command(name='notify', help='manually call notify function')
async def notify(ctx, ping=False):
    guild = get_guild(main_guild)
    t = Tasks()
    important = await t.get_important()
    for branch in important:
        role = find_role(branch, guild)
        channel = get_channel(branch, guild)
        await t.notify_channel(role, channel, important[branch], ping)


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


@bot.command(name='sheet',
             help='gives link to spreadsheets: strikes, meetings')
async def sheet(ctx, name):
    name = name.lower().strip()
    if name == 'strike' or name == 'strikes':
        s = StrikeSheet(ctx)
        await s.spreadsheet()
    elif name == 'meeting' or name == 'meetings' or name == 'meet':
        m = MeetingSheet(ctx)
        await m.spreadsheet()
    else:
        await ctx.send('valid parameters: strikes, meetings')


# Tasks
@tasks.loop(hours=1)
async def notify_tasks():
    if cards.isHour(14):
        await notify(None, ping=True)


@tasks.loop(minutes=1)
async def checks():
    m = MeetingSheet(None)
    meeting_times = await m.get_times()
    for row, branch in enumerate(meeting_times):
        for col, meeting in enumerate(branch[1:]):
            if meeting == '':
                continue
            meeting = Meeting(meeting)
            if bot_utils.check(meeting.time, '3 days ago'):
                await alert(branch[0], meeting, 'in 3 days')
            elif bot_utils.check(meeting.time, 'a day ago'):
                await alert(branch[0], meeting, 'in a day')
            elif bot_utils.check(meeting.time, 'an hour ago'):
                await alert(branch[0], meeting, 'in an hour')
            elif bot_utils.isNow(meeting.time):
                await alert(branch[0], meeting, 'right now')
                m.clear_cell(row + 1, col + 2)
    print('checks done')


# All bot event handlers and commands
@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')
    notify_tasks.start()
    checks.start()


bot.run(TOKEN)
