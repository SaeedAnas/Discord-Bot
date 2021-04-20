import os

import discord
from discord.ext import commands
from dotenv import load_dotenv

from spreadsheet import StrikeSheet

load_dotenv('.env')

TOKEN = os.getenv('TOKEN')

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)


@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')


async def is_admin(ctx):
    roles = list(filter(lambda role: role.name == 'Leader', ctx.author.roles))
    return len(roles) > 0


def get_user(ctx, uid):
    members = ctx.guild.members
    user = list(filter(lambda m: f'<@!{m.id}>' == uid, members))

    if len(user) == 0:
        return None

    return user[0]


def get_roles(user):
    return [role.name for role in user.roles][1:]


@bot.command(name='registerall', help='logs all users onto spreadsheet')
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


@bot.command(name='strike', help='Strikes a user')
@commands.check(is_admin)
async def strike(ctx, *args):
    user = args[0]
    reason = ' '.join(args[1:])
    s = StrikeSheet(ctx)
    try:
        await s.strike_user(user, reason)
    except Exception:
        await ctx.send('Please enter a valid user id')


@bot.command(name='unstrike', help='Strikes a user')
@commands.check(is_admin)
async def unstrike(ctx, uid):
    s = StrikeSheet(ctx)
    try:
        await s.remove_strike(uid)
    except Exception:
        await ctx.send('Please enter a valid user id')


@bot.command(name='spreadsheet', help='Gives link to strikesheet')
async def spreadsheet(ctx):
    s = StrikeSheet(ctx)
    await s.spreadsheet()


@bot.command(name='profile', help='print profile for user')
async def profile(ctx, user=None):
    if user is None:
        user = ctx.author
    else:
        user = get_user(ctx, user)
        if user is None:
            await ctx.send('Please enter a valid user id')

    roles = get_roles(user)

    s = StrikeSheet(ctx)
    user_cell = s.find_user(f'<@!{user.id}>')

    embed = discord.Embed(title=f'{user.display_name}',
                          description=', '.join(roles),
                          colour=user.colour)

    try:
        embed.add_field(name='strikes', value=s.get_strikes(user_cell))
    except Exception:
        print('no strikes available')

    embed.set_thumbnail(url=user.avatar_url)
    await ctx.send(embed=embed)


bot.run(TOKEN)
