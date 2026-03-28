---
platform: android
difficulty: easy
category: generate
max_score: 10
timeout: 300
validation:
  type: both
  expected_files:
    - "app/src/main/java/com/benchmark/app/MainActivity.kt"
  build_command: "./gradlew assembleDebug"
  patterns:
    - "@Composable"
    - "Text("
    - "Surface"
    - "MaterialTheme"
    - "setContent"
---

Create `app/src/main/java/com/benchmark/app/MainActivity.kt` with a Jetpack Compose "Hello, World!" screen. The `MainActivity` should use `setContent` with a `MaterialTheme`. Create a `Greeting` composable that displays "Hello, World!" centered on screen with `MaterialTheme.colorScheme.primary` as background and white text using `headlineLarge` typography. Include a `@Preview` annotated composable.
