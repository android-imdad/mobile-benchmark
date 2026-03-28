---
platform: flutter
difficulty: medium
category: generate
max_score: 10
timeout: 300
validation:
  type: both
  expected_files:
    - "lib/todo/todo_model.dart"
    - "lib/todo/todo_list_page.dart"
    - "lib/todo/add_todo_dialog.dart"
  build_command: "flutter analyze && flutter build apk --debug"
  patterns:
    - "class Todo"
    - "StatefulWidget"
    - "setState"
    - "ListView"
    - "Dismissible"
    - "TextField"
    - "FloatingActionButton"
    - "showDialog"
    - "Checkbox"
---

Create a Todo app with 3 files:

1. `lib/todo/todo_model.dart` - Define a `Todo` class with: `String id` (use uuid or timestamp), `String title`, `bool isCompleted`, `DateTime createdAt`. Include `copyWith` method and factory constructor `Todo.create(String title)`.

2. `lib/todo/todo_list_page.dart` - A StatefulWidget `TodoListPage` with:
   - `List<Todo>` stored in state
   - `ListView.builder` showing todos with `Dismissible` for swipe-to-delete
   - Each item: `Checkbox` + title (with `TextDecoration.lineThrough` if completed)
   - `FloatingActionButton` that opens AddTodoDialog
   - `AppBar` showing "Todos (X/Y)" where X is completed and Y is total
   - Empty state with icon and text when list is empty

3. `lib/todo/add_todo_dialog.dart` - A StatefulWidget dialog with:
   - `TextField` with controller and autofocus
   - "Cancel" and "Add" action buttons
   - Validate title is not empty before allowing add
   - Return the todo title via `Navigator.pop`
