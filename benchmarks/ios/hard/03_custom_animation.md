---
platform: ios
difficulty: hard
category: generate
max_score: 10
timeout: 300
validation:
  type: both
  expected_files:
    - "App/Animations/PulsingButton.swift"
    - "App/Animations/ParticleEffect.swift"
    - "App/Animations/AnimationShowcase.swift"
  build_command: "xcodebuild -scheme BenchmarkApp -destination 'platform=iOS Simulator,name=iPhone 16' build CODE_SIGNING_ALLOWED=NO"
  patterns:
    - "AnimatableModifier"
    - "GeometryEffect"
    - "TimelineView"
    - "Canvas"
    - "withAnimation"
    - "@State"
    - "animatableData"
---

Create 3 custom animation files for SwiftUI:

1. `App/Animations/PulsingButton.swift` - A reusable `PulsingButton` view that:
   - Scales up/down continuously with a breathing animation
   - Shows a ripple ring effect on tap (expanding circle that fades)
   - Uses `AnimatableModifier` for the ripple
   - Accepts label text and action closure
   - Has configurable pulse speed and color

2. `App/Animations/ParticleEffect.swift` - A particle emitter view using `TimelineView` and `Canvas`:
   - Spawns particles from a center point
   - Particles have random velocity, size, color, and lifetime
   - Uses `Canvas` for efficient rendering
   - Supports configurable particle count, colors, and spawn rate
   - Particles fade out as they age

3. `App/Animations/AnimationShowcase.swift` - A showcase view combining both:
   - Displays the PulsingButton in the center
   - On tap, triggers ParticleEffect burst from button location
   - Uses `GeometryReader` to coordinate positions
   - Smooth transitions between states using `withAnimation(.spring())`
   - Include a reset button
