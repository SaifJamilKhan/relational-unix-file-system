import mysql.connector

from datetime import datetime

###################################
## Database connection constants ##
###################################

DB_CONNECTION = {
    'host': 'localhost',
    'database': 'my_db',
    'user':	 'root',
    'password': 'password'
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
        print('\n'.join(child.full_ls_format() for child in children))
    print('\t'.join(child.name for child in children))


def pwd():
    pwd_fileID = run_query('SELECT * FROM PWD')[0][0]
    pwd_path = run_query('SELECT name FROM File WHERE ID=' + str(pwd_fileID))[0][0]
    paths = get_parent_path(pwd_fileID)
    print(pwd_path)


def cd(destination):
    global path_id, path_name

    if destination.startswith("../"):
        destination, path_id, path_name = trim_start_path(destination)
        if len(destination) == 0:
            run_query("UPDATE PWD SET DIR_ID = '" + str(path_id) + "'")
            return
    else:
        path_id, path_name = find_current_dir_id()

    if not destination.startswith("/"):
        destination = "/" + destination

    names = destination.split('/')
    names = names[1:]  # If the path begins with a slash, the first child is an empty string

    for i in range(len(names)):
        find_child = run_query("SELECT ID, name from File WHERE parent = '" + str(path_id) + "' AND name = '" + names[i]
                               + "' AND type = 'dir'")
        if len(find_child) == 0:
            print("Invalid Path")
            return
        path_id = find_child[0][0]
    run_query("UPDATE PWD SET DIR_ID = '" + str(path_id) + "'")
    pwd()
    return


def find(path, name):
    parent_folders = path.split('/')

    if len(parent_folders) <= 1:  # no slash in path
        return False
    elif len(parent_folders) >= 2:
        if path.startswith("/"):
            path_id, path_name = find_current_dir_id()
            find_recursive(path, name, [path_id], [path_name])
        elif path.startswith("../"):
            start_path, start_path_id, start_path_name = trim_start_path(path)
            find_recursive("/" + start_path, name, [start_path_id], [start_path_name])
        else:
            path_id, path_name = find_current_dir_id()
            find_recursive("/" + path, name, [path_id], [path_name])


### Helpers
def get_parent_path(pwd_fileID):
    if (pwd_fileID == 0):  # root folder
        return ''
    else:
        pwd_parent_id = run_query('SELECT parent FROM File WHERE ID=' + str(pwd_fileID))[0][0]
        pwd_parent_name = run_query('SELECT name from File WHERE ID=' + str(pwd_parent_id))[0][0]

        if (pwd_parent_name != '/'):
            return get_parent_path(pwd_parent_id) + '/' + pwd_parent_name
        else:
            return pwd_parent_name


def trim_start_path(path):
    pwd_file_id, _ = find_current_dir_id()

    while path.startswith("../"):
        parent_query = run_query("SELECT parent FROM File WHERE ID ='" + str(pwd_file_id) + "'")
        if len(parent_query) == 0:
            print("Invalid Path - Trim")
            return

        pwd_file_id = parent_query[0][0]
        path = path[3:]
    parent_name_query = run_query("SELECT name FROM File WHERE ID='" + str(pwd_file_id) + "'")
    return path, pwd_file_id, parent_name_query[0][0]


def find_recursive(path, name, parent_ids, parent_names):
    parent_folders = path.split('/')

    if len(parent_folders) <= 1:  # no slashes in path
        find_in_directory(name, parent_ids[-2], "/" + '/'.join(parent_names))
    else:
        response = run_query("SELECT ID, name FROM File WHERE type = 'dir' AND name = '" + parent_folders[1]
                             + "'AND parent = " + str(parent_ids[-1]))

        if len(response) <= 0:
            print("Invalid Path")
            return False
        else:
            shortened_path = ""
            if len(parent_folders) > 2:
                shortened_path = "/".join(parent_folders.slice(1, len(parent_folders), 1))  # remove top folder
            find_recursive(shortened_path, name, parent_ids + [response[0][0]], parent_names + [response[0][1]])
            return True


def find_in_directory(name, parent_id, path):
    file_search = run_query("SELECT name FROM File WHERE name = '" + name
                         + "' AND parent = '" + str(parent_id) + "'")

    if len(file_search) > 0:
        print(path + '/' + name)

    folder_search = run_query("SELECT ID, name FROM File WHERE type = 'dir' AND parent = '" + str(parent_id) + "'")

    if len(folder_search) > 0:
        for i in range(len(folder_search)):
            folder_id = folder_search[i][0]
            folder_name = folder_search[i][1]
            find_in_directory(name, folder_id, path + '/' + folder_name)


def find_current_dir_id():
    root_id = run_query('SELECT DIR_ID FROM PWD')[0][0]
    name = run_query("SELECT name FROM FILE WHERE ID = '" + str(root_id) + "'")[0][0]
    return root_id, name


connection = mysql.connector.connect(**DB_CONNECTION)


# Testing code (need to impliment a loop asking for user input)
try:
    path = 'home/root/.bashrc'
    print("cd: ", cd(path))
    print(ls(True))
    # print(cd('home/bob/../root'))
    print(ls(True))
    print(find('/file/hello', 'bash'))
    user_input = input()
    while not user_input.startswith('exit'):
        if user_input.startswith("pwd"):
            pwd()
        elif user_input.startswith("ls"):
            ls()
        elif user_input.startswith("cd"):
            params = user_input.split(" ")
            cd(params[1])
        elif user_input.startswith("find"):
            params = user_input.split(" ")
            find(params[1], params[2])
        user_input = input()

finally:
    connection.close()
