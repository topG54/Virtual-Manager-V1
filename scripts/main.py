import cmd
import os
import sqlite3
import shlex
import json

'''
            case 'routine':
                add_routine(title)
            case 'guide':
                add_guide(title)
            case 'todo':
                add_todo(title)
            case 'repository':
                add_repository(title)
            case 'task':
                add_task(title)
            case 'note':
                add_note(title)
            case 'checklist':
                add_checklist(title)
'''

CATEGORIES = ['project', 'recurring', 'guide', 'todo', 'repository', 'task', 'note', 'checklist']
STATUS_OPTIONS = ['open', 'closed', 'deprecated']
DEFAULT_TAGS = []

# Path to the directory containing this script
SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(SCRIPTS_DIR, "..", "vm.db")
DB_PATH = os.path.abspath(DB_PATH)

class Virtual_Manager(cmd.Cmd):
    intro = 'Virtual Manager v1. Type help to list commands.'
    prompt = '[vm]> '

    def default(self, line):
        print(f'\'{line}\' is not a recognised command. Type help to list commands.')

    def do_exit(self, arg):
        '''exits the shell'''
        print('Goodbye')
        return True
    
    def do_init_db(self, arg):
        '''initialises the empty database if it doesnt exist'''
        if os.path.exists(DB_PATH):
            print('database already exists. delete database before init')
            return
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        #nodes table
        c.execute('''
            CREATE TABLE nodes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                category TEXT NOT NULL CHECK(category IN ('project', 'recurring', 'guide', 'todo', 'task', 'note')),
                parent_id INTEGER,
                status TEXT DEFAULT NULL CHECK(status IN ('open', 'closed', 'deprecated') OR status IS NULL),
                tags JSON DEFAULT '[]',
                priority_group INTEGER DEFAULT 0,
                content TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                last_updated TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(parent_id) REFERENCES nodes(id)
                )
        ''')
        
        #dependencies table
        c.execute('''
            CREATE TABLE dependencies (
                dependent INTEGER NOT NULL,
                dependency INTEGER NOT NULL,
                FOREIGN KEY(dependent) REFERENCES nodes(id), 
                FOREIGN KEY(dependency) REFERENCES nodes(id),
                PRIMARY KEY(dependent, dependency)
                )
        ''')
        conn.commit()
        conn.close()
        print('db init success')

    def do_delete_db(self, arg):
        '''deletes the database if it exists'''
        if os.path.exists(DB_PATH):
            if input('DELETE THE DATABASE? (y/n): ').lower() == 'y':
                os.remove(DB_PATH)
                print('success')
        else:
            print('database does not exist')

    def do_add(self, arg):
        '''adds a node in the database
        format: add <category> <title>
        afterwards, you will get asked for attributes
        it will ask for another attribute repeatedly
        just press enter if you dont want to add any more of that atribute'''
        args = shlex.split(arg)
        if len(args) < 2:
            print('invalid format. format: add <category> <title>')
            return
        title = ' '.join(args[1:])
        match args[0]:
            case 'project':
                add_project(title)
            case 'recurring':
                add_recurring(title)
            case 'todo':
                add_todo(title)
            case 'task':
                add_task(title)
            case 'note':
                add_note(title)
            case _:
                print("invalid category. categories: project, recurring, guide, todo, task, note, checklist, repository.")

    def do_show_all(self, arg):
        '''Shows all nodes in the database'''
        if not os.path.exists(DB_PATH):
            print("Database not found.")
            return

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT * FROM nodes")
        rows = c.fetchall()
        conn.close()

        if not rows:
            print("No nodes found.")
            return

        for row in rows:
            print("=" * 40)
            print(f"id: {row[0]}")
            print(f"title: {row[1]}")
            print(f"category: {row[2]}")
            print(f"parent id: {row[3]}")
            print(f"status: {row[4]}")
            tags = json.loads(row[5]) if row[5] else []
            print(f"tags: {tags}")
            print(f"priority Group: {row[6]}")
            print(f"content: {row[7]}")
            print(f"created At: {row[8]}")
            print(f"last Updated: {row[9]}")

    def do_tree(self, arg):
        '''gives a tree view of all nodes starting from root node with id specified
        if no argument id given, entire tree is shown'''
        if arg:
            if not arg.isnumeric():
                print('invalid id')
                return
            return show_tree(int(arg))
        return show_tree(None)

    def do_inspect(self, arg):
        '''show details of a node by id'''
        if not arg.isdigit():
            print('invalid id')
            return
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT * FROM nodes WHERE id=?", (int(arg),))
        row = c.fetchone()
        conn.close()
        if not row:
            print("Node not found")
            return
        print(json.dumps({
            "id": row[0],
            "title": row[1],
            "category": row[2],
            "parent_id": row[3],
            "status": row[4],
            "tags": json.loads(row[5] or "[]"),
            "priority_group": row[6],
            "content": row[7],
            "created_at": row[8],
            "last_updated": row[9],
        }, indent=2))












def show_tree(root_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT id, title, category, parent_id, priority_group FROM nodes ')
    nodes = c.fetchall()
    conn.close()

    parent_to_child = {}
    for node in nodes:
        parent = node[3]
        parent_to_child.setdefault(parent, []).append(node)
    
    def print_tree_helper(cur_id, indent):
        children = parent_to_child.get(cur_id, [])
        if not children:
            return
        children.sort(key=lambda x: x[4])
        for child in children:
            print('  ' * indent + f'{child[0]}_{child[2]}_{child[1]}')
            print_tree_helper(child[0], indent+1)
    
    print_tree_helper(root_id, 1)


def get_attribute(attr_name, optional = False, valid_attrs = [], multiple = False):
    print('\tenter to end. type reset to reset entry.')
    if optional:
        prompt = f'{attr_name}(optional): '
    else:
        prompt = f'{attr_name}: '

    attr_list = []

    while True:
        attr = input(f'\t{prompt}').strip().lower()
        if not attr:
            if not optional and not attr_list:
                print('\tthis attribute is not optional')
            elif multiple:
                return attr_list
            elif attr_list:
                return attr_list[0]
            else:
                return None
            
        if (not attr in valid_attrs) and valid_attrs:
            print('\tinvalid entry. valid: ' + ', '.join(valid_attrs))

        if attr == 'reset':
            attr_list = []
        else:
            if not multiple and attr_list:
                print('\tyou cannot make multiple entries')
            elif attr:
                attr_list.append(attr)

        print('\tentered: ' + ', '.join(attr_list))


def insert_node(title, category, parent_id=None, status=None, tags=None, content=None):
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('''
            INSERT INTO nodes (title, category, parent_id, status, tags, content)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            title,
            category,
            parent_id,
            status,
            json.dumps(tags or []),
            content
        ))
        conn.commit()
        conn.close()
        print('success')
    except Exception as e:
        print('database insertion failed:', e)


def add_project(title):
    parent_id = get_attribute('parent', optional=True)
    tags = get_attribute('tags', optional=True, multiple=True)
    status = get_attribute('status', optional=True, valid_attrs=STATUS_OPTIONS)
    if not status:
        status = 'open'
    print(f"creating project...\ntitle: {title}\nparent: {parent_id}\ntags: {tags}\nstatus: {status}")

    insert_node(title, 'project', parent_id=parent_id, status=status, tags=tags)


def add_recurring(title):
    parent_id = get_attribute('parent', optional=True)
    status = get_attribute('status', optional=True, valid_attrs=STATUS_OPTIONS)
    if not status:
        status = 'open'
    print(f"creating recurring...\ntitle: {title}\nparent: {parent_id}\nstatus: {status}")

    insert_node(title, 'recurring', parent_id=parent_id, status=status)


def add_todo(title):
    parent_id = get_attribute('parent', optional=True)
    status = get_attribute('status', optional=True, valid_attrs=STATUS_OPTIONS)
    if not status:
        status = 'open'
    print(f"creating todo...\ntitle: {title}\nparent: {parent_id}\nstatus: {status}")

    insert_node(title, 'todo', parent_id=parent_id, status=status)


def add_task(title):
    parent_id = get_attribute('parent', optional=False) #shld always be under something
    tags = get_attribute('tags', optional=True, multiple=True)
    status = get_attribute('status', optional=True, valid_attrs=STATUS_OPTIONS)
    content = get_attribute('content', optional=True)
    if not status:
        status = 'open'
    print(f"creating task...\ntitle: {title}\nparent: {parent_id}\ntags: {tags}\nstatus: {status}\ncontent: {content}")
    
    insert_node(title, 'task', parent_id=parent_id, status=status, tags=tags, content=content)


def add_note(title):
    parent_id = get_attribute('parent', optional=False) #shld always be under something
    content = get_attribute('content', optional=True)
    print(f"creating note...\ntitle: {title}\nparent: {parent_id}\ncontent: {content}")

    insert_node(title, 'note', parent_id=parent_id, content=content)







if __name__ == '__main__':
    vm = Virtual_Manager()
    vm.cmdloop()
