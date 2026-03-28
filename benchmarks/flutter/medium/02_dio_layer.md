---
platform: flutter
difficulty: medium
category: generate
max_score: 10
timeout: 300
validation:
  type: both
  expected_files:
    - "lib/network/api_client.dart"
    - "lib/network/post_model.dart"
    - "lib/network/post_list_page.dart"
  build_command: "flutter analyze && flutter build apk --debug"
  patterns:
    - "class ApiClient"
    - "http.get"
    - "jsonDecode"
    - "fromJson"
    - "Future<"
    - "FutureBuilder"
    - "CircularProgressIndicator"
    - "class Post"
---

Create a networking layer with 3 files (using the `http` package which is already in pubspec):

1. `lib/network/post_model.dart` - Define `Post` class with: `int id`, `int userId`, `String title`, `String body`. Include `factory Post.fromJson(Map<String, dynamic> json)` and `Map<String, dynamic> toJson()` methods.

2. `lib/network/api_client.dart` - Create `ApiClient` class with:
   - Base URL `https://jsonplaceholder.typicode.com`
   - `Future<List<Post>> fetchPosts()` using `http.get`, parsing JSON response
   - `Future<Post> fetchPost(int id)` for single post
   - Custom `ApiException` class with status code and message
   - Proper error handling: check status code, catch `SocketException` for no internet

3. `lib/network/post_list_page.dart` - A StatefulWidget with:
   - `late Future<List<Post>>` initialized in `initState`
   - `FutureBuilder` to handle loading/error/data states
   - `CircularProgressIndicator` while loading
   - Error widget with message and "Retry" button that calls `setState` to refetch
   - `ListView.builder` with `Card` widgets showing post title and truncated body
   - Pull-to-refresh with `RefreshIndicator`
