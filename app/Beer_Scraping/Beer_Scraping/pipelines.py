import psycopg2
from itemadapter import ItemAdapter

class BeerScrapingPipeline:
    def __init__(self, db_url):
        self.db_url = db_url

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            db_url=crawler.settings.get('DATABASE_URL')
        )

    def open_spider(self, spider):
        self.conn = psycopg2.connect(self.db_url)
        self.cur = self.conn.cursor()

    def close_spider(self, spider):
        self.cur.close()
        self.conn.close()

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)

        # Insert or get currency
        self.cur.execute("INSERT INTO currencies (currency_code, currency_name) VALUES (%s, %s) ON CONFLICT (currency_code) DO UPDATE SET currency_name = EXCLUDED.currency_name RETURNING currency_id",
                         (adapter['currency_code'], adapter['currency_name']))
        currency_id = self.cur.fetchone()[0]

        # Insert or get unit
        self.cur.execute("INSERT INTO units (unit_name) VALUES (%s) ON CONFLICT (unit_name) DO UPDATE SET unit_name = EXCLUDED.unit_name RETURNING unit_id",
                         (adapter['unit_name'],))
        unit_id = self.cur.fetchone()[0]

        # Insert or get supplier
        self.cur.execute("INSERT INTO suppliers (supplier_name, postal_code) VALUES (%s, %s) ON CONFLICT (supplier_name) DO UPDATE SET postal_code = EXCLUDED.postal_code RETURNING supplier_id",
                         (adapter['supplier_name'], adapter['postal_code']))
        supplier_id = self.cur.fetchone()[0]

        # Insert or get brand
        self.cur.execute("INSERT INTO brands (brand_name) VALUES (%s) ON CONFLICT (brand_name) DO UPDATE SET brand_name = EXCLUDED.brand_name RETURNING brand_id",
                         (adapter['brand_name'],))
        brand_id = self.cur.fetchone()[0]

        # Insert or get material
        self.cur.execute("INSERT INTO materials (material_name) VALUES (%s) ON CONFLICT (material_name) DO UPDATE SET material_name = EXCLUDED.material_name RETURNING material_id",
                         (adapter['material_name'],))
        material_id = self.cur.fetchone()[0]

        # Insert or get deposit_type
        self.cur.execute("INSERT INTO deposit_types (deposit_type_name) VALUES (%s) ON CONFLICT (deposit_type_name) DO UPDATE SET deposit_type_name = EXCLUDED.deposit_type_name RETURNING deposit_type_id",
                         (adapter['deposit_type_name'],))
        deposit_type_id = self.cur.fetchone()[0]

        # Insert or update beer
        self.cur.execute("INSERT INTO beers (name, brand_id, description, alcohol_content) VALUES (%s, %s, %s, %s) ON CONFLICT (name) DO UPDATE SET brand_id = EXCLUDED.brand_id, description = EXCLUDED.description, alcohol_content = EXCLUDED.alcohol_content RETURNING beer_id",
                         (adapter['name'], brand_id, adapter['description'], adapter['alcohol_content']))
        beer_id = self.cur.fetchone()[0]

        # Insert beer_data
        self.cur.execute("""
            INSERT INTO beer_data (
                beer_id, price, currency_id, quantity, unit_id, supplier_id,
                material_id, deposit_type_id, article_number, delivery_time, scrape_date
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
        """, (
            beer_id, adapter['price'], currency_id, adapter['quantity'], unit_id,
            supplier_id, material_id, deposit_type_id, adapter['article_number'],
            adapter['delivery_time']
        ))

        self.conn.commit()
        return item