---
platform: ios
difficulty: medium
category: generate
max_score: 10
timeout: 300
validation:
  type: both
  expected_files:
    - "App/NetworkManager.swift"
    - "App/PostModel.swift"
    - "App/PostListView.swift"
  build_command: "xcodebuild -scheme BenchmarkApp -destination 'platform=iOS Simulator,name=iPhone 16' build CODE_SIGNING_ALLOWED=NO"
  patterns:
    - "URLSession"
    - "async"
    - "await"
    - "Codable"
    - "JSONDecoder"
    - "throws"
    - "@Observable"
---

Create a networking layer with 3 files:

1. `App/PostModel.swift` - Define a `Post` struct conforming to `Codable` and `Identifiable` with properties: `id` (Int), `userId` (Int), `title` (String), `body` (String).

2. `App/NetworkManager.swift` - Create a `NetworkManager` class using `@Observable` with:
   - A generic `fetch<T: Decodable>(url: URL) async throws -> T` method using URLSession
   - A `fetchPosts() async` method that fetches from `https://jsonplaceholder.typicode.com/posts` and stores results in a published `posts` array
   - Proper error handling with a custom `NetworkError` enum (invalidURL, decodingError, serverError)
   - A `isLoading` boolean and optional `errorMessage` string

3. `App/PostListView.swift` - A SwiftUI view that displays posts using the NetworkManager. Show a `ProgressView` while loading, error state with retry button, and a `List` of posts showing title and truncated body.
