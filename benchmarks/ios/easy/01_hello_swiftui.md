---
platform: ios
difficulty: easy
category: generate
max_score: 10
timeout: 300
validation:
  type: both
  expected_files:
    - "App/ContentView.swift"
  build_command: "xcodebuild -scheme BenchmarkApp -destination 'platform=iOS Simulator,name=iPhone 16' build CODE_SIGNING_ALLOWED=NO"
  patterns:
    - "struct ContentView"
    - "var body: some View"
    - "Text("
    - ".background"
---

Create a SwiftUI view in `App/ContentView.swift` that displays "Hello, World!" centered on the screen with a blue background and white text. The text should use the `.largeTitle` font. Include proper `PreviewProvider` support.
