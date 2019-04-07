import mysql.connector

from datetime import datetime

###################################
## Database connection constants ##
###################################

DB_CONNECTION = {
    'host': 'localhost',
    'database': 'my_db',
    'user':	 'root',
    'password': 'pakistan'
}


class File:
    def __init__(self, file_tuple):
        self.ID, self.type, self.parent, self.name, self.uid, self.gid, \
            self.size, self.perms, self.atime, self.mtime, self.ctime = file_tuple

    def full_ls_format(self):
        children = [File(tup) for tup in run_query('SELECT * FROM File WHERE parent = {}'.format(self.ID))]

        if self.type == 'dir':
            num_dir_children = len(list(child for child in children if child.type in ('dir', 'slnk', 'hlnk'))) + 2
            file_size = len(children) + 2
        else:
            num_dir_children = 1
            file_size = self.size

        last_modified_time = datetime.fromtimestamp(self.mtime)
        time_str = datetime.strftime(last_modified_time, '%b %w %H:%M:%S')

        return '{}{} {} {}\t{}\t{} {} {}'.format(
                'd' if self.type == 'dir' else '-', self.perms, num_dir_children, self.uid, self.gid,
                file_size, time_str, self.name
        )


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
    children = run_query('SELECT * FROM File WHERE parent = (SELECT * FROM PWD)')
    children = [File(child) for child in children]
    if l_flag:
        return '\n'.join(child.full_ls_format() for child in children)
    return '/t'.join(child.name for child in children)

def pwd():
    pwd_fileID = run_query('SELECT * FROM PWD')[0][0]
    pwd_path = run_query('SELECT name FROM File WHERE ID=' + str(pwd_fileID))[0][0]
    paths = get_parent_path(pwd_fileID)
    return pwd_path if pwd_path=='/' else paths + '/' + str(pwd_path)

def get_parent_path(pwd_fileID):
    if(pwd_fileID == 0): #root folder
        return ''
    else:
        pwd_parent_id = run_query('SELECT parent FROM File WHERE ID=' + str(pwd_fileID))[0][0]
        pwd_parent_name = run_query('SELECT name from File WHERE ID=' + str(pwd_parent_id))[0][0]
        
        if(pwd_parent_name != '/'):
            return get_parent_path(pwd_parent_id) + '/' + pwd_parent_name 
        else:
            return pwd_parent_name


def cd(path):
    return ''

def find(path, name):
    parent_folders = path.split('/')

    print("first is " + parent_folders[0])
    print("second is " + parent_folders[1])
    if len(parent_folders) <= 1:  # no slash in path
        return False
    elif len(parent_folders) >= 2:
        find_recursive(path, name, [], [])


def find_recursive(path, name, parent_ids, parent_names):
    run_query("SELECT * FROM File")

    parent_folders = path.split('/')
    print(len(parent_folders))

    if len(parent_folders) <= 1: # no slashes in path
        find_in_directory(name, parent_ids[len(parent_ids) - 1], "/" + "/".join(parent_names))
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

def find_in_directory(name, parent_id, path):
    response = run_query("SELECT name FROM File WHERE type = 'reg', name = '" + name
                         + "', parent = " + parent_id)

    if len(response) > 0:
        print(path + '/' + name)
        return True

connection = mysql.connector.connect(**DB_CONNECTION)


# Testing code (need to impliment a loop asking for user input)
try:
    print(ls(True))
    print(cd('home/bob/../root'))
    print(ls(True))
    print(find('/file/hello', 'bash'))
finally:
    connection.close()