import gspread


def get_sheet(name):
    gc = gspread.service_account(filename='./service_account.json')
    sh = gc.open(name)
    return sh.sheet1


class StrikeSheet:
    strike_col = 3
    reason_col = 4
    sheet = 'https://docs.google.com/spreadsheets/d/1DVPDeYkLLwjkL2BTBlBRUWsmnpew-z5fjT9T9wMYri0/edit#gid=0'
    admin_id = '<@!689626652258467851>'

    def __init__(self, ctx):
        self.ws = get_sheet("Strike Tracker")
        self.ctx = ctx

    async def register_member(self, member):
        if not member.bot:
            name = member.display_name.split(' ')[0]
            uid = f'<@!{member.id}>'

            try:
                self.find_user(uid)
                await self.ctx.send(f'{name} is already registered!')
            except Exception:
                self.ws.append_row([name, uid, 0])
                await self.ctx.send(f'{name} has been registered')

    async def register_members(self, members):
        for member in members:
            await self.register_member(member)

    def find_user(self, uid):
        return self.ws.find(uid).row

    def get_strikes(self, user):
        return int(self.ws.cell(user, self.strike_col).value)

    def update_strikes(self, user, value):
        return self.ws.update_cell(user, self.strike_col, value)

    def get_reason(self, user, strike):
        return self.ws.cell(user, self.reason_col + strike - 1).value

    def update_reason(self, user, strike, reason):
        return self.ws.update_cell(user, self.reason_col + strike - 1, reason)

    async def strike_user(self, uid, reason):
        user = self.find_user(uid)
        strikes = self.get_strikes(user) + 1
        if strikes >= 3:
            await self.ctx.send(
                f"{uid} has been striked 3 times! His fate is now under {self.admin_id}'s control"
            )
            self.update_strikes(user, strikes)
            self.update_reason(user, strikes, reason)
            return
        self.update_strikes(user, strikes)
        self.update_reason(user, strikes, reason)
        await self.ctx.send(
            f'{self.admin_id}, User: {uid} is striked because: {reason}. Strike count is {self.get_strikes(user)}'
        )

    async def remove_strike(self, uid):
        user = self.find_user(uid)
        strikes = self.get_strikes(user)
        if strikes < 1:
            await self.ctx.send(f'{uid} has no strikes...')
            return
        self.update_strikes(user, strikes - 1)
        self.update_reason(user, strikes, '')
        await self.ctx.send(
            f'{self.admin_id}, User: {uid} has been unstriked. Strike count is {self.get_strikes(user)}'
        )

    async def spreadsheet(self):
        await self.ctx.send(f'{self.sheet}')
