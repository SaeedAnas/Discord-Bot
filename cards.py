import json
from datetime import timedelta
from trello import TrelloClient
import discord

import bot_utils


async def connect():
    return Tasks()


def isHour(hour):
    date = bot_utils.get_pst()
    return date.hour == hour


def isOverdue(time):
    due = bot_utils.to_pst(time)
    present = bot_utils.get_pst()
    return due.date() < present.date()


def isApproaching(time):
    due = bot_utils.to_date(time) - timedelta(hours=36)
    present = bot_utils.get_utc_time()
    return present.date() >= due.date()


def isCompleted(card):
    return card.get('dueComplete')


def format_card(card, dict):
    if dict:
        try:
            date = bot_utils.format_pst(card.get("due"))
            return f'● [{card.get("name")}]({card.get("url")})\n  Due {date}'
        except Exception:
            return f'● [{card.get("name")}]({card.get("url")})'
    date = bot_utils.format_pst(card.due)
    return f'● [{card.name}]({card.url})\n  Due {date}'


def print_card(card):
    d = bot_utils.format_pst(card.due)
    print(f'● [{card.name}]({card.url})\n Due: {d}')


def format_tasks(cards, dict=True):
    formatted = ''
    for card in cards:
        formatted += f'{format_card(card, dict=dict)}\n'
    return formatted


def add_cards(type, list, dict):
    for card in list:
        branch = card.get_list().name
        if not (branch in dict):
            dict[branch] = {'a': [], 'o': []}
        content = dict[branch]
        content[type].append(card)


class Tasks:
    warning = '❗️'
    check = '✅'
    todo = '📝'
    no_date = ''

    def __init__(self):

        with open('trello_auth.json') as trello_auth:
            cred = json.load(trello_auth)

        self.client = TrelloClient(api_key=cred.get('api_key'),
                                   api_secret=cred.get('api_secret'),
                                   token=cred.get('token'),
                                   token_secret=cred.get('token_secret'))

    def get_board(self):
        boards = self.client.list_boards()
        return list(
            filter(lambda b: b.name == "Inspire Speaker Series", boards))[0]

    def get_members(self):
        board = self.get_board()
        return board.all_members()

    def get_member(self, user):
        members = self.get_members()
        name = user.split(' ')[0]

        return list(
            filter(lambda m: m.full_name.split(' ')[0].lower() == name.lower(),
                   members))[0]

    async def get_tasks(self, user):
        member = self.get_member(user)
        cards = member.fetch_cards()
        overdue = []
        to_do = []
        completed = []
        no_date = []
        for card in cards:
            if isCompleted(card):
                completed.append(card)
            elif card.get('due') is None:
                no_date.append(card)
            elif isOverdue(card.get('due')):
                overdue.append(card)
            else:
                to_do.append(card)
        return {
            f'{self.warning} Overdue': overdue,
            f'{self.todo} To Do': to_do,
            f'{self.no_date} No Due Date': no_date,
            # f'{self.check} Completed': completed
        }

    def get_cards(self):
        board = self.get_board()
        return board.open_cards()

    async def get_approaching_tasks(self, cards=None):
        if cards is None:
            cards = self.get_cards()
        approaching = []
        for card in cards:
            if card.due is not None:
                if isOverdue(card.due) or card.is_due_complete:
                    continue
                if isApproaching(card.due):
                    approaching.append(card)

        return approaching

    async def get_overdue_tasks(self, cards=None):
        if cards is None:
            cards = self.get_cards()
        overdue = []
        for card in cards:
            if card.due is not None:
                if isOverdue(card.due) and not card.is_due_complete:
                    overdue.append(card)

        return overdue

    async def get_important(self):
        cards = self.get_cards()
        overdue = await self.get_overdue_tasks(cards=cards)
        approaching = await self.get_approaching_tasks(cards=cards)

        tasks = {}
        add_cards('a', approaching, tasks)
        add_cards('o', overdue, tasks)

        return tasks

    async def notify_channel(self, role, channel, tasks, ping):
        if ping:
            await channel.send(f'<@&{role.id}>')
        embed = discord.Embed(title='You have tasks that are:',
                              colour=role.colour)

        if len(tasks['o']) > 0:
            o = format_tasks(tasks['o'], dict=False)
            embed.add_field(name=f'{self.warning} Overdue',
                            value=o,
                            inline=False)
        if len(tasks['a']) > 0:
            a = format_tasks(tasks['a'], dict=False)
            embed.add_field(name=f'{self.todo} Approaching',
                            value=a,
                            inline=False)

        await channel.send(embed=embed)
