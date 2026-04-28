import psycopg2

# Your Aiven PostgreSQL connection details
conn = psycopg2.connect(
    host="pg-3ad1423a-mpesa-transaction123.a.aivencloud.com",
    port=17131,
    dbname="defaultdb",
    user="avnadmin",
    password="YOUR_PASSWORD",
    sslmode="require"
)

cursor = conn.cursor()

# Read and execute the schema file
with open("database/schema.sql", "r") as f:
    schema_sql = f.read()

cursor.execute(schema_sql)
conn.commit()

print("✅ Schema executed successfully!")
cursor.close()
conn.close()