import mysql.connector

###################################
## Database connection constants ##
###################################

DB_CONNECTION = {
    'host': 'localhost',
    'database': 'my_db',
    'user':	 'root',
    'password': 'pakistan'
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
    parent_folders = path.split('/')

    print("first is " + parent_folders[0])
    print("second is " + parent_folders[1])
    if len(parent_folders) <= 1:  # no slash in path
        return False
    elif len(parent_folders) >= 2:
        find_recursive(path, name, [])


def find_recursive(path, name, parent_ids):
    run_query("SELECT * FROM File")

    parent_folders = path.split('/')
    print(len(parent_folders))

    if len(parent_folders) <= 1: # no slashes in path
        response = run_query("SELECT name FROM File WHERE type = 'reg', name = '" + name
                             + "', parent = " + parent_ids[len(parent_ids) - 1])

        if len(response) > 0:
            print(path + '/' + name)
            return True
    elif len(parent_folders) == 2:
        response = run_query("SELECT ID FROM File WHERE type = 'dir', name = '" + parent_folders[1]
                             + "', parent = " + parent_ids[len(parent_ids) - 1])

        if len(response) > 0:
            find_recursive("", name, parent_folders + [response[0][0]])
            return True

    else:
        response = run_query("SELECT ID, name FROM File WHERE type = 'dir', name = '" + parent_folders[0]
                             + "', parent = " + parent_ids[len(parent_ids) - 1])

        if len(response) == 0:
            return False
        else:
            shortened_path = "/".join(parent_folders.slice(1, len(parent_folders), 1))  # remove top folder
            find_recursive(shortened_path, name, parent_ids + [response[0][0]])
            return


connection = mysql.connector.connect(**DB_CONNECTION)


# Testing code (need to impliment a loop asking for user input)
try:
    print(ls(True))
    print(cd('home/bob/../root'))
    print(ls(True))
    print(find('/file/hello', 'bash'))
finally:
    connection.close()