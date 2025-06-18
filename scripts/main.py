import cmd
import os
import sqlite3
import shlex
import json
import itertools
from peewee import *
import datetime
from playhouse.shortcuts import model_to_dict

RED     = '\033[0;31m'
GREEN   = '\033[0;32m'
YELLOW  = '\033[0;33m'
BLUE    = '\033[0;34m'
MAGENTA = '\033[0;35m'
CYAN    = '\033[0;36m'
PINK    = '\033[0;201m'
WHITE   = '\033[0;37m'
RESET   = '\033[0m'

RESET_TEXT_COLOUR = '\033[39m'


CATEGORIES = ['project', 'recurring', 'manual', 'todo', 'task', 'note', 'folder']
STATUS_OPTIONS = ['open', 'closed', 'deprecated', 'deleted']
DEFAULT_TAGS = []

# Path to the directory containing this script
SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(SCRIPTS_DIR, '..', 'vm.db')
DB_PATH = os.path.abspath(DB_PATH)
ROOT_DIR = os.path.join(SCRIPTS_DIR, '..')
ROOT_DIR = os.path.abspath(ROOT_DIR)
MIRROR = os.path.join(ROOT_DIR, 'fs_mirror')

db = SqliteDatabase(DB_PATH)

class BaseModel(Model):
    class Meta:
        database = db


class Nodes(BaseModel):
    id = AutoField()
    title = TextField()
    category = TextField()
    parent = ForeignKeyField('self', backref='children', null=True, on_delete='SET NULL')
    status = TextField(null=True, default='open')
    priority_group = IntegerField(default=0)
    created_at = DateTimeField(default = datetime.datetime.now().isoformat)
    last_updated = DateTimeField(default = datetime.datetime.now().isoformat)
    content = TextField(null=True)


class NodeTags(BaseModel):
    node = ForeignKeyField(Nodes, backref='tags', on_delete='CASCADE')
    tag = TextField()


db.connect()


class Virtual_Manager(cmd.Cmd):
    intro = 'Virtual Manager v1. Type help to list commands.'
    prompt = '[vm]> '

    def default(self, line):
        print(f'\'{line}\' is not a recognised command. type help to list commands.')

    def emptyline(self):
        pass  # Prevent repeat of last command

    def do_x(self, arg):
        '''exits the shell'''
        print('goodbye')
        return True
    
    def do_init_db(self, arg):
        '''initialises the empty database if it doesnt exist'''
        
        try:
            db.create_tables([Nodes, NodeTags])
            print('db init success')
        except Exception as e:
            print('failed: ', e)
        
    def do_delete_db(self, arg):
        '''deletes the database if it exists'''
        if os.path.exists(DB_PATH):
            if input('DELETE THE DATABASE? (y/n): ').lower() == 'y':
                db.close()
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

        if not db_existence():
            return

        args = shlex.split(arg)
        if len(args) < 2:
            print('invalid format. format: add <category> <title>')
            return
        title = ' '.join(args[1:])
        match args[0]:
            case 'project':
                n = Nodes.create(
                    title = title,
                    category = args[0],
                    parent = get_attribute('parent', optional=True),
                    status = get_attribute('status', optional=True, valid_attrs=STATUS_OPTIONS) and 'open')

                for tag in get_attribute('tags', optional=True, multiple=True):
                    NodeTags.create(node=n, tag=tag)
                    print('tag: ', tag)

            case 'recurring' | 'todo' | 'folder' | 'manual':
                n = Nodes.create(
                    title = title,
                    category = args[0],
                    parent = get_attribute('parent', optional=True),
                    status = get_attribute('status', optional=True, valid_attrs=STATUS_OPTIONS))
                
            case 'task':
                n = Nodes.create(
                    title = title,
                    category = args[0],
                    parent = get_attribute('parent', optional=False),
                    status = get_attribute('status', optional=True, valid_attrs=STATUS_OPTIONS) and 'open',
                    content = get_attribute('content', optional=True))

                for tag in get_attribute('tags', optional=True, multiple=True):
                    NodeTags.create(node=n, tag=tag)
                    print('tag: ', tag)
                
            case 'note':
                n = Nodes.create(
                    title = title,
                    category = args[0],
                    parent = get_attribute('parent', optional=False),
                    content = get_attribute('content', optional=True))

            case _:
                print('invalid category. categories: project, recurring, manual, todo, task, note, folder.')
                return

        for k, v in model_to_dict(n).items():
            if k == 'parent':
                print(f'{k}: {v and v['id']}') #handle parent == None case
            else:
                print(f'{k}: {v}')

    def do_show_all(self, arg):
        '''shows all nodes in the database'''
        
        if not db_existence():
            return

        query = prefetch(Nodes.select(), NodeTags.select())

        for node in query:
            print(f'id: {node.id}')
            print(f'title: {node.title}')
            print(f'category: {node.category}')
            print(f'status: {node.status}')
            print(f'priority group: {node.priority_group}')
            print(f'created at: {node.created_at}')
            print(f'last Updated: {node.last_updated}')
            print(f'content: {node.content}')

            print('tags: ', [tag.tag for tag in node.tags])

    def do_tree(self, arg):
        '''gives a tree view of all nodes starting from root node with id specified
        if no argument id given, entire tree is shown
        format: tree <id(optional)>'''
        
        if not db_existence():
            return
        
        if arg:
            if not arg.isnumeric():
                print('invalid id')
                return
            return show_tree(int(arg))
        return show_tree(None)

    def do_inspect(self, arg):
        '''show details of a node by id'''

        if not db_existence():
            return

        try:
            id == int(arg)
        except:
            print('invalid format. argument must be an integer')
            return

        query = prefetch(Nodes.select().where(Nodes.id == int(arg)), NodeTags.select())

        if not query:
            print('node does not exist')
            return

        for node in query:
            print(f'id: {node.id}')
            print(f'title: {node.title}')
            print(f'category: {node.category}')
            print(f'status: {node.status}')
            print(f'priority group: {node.priority_group}')
            print(f'created at: {node.created_at}')
            print(f'last Updated: {node.last_updated}')
            print(f'content: {node.content}')

            print('tags: ', [tag.tag for tag in node.tags])

    def do_priority(self,arg):
        '''format: priority <id> <change by>
        changes the priority group of node by specified amount (can be negative)'''

        if not db_existence():
            return

        try:
            id, change_by = shlex.split(arg)
            change_by = int(change_by)
            id = int(id)
        except Exception as e:
            print('invalid format. format: priority <id> <change by>', e)
            return

        priorities = []

        parent = Nodes.select(Nodes.parent_id).where(Nodes.id == id).first().parent_id

        nodes = list(Nodes.select(Nodes.id, Nodes.priority_group).where(Nodes.parent_id == parent).tuples())

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
            if child == id:
                new += change_by
            Nodes.update(priority_group = new).where(Nodes.id == child).execute()
        print('success')

    def do_search(self, arg):
        '''format: search [[key, value], [key, value], ...]
        options: id, title, category, status
        example: search tag research category task'''
        
        if not db_existence():
            return

        args = shlex.split(arg)
        if len(args) % 2 != 0:
            print('''invalid format. format: search [[key, value], [key, value], ...]
            example: search tag research category task
            you can only search one tag at a time''')
            return

        filters = {}
        for i in range(0, len(args), 2):
            key = args[i].lower()
            value = args[i+1]
            filters[key] = value
        
        conditions = True  # start with a neutral condition (like WHERE 1=1)

        if 'id' in filters:
            conditions &= (Nodes.id == int(filters['id']))

        if 'category' in filters:
            conditions &= (Nodes.category == filters['category'])

        if 'status' in filters:
            conditions &= (Nodes.status == filters['status'])

        if 'title' in filters:
            conditions &= (Nodes.title.contains(filters['title']))

        # Special case: join with tags
        query = Nodes.select().join(NodeTags, on=(Nodes.id == NodeTags.node_id), join_type=JOIN.LEFT_OUTER)

        if 'tag' in filters:
            conditions &= (NodeTags.tag.contains(filters['tag']))

        query = query.where(conditions).distinct()


        if not query:
            print('no nodes found.')
            return

        for node in query:
            output = ''
            output += f'{node.id}-{node.category}: {node.title}  '
            if 'status' in filters:
                output +=  f'status: {node.status}, '
            if 'tag' in filters:
                output += f'tags: {[tag.tag for tag in node.tags]}, '
            print(output)

    def do_delete(self, arg):
        '''deletes a node by id. 
        format: delete <id> <hard>
        example: delete 4245 hard (does hard delete)
        example delete 67943 (does soft delete)'''
        
        if not db_existence():
            return
        
        try:
            id = int(shlex.split(arg)[0])
            hard = shlex.split(arg)[1] == 'hard'
        except Exception as e:
            print('invalid format, format: delete <id> <hard>', e)
            return
        
        if hard:
            count = Nodes.delete().where(Nodes.id == id).execute()
        else:
            count = Nodes.update({Nodes.status: 'deleted'}).where(Nodes.id == id).execute() #simply marks it as such

        if not count:
            print('no nodes found')
        else:
            print('success')

    def do_edit(self, arg):
        '''format: edit <id> [[key, new value], [key, new value], ...]
        options: title, parent, status, content
        example: edit 3902 status deprecated title \'new title\'
        please use quotes for new values with spaces'''
        
        if not db_existence():
            return

        args = shlex.split(arg)

        try:
            id = int(args[0])
            updates = args[1:]
            if len(updates) % 2 != 0 or len(updates) == 0:
                raise Exception
        except Exception as e:
            print('invalid format. format: edit <id> [[key, new value], [key, new value], ...]\n' \
            'example: edit 3902 status deprecated title Y\n', e)
            return

        updates_dict = {}

        for i in range(0, len(updates), 2):
            key = updates[i].lower()
            value = updates[i+1]
            updates_dict[key] = value

        try:
            Nodes.update(updates_dict).where(Nodes.id == id).execute()
        except Exception as e:
            print('error: ', e)
        print('success')

    def do_complete(self, arg):
        '''sets node status to closed'''

        if not db_existence():
            return

        new = arg + ' status closed'
        self.do_edit(new)

    def do_push(self, arg):
        '''\'pushes\' the changes in the database to the file system mirror
        warning: all changes in mirror will be lost if not pulled first
        try to edit only one side at a time to avoid loss of data'''

        if not db_existence():
            return
        
        nodes_with_tags = prefetch(Nodes.select(), NodeTags.select())

        nodes = []
        for node in nodes_with_tags:
            tag_list = [tag.tag for tag in node.tags]
            nodes.append(list(node.__data__.values()) + [tag_list,])

        parent_to_child = {}
        for node in nodes:
            parent = node[3]
            parent_to_child.setdefault(parent, []).append(node)
        
        def helper(cur_path, cur_id):
            children = parent_to_child.get(cur_id, [])
            if not children:
                return
            
            for child in children:
                id = child[0]
                title = child[1]
                category = child[2]

                keys = ['id', 'title', 'category', 'parent_id', 'status', 'priority_group', 'created_at', 'last_updated', 'content', 'tags']
                node_dict = dict(zip(keys, child))
                content = node_dict.pop('content') or ''  # content will be separate and at the end
                output = '--vmgr\n' + json.dumps(node_dict, indent=2) + '\n\n' + content
                
                name = f'{id}_{category}_{title}'
                new_path = os.path.join(cur_path, name) #either folder or file

                if category in ['task', 'note']: #doesnt make new folder
                    with open(new_path + '.md', 'w') as f:
                        f.write(output)
                    helper(cur_path, id)
                
                else:
                    os.makedirs(new_path, exist_ok=True)
                    desc_path = os.path.join(new_path, '_description.md')
                    with open(desc_path, 'w') as f:
                        f.write(output)
                    helper(new_path, id)

        os.makedirs(MIRROR, exist_ok=True)
        try:
            helper(MIRROR, None)
            print('success')
        except Exception as e:
            print('failed', e)

    def do_pull(self, arg):
        '''if there are md files in mirror, they will be used to edit existing nodes based on id.
        new nodes will not be created, and nodes will not be deleted with this method
        format: pull <id(optional)>'''

        if not db_existence():
            return
        
        def extract_md(path):
            with open(path, 'r') as f:
                text = f.read()
                if text[:7] != '--vmgr\n':
                    return None
                metadata, content = text[7:].split('\n\n', 1)
            node_dict = json.loads(metadata)
            node_dict['content'] = content
            return node_dict

        #getting paths to all .md files
        md_paths = []
        os.makedirs(MIRROR, exist_ok=True)
        for path, dirs, files in os.walk(MIRROR):
            for file in files:
                if file[-3:] == '.md':
                    md_paths.append(os.path.join(path, file))

        for path in md_paths:
            try:
                node_dict = extract_md(path)
                if not node_dict:
                    continue
                
                Nodes.update(
                title=node_dict['title'],
                category=node_dict['category'],
                parent_id=node_dict['parent_id'],
                status=node_dict['status'],
                priority_group=node_dict['priority_group'],
                content=node_dict['content'],
                created_at=node_dict['created_at'],
                last_updated=node_dict['last_updated']
                ).where(Nodes.id == node_dict['id']).execute()

                NodeTags.delete().where(NodeTags.node_id == node_dict['id']).execute()

                new_tags = node_dict.get('tags', [])
                NodeTags.insert_many([{'node_id': node_dict['id'], 'tag': tag} for tag in new_tags]).execute()

                
            except Exception as e:
                print(f'file at {path} could not be used to update database', e)
                print('please check if the JSON formatting is correct and that there are two newline characters after the JSON')

        print('success')

    def do_newtag(self, arg):
        '''adds tags to a node.
        format: newtag <id> wip \"long term\"'''
        if not db_existence():
            return
        
        id, *args = shlex.split(arg)
        
        if NodeTags.insert_many([{'node': int(id), 'tag': tag} for tag in args]).execute():
            print('success')
        else:
            print('Node not found')



def db_existence():
    if 'nodes' in db.get_tables() and 'nodetags' in db.get_tables():
        return True
    print('database not found.')
    return False


def show_tree(root_id):
    query = Nodes.select(
        Nodes.id,
        Nodes.title,
        Nodes.category,
        Nodes.parent_id,
        Nodes.priority_group,
        Nodes.status)
    nodes = list(query.tuples())


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
                    case 'manual':
                        colour = BLUE
                    case 'folder':
                        colour  = WHITE
                    case _:
                        colour = PINK
                
                closed_effect = ''
                if priority_group[child][5] in ['closed', 'deprecated']:
                    closed_effect = '\033[90m' #makes it gray
                colour += closed_effect
                print(preceeding_string + connector + f'{closed_effect}{priority_group[child][0]}-{colour}{priority_group[child][2]}{WHITE}{closed_effect}: {priority_group[child][1]}{RESET}')

                if closed_effect: #dont print children of closed
                    return
                
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


def sanitize_name(title, id, status):
    title = title.lower().replace(' ', '_')
    name = f'{title}_{id}'
    if status.lower() != 'open':
        name = f'CLOSED_{name}'
    return name




if __name__ == '__main__':
    vm = Virtual_Manager()
    vm.cmdloop()



