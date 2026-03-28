---
platform: android
difficulty: medium
category: generate
max_score: 10
timeout: 300
validation:
  type: both
  expected_files:
    - "app/src/main/java/com/benchmark/app/network/ApiService.kt"
    - "app/src/main/java/com/benchmark/app/network/PostModel.kt"
    - "app/src/main/java/com/benchmark/app/network/PostListScreen.kt"
  build_command: "./gradlew assembleDebug"
  patterns:
    - "interface ApiService"
    - "suspend fun"
    - "@GET"
    - "Retrofit"
    - "data class Post"
    - "sealed class"
    - "LazyColumn"
    - "CircularProgressIndicator"
---

Create a Retrofit networking layer with 3 files:

1. `app/src/main/java/com/benchmark/app/network/PostModel.kt` - Define `Post` data class with: `id` (Int), `userId` (Int), `title` (String), `body` (String). Also define a sealed class `UiState<out T>` with variants: `Loading`, `Success(val data: T)`, `Error(val message: String)`.

2. `app/src/main/java/com/benchmark/app/network/ApiService.kt` - Define:
   - `ApiService` interface with `@GET("posts") suspend fun getPosts(): List<Post>` and `@GET("posts/{id}") suspend fun getPost(@Path("id") id: Int): Post`
   - `RetrofitClient` object with lazy `Retrofit.Builder()` using base URL `https://jsonplaceholder.typicode.com/`, `GsonConverterFactory`, and `OkHttpClient` with logging interceptor
   - `PostRepository` class wrapping ApiService with try/catch returning `UiState`

3. `app/src/main/java/com/benchmark/app/network/PostListScreen.kt` - Composable with:
   - ViewModel that calls repository in `init` via `viewModelScope.launch`
   - `when` expression on `UiState`: show `CircularProgressIndicator`, error with retry `Button`, or `LazyColumn` of posts
   - Each post card uses `Card` with `elevation`, showing title in bold and truncated body
