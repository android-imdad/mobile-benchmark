---
platform: android
difficulty: hard
category: generate
max_score: 10
timeout: 300
validation:
  type: both
  expected_files:
    - "app/src/main/java/com/benchmark/app/compose/CircularProgressChart.kt"
    - "app/src/main/java/com/benchmark/app/compose/AnimatedWaveform.kt"
    - "app/src/main/java/com/benchmark/app/compose/ChartShowcase.kt"
  build_command: "./gradlew assembleDebug"
  patterns:
    - "Canvas"
    - "drawArc"
    - "drawPath"
    - "Animatable"
    - "animateFloatAsState"
    - "Path()"
    - "@Composable"
    - "remember"
    - "LaunchedEffect"
---

Create 3 custom Composable files with advanced drawing:

1. `app/src/main/java/com/benchmark/app/compose/CircularProgressChart.kt` - A reusable `CircularProgressChart` composable:
   - Draws a circular/donut chart using `Canvas` and `drawArc`
   - Accepts `List<ChartSegment>` (data class with `value: Float`, `color: Color`, `label: String`)
   - Animated segments that grow from 0 to target angle on first composition using `Animatable`
   - Center text showing total or selected segment value
   - Optional click detection on segments using `pointerInput`

2. `app/src/main/java/com/benchmark/app/compose/AnimatedWaveform.kt` - A `AnimatedWaveform` composable:
   - Draws a continuous sine wave using `Canvas` and `Path`
   - Wave animates horizontally using `rememberInfiniteTransition`
   - Configurable: amplitude, frequency, color, strokeWidth, speed
   - Multiple layered waves with different phases for depth effect
   - Gradient fill below the wave using `drawPath` with `Brush.verticalGradient`

3. `app/src/main/java/com/benchmark/app/compose/ChartShowcase.kt` - Showcase screen combining both:
   - Top half: CircularProgressChart with sample data (4 segments)
   - Bottom half: AnimatedWaveform with theme colors
   - Animated visibility toggle for each section
   - Uses `AnimatedVisibility` with `expandVertically`/`shrinkVertically`
   - Slider to control waveform amplitude in real-time
