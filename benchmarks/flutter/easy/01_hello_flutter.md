---
platform: flutter
difficulty: easy
category: generate
max_score: 10
timeout: 300
validation:
  type: both
  expected_files:
    - "lib/main.dart"
  build_command: "flutter analyze && flutter build apk --debug"
  patterns:
    - "MaterialApp"
    - "Scaffold"
    - "Center"
    - "Text("
    - "AppBar"
    - "void main()"
    - "runApp"
---

Create `lib/main.dart` with a Flutter "Hello, World!" app. The `MyApp` StatelessWidget should return a `MaterialApp` with a `Scaffold` containing an `AppBar` titled "Hello App" and a `Center`ed `Text("Hello, World!")` with font size 32 and blue color. Use `ThemeData` with `useMaterial3: true` and a blue color scheme.
