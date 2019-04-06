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
        return '\n'.join(child.full_ls_format() for child in children)
    return '/t'.join(child.name for child in children)

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