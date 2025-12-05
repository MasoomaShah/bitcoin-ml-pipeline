import psycopg2
import pandas as pd

# Connect to Postgres
def load_data_from_postgres():
    conn = psycopg2.connect(
        dbname="mlops",
        user="postgres",
        password="postgres",
        host="localhost",
        port="5432"
    )

    # Pull the table
    df = pd.read_sql("SELECT * FROM raw_movies", conn)  # Replace 'movie_data' with your table name
    conn.close()

    return df

if __name__ == "__main__":
    df = load_data_from_postgres()
    print(df.head())
