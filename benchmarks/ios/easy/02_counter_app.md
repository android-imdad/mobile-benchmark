---
platform: ios
difficulty: easy
category: generate
max_score: 10
timeout: 300
validation:
  type: both
  expected_files:
    - "App/CounterView.swift"
  build_command: "xcodebuild -scheme BenchmarkApp -destination 'platform=iOS Simulator,name=iPhone 16' build CODE_SIGNING_ALLOWED=NO"
  patterns:
    - "@State"
    - "private var count"
    - "Button"
    - "Text("
---

Create a SwiftUI counter app in `App/CounterView.swift`. It should display a count number and have two buttons: "Increment" (+1) and "Decrement" (-1). Use `@State` for the counter value. Style the buttons with `.buttonStyle(.borderedProminent)`. The count should not go below 0.
