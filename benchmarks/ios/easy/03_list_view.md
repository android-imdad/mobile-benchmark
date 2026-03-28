---
platform: ios
difficulty: easy
category: generate
max_score: 10
timeout: 300
validation:
  type: both
  expected_files:
    - "App/FruitListView.swift"
  build_command: "xcodebuild -scheme BenchmarkApp -destination 'platform=iOS Simulator,name=iPhone 16' build CODE_SIGNING_ALLOWED=NO"
  patterns:
    - "struct FruitListView"
    - "List"
    - "ForEach"
    - "NavigationStack"
    - "navigationTitle"
---

Create a SwiftUI view in `App/FruitListView.swift` that displays a scrollable list of 10 fruits with their emoji icons. Use `NavigationStack` with a title "Fruits". Each row should show the emoji and fruit name side by side using an `HStack`. Use a `ForEach` with identifiable data.
