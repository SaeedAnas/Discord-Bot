import discord
from discord.ext import commands
import os

from dotenv import load_dotenv

load_dotenv('.env')


client = discord.Client()
client=commands.Bot(command_prefix = '!')


@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    
    names = [' ','aditya','anas','anokhi','anuj','harshil','krish','naman','neil','poorvi','preet','ray','shanjay','shreyes','sreshta','srinidhi']

    if message.content.startswith('!strike'):
        name = message.content.split(' ')[1]
        if name.lower() in names:
            split_version = message.content.split(' - ')
            if len(split_version) == 2:
                await message.channel.send(name + ' is striked for ' + split_version[1])
            else:
                await message.channel.send('Please write it in the format: !strike name - reason')
        else:
            await message.channel.send(name + ' is not registered')
            await message.channel.send('Please write it in the format: !strike name - reason')
    elif message.content.startswith('!unstrike'):
        Name = message.content.split(' ')[1]
        await message.channel.send(Name + ' is unstriked')
    elif message.content.startswith('!spreadsheet'):
        await message.channel.send('https://docs.google.com/spreadsheets/d/1DVPDeYkLLwjkL2BTBlBRUWsmnpew-z5fjT9T9wMYri0/edit?usp=sharing')

client.run(os.getenv('TOKEN'))
