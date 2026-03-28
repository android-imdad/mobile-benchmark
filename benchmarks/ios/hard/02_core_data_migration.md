---
platform: ios
difficulty: hard
category: modify
max_score: 10
timeout: 300
validation:
  type: both
  expected_files:
    - "App/Persistence/CoreDataStack.swift"
    - "App/Persistence/MigrationManager.swift"
    - "App/Models/TaskItem+CoreDataProperties.swift"
  build_command: "xcodebuild -scheme BenchmarkApp -destination 'platform=iOS Simulator,name=iPhone 16' build CODE_SIGNING_ALLOWED=NO"
  patterns:
    - "NSPersistentContainer"
    - "NSManagedObjectModel"
    - "NSMappingModel"
    - "NSMigrationManager"
    - "performMigration"
    - "viewContext"
    - "func save()"
---

Create a Core Data stack with migration support in 3 files:

1. `App/Persistence/CoreDataStack.swift` - Implement a `CoreDataStack` class with:
   - `NSPersistentContainer` setup with a model name parameter
   - Lazy `viewContext` on main queue
   - Background context creation method
   - `save()` method with error handling
   - `performBackgroundTask` wrapper
   - Singleton `shared` instance with default model name "BenchmarkApp"

2. `App/Persistence/MigrationManager.swift` - Implement `MigrationManager` that:
   - Checks if migration is needed between store versions
   - Discovers source/destination `NSManagedObjectModel` from bundle
   - Finds or infers `NSMappingModel`
   - Performs lightweight migration first, falls back to heavyweight
   - Has a `performMigration(at storeURL: URL) throws` method
   - Logs migration progress

3. `App/Models/TaskItem+CoreDataProperties.swift` - Define Core Data managed object subclass `TaskItem` with properties: `id` (UUID), `title` (String), `taskDescription` (String), `priority` (Int16), `isCompleted` (Bool), `createdAt` (Date), `dueDate` (Date?). Include a `fetchRequest()` static method and computed `priorityLevel` enum (low/medium/high).
