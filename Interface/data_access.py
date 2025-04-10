import mariadb

def fetch_tables(cursor):
    """
    Fetches and returns a list of tables from the database.
    """
    try:
        cursor.execute("SHOW TABLES;")
        tables = [table[0] for table in cursor.fetchall()]
        return tables
    except mariadb.Error as e:
        raise Exception(f"Failed to retrieve tables: {e}")
