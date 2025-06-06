import cmd
import os
import sqlite3
import shlex
import json
import itertools

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

RED     = "\033[0;31m"
GREEN   = "\033[0;32m"
YELLOW  = "\033[0;33m"
BLUE    = "\033[0;34m"
MAGENTA = "\033[0;35m"
CYAN    = "\033[0;36m"
RESET   = "\033[0m"


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
        print(f'\'{line}\' is not a recognised command. type help to list commands.')

    def do_exit(self, arg):
        '''exits the shell'''
        print('goodbye')
        return True
    
    def do_init_db(self, arg):
        '''initialises the empty database if it doesnt exist'''
        if os.path.exists(DB_PATH):
            print('database already exists')
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
        '''shows all nodes in the database'''
        if not os.path.exists(DB_PATH):
            print("database not found.")
            return

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT * FROM nodes")
        rows = c.fetchall()
        conn.close()

        if not rows:
            print("no nodes found.")
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
            print(f"priority group: {row[6]}")
            print(f"content: {row[7]}")
            print(f"created at: {row[8]}")
            print(f"last updated: {row[9]}")

    def do_tree(self, arg):
        '''gives a tree view of all nodes starting from root node with id specified
        if no argument id given, entire tree is shown'''
        
        if not os.path.exists(DB_PATH):
            print("database not found.")
            return
        
        if arg:
            if not arg.isnumeric():
                print('invalid id')
                return
            return show_tree(int(arg))
        return show_tree(None)

    def do_inspect(self, arg):
        '''show details of a node by id'''

        if not os.path.exists(DB_PATH):
            print("database not found.")
            return

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

    def do_priority(self,arg):
        '''format: priority <id> <change by>
        changes the priority group of node by specified amount (can be negative)'''

        if not os.path.exists(DB_PATH):
            print("database not found.")
            return

        try:
            id, change_by = shlex.split(arg)
            change_by = int(change_by)
        except Exception as e:
            print('invalid format. format: priority <id> <change by>', e)
            return

        priorities = []
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        parent = c.execute('''SELECT parent_id FROM nodes WHERE id = ?''', (id,)).fetchone()
        parent = parent[0] if parent else None
        nodes = c.execute('''SELECT id, priority_group FROM nodes WHERE parent_id = ?''', (parent,)).fetchall()

        priorities = [i[1] for i in nodes]
        children = [i[0] for i in nodes]
        priorities = sorted(set(priorities)) # removes duplicates

        priority_lookup = dict(nodes) # to find original priority from id

        new_priorities = {}
        for i in range(len(priorities)):
            new_priorities[priorities[i]] = i
        #now we have all priorities one away from each other

        for child in children:
            original = priority_lookup[child]
            new = int(new_priorities[original])
            if child == int(id.strip()):
                new += change_by
            c.execute('''UPDATE nodes SET priority_group = ? WHERE id = ?''', (int(new), int(child)))
            conn.commit()
        conn.close()
        print('success')

    def do_search(self, arg):
        """format: search [[key, value], [key, value], ...]
        options: id, title, category, status
        example: search tag research category task"""
        if not os.path.exists(DB_PATH):
            print("database not found.")
            return

        args = shlex.split(arg)
        if len(args) % 2 != 0:
            print("invalid format. format: search [[key, value], [key, value], ...]" \
            "example: search tag research category task")
            return

        filters = {}
        for i in range(0, len(args), 2):
            key = args[i].lower()
            value = args[i+1]
            filters[key] = value

        query = "SELECT * FROM nodes WHERE 1=1"
        params = []

        if "id" in filters:
            query += " AND id = ?"
            params.append(filters["id"])

        if "title" in filters:
            query += " AND title LIKE ?"
            params.append(f"%{filters['title']}%")

        if "tags" in filters:
            query += " AND json_extract(tags, '$') LIKE ?"
            params.append(f"%{filters['tags']}%")

        if "category" in filters:
            query += " AND category = ?"
            params.append(filters["category"])

        if "status" in filters:
            query += " AND status = ?"
            params.append(filters["status"])

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute(query, params)
        results = c.fetchall()
        conn.close()

        if not results:
            print("no nodes found.")
            return

        for row in results:
            output = ''
            output += f"{row[0]}-{row[2]}: {row[1]}  "
            if "status" in filters:
                output +=  f"status: {row[4]}, "
            if "tags" in filters:
                tags = json.loads(row[5]) if row[5] else []
                output += f"tags: {tags}, "
            print(output)

    def do_delete(self, arg):
        '''deletes a node by id.
        format: delete <id>'''
        
        if not os.path.exists(DB_PATH):
            print("database not found.")
            return
        
        try:
            id = int(shlex.split(arg)[0])
        except:
            print('invalid format, format: delete <id>') 
            return
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        print('deleting node:')
        self.do_inspect(self, str(id))
        node = c.execute('''SELECT id FROM nodes WHERE id = ?''', (id,)).fetchone()
        if not node:
            print('node does not exist')
            return
        c.execute('''DELETE FROM nodes WHERE id = ?''', (id,))
        conn.commit()
        conn.close()
        print('success')

    def do_edit(self, arg):
        """format: edit <id> [[key, new value], [key, new value], ...]
        options: title, parent, status, content
        example: edit 3902 status deprecated title \"new title\"
        please use quotes for new values with spaces"""
        if not os.path.exists(DB_PATH):
            print("database not found.")
            return

        args = shlex.split(arg)
        try:
            id = int(args[0])
            args = args[1:]
            if len(args) % 2 != 0:
                raise Exception
        except:
            print("invalid format. format: edit <id> [[key, new value], [key, new value], ...]" \
            "example: edit 3902 status deprecated title Y")
            return

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        node = c.execute('''SELECT id FROM nodes WHERE id = ?''', (id,)).fetchone()
        if not node:
            print('node does not exist')
            return

        filters = {}
        for i in range(0, len(args), 2):
            key = args[i].lower()
            value = args[i+1]
            filters[key] = value

        params = []
        updates = ''
        if "title" in filters:
            updates += "title = ?, "
            params.append(filters["title"])

        if "parent" in filters:
            updates += "parent_id = ?, "
            params.append(filters["parent"])

        if "status" in filters:
            updates += "status = ?, "
            params.append(filters["status"])

        if "content" in filters:
            updates += "content = ?, "
            params.append(filters["content"])
        
        params.append(id)
        query = f"UPDATE nodes SET {updates[:-2]} WHERE id = ?"
        
        try:
            c.execute(query, params)
            conn.commit()
            conn.close()
        except Exception as e:
            print('error: ', e)
        print('sucsess')





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
    
    def print_tree_helper(cur_id, preceeding_string=''):
        children = parent_to_child.get(cur_id, [])
        if not children:
            return
        children.sort(key=lambda x: x[4], reverse=True)
        children = [list(group) for key, group in itertools.groupby(children, key=lambda x: x[4])] # groups into priority groups 2d list
        for priority_group in children:
            for child in range(len(priority_group)):
                if len(priority_group) == 1: #single element
                    connector = '    ' + '['
                elif child == 0 and len(priority_group) > 1: # first element
                    connector = '    ' + '┌' 
                elif child == len(priority_group)-1 and len(priority_group) > 1: # last element
                    connector = '    ' + '└'
                else: #middle element
                    connector = '    ' + '├'

                category = priority_group[child][2]
                match category:
                    case 'project':
                        colour = GREEN
                    case 'task':
                        colour = RED
                    case 'recurring':
                        colour = YELLOW
                    case 'todo':
                        colour = CYAN
                    case 'note':
                        colour = MAGENTA
                    case _:
                        colour = BLUE
                print(preceeding_string + connector + f'{priority_group[child][0]}-{colour}{priority_group[child][2]}{RESET}: {priority_group[child][1]}')

                if child == len(priority_group) - 1: # secondary nodes after last element have no added '│'
                    print_tree_helper(priority_group[child][0], preceeding_string + '    ')
                else:
                    print_tree_helper(priority_group[child][0], preceeding_string + '    │')
                

                

                

    
    print_tree_helper(root_id)


def get_attribute(attr_name, optional=False, valid_attrs=[], multiple=False):
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



