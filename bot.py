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
    roles = list(filter(lambda role: role.name == 'Admin', ctx.author.roles))
    return len(roles) > 0


@bot.command(name='registerall', help='logs all users onto spreadsheet')
@commands.check(is_admin)
async def init_sheet(ctx):
    members = ctx.guild.members
    s = StrikeSheet(ctx)
    await s.register_members(members)


@bot.command(name='register', help='register new member')
@commands.check(is_admin)
async def register(ctx, uid):
    members = ctx.guild.members
    member = filter(lambda m: f'<@!{m.id}>' == uid, members)
    s = StrikeSheet(ctx)
    await s.register_member(member[0])


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


bot.run(TOKEN)
