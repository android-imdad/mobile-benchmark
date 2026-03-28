---
platform: ios
difficulty: hard
category: generate
max_score: 10
timeout: 300
validation:
  type: both
  expected_files:
    - "App/Models/Note.swift"
    - "App/ViewModels/NoteListViewModel.swift"
    - "App/ViewModels/NoteDetailViewModel.swift"
    - "App/Views/NoteListView.swift"
    - "App/Views/NoteDetailView.swift"
    - "App/Services/NoteRepository.swift"
  build_command: "xcodebuild -scheme BenchmarkApp -destination 'platform=iOS Simulator,name=iPhone 16' build CODE_SIGNING_ALLOWED=NO"
  patterns:
    - "protocol NoteRepositoryProtocol"
    - "@Observable"
    - "class NoteListViewModel"
    - "class NoteDetailViewModel"
    - "struct NoteListView"
    - "struct NoteDetailView"
    - "private let repository"
    - "init("
---

Build a Notes app following strict MVVM architecture with 6 files:

1. `App/Models/Note.swift` - `Note` struct with: `id` (UUID), `title` (String), `content` (String), `createdAt` (Date), `updatedAt` (Date). Conform to `Identifiable` and `Codable`.

2. `App/Services/NoteRepository.swift` - Define `NoteRepositoryProtocol` with methods: `fetchAll() -> [Note]`, `save(_ note: Note)`, `delete(id: UUID)`, `find(id: UUID) -> Note?`. Implement `InMemoryNoteRepository` conforming to this protocol using an in-memory array. Also create a `MockNoteRepository` for testing with preset data.

3. `App/ViewModels/NoteListViewModel.swift` - `@Observable` class with dependency injection of `NoteRepositoryProtocol`. Properties: `notes`, `searchText`, `filteredNotes` (computed). Methods: `loadNotes()`, `deleteNote(at:)`, `deleteNote(id:)`.

4. `App/ViewModels/NoteDetailViewModel.swift` - `@Observable` class for creating/editing a note. Accept repository via init. Properties: `title`, `content`, `isEditing`, `canSave` (computed). Methods: `save()`, `loadNote(id:)`.

5. `App/Views/NoteListView.swift` - SwiftUI view with NavigationStack, searchable list, swipe-to-delete, and navigation to detail view. Use `.searchable` modifier.

6. `App/Views/NoteDetailView.swift` - Form-based editor with TextField for title, TextEditor for content, and save button in toolbar. Dismiss on save.
