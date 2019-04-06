import mysql.connector

###################################
## Database connection constants ##
###################################

DB_CONNECTION = {
    'host': 'localhost',
    'database': 'my_db',
    'user':	 'root',
    'password': 'password'
}


### Runs a query on the database and returns results if any
def run_query(query):
    results = None
    cursor = connection.cursor()
    try:
        cursor.execute(query)
        if cursor.with_rows:
            results = cursor.fetchall()
    finally:
       cursor.close()
    return results or []


### Utilities

def ls(l_flag=False):
    return ''

def cd(path):
    return ''

def find(path, name):
    run_query("SELECT * FROM File")

    return ''


connection = mysql.connector.connect(**DB_CONNECTION)


# Testing code (need to impliment a loop asking for user input)
try:
    print(ls(True))
    print(cd('home/bob/../root'))
    print(ls(True))
    print(find('..', 'bash'))
finally:
    connection.close()