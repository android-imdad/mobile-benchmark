// swift-tools-version:5.9
import PackageDescription

let package = Package(
    name: "BenchmarkApp",
    platforms: [.iOS(.v17)],
    targets: [
        .executableTarget(
            name: "BenchmarkApp",
            path: "App"
        )
    ]
)
