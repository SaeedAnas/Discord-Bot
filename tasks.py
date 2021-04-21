import json
from datetime import datetime
from trello import TrelloClient


async def connect(ctx):
    return Tasks(ctx)


def date(time):
    return datetime.strptime(time, "%Y-%m-%dT%H:%M:%S.000Z")


def isOverdue(time):
    due = date(time)
    present = datetime.now()
    return due.date() < present.date()


def format_card(card):
    return f'- {card.get("name")} :: {date(card.get("due")).strftime("%m/%d/%y")}'


def format_tasks(cards):
    formatted = ''
    for card in cards:
        formatted += f'{format_card(card)}\n'
    return formatted


class Tasks:
    warning = '❗️'
    check = '✅'
    todo = '📝'

    def __init__(self, ctx):
        self.ctx = ctx

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
            filter(lambda m: m.full_name.split(' ')[0] == name, members))[0]

    async def get_tasks(self, user):
        member = self.get_member(user)
        cards = member.fetch_cards()
        overdue = []
        to_do = []
        completed = []
        for card in cards:
            if card.get('dueComplete'):
                completed.append(card)
            elif isOverdue(card.get('due')):
                overdue.append(card)
            else:
                to_do.append(card)
        return {
            f'{self.warning} Overdue': overdue,
            f'{self.todo} To Do': to_do,
            # f'{self.check} Completed': completed
        }
