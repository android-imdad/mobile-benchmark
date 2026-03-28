---
platform: ios
difficulty: medium
category: debug
max_score: 10
timeout: 300
validation:
  type: both
  expected_files:
    - "App/ImageCache.swift"
  build_command: "xcodebuild -scheme BenchmarkApp -destination 'platform=iOS Simulator,name=iPhone 16' build CODE_SIGNING_ALLOWED=NO"
  patterns:
    - "NSCache"
    - "weak"
    - "[weak self]"
    - "final class"
    - "static let shared"
---

The following `App/ImageCache.swift` file has a memory leak caused by a retain cycle and improper cache management. Fix all issues:

```swift
import UIKit

class ImageCache {
    static let shared = ImageCache()
    var cache = [String: UIImage]()
    var delegates = [ImageCacheDelegate]()

    func loadImage(url: String, completion: @escaping (UIImage?) -> Void) {
        if let cached = cache[url] {
            completion(cached)
            return
        }

        let task = URLSession.shared.dataTask(with: URL(string: url)!) { data, _, _ in
            if let data = data, let image = UIImage(data: data) {
                self.cache[url] = image
                self.delegates.forEach { $0.didCacheImage(url: url) }
                completion(image)
            }
        }
        task.resume()
    }
}

protocol ImageCacheDelegate {
    func didCacheImage(url: String)
}
```

Issues to fix:
1. Strong reference cycle in the closure capturing `self`
2. Unbounded dictionary cache (should use `NSCache`)
3. Strong delegate references (should be weak)
4. Force unwrap on URL
5. Missing thread safety (completion should dispatch to main)
6. Class should be `final`

Write the corrected version to `App/ImageCache.swift`.
