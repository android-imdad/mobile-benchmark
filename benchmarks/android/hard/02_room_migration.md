---
platform: android
difficulty: hard
category: modify
max_score: 10
timeout: 300
validation:
  type: both
  expected_files:
    - "app/src/main/java/com/benchmark/app/db/AppDatabase.kt"
    - "app/src/main/java/com/benchmark/app/db/TaskDao.kt"
    - "app/src/main/java/com/benchmark/app/db/TaskEntity.kt"
    - "app/src/main/java/com/benchmark/app/db/Migration.kt"
  build_command: "./gradlew assembleDebug"
  patterns:
    - "@Database"
    - "@Entity"
    - "@Dao"
    - "@Query"
    - "@Insert"
    - "@Delete"
    - "Migration("
    - "Room.databaseBuilder"
    - "addMigrations"
    - "Flow<List"
---

Create a Room database with migration support in 4 files:

1. `app/src/main/java/com/benchmark/app/db/TaskEntity.kt` - Room entity `TaskEntity` with: `@PrimaryKey id` (Int, autoGenerate), `title` (String), `description` (String), `priority` (Int, default 0), `isCompleted` (Boolean, default false), `createdAt` (Long), `dueDate` (Long?, nullable), `category` (String, default "general"). Include `@ColumnInfo` annotations with custom column names.

2. `app/src/main/java/com/benchmark/app/db/TaskDao.kt` - DAO interface with: `@Query getAllTasks(): Flow<List<TaskEntity>>`, `@Query getTasksByPriority(priority: Int): Flow<List<TaskEntity>>`, `@Query searchTasks(query: String)` using LIKE, `@Insert(onConflict = REPLACE) insertTask`, `@Update updateTask`, `@Delete deleteTask`, `@Query deleteCompleted()`.

3. `app/src/main/java/com/benchmark/app/db/Migration.kt` - Define migrations:
   - `MIGRATION_1_2`: adds `priority` column (INTEGER NOT NULL DEFAULT 0)
   - `MIGRATION_2_3`: adds `dueDate` column (INTEGER nullable) and `category` column (TEXT NOT NULL DEFAULT 'general')
   - `MIGRATION_3_4`: creates an index on `category` column
   Each migration uses `database.execSQL()`.

4. `app/src/main/java/com/benchmark/app/db/AppDatabase.kt` - Abstract `RoomDatabase` class with `@Database` annotation (entities, version=4). Abstract `taskDao()`. Companion object with singleton pattern using `Room.databaseBuilder` with `.addMigrations(MIGRATION_1_2, MIGRATION_2_3, MIGRATION_3_4)` and `.fallbackToDestructiveMigration()` as last resort.
