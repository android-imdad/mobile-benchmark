---
platform: android
difficulty: hard
category: generate
max_score: 10
timeout: 300
validation:
  type: both
  expected_files:
    - "app/src/main/java/com/benchmark/app/clean/domain/model/Article.kt"
    - "app/src/main/java/com/benchmark/app/clean/domain/repository/ArticleRepository.kt"
    - "app/src/main/java/com/benchmark/app/clean/domain/usecase/GetArticlesUseCase.kt"
    - "app/src/main/java/com/benchmark/app/clean/data/ArticleRepositoryImpl.kt"
    - "app/src/main/java/com/benchmark/app/clean/presentation/ArticleViewModel.kt"
    - "app/src/main/java/com/benchmark/app/clean/presentation/ArticleListScreen.kt"
  build_command: "./gradlew assembleDebug"
  patterns:
    - "data class Article"
    - "interface ArticleRepository"
    - "class GetArticlesUseCase"
    - "operator fun invoke"
    - "class ArticleRepositoryImpl"
    - "class ArticleViewModel"
    - "StateFlow"
    - "@Composable"
---

Build an Articles feature following Clean Architecture with 6 files:

1. `app/src/main/java/com/benchmark/app/clean/domain/model/Article.kt` - Domain entity: `Article` data class with `id` (Int), `title` (String), `summary` (String), `author` (String), `publishedAt` (String), `isFavorite` (Boolean).

2. `app/src/main/java/com/benchmark/app/clean/domain/repository/ArticleRepository.kt` - Interface with: `suspend fun getArticles(): Result<List<Article>>`, `suspend fun getArticle(id: Int): Result<Article>`, `suspend fun toggleFavorite(id: Int): Result<Article>`.

3. `app/src/main/java/com/benchmark/app/clean/domain/usecase/GetArticlesUseCase.kt` - Use case class accepting `ArticleRepository` in constructor. Implement `operator fun invoke(): Flow<Result<List<Article>>>` using `flow { }` builder with emit.

4. `app/src/main/java/com/benchmark/app/clean/data/ArticleRepositoryImpl.kt` - Implementation returning fake/mock articles. Implement all interface methods with simulated delay using `kotlinx.coroutines.delay`.

5. `app/src/main/java/com/benchmark/app/clean/presentation/ArticleViewModel.kt` - ViewModel using `GetArticlesUseCase`. Expose `uiState` as `StateFlow` using sealed interface `ArticleUiState` (Loading, Success, Error). Collect flow in `init` block.

6. `app/src/main/java/com/benchmark/app/clean/presentation/ArticleListScreen.kt` - Composable consuming ViewModel state. Show loading/error/list states. Each article in a `Card` with title, author, date, summary preview, and favorite toggle icon.
