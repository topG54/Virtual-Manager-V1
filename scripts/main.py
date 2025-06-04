import cmd
import os
import sqlite3

# Path to the directory containing this script
SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(SCRIPTS_DIR, "..", "vm.db")
DB_PATH = os.path.abspath(DB_PATH)

class Virtual_Manager(cmd.Cmd):
    intro = 'Virtual Manager v1. Type help to list commands'
    prompt = '[vm]> '

    def do_exit(self, arg):
        '''exits the shell'''
        print('Goodbye')
        return True


def init_db():
    if os.path.exists(DB_PATH):
        print('database already exists. delete database before init')
        return
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE Nodes (
              id INTEGER PRIMARK KEY AUTOINCREMENT,
              title TEXT NOT NULL,
              category TEXT NOT NULL,
              parent_id INTEGER,
              status TEXT CHECK(category IN ('project', 'routine', 'guide', 'todo', )),
              tags JSON DEFAULT 'open',
              priority_group INTEGER,
              content TEXT,

              
              
              
              
              
              
              
              
              
              
              

              
              
              
              )

    ''')
    







if __name__ == '__main__':
    vm = Virtual_Manager()
    vm.cmdloop()
