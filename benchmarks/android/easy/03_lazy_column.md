---
platform: android
difficulty: easy
category: generate
max_score: 10
timeout: 300
validation:
  type: both
  expected_files:
    - "app/src/main/java/com/benchmark/app/FruitListScreen.kt"
  build_command: "./gradlew assembleDebug"
  patterns:
    - "LazyColumn"
    - "items("
    - "@Composable"
    - "data class"
    - "Text("
    - "Row("
---

Create `app/src/main/java/com/benchmark/app/FruitListScreen.kt` with a Jetpack Compose scrollable list. Define a `Fruit` data class with `name` and `emoji` properties. Create a `FruitListScreen` composable that:
- Shows a top bar with title "Fruits" using `Scaffold` and `TopAppBar`
- Displays 10 fruits in a `LazyColumn`
- Each item is a `Row` showing the emoji and name with `16.dp` padding
- Add a `Divider` between items
- Include `@Preview`
