---
platform: android
difficulty: easy
category: generate
max_score: 10
timeout: 300
validation:
  type: both
  expected_files:
    - "app/src/main/java/com/benchmark/app/CounterScreen.kt"
  build_command: "./gradlew assembleDebug"
  patterns:
    - "remember"
    - "mutableStateOf"
    - "@Composable"
    - "Button"
    - "onClick"
    - "Text("
---

Create `app/src/main/java/com/benchmark/app/CounterScreen.kt` with a Jetpack Compose counter. Create a `CounterScreen` composable with:
- A counter value displayed using `headlineLarge` typography
- An "Increment" button that adds 1
- A "Decrement" button that subtracts 1
- A "Reset" button that sets count to 0
- Counter should not go below 0
- Use `remember { mutableStateOf(0) }` for state
- Arrange buttons in a `Row` with `Arrangement.spacedBy(8.dp)`
- Include `@Preview`
