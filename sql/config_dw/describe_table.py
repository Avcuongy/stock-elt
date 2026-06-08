import duckdb

# Kết nối với database
con = duckdb.connect(database="../../datawarehouse.duckdb")

con.sql("DESCRIBE dim_date;").show()
con.sql("DESCRIBE dim_company;").show()
con.sql("DESCRIBE dim_topic;").show()
con.sql("DESCRIBE dim_news_source;").show()
con.sql("DESCRIBE fact_stock_daily;").show()
con.sql("DESCRIBE fact_news_sentiment;").show()

con.close()
