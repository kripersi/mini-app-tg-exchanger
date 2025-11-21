import gspread


class GoogleSheet:
    def __init__(self, credentials_path, sheet_name, tab_name=None):
        """
        credentials_path – путь к JSON ключу
        sheet_name – имя Google Spreadsheet (файла)
        tab_name – имя вкладки внутри файла (по умолчанию sheet1)
        """
        self.gc = gspread.service_account(filename=credentials_path)
        self.sh = self.gc.open(sheet_name)

        if tab_name:
            self.ws = self.sh.worksheet(tab_name)
        else:
            self.ws = self.sh.sheet1

    def get_all_records(self):
        return self.ws.get_all_records()

    def update_range(self, row, col, values):
        """
        values – двумерный список (как gspread.update)
        """
        self.ws.update(values, f"{col}{row}")
