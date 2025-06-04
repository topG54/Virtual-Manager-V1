
### Virtual Manager v1

---

Everything is stored on an sqlite database and queried with a python shell. You can generate a human friendly version with the shell.

The high level types of 'nodes' are:

| Category       | Description                                                         | Storage                        |
| -------------- | ------------------------------------------------------------------- | ------------------------------ |
| **Repository** | A vault of knowledge, ideas, research, writing, etc.                | **Obsidian**                   |
| **Project**    | Mid-to-long term goal-oriented efforts. Multiple TODOs, notes, etc. | SQLite                         |
| **Routine**    | Recurring tasks/systems (daily/weekly/etc.)                         | SQLite                         |
| **Guide**      | Reference materials: plans, checklists, templates, etc.             | SQLite                         |
| **TODO**       | Small, atomic, possibly categorized tasks                           | SQLite                         |


lower level 'nodes' are:


| Category       | Description                                                         | Storage                        |
| -------------- | ------------------------------------------------------------------- | ------------------------------ |
| **Task**       | Like a note but has more characteristics(due date, recurring, etc)  | SQLite                         |
| **Note**       | Stores text. can be used in any place.                              | SQLite                         |
| **Checklist**  | Markdown checklist.                                                 | SQLite                         |

---










