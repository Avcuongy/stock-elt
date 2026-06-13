CREATE SCHEMA IF NOT EXISTS DataWarehouse;

SET schema
    = 'DataWarehouse';

CREATE SEQUENCE IF NOT EXISTS seq_company_key START 1;

CREATE SEQUENCE IF NOT EXISTS seq_industry_key START 1;

CREATE SEQUENCE IF NOT EXISTS seq_exchange_key START 1;

-- DIM_DATE
CREATE TABLE DIM_DATE (
    date_key INTEGER PRIMARY KEY,
    full_date TIMESTAMP,
    day INTEGER,
    month INTEGER,
    year INTEGER,
    quarter INTEGER,
    day_of_week VARCHAR,
    week_of_year INTEGER,
    is_weekend BOOLEAN,
    is_holiday BOOLEAN
);

-- DIM_COMPANY
CREATE TABLE DIM_COMPANY (
    company_key INTEGER DEFAULT nextval('seq_company_key') PRIMARY KEY,
    company_ticker VARCHAR,
    company_name VARCHAR,
    company_cik VARCHAR,
    company_is_delisted BOOLEAN,
    company_location VARCHAR,
    is_current BOOLEAN DEFAULT TRUE
);

-- DIM_INDUSTRY
CREATE TABLE DIM_INDUSTRY (
    industry_key INTEGER DEFAULT nextval('seq_industry_key') PRIMARY KEY,
    industry_sector VARCHAR,
    industry_name VARCHAR,
    company_category VARCHAR,
    sic_industry VARCHAR,
    sic_sector VARCHAR,
    is_current BOOLEAN DEFAULT TRUE
);

-- DIM_EXCHANGE
CREATE TABLE DIM_EXCHANGE (
    exchange_key INTEGER DEFAULT nextval('seq_exchange_key') PRIMARY KEY,
    exchange_name VARCHAR,
    region_name VARCHAR,
    region_market_type VARCHAR,
    region_local_open TIME,
    region_local_close TIME,
    is_current BOOLEAN DEFAULT TRUE
);

-- FACT_STOCK_DAILY
CREATE TABLE FACT_STOCK_DAILY (
    date_key INTEGER NOT NULL,
    company_key INTEGER NOT NULL,
    industry_key INTEGER NOT NULL,
    exchange_key INTEGER NOT NULL,
    -- Metrics
    open_price DECIMAL(18, 4),
    high_price DECIMAL(18, 4),
    low_price DECIMAL(18, 4),
    close_price DECIMAL(18, 4),
    volume BIGINT,
    price_change DECIMAL(18, 4),
    price_trend VARCHAR,
    -- Foreign Key Constraints
    FOREIGN KEY (date_key) REFERENCES DIM_DATE(date_key),
    FOREIGN KEY (company_key) REFERENCES DIM_COMPANY(company_key),
    FOREIGN KEY (industry_key) REFERENCES DIM_INDUSTRY(industry_key),
    FOREIGN KEY (exchange_key) REFERENCES DIM_EXCHANGE(exchange_key)
);