---
platform: flutter
difficulty: hard
category: generate
max_score: 10
timeout: 300
validation:
  type: both
  expected_files:
    - "lib/painter/clock_painter.dart"
    - "lib/painter/wave_painter.dart"
    - "lib/painter/painter_showcase.dart"
  build_command: "flutter analyze && flutter build apk --debug"
  patterns:
    - "CustomPainter"
    - "paint("
    - "Canvas"
    - "drawCircle"
    - "drawLine"
    - "drawPath"
    - "Path()"
    - "AnimationController"
    - "shouldRepaint"
    - "CustomPaint"
---

Create 3 custom painting files for Flutter:

1. `lib/painter/clock_painter.dart` - An analog clock `CustomPainter`:
   - Draws clock face circle with tick marks (60 minute, 12 hour ticks)
   - Hour, minute, second hands with different lengths and colors
   - Accepts `DateTime` to render
   - Second hand in red, smooth rotation
   - Center dot decoration
   - Hour numbers (12, 3, 6, 9) drawn with `TextPainter`
   - `shouldRepaint` returns true when time changes

2. `lib/painter/wave_painter.dart` - An animated wave `CustomPainter`:
   - Draws a multi-layered sine wave using `Path` and `quadraticBezierTo`
   - Accepts `animationValue` (0.0-1.0) for horizontal offset
   - 3 wave layers with different amplitudes, frequencies, and opacity
   - Gradient fill below waves using `shader` from `LinearGradient`
   - Configurable wave color, amplitude, and frequency

3. `lib/painter/painter_showcase.dart` - StatefulWidget showcase:
   - Top: Analog clock updating every second via `AnimationController` with `vsync` from `TickerProviderStateMixin`
   - Bottom: Animated wave using a looping `AnimationController`
   - Toggle button to pause/resume animations
   - Slider to adjust wave amplitude
   - Both wrapped in `CustomPaint` with proper `size` constraints
   - Dispose controllers in `dispose()`
