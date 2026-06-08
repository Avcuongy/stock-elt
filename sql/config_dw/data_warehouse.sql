CREATE SCHEMA IF NOT EXISTS data_warehouse;

SET schema
    'data_warehouse';

-- Dimension Tables (DIM)
-- DIM_DATE
CREATE TABLE IF NOT EXISTS dim_date (
    date_key INTEGER PRIMARY KEY,
    -- surrogate key (có thể = yyyymmdd)
    full_date DATE NOT NULL,
    month INTEGER NOT NULL,
    quarter INTEGER NOT NULL,
    year INTEGER NOT NULL
);

-- DIM_COMPANY
CREATE TABLE IF NOT EXISTS dim_company (
    company_key INTEGER PRIMARY KEY,
    -- surrogate key
    company_ticker VARCHAR NOT NULL,
    company_name VARCHAR,
    company_is_delisted BOOLEAN,
    exchange_name VARCHAR,
    industry_name VARCHAR,
    industry_sector VARCHAR,
    sic_industries VARCHAR
);

-- DIM_NEWS_SOURCE
CREATE TABLE IF NOT EXISTS dim_news_source (
    source_key INTEGER PRIMARY KEY,
    -- surrogate key
    source VARCHAR NOT NULL,
    source_domain VARCHAR
);

-- DIM_TOPIC
CREATE TABLE IF NOT EXISTS dim_topic (
    topic_key INTEGER PRIMARY KEY,
    -- surrogate key
    topic VARCHAR NOT NULL
);

-- Fact Tables (FACT)
-- FACT_STOCK_DAILY
CREATE TABLE IF NOT EXISTS fact_stock_daily (
    -- key
    date_key INTEGER NOT NULL,
    company_key INTEGER NOT NULL,
    -- measures
    open_price DECIMAL(18, 4),
    high_price DECIMAL(18, 4),
    low_price DECIMAL(18, 4),
    close_price DECIMAL(18, 4),
    volume BIGINT,
    volume_weighted_avg_price DECIMAL(18, 6),
    trade_count BIGINT,
    -- constraints
    CONSTRAINT fk_fact_stock_date FOREIGN KEY (date_key) REFERENCES dim_date(date_key)
);

-- FACT_NEWS_SENTIMENT
CREATE TABLE IF NOT EXISTS fact_news_sentiment (
    news_key BIGINT PRIMARY KEY,
    -- degenerate dimension / natural key
    date_key INTEGER NOT NULL,
    source_key INTEGER,
    company_key INTEGER,
    title VARCHAR,
    url VARCHAR,
    overall_sentiment_score DECIMAL(9, 6),
    overall_sentiment_label VARCHAR,
    ticker_relevance_score DECIMAL(9, 6),
    ticker_sentiment_score DECIMAL(9, 6),
    ticker_sentiment_label VARCHAR,
    CONSTRAINT fk_fact_news_date FOREIGN KEY (date_key) REFERENCES dim_date(date_key),
    CONSTRAINT fk_fact_news_source FOREIGN KEY (source_key) REFERENCES dim_news_source(source_key),
    CONSTRAINT fk_fact_news_company FOREIGN KEY (company_key) REFERENCES dim_company(company_key)
);

-- BRIDGE_NEWS_TOPIC
CREATE TABLE IF NOT EXISTS bridge_news_topic (
    news_key BIGINT NOT NULL,
    topic_key INTEGER NOT NULL,
    relevance_score DECIMAL(9, 6),
    CONSTRAINT pk_bridge_news_topic PRIMARY KEY (news_key, topic_key),
    CONSTRAINT fk_bridge_topic FOREIGN KEY (topic_key) REFERENCES dim_topic(topic_key)
);