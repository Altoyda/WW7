import sqlite3


class Database:
    """Class for easier work with database"""
    def __init__(self, print_out_state=True):
        try:
            self.get_connection()
            self.db.close()
            if print_out_state:
                print("Database connected, tables created!")
        except Exception as exc:
            if print_out_state:
                print("Something went wrong with the database! See the error below:")
            print(exc)

    def get_connection(self):
        """Establish a new connection to the database"""
        self.db = sqlite3.connect('database/database.db')  # Replace 'database.db' with the name of your SQLite3 database file
        self.cursor = self.db.cursor()

    def close_connection(self):
        """Close the connection with the database"""
        self.cursor.close()
        self.db.close()

    def check_create_table(self, tbname, columns):
        """Handles table creation"""
        self.get_connection()
        self.cursor.execute(f"CREATE TABLE IF NOT EXISTS {tbname} ({columns});")
        self.close_connection()

    def get_boolean(self, tbname, column, id):
        """Gets true/false from the database based on the args"""
        self.get_connection()
        self.cursor.execute(f"SELECT {column} FROM {tbname} WHERE {id}=1;")
        result = self.cursor.fetchall()
        self.close_connection()
        if len(result):
            return True
        return False

    def check_contains(self, tbname, column, value):
        """Return true/false based on if the database contains a specific value"""
        self.get_connection()
        self.cursor.execute(f"SELECT * FROM {tbname} WHERE {column}={value};")
        result = self.cursor.fetchall()
        self.close_connection()
        if len(result):
            return True
        return False

    def insert(self, tbname, columns, values):
        """Handles inserting new data into the database"""
        self.get_connection()
        self.cursor.execute(f"INSERT INTO {tbname} ({columns}) VALUES ({values});")
        self.db.commit()
        self.close_connection()

    def get_next_auto_increment(self, tbname):
        """Gets the next auto increment value of a certain table"""
        self.get_connection()
        self.cursor.execute(f"SELECT seq FROM sqlite_sequence WHERE name='{tbname}';")
        result = self.cursor.fetchone()
        self.close_connection()
        if result:
            return result[0] + 1
        return 1

    def get_count(self, tbname, condition):
        """Gets the count of records that match a certain condition"""
        self.get_connection()
        self.cursor.execute(f"SELECT COUNT(*) FROM {tbname} WHERE {condition}")
        result = self.cursor.fetchone()
        self.close_connection()
        return result[0]

    def get_id(self, tbname, condition):
        """Gets the id of an object with certain properties from the database"""
        self.get_connection()
        self.cursor.execute(f"SELECT id FROM {tbname} WHERE {condition}")
        result = self.cursor.fetchone()
        self.close_connection()
        return result[0]

    def update_data(self, tbname, column, value, condition):
        """Handles updating data in the database"""
        self.get_connection()
        self.cursor.execute(f"UPDATE {tbname} SET {column}={value} WHERE {condition}")
        self.db.commit()
        self.close_connection()

    def get_value_general(self, tbname, column, condition):
        """Gets a value from the database based on the given condition"""
        self.get_connection()
        self.cursor.execute(f"SELECT {column} FROM {tbname} WHERE {condition};")
        result = self.cursor.fetchone()
        self.close_connection()
        return result[0]

    def delete_value_general(self, table_name, condition):
        """Removes a row from the database depending on the condition"""
        self.get_connection()
        self.cursor.execute(f"DELETE FROM {table_name} WHERE {condition}")
        self.db.commit()
        self.close_connection()

    def get_values_general(self, table_name, columns, condition):
        """Gets a list of values from the database"""
        self.get_connection()
        self.cursor.execute(f"SELECT {columns} FROM {table_name} WHERE {condition};")
        result = list(self.cursor)
        self.close_connection()
        return result

    def add_steam_profile(self, discord_id, steam_id, player_name, avatar_url, profile_url, country, gbl_status):
        """Add a Steam profile to the database"""
        self.get_connection()
        self.cursor.execute("INSERT INTO Steam (discord_id, steam_id, player_name, avatar_url, profile_url, country, gbl_status) VALUES (?, ?, ?, ?, ?, ?, ?)",
                            (discord_id, steam_id, player_name, avatar_url, profile_url, country, gbl_status))
        self.db.commit()
        self.close_connection()

    def get_steam_profile(self, discord_id):
        """Retrieve a Steam profile from the database"""
        self.get_connection()
        self.cursor.execute("SELECT * FROM Steam WHERE discord_id = ?", (discord_id,))
        profile = self.cursor.fetchone()
        self.close_connection()
        return profile