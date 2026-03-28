---
platform: android
difficulty: medium
category: generate
max_score: 10
timeout: 300
validation:
  type: both
  expected_files:
    - "app/src/main/java/com/benchmark/app/todo/TodoModel.kt"
    - "app/src/main/java/com/benchmark/app/todo/TodoViewModel.kt"
    - "app/src/main/java/com/benchmark/app/todo/TodoScreen.kt"
  build_command: "./gradlew assembleDebug"
  patterns:
    - "data class Todo"
    - "ViewModel"
    - "StateFlow"
    - "mutableStateListOf"
    - "LazyColumn"
    - "SwipeToDismiss"
    - "TextField"
    - "FloatingActionButton"
---

Create a Todo app with 3 files:

1. `app/src/main/java/com/benchmark/app/todo/TodoModel.kt` - Define `Todo` data class with: `id` (UUID), `title` (String), `isCompleted` (Boolean), `createdAt` (Long = System.currentTimeMillis()).

2. `app/src/main/java/com/benchmark/app/todo/TodoViewModel.kt` - `TodoViewModel` extending `ViewModel` with:
   - `_todos` as `mutableStateListOf<Todo>()`
   - `todos` exposed as read-only list
   - Methods: `addTodo(title: String)`, `toggleTodo(id: UUID)`, `deleteTodo(id: UUID)`
   - Computed `completedCount` and `pendingCount`

3. `app/src/main/java/com/benchmark/app/todo/TodoScreen.kt` - Composable screen with:
   - `Scaffold` with TopAppBar showing "Todos" and counts
   - `LazyColumn` with swipe-to-dismiss for delete
   - Each item shows checkbox, title (strikethrough if done), and delete icon
   - `FloatingActionButton` that opens an `AlertDialog` with `TextField` to add new todo
   - Empty state composable when no todos exist
