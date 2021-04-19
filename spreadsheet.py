import gspread

gc = gspread.service_account(filename='./service_account.json')

sh = gc.open("Strike Tracker")

worksheet = sh.sheet1

worksheet.update_cell(2, 3, '')
