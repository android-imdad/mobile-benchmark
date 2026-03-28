---
platform: flutter
difficulty: medium
category: debug
max_score: 10
timeout: 300
validation:
  type: both
  expected_files:
    - "lib/shopping_cart.dart"
  build_command: "flutter analyze && flutter build apk --debug"
  patterns:
    - "ChangeNotifier"
    - "notifyListeners"
    - "List<CartItem>"
    - "UnmodifiableListView"
    - "double get totalPrice"
    - "void addItem"
    - "void removeItem"
---

The following `lib/shopping_cart.dart` has multiple state management bugs. Fix all issues:

```dart
import 'package:flutter/material.dart';

class CartItem {
  String name;
  double price;
  int quantity;

  CartItem(this.name, this.price, this.quantity);
}

class ShoppingCart extends ChangeNotifier {
  List<CartItem> items = [];

  // BUG 1: Directly exposing mutable list
  List<CartItem> get cartItems => items;

  // BUG 2: Not calling notifyListeners
  void addItem(CartItem item) {
    final existing = items.where((i) => i.name == item.name).first;
    if (existing != null) {
      existing.quantity += item.quantity;
    } else {
      items.add(item);
    }
  }

  // BUG 3: ConcurrentModificationError - modifying list while iterating
  void removeAllExpensive(double threshold) {
    for (var item in items) {
      if (item.price > threshold) {
        items.remove(item);
      }
    }
    notifyListeners();
  }

  // BUG 4: Wrong total calculation (ignores quantity)
  double get totalPrice {
    return items.fold(0, (sum, item) => sum + item.price);
  }

  // BUG 5: Doesn't handle empty list
  CartItem get mostExpensive {
    return items.reduce((a, b) => a.price > b.price ? a : b);
  }

  void clear() {
    items = [];
    // BUG 6: Missing notifyListeners
  }
}
```

Issues to fix:
1. Expose `UnmodifiableListView` instead of mutable list
2. Call `notifyListeners()` in `addItem`
3. Fix `ConcurrentModificationError` in `removeAllExpensive` (use `removeWhere`)
4. Fix total calculation to multiply price * quantity
5. Handle empty list in `mostExpensive` (return null or throw descriptive error)
6. Call `notifyListeners()` in `clear`
7. Fix `.first` which throws on empty (use `firstWhere` with orElse)
8. Make `CartItem` immutable with final fields and `copyWith`

Write the corrected version to `lib/shopping_cart.dart`.
