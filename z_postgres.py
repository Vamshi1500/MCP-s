from mcp.server.fastmcp import FastMCP
from typing import Annotated
import psycopg2

# Create MCP instance
mcp = FastMCP("Postgres_MCP")

# Define your tool
@mcp.tool()
def create_postgres_db(
    db_name: Annotated[str, "Name of the database to create"]
) -> str:
    """Create a PostgreSQL database with the provided name.
    Example: create_postgres_db {db_name}"""
    try:
        conn = psycopg2.connect(
            dbname="postgres",  # use existing database to create others
            user="postgres",
            password="12345",
            host="localhost",
            port="5432"
        )
        conn.autocommit = True
        cur = conn.cursor()
        cur.execute(f"CREATE DATABASE {db_name}")
        cur.close()
        conn.close()
        return f"Database '{db_name}' created successfully!"
    except Exception as e:
        return f"Failed to create database: {e}"
    
current_db = {"name": "postgres"} 

@mcp.tool()
def value_of_current_db() -> str:
    """Get the name of the current database."""
    return f"Current database is: {current_db['name']}"

@mcp.tool()
def connect_to_postgres_db(
    db_name: Annotated[str, "Name of the database to connect to"]
) -> str:
    """
    Connect to a specific PostgreSQL database.
    This just validates if the DB exists and sets it as the 'current' database.
    Example: connect to database {db_name}
    """
    try:
        # Check if the database exists
        conn = psycopg2.connect(
            dbname=db_name,
            user="postgres",
            password="12345",
            host="localhost",
            port="5432"
        )
        
        # Update the global variable `current_db`
        current_db["name"] = db_name
        print(f"Connected to database: {current_db['name']}")
        # Return success message
        return f"Successfully connected to the database '{db_name}'."
    except Exception as e:
        return f"Failed to connect to database: {e}"

@mcp.tool() # create a table in the current database
def create_postgres_table(
    table_name: Annotated[str, "Name of the table to create"],
    table_schema: Annotated[str, "Schema of the table (e.g., id SERIAL PRIMARY KEY, name TEXT, email TEXT)"]
) -> str:
    """
    Create a table {table_name} in the currently connected database ({current_db['name']})
    with attributes {...}
    Example: create table {table_name} with attributes 'id SERIAL PRIMARY KEY, name TEXT, email TEXT'
    """
    try:
        # Connect to the current database
        conn = psycopg2.connect(
            dbname=current_db["name"],
            user="postgres",
            password="12345",
            host="localhost",
            port="5432"
        )
        conn.autocommit = True
        cur = conn.cursor()

        # Formulate the create table query
        create_query = f"CREATE TABLE IF NOT EXISTS {table_name} ({table_schema})"
        cur.execute(create_query)

        cur.close()
        conn.close()
        return f"Table '{table_name}' created successfully in database '{current_db['name']}'."

    except Exception as e:
        return f"Failed to create table: {e}"

@mcp.tool() # create a table in a specific database
def create_postgres_table_db(
    db_name: Annotated[str, "Database name to create the table in"],
    table_name: Annotated[str, "Name of the table to create"],
    table_schema: Annotated[str, "Schema of the table (e.g., id SERIAL PRIMARY KEY, name TEXT)"]
) -> str:
    """
    Create table {table_name} in database {db_name} with attributes {table_schema}.
    Example:
        create postgres table in mydb named users 'id SERIAL PRIMARY KEY, name TEXT, email TEXT'
    """
    try:
        conn = psycopg2.connect(
            dbname=db_name,
            user="postgres",
            password="12345",
            host="localhost",
            port="5432"
        )
        conn.autocommit = True
        cur = conn.cursor()

        create_query = f"CREATE TABLE IF NOT EXISTS {table_name} ({table_schema})"
        cur.execute(create_query)

        cur.close()
        conn.close()
        return f"Table '{table_name}' created successfully in database '{db_name}'."

    except Exception as e:
        return f"Failed to create table: {e}"

@mcp.tool() # delete a tanle from current database
def delete_postgres_table(
    table_name: Annotated[str, "Name of the table to delete"]
):
    """Delete the table {table_name} from the currently connected database ({current_db['name']}).
    Example: delete table {table_name}"""
    try:
        # Connect to the current database
        conn = psycopg2.connect(
            dbname=current_db["name"],
            user="postgres",
            password="12345",
            host="localhost",
            port="5432"
        )
        conn.autocommit = True
        cur = conn.cursor()

        # Formulate the create table query
        create_query = f"DROP TABLE IF EXISTS {table_name}"
        cur.execute(create_query)

        cur.close()
        conn.close()
        return f"Table '{table_name}' deleted successfully from database '{current_db['name']}'."

    except Exception as e:
        return f"Failed to create table: {e}"

@mcp.tool()
def insert_into_table(
    table_name: Annotated[str, "Name of the table to insert data into"],
    values: Annotated[dict, "Key-value pairs of columns and their values to insert"]
) -> str:
    """
    Insert a row into the table {table_name} in the current database ({current_db['name']})
    using provided column-value pairs.
    Example: insert row into users {'name': 'Alice', 'email': 'alice@example.com'}
    """
    try:
        conn = psycopg2.connect(
            dbname=current_db["name"],
            user="postgres",
            password="12345",
            host="localhost",
            port="5432"
        )
        conn.autocommit = True
        cur = conn.cursor()

        # Prepare query
        columns = ', '.join(values.keys())
        placeholders = ', '.join(['%s'] * len(values))
        query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
        cur.execute(query, list(values.values()))

        cur.close()
        conn.close()
        return f"Inserted row into '{table_name}' in database '{current_db['name']}'."

    except Exception as e:
        return f"Failed to insert row: {e}"
    
@mcp.tool()
def insert_into_table(
    table_name: Annotated[str, "Name of the table to insert data into"],
    values: Annotated[dict, "Key-value pairs of columns and their values to insert"]
) -> str:
    """
    Insert a row into the table {table_name} in the current database ({current_db['name']})
    using provided column-value pairs.
    Example: insert row into users {'name': 'Alice', 'email': 'alice@example.com'}
    """
    try:
        conn = psycopg2.connect(
            dbname=current_db["name"],
            user="postgres",
            password="12345",
            host="localhost",
            port="5432"
        )
        conn.autocommit = True
        cur = conn.cursor()

        # Prepare query
        columns = ', '.join(values.keys())
        placeholders = ', '.join(['%s'] * len(values))
        query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
        cur.execute(query, list(values.values()))

        cur.close()
        conn.close()
        return f"Inserted row into '{table_name}' in database '{current_db['name']}'."

    except Exception as e:
        return f"Failed to insert row: {e}"
    
@mcp.tool()
def delete_from_table(
    table_name: Annotated[str, "Name of the table to delete data from"],
    condition: Annotated[str, "SQL WHERE clause to specify which rows to delete"]
) -> str:
    """
    Delete rows from {table_name} in the current database ({current_db['name']})
    matching the given condition.
    
    Example: delete record from {table_name} with name = 'Alice'
    """
    try:
        conn = psycopg2.connect(
            dbname=current_db["name"],
            user="postgres",
            password="12345",
            host="localhost",
            port="5432"
        )
        conn.autocommit = True
        cur = conn.cursor()

        query = f"DELETE FROM {table_name} WHERE {condition}"
        cur.execute(query)

        cur.close()
        conn.close()
        return f"Deleted rows from '{table_name}' in database '{current_db['name']}' where {condition}."

    except Exception as e:
        return f"Failed to delete rows: {e}"
    
@mcp.tool()
def update_postgres_table(
    table_name: Annotated[str, "Name of the table to update"],
    set_values: Annotated[str, "Column values to set, e.g. name = 'Bob', email = 'bob@example.com'"],
    condition: Annotated[str, "SQL WHERE clause to specify which rows to update"]
) -> str:
    """
    Update rows in {table_name} of the current database ({current_db['name']})
    by setting {set_values} where {condition}.

    Example:
        update records of {table_name} to name = 'Bob', email = 'bob@example.com' where id = 2
    """
    try:
        conn = psycopg2.connect(
            dbname=current_db["name"],
            user="postgres",
            password="12345",
            host="localhost",
            port="5432"
        )
        conn.autocommit = True
        cur = conn.cursor()

        query = f"UPDATE {table_name} SET {set_values} WHERE {condition}"
        cur.execute(query)

        cur.close()
        conn.close()
        return f"Updated rows in '{table_name}' where {condition} with values {set_values}."

    except Exception as e:
        return f"Failed to update rows: {e}"

@mcp.tool()
def add_column_to_table(
    table_name: Annotated[str, "Name of the table to modify"],
    column_definition: Annotated[str, "Definition of the new column (e.g., age INT, or email TEXT UNIQUE NOT NULL)"]
) -> str:
    """
    Add a new column to the table {table_name} in the current database ({current_db['name']}).
    Example: add [list of column names to be added] to table {table_name}
    """
    try:
        conn = psycopg2.connect(
            dbname=current_db["name"],
            user="postgres",
            password="12345",
            host="localhost",
            port="5432"
        )
        conn.autocommit = True
        cur = conn.cursor()

        query = f"ALTER TABLE {table_name} ADD COLUMN {column_definition}"
        cur.execute(query)

        cur.close()
        conn.close()
        return f"Added column '{column_definition}' to table '{table_name}' in database '{current_db['name']}'."

    except Exception as e:
        return f"Failed to add column: {e}"

@mcp.tool()
def delete_column_from_table(
    table_name: Annotated[str, "Name of the table to modify"],
    column_name: Annotated[str, "Name of the column to delete"]
) -> str:
    """
    Delete column {column_name} from table {table_name} in the current database ({current_db['name']}).
    Example: delete column [list of column names] from {table_name}
    """
    try:
        conn = psycopg2.connect(
            dbname=current_db["name"],
            user="postgres",
            password="12345",
            host="localhost",
            port="5432"
        )
        conn.autocommit = True
        cur = conn.cursor()

        query = f"ALTER TABLE {table_name} DROP COLUMN IF EXISTS {column_name}"
        cur.execute(query)

        cur.close()
        conn.close()
        return f"Column '{column_name}' deleted successfully from table '{table_name}' in database '{current_db['name']}'."

    except Exception as e:
        return f"Failed to delete column: {e}"
    
# process a raw query:
@mcp.tool()
def run_sql_query(
    query: Annotated[str, "Raw SQL query to execute"]
) -> str:
    """
    Run a raw SQL query on the currently connected database ({current_db['name']}).
    Example: run query "SELECT * FROM users"
    """
    try:
        conn = psycopg2.connect(
            dbname=current_db["name"],
            user="postgres",
            password="12345",
            host="localhost",
            port="5432"
        )
        conn.autocommit = True
        cur = conn.cursor()

        cur.execute(query)

        # If it's a SELECT, fetch and return rows
        if query.strip().lower().startswith("select"):
            rows = cur.fetchall()
            colnames = [desc[0] for desc in cur.description]
            formatted = [dict(zip(colnames, row)) for row in rows]
            cur.close()
            conn.close()
            return f"Query executed. Results:\n{formatted}"

        cur.close()
        conn.close()
        return "Query executed successfully."

    except Exception as e:
        return f"Failed to execute query: {e}"

@mcp.tool()
def get_events_between_dates(
    table_name: Annotated[str, "Table name to fetch events from"],
    date_column_name: Annotated[str, "Date column name in the table (e.g., event_date)"],
    start_date: Annotated[str, "Start date in YYYY-MM-DD format"],
    end_date: Annotated[str, "End date in YYYY-MM-DD format"]
) -> str:
    """
    Get events from {table_name} where {date_column_name} is between {start_date} and {end_date}.
    Example: get events from 'events' where 'event_date' is between '2022-01-01' and '2023-12-31'
    """
    try:
        # Connect to the current database
        conn = psycopg2.connect(
            dbname=current_db["name"],
            user="postgres",
            password="12345",
            host="localhost",
            port="5432"
        )
        cur = conn.cursor()

        # Build the dynamic query to select records within the date range
        query = f"""
            SELECT * FROM {table_name}
            WHERE {date_column_name} BETWEEN %s AND %s
        """

        # Execute the query with the provided date range
        cur.execute(query, (start_date, end_date))
        rows = cur.fetchall()

        cur.close()
        conn.close()

        # If no records are found
        if not rows:
            return f"No events found in '{table_name}' between {start_date} and {end_date}."

        # Format the result to make it readable
        result = "\n".join(str(row) for row in rows)
        return f"Events from '{table_name}' between {start_date} and {end_date}:\n{result}"

    except Exception as e:
        return f"Error fetching events: {e}"

@mcp.tool()
def get_record_with_nth_highest_value(
    table_name: Annotated[str, "Name of the table (e.g., employee)"],
    column_to_rank: Annotated[str, "Column name to rank (e.g., salary)"],
    name_column: Annotated[str, "Column name for the record identifier (e.g., employee_name)"],
    rank: Annotated[int, "Rank of the value (1 for highest, 2 for second highest, etc.)"]
) -> str:
    """
    Get the record with the {rank} highest value in the specified column from the table.
    Example:
        get_record_with_nth_highest_value employee salary employee_name 2
        This will return the record with the second-highest salary from the employee table.

        get name of the employee with 2nd highest salary from table {table_name}

        get name of the person with 1st highest salary from table {table_name}
    """
    try:
        # Connect to the current database
        conn = psycopg2.connect(
            dbname=current_db["name"],
            user="postgres",
            password="12345",
            host="localhost",
            port="5432"
        )
        conn.autocommit = True
        cur = conn.cursor()

        # General SQL query to get the record with nth highest value
        query = f"""
            SELECT {name_column}
            FROM (SELECT {name_column}, {column_to_rank}, RANK() OVER (ORDER BY {column_to_rank} DESC) as rank
                  FROM {table_name}) AS ranked_records
            WHERE rank = %s;
        """
        
        cur.execute(query, (rank,))
        result = cur.fetchone()

        cur.close()
        conn.close()

        if result:
            return f"Record with the {rank} highest {column_to_rank} in the table '{table_name}' is: {result[0]}"
        else:
            return f"No record found with rank {rank} in the table '{table_name}'."

    except Exception as e:
        return f"Error: {e}"



# Start MCP server
if __name__ == "__main__":
    mcp.settings.port = 8200
    mcp.settings.sse_path = "/postgres_crud"
    mcp.run(transport="sse")
