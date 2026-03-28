---
platform: ios
difficulty: medium
category: generate
max_score: 10
timeout: 300
validation:
  type: both
  expected_files:
    - "App/TodoModel.swift"
    - "App/TodoListView.swift"
    - "App/AddTodoView.swift"
  build_command: "xcodebuild -scheme BenchmarkApp -destination 'platform=iOS Simulator,name=iPhone 16' build CODE_SIGNING_ALLOWED=NO"
  patterns:
    - "struct Todo"
    - "Identifiable"
    - "@Observable"
    - "TextField"
    - "onDelete"
    - "NavigationStack"
---

Create a Todo app with 3 files:

1. `App/TodoModel.swift` - Define a `Todo` struct conforming to `Identifiable` with properties: `id` (UUID), `title` (String), `isCompleted` (Bool). Create a `TodoStore` class using `@Observable` macro that holds an array of todos and has methods: `add(title:)`, `toggle(id:)`, `delete(at:)`.

2. `App/TodoListView.swift` - A SwiftUI view showing all todos in a `List` with swipe-to-delete. Each row shows a checkmark (SF Symbol), the title (with strikethrough if completed), and tapping toggles completion. Include a NavigationStack with title "Todos" and a toolbar button to navigate to AddTodoView.

3. `App/AddTodoView.swift` - A form with a `TextField` for the title and a "Save" button. Dismiss the view after saving. Validate that the title is not empty.
