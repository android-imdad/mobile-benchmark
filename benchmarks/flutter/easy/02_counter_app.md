---
platform: flutter
difficulty: easy
category: generate
max_score: 10
timeout: 300
validation:
  type: both
  expected_files:
    - "lib/counter_page.dart"
  build_command: "flutter analyze && flutter build apk --debug"
  patterns:
    - "StatefulWidget"
    - "setState"
    - "ElevatedButton"
    - "Text("
    - "int _counter"
    - "Column"
---

Create `lib/counter_page.dart` with a Flutter counter widget. Create a `CounterPage` StatefulWidget with:
- A counter value displayed with `headlineLarge` text style
- Three `ElevatedButton`s: "Increment" (+1), "Decrement" (-1), "Reset" (set to 0)
- Counter should not go below 0
- Buttons arranged in a `Row` with `MainAxisAlignment.spaceEvenly`
- Use `setState` for state management
- Centered layout using `Column` with `MainAxisAlignment.center`
