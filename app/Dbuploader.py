import psycopg2
from contextlib import contextmanager

class BeerDatabase:
    def __init__(self, dbname, user, password, host='postgres', port='5432'):
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

    def get_or_insert_beer(self, name, alcohol_percentage=None):
        select_query = """
            SELECT beer_id FROM Beers WHERE name = %s;
        """
        result = self._execute_query(select_query, (name,))
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

    def get_or_insert_reseller(self, reseller_name, zipcode):
        select_query = """
            SELECT reseller_id FROM Resellers WHERE reseller_name = %s AND zipcode = %s;
        """
        result = self._execute_query(select_query, (reseller_name,zipcode,))
        if result:
            return result[0]
        else:
            insert_query = """
                INSERT INTO Resellers (reseller_name, zipcode)
                VALUES (%s, %s)
                RETURNING reseller_id;
            """
            return self._execute_query(insert_query, (reseller_name, zipcode))[0]

    def insert_price(self, beer_id, format_id, reseller_id, price, currency, date, url):
        query = """
            INSERT INTO Prices (beer_id, format_id, reseller_id, price, currency, date, url)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING price_id;
        """
        return self._execute_query(query, (beer_id, format_id, reseller_id, price, currency, date, url))[0]

    def process_entry(self, entry):
        beer_id = self.get_or_insert_beer(entry.get('name'), entry.get('alcohol_content'))
        format_id = self.get_or_insert_format(beer_id, entry.get('quantity'), entry.get('unit'))
        reseller_id = self.get_or_insert_reseller(entry.get('reseller'), entry.get('zipcode'))
        price_id = self.insert_price(beer_id, format_id, reseller_id, entry.get('price'), entry.get('currency'), entry.get('date'), entry.get('url'))

        return {
            'beer_id': beer_id,
            'format_id': format_id,
            'price_id': price_id,
            'reseller_id': reseller_id,
        }

    def process_entries(self, entries):
        if isinstance(entries, list):
            return [self.process_entry(element) for element in entries]
        else:
            return self.process_entry(entries)

if __name__ == "__main__":
    db = BeerDatabase(dbname='crawler_db', user='crawler_user', password='crawler_password', host='postgres', port='5432')

    entry = {
        'name': 'Jever Pilsener',
        'quantity': 0.33,
        'unit': 'l',
        'price': 1.09,
        'currency': '€',
        'date': '2024-09-08',
        'reseller': 'Flink',
        'zipcode': '12345',
        'alcohol_content': 4.3,
        'url': 'google'
    }
    result = db.process_entries(entry)
    print(f"Inserted/Retrieved IDs: {result}")
