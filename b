
CREATE TABLE beer_data (
    ID SERIAL PRIMARY KEY,
    NAME VARCHAR(255) NOT NULL,
    PREIS NUMERIC(10, 2) NOT NULL,
    WAEHRUNG VARCHAR(50)
    MENGE NUMERIC(10, 2) NOT NULL,
    MENGENEINHEIT VARCHAR(25)
    ANBIETER VARCHAR(255) NOT NULL,
    PLZ VARCHAR(10) NOT NULL,
    SCRAPE_DATE DATETIME NOT NULL
);