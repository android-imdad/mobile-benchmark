---
platform: flutter
difficulty: hard
category: modify
max_score: 10
timeout: 300
validation:
  type: both
  expected_files:
    - "lib/db/database_helper.dart"
    - "lib/db/migration_runner.dart"
    - "lib/db/note_dao.dart"
    - "lib/db/note_entity.dart"
  build_command: "flutter analyze && flutter build apk --debug"
  patterns:
    - "class DatabaseHelper"
    - "openDatabase"
    - "onCreate"
    - "onUpgrade"
    - "class MigrationRunner"
    - "class NoteDao"
    - "Future<"
    - "class NoteEntity"
    - "Map<String, dynamic>"
    - "batch.execute"
---

Create an sqflite database layer with migration support in 4 files:

1. `lib/db/note_entity.dart` - `NoteEntity` class with: `int? id`, `String title`, `String content`, `String category`, `int priority`, `bool isPinned`, `DateTime createdAt`, `DateTime updatedAt`. Include `toMap()` returning `Map<String, dynamic>`, `factory NoteEntity.fromMap(Map<String, dynamic>)`, and `copyWith` method. Store DateTime as ISO8601 string, bool as int (0/1).

2. `lib/db/migration_runner.dart` - `MigrationRunner` class with:
   - `static List<Migration>` defining all migrations
   - Each `Migration` has `version` (int) and `migrate(Database db)` async method
   - Migration 2: adds `category` TEXT DEFAULT 'general'
   - Migration 3: adds `priority` INTEGER DEFAULT 0 and `isPinned` INTEGER DEFAULT 0
   - Migration 4: creates index on `category` and `priority`
   - `static Future<void> runMigrations(Database db, int oldVersion, int newVersion)` that runs applicable migrations in order

3. `lib/db/database_helper.dart` - Singleton `DatabaseHelper` with:
   - Private constructor, static instance
   - `Future<Database> get database` lazy initialization
   - `openDatabase` with `version: 4`, `onCreate` creating full schema, `onUpgrade` delegating to MigrationRunner
   - `Future<void> close()`

4. `lib/db/note_dao.dart` - `NoteDao` class with:
   - Constructor accepting `DatabaseHelper`
   - `Future<int> insert(NoteEntity note)`
   - `Future<int> update(NoteEntity note)`
   - `Future<int> delete(int id)`
   - `Future<NoteEntity?> getById(int id)`
   - `Future<List<NoteEntity>> getAll({String? category, String? orderBy})`
   - `Future<List<NoteEntity>> search(String query)` using LIKE on title and content
   - `Future<int> deleteAll()`
   - All methods use the database from DatabaseHelper
