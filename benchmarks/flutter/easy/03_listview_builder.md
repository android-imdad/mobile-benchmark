---
platform: flutter
difficulty: easy
category: generate
max_score: 10
timeout: 300
validation:
  type: both
  expected_files:
    - "lib/fruit_list_page.dart"
  build_command: "flutter analyze && flutter build apk --debug"
  patterns:
    - "ListView.builder"
    - "ListTile"
    - "itemCount"
    - "itemBuilder"
    - "StatelessWidget"
    - "AppBar"
---

Create `lib/fruit_list_page.dart` with a Flutter scrollable list. Create a `FruitListPage` StatelessWidget that:
- Displays a list of 10 fruits with emoji icons
- Uses `ListView.builder` for efficient scrolling
- Each item is a `ListTile` with `leading` emoji Text, `title` fruit name, and `trailing` arrow icon
- Has an `AppBar` with title "Fruits"
- Add a `Divider` between items using `ListView.separated`
- Tapping an item shows a `SnackBar` with the fruit name
