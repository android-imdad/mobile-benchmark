---
platform: android
difficulty: medium
category: debug
max_score: 10
timeout: 300
validation:
  type: both
  expected_files:
    - "app/src/main/java/com/benchmark/app/HeavyWorkScreen.kt"
  build_command: "./gradlew assembleDebug"
  patterns:
    - "Dispatchers.IO"
    - "withContext"
    - "LaunchedEffect"
    - "rememberCoroutineScope"
    - "@Composable"
    - "mutableStateOf"
---

The following `app/src/main/java/com/benchmark/app/HeavyWorkScreen.kt` has an ANR (Application Not Responding) bug because heavy computation runs on the main thread. Fix all issues:

```kotlin
package com.benchmark.app

import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp

@Composable
fun HeavyWorkScreen() {
    var result by remember { mutableStateOf("") }
    var isLoading by remember { mutableStateOf(false) }

    Column(
        modifier = Modifier.fillMaxSize().padding(16.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center
    ) {
        Button(onClick = {
            isLoading = true
            // BUG: This blocks the main thread causing ANR
            val data = fetchDataFromNetwork()
            val processed = processData(data)
            result = processed
            isLoading = false
        }) {
            Text("Start Heavy Work")
        }

        if (isLoading) {
            CircularProgressIndicator()
        }

        Text(result)
    }
}

fun fetchDataFromNetwork(): String {
    Thread.sleep(3000) // Simulates network call
    return "raw data from server"
}

fun processData(input: String): String {
    Thread.sleep(2000) // Simulates heavy processing
    return "Processed: ${input.uppercase()}"
}
```

Issues to fix:
1. Move blocking operations off the main thread using coroutines with `Dispatchers.IO`
2. Use `rememberCoroutineScope` or `LaunchedEffect` properly
3. Make `fetchDataFromNetwork` and `processData` suspend functions using `withContext(Dispatchers.IO)`
4. Add proper error handling with try/catch
5. Show error state to user if operations fail
6. Disable button while loading to prevent duplicate calls

Write the corrected version to `app/src/main/java/com/benchmark/app/HeavyWorkScreen.kt`.
