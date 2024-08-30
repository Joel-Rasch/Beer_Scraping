-- Create the Beers table  
CREATE TABLE Beers (  
    beer_id SERIAL PRIMARY KEY,  
    name VARCHAR(255) NOT NULL,  
    alcohol_percentage DECIMAL(5, 2)  
);  

-- Create the Formats table  
CREATE TABLE Formats (  
    format_id SERIAL PRIMARY KEY,  
    beer_id INT,  
    quantity DECIMAL(8, 2) NOT NULL,  
    unit VARCHAR(50) NOT NULL,  
    FOREIGN KEY (beer_id) REFERENCES Beers(beer_id)  
);  

-- Create the Prices table  
CREATE TABLE Prices (  
    price_id SERIAL PRIMARY KEY,  
    format_id INT,  
    price DECIMAL(10, 2) NOT NULL,  
    currency VARCHAR(10) NOT NULL,  
    date DATE NOT NULL,  
    FOREIGN KEY (format_id) REFERENCES Formats(format_id)  
);  

-- Create the Resellers table  
CREATE TABLE Resellers (  
    reseller_id SERIAL PRIMARY KEY,  
    reseller_name VARCHAR(255) NOT NULL,  
    zipcode VARCHAR(20)  
    UNIQUE (reseller_name, zipcode) 
);

CREATE TABLE Format_Resellers ( 
format_reseller_id SERIAL PRIMARY KEY, 
format_id INT, reseller_id INT, 
FOREIGN KEY (format_id) REFERENCES Formats(format_id), 
FOREIGN KEY (reseller_id) REFERENCES Resellers(reseller_id) 
);

-- Create a view for beer analysis
CREATE VIEW BeerAnalysis AS
SELECT
    b.name AS beer_name,
    b.alcohol_percentage,
    f.quantity AS format_quantity,
    f.unit AS format_unit,
    p.price AS latest_price,
    p.currency,
    p.date AS price_date,
    r.reseller_name,
    r.zipcode
FROM
    Beers b
JOIN
    Formats f ON b.beer_id = f.beer_id
JOIN
    Prices p ON f.format_id = p.format_id
JOIN
    Format_Resellers fr ON f.format_id = fr.format_id
JOIN
    Resellers r ON fr.reseller_id = r.reseller_id
