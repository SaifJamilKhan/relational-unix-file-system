import mysql.connector

from datetime import datetime
from getpass import getpass

###################################
## Database connection constants ##
###################################

DB_CONNECTION = {
    'host': 'localhost',
    'database': 'unix',
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

def resolve_link(file_id):
    while True:
        lnk = run_query('SELECT * FROM File WHERE ID in (SELECT target FROM SoftLink WHERE source = {})'.format(file_id))
        if not lnk:
            raise Exception('Bad softlink')
        lnk = File(lnk[0])
        if lnk.type != 'slnk':
            return lnk

def validate_path(path):
    if path.startswith('/'):
        current_dir = 0
    else:
        current_dir = run_query('SELECT * FROM PWD')[0][0]
    for name in path.split('/'):
        if name == '..':
            parent = run_query('SELECT parent FROM File WHERE ID = {}'.format(current_dir))
            if not parent:
                raise Exception('Bad path')
            current_dir = parent[0][0]
        elif name in ('.', ''):
            pass
        else:
            chosen = run_query('SELECT * FROM File WHERE parent = {} AND name = "{}"'.format(current_dir, name))
            if not chosen:
                raise Exception('Bad path')
            chosen = File(chosen[0])
            if chosen.type == 'slnk':
                chosen = resolve_link(chosen.ID)
            current_dir = chosen.ID
    return current_dir

def login():
    while True:
        username = input('username: ')
        password = input('password: ')

        user = run_query('SELECT ID FROM User WHERE ID = "{}" AND pswd = "{}"'.format(username, password))
        if user:
            return user[0][0]

### Utilities

def ls(l_flag=False, dir_id=None, path=None):
    if dir_id is None:
        dir_id = run_query('SELECT * FROM PWD')[0][0]

    file = File(run_query('SELECT * FROM File WHERE ID = {}'.format(dir_id))[0])
    if path:
        file.name = path
    children = [file]
    if file.type == 'dir':
        children = run_query('SELECT * FROM File WHERE parent = {}'.format(dir_id))
        children = [File(child) for child in children]

    if l_flag:
        print('\n'.join(child.full_ls_format() for child in children))
        return 0
    print('  '.join(child.name for child in children))
    return 0

def cd(path):
    file_id = validate_path(path)
    file_type = run_query('SELECT type FROM File WHERE ID = {}'.format(file_id))[0][0]
    if file_type != 'dir':
        raise Exception('Cannot cd to {}, not a directory'.format(path))
    run_query('UPDATE PWD SET dir_id = {}'.format(file_id))
    return 0

def find(path, name):
    file_id = validate_path(path)

    dirs = [(file_id, '' if path.startswith('/') else path)]
    found = []
    while dirs:
        dir_id, dir_path = dirs.pop()
        for tup in run_query('SELECT * FROM File WHERE parent = {}'.format(dir_id)):
            child = File(tup)
            # Add child to found if name matches
            if name in child.name:
                found.append('/'.join([dir_path, child.name]))
            # Follow symlinks
            if child.type == 'slnk':
                target = resolve_link(child.ID)
                dirs.append((target.ID, '/'.join([dir_path, child.name])))
            elif child.type == 'dir':
                dirs.append((child.ID, '/'.join([dir_path, child.name])))
    
    for path in found:
        dir_id = validate_path(path)
        print(path)
        ls(True, dir_id)
        print()
    return 0

def pwd():
    current_dir = File(run_query('SELECT * FROM File WHERE ID = (SELECT * FROM PWD)')[0])
    path = current_dir.name
    while current_dir.ID != 0:
        current_dir = File(run_query('SELECT * FROM File WHERE ID = {}'.format(current_dir.parent))[0])
        path = current_dir.name + '/' + path
    return path.replace('//', '/')


## Main loop

def command_loop():
    cmd = input('{} {} $ '.format(user, pwd()))
    words = cmd.split()
    try:
        if words[0] == 'pwd':
            print(pwd())
        elif words[0] == 'ls':
            ls(len(words) == 2 and words[1] == '-l')
        elif words[0] == 'cd':
            cd(words[1])
        elif words[0] == 'find':
            find(words[1], words[2])
        elif words[0] == 'exit':
            return False
    except Exception as e:
        print(e)
    return True


connection = mysql.connector.connect(**DB_CONNECTION)

# Testing code (need to impliment a loop asking for user input)
try:
    user = login()
    while command_loop():
        pass
finally:
    connection.close()
