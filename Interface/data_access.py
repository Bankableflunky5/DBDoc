import mariadb
from datetime import datetime

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

def fetch_table_data(cursor, table_name, limit=50, offset=0, order_by=None, descending=True):
    order_clause = ""
    if order_by:
        order_clause = f"ORDER BY {order_by} {'DESC' if descending else 'ASC'}"

    query = f"SELECT * FROM {table_name} {order_clause} LIMIT {limit} OFFSET {offset}"
    cursor.execute(query)
    return cursor.fetchall()

def fetch_table_data_with_columns(cursor, table_name, limit=50, offset=0, order_by=None, descending=True):
    """
    Fetches rows and column names from a table. Use for UI rendering.
    """
    rows = fetch_table_data(cursor, table_name, limit, offset, order_by, descending)
    columns = [desc[0] for desc in cursor.description]
    return rows, columns

def fetch_primary_key_column(cursor, table_name):
    cursor.execute(f"SHOW KEYS FROM {table_name} WHERE Key_name = 'PRIMARY'")
    pk_info = cursor.fetchone()
    return pk_info[4] if pk_info else None

def paginate_table_data(fetch_function, table_name, limit, offset):
    """Handles pagination logic and returns the new offset and data."""
    new_offset = max(0, offset)
    data = fetch_function(table_name, limit, new_offset)
    return new_offset, data

def get_primary_key_column(cursor, table_name):
    cursor.execute(f"SHOW KEYS FROM {table_name} WHERE Key_name = 'PRIMARY'")
    result = cursor.fetchone()
    return result[4] if result else None

def check_primary_key_exists(cursor, table_name, pk_column, pk_value):
    cursor.execute(f"SELECT {pk_column} FROM {table_name} WHERE {pk_column} = %s", (pk_value,))
    result = cursor.fetchone()
    return result[0] if result else None

def check_duplicate_primary_key(cursor, table_name, pk_column, new_pk_value):
    cursor.execute(f"SELECT COUNT(*) FROM {table_name} WHERE {pk_column} = %s", (new_pk_value,))
    return cursor.fetchone()[0] > 0

def update_column(cursor, conn, table_name, column_name, new_value, pk_column, pk_value):
    cursor.execute(
        f"UPDATE {table_name} SET {column_name} = %s WHERE {pk_column} = %s",
        (new_value, pk_value)
    )
    conn.commit()

def update_primary_key(cursor, conn, table_name, pk_column, old_pk, new_pk):
    cursor.execute(
        f"UPDATE {table_name} SET {pk_column} = %s WHERE {pk_column} = %s",
        (new_pk, old_pk)
    )
    conn.commit()

def update_auto_increment_if_needed(cursor, conn, table_name, pk_column):
    cursor.execute(f"SELECT MAX({pk_column}) FROM {table_name}")
    max_pk = cursor.fetchone()[0]

    if max_pk is None:
        return

    cursor.execute(f"SHOW TABLE STATUS LIKE %s", (table_name,))
    table_status = cursor.fetchone()
    if table_status is None:
        return

    current_ai = table_status[10]
    new_ai = max_pk + 1

    if current_ai != new_ai:
        cursor.execute(f"ALTER TABLE {table_name} AUTO_INCREMENT = {new_ai}")
        conn.commit()

def update_status(cursor, conn, table_name, pk_column, pk_value, new_status):
    try:
        if new_status == "Completed":
            current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            query = f"""
                UPDATE {table_name}
                SET status = %s, EndDate = %s
                WHERE {pk_column} = %s
            """
            cursor.execute(query, (new_status, current_datetime, pk_value))
        else:
            query = f"""
                UPDATE {table_name}
                SET status = %s
                WHERE {pk_column} = %s
            """
            cursor.execute(query, (new_status, pk_value))

        conn.commit()
        return True

    except Exception as e:
        print(f"❌ ERROR in update_status: {e}")
        return False
