import csv, json
import pandas as pd

class FileUtils():
    def __init__(self):
        pass

    async def open_csv_file(self, path):
        rows = []
        with open(path, 'r') as file:
            reader = csv.reader(file)
            for row in reader:
                # Process each row asynchronously
                processed_row = await self.process_row(row)
                rows.append(processed_row)
        return rows

    async def open_text_file(self, path):
        with open(path, 'r') as f:
            return f.read()

    async def open_json_file(self, path):
        with open(path) as json_file:
            json_data = json.load(json_file)
            return json_data

    async def process_row(self, row):
        # Perform some processing on each row asynchronously
        return row

    def get_libraries_json(self):
        df = pd.read_csv('app/schemas/libraries.csv')
        libraries_json = df.to_json(orient='records')
        return libraries_json
