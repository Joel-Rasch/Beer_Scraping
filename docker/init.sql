-- Beers table  
CREATE TABLE Beers (  
    beer_id SERIAL PRIMARY KEY,  
    name VARCHAR(255) NOT NULL,  
    alcohol_percentage DECIMAL(5,2)  
);  
  
-- Formats table  
CREATE TABLE Formats (  
    format_id SERIAL PRIMARY KEY,  
    beer_id INT,  
    quantity DECIMAL(10,2) NOT NULL,  
    unit VARCHAR(50) NOT NULL,  
    FOREIGN KEY (beer_id) REFERENCES Beers(beer_id)  
);  
  
-- Resellers table  
CREATE TABLE Resellers (  
    reseller_id SERIAL PRIMARY KEY,  
    reseller_name VARCHAR(255) NOT NULL,  
    zipcode VARCHAR(20)  
);  
  
-- Prices table  
CREATE TABLE Prices (  
    price_id SERIAL PRIMARY KEY,  
    beer_id INT,  
    format_id INT,  
    reseller_id INT,  
    price DECIMAL(10,2) NOT NULL,  
    currency VARCHAR(10) NOT NULL,  
    date DATE,  
    url VARCHAR(2000) NOT NULL,  
    FOREIGN KEY (beer_id) REFERENCES Beers(beer_id),  
    FOREIGN KEY (format_id) REFERENCES Formats(format_id),  
    FOREIGN KEY (reseller_id) REFERENCES Resellers(reseller_id)  
);  
