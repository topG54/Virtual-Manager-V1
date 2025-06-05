
# Virtual Manager v1

---

A terminal based manager for tasks, projects, note taking etc.

Everything is stored on an sqlite database and queried with a python shell. You can generate a human friendly version to edit with the shell.

---

## Features

- Lightweight CLI (`cmd.Cmd`-based shell)
- Persistent local database (`SQLite`)
- Modular nodes with hierarchy & dependencies
- Tagging & status tracking
- Tree view of nested nodes

---

## Node Categories

Each node type represents a distinct unit of work or structure. Nodes do not overlap in purpose.

| Category     | Description                                 |
|--------------|---------------------------------------------|
| `project`    | A container for broader goals               |
| `recurring`  | A repeating routine or workflow             |
| `guide`      | A reference document or SOP                 |
| `todo`       | A simple checklist item                     |
| `repository` | A code or asset repository                  |
| `task`       | A structured unit of work with content      |
| `note`       | A standalone or attached content block      |
| `checklist`  | A list of verifiable steps or items         |

---

## Commands

### `init_db`
Initializes the SQLite database and creates required tables. Fails if database already exists.

### `delete_db`
Deletes the existing database after confirmation.

### `add <category> <title>`
Interactively adds a node to the database. Prompts for:
- `parent` (required for some)
- `tags` (optional, multiple allowed)
- `status` (optional: open, closed, deprecated)
- `content` (optional)

### `show_all`
Displays all nodes and their attributes.

### `tree [id]`
Shows a tree view of nodes starting from the root or a given node ID.

### `exit`
Exits the shell.

---

## Setup

Everything other than the scripts folder is just an example use case. 
Just copy the scripts folder into an empty folder

---

Yes, I did generate this with chatgpt. I dont know markdown that well

