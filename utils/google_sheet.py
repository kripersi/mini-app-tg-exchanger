import gspread


class GoogleSheet:
    def __init__(self, credentials_path, sheet_name):
        self.gc = gspread.service_account(filename=credentials_path)
        self.sh = self.gc.open(sheet_name)
        self.ws = self.sh.sheet1

    def get_all_records(self):
        return self.ws.get_all_records()

    def update_cell(self, row, col, value):
        self.ws.update_cell(row, col, value)
