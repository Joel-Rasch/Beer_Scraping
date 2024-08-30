import psycopg2
from contextlib import contextmanager

class BeerDatabase:
    def __init__(self, dbname, user, password, host='localhost', port='5432'):
        self.connection_params = {
            'dbname': dbname,
            'user': user,
            'password': password,
            'host': host,
            'port': port
        }

    @contextmanager
    def get_cursor(self):
        with psycopg2.connect(**self.connection_params) as conn:
            with conn.cursor() as cursor:
                yield cursor

    def _execute_query(self, query, params):
        with self.get_cursor() as cursor:
            cursor.execute(query, params)
            return cursor.fetchone()

    def get_or_insert_beer(self, name, alcohol_percentage):
        select_query = """
        SELECT beer_id FROM Beers WHERE name = %s AND alcohol_percentage = %s;
        """
        result = self._execute_query(select_query, (name, alcohol_percentage))
        if result:
            return result[0]
        else:
            insert_query = """
            INSERT INTO Beers (name, alcohol_percentage)
            VALUES (%s, %s)
            RETURNING beer_id;
            """
            return self._execute_query(insert_query, (name, alcohol_percentage))[0]

    def get_or_insert_format(self, beer_id, quantity, unit):
        select_query = """
        SELECT format_id FROM Formats WHERE beer_id = %s AND quantity = %s AND unit = %s;
        """
        result = self._execute_query(select_query, (beer_id, quantity, unit))
        if result:
            return result[0]
        else:
            insert_query = """
            INSERT INTO Formats (beer_id, quantity, unit)
            VALUES (%s, %s, %s)
            RETURNING format_id;
            """
            return self._execute_query(insert_query, (beer_id, quantity, unit))[0]

    def insert_price(self, format_id, price, currency, date):
        query = """
        INSERT INTO Prices (format_id, price, currency, date)
        VALUES (%s, %s, %s, %s)
        RETURNING price_id;
        """
        return self._execute_query(query, (format_id, price, currency, date))[0]

    def get_or_insert_reseller(self, reseller_name, zipcode):
        select_query = """
        SELECT reseller_id FROM Resellers WHERE reseller_name = %s AND zipcode = %s;
        """
        result = self._execute_query(select_query, (reseller_name, zipcode))
        if result:
            return result[0]
        else:
            insert_query = """
            INSERT INTO Resellers (reseller_name, zipcode)
            VALUES (%s, %s)
            RETURNING reseller_id;
            """
            return self._execute_query(insert_query, (reseller_name, zipcode))[0]

    def get_or_insert_format_reseller(self, format_id, reseller_id):
        select_query = """
        SELECT format_reseller_id FROM Format_Resellers WHERE format_id = %s AND reseller_id = %s;
        """
        result = self._execute_query(select_query, (format_id, reseller_id))
        if result:
            return result[0]
        else:
            insert_query = """
            INSERT INTO Format_Resellers (format_id, reseller_id)
            VALUES (%s, %s)
            RETURNING format_reseller_id;
            """
            return self._execute_query(insert_query, (format_id, reseller_id))[0]

    def process_entry(self, entry):
        beer_id = self.get_or_insert_beer(entry['name'], entry['alcohol_content'])
        format_id = self.get_or_insert_format(beer_id, entry['quantity'], entry['unit'])
        price_id = self.insert_price(format_id, entry['price'], entry['currency'], entry['date'])
        reseller_id = self.get_or_insert_reseller(entry['reseller'], entry['zipcode'])
        format_reseller_id = self.get_or_insert_format_reseller(format_id, reseller_id)

        return {
            'beer_id': beer_id,
            'format_id': format_id,
            'price_id': price_id,
            'reseller_id': reseller_id,
            'format_reseller_id': format_reseller_id
        }

    def process_entries(self, entries):
        if isinstance(entries, list):
            return [self.process_entry(element) for element in entries]
        else:
            return self.process_entry(entries)

if __name__ == "__main__":
    db = BeerDatabase(dbname='crawler_db', user='crawler_user', password='crawler_password', host='postgres', port='5432')


## For Debug and to see data structure and type
    entry = {
        'name': 'Jever Pilsener',
        'quantity': 0.33,
        'unit': 'l',
        'price': 1.09,
        'currency': '€',
        'date': '2024-09-08',
        'reseller': 'Flink',
        'zipcode': '12345',
        'alcohol_content': 4.3
    }

    result = db.process_entries(entry)
    print(f"Inserted/Retrieved IDs: {result}")
