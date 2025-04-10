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

def connect_to_database(username, password, host, database, ssl_enabled=False, ssl_cert_path=None):
    """
    Attempts to connect to the database with optional SSL.
    Returns connection and cursor objects if successful.
    Raises an exception if connection fails.
    """
    try:
        connection_kwargs = {
            "user": username,
            "password": password,
            "host": host,
            "database": database
        }

        if ssl_enabled and ssl_cert_path:
            connection_kwargs.update({
                "ssl_ca": ssl_cert_path,
                "ssl_cert": ssl_cert_path,
                "ssl_key": ssl_cert_path
            })

        conn = mariadb.connect(**connection_kwargs)
        cursor = conn.cursor()
        return conn, cursor

    except mariadb.Error as e:
        raise Exception(f"Database connection failed: {e}")

def fetch_data(cursor, table_name, limit=50, offset=0):
    """
    Fetch data in batches from the specified table in the database.

    Args:
        cursor (mariadb.cursor): The database cursor.
        table_name (str): Name of the table to fetch data from.
        limit (int): Number of records to fetch.
        offset (int): Offset for pagination.

    Returns:
        list: Fetched records or an empty list on error.
    """
    try:
        query = f"SELECT * FROM {table_name} ORDER BY 1 DESC LIMIT %s OFFSET %s"
        cursor.execute(query, (limit, offset))
        return cursor.fetchall()
    except mariadb.Error as e:
        print(f"Database Error: {e}")
        return []

def close_connection(conn):
    """Safely closes a database connection if it exists."""
    if conn:
        try:
            conn.close()
        except Exception:
            pass
        return None
    return conn
