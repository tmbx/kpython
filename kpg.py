# This module contains code that manages Postgres connections.

from kbase import *
from pyPgSQL import PgSQL
import pgdb

# pyPgSQL API reminder:
# - The connection object supports the functions commit(), rollback() and
#   close(). The functions commit() and rollback() can be called many times
#   without causing an error.
# - The cursor object has the attribute 'rowcount' which contains the number of
#   rows returned by the last statement executed.
# - The cursor object has the method fetchone() which returns a single row of
#   results or 'None' if there are no more results.
# - The row object can be indexed by column number or by column name.
# - Do not use PgSQL.PgQuoteBytea(). It doesn't work.

# This function returns a connection object for the Postgres database specified.
def open_pg_conn(database, host=None, port=None, user=None, password=None):
    return PgSQL.connect(database=database, port=port, host=host, user=user, password=password)
    
# This function opens a transaction if no transaction is currently open,
# executes the statement specified and returns the cursor containing the results
# of the statement. The transaction is kept open after the statement has been
# executed. It must be rolled back or commited manually. Note that doing either
# of these actions invalidates the cursor returned by this function. In other
# words, it is not possible to have a valid cursor without having also an open
# transaction. Hence, try not to forget to commit the transaction after each
# statement.
def exec_pg_query(conn, *query):
    cur = conn.cursor()
    cur.execute(*query)
    return cur

# This function does the same thing as exec_pg_query but also automatically rollbacks
# on exception.
def exec_pg_query_rb_on_except(conn, *query):
    try:
         return exec_pg_query(conn, *query)
    except Exception, e:
        conn.rollback()
        raise e

# This function does a select query, gets the returned result, rollbacks and returns the data.
# CAUTION: use for small queries only!
def exec_pg_select_rb(conn, *query):
    try:
        cur = exec_pg_query(conn, *query)
        t = cur.fetchall()
        conn.rollback()
        return t

    except Exception, e:
        conn.rollback()
        raise e

# This function escapes a bytea string. Note that the bytea string returned will
# be enclosed within E' and ', e.g. E'mybytea'.
def escape_pg_bytea(bytea):
    return "E'" + pgdb.escape_bytea(bytea) + "'"

# This function unescapes a bytea string returned by Postgres.
def unescape_pg_bytea(bytea):
    return pgdb.unescape_bytea(bytea)

# This function escapes a textual string. Note that the textual string returned
# will be enclosed within single quotes, e.g. 'mystring'.
def escape_pg_string(string):
    return "'" + pgdb.escape_string(string) + "'"

# This function checks that parameter is a number, and then converts it to a string.
def ntos(n):
    try:
        s = str(abs(n))
        if s.isdigit(): return str(n)
        raise
    except:
        raise Exception("Parameter is not a number: '%s'" % ( str(n) ) )

# This function checks if table has at least one matching field=value row.
def is_in_pg_table(db, table_name, field_name, value):
    cur = exec_pg_query(db, "SELECT %s FROM %s WHERE %s = %s" % \
                            (field_name, table_name, field_name, escape_pg_string(value)))
    return (cur.fetchone() != None)

# Check if database exists in database.
def is_pg_database(db, database_name):
    return is_in_pg_table(db, "pg_database", "datname", database_name)

# Check if table exists in database.
def is_pg_table(db, table_name):
    return is_in_pg_table(db, "pg_tables", "tablename", table_name)

# Check if role exists in database.
def is_pg_role(db, role_name):
    return is_in_pg_table(db, "pg_roles", "rolname", role_name)

# Check if language exists in database.
def is_pg_lang(db, lang_name):
    return is_in_pg_table(db, "pg_language", "lanname", lang_name)

# Check if user exists in database.
def is_pg_user(db, user_name):
    return is_in_pg_table(db, "pg_user", "usename", user_name)

# Check if type exists in database.
def is_pg_type(db, type_name):
    return is_in_pg_table(db, "pg_type", "typname", type_name)

# Check if index exists in database.
def is_pg_index(db, index_name):
    return is_in_pg_table(db, "pg_indexes", "indexname", index_name)

