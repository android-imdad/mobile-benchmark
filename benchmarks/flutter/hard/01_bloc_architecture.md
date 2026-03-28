---
platform: flutter
difficulty: hard
category: generate
max_score: 10
timeout: 300
validation:
  type: both
  expected_files:
    - "lib/bloc/weather/weather_event.dart"
    - "lib/bloc/weather/weather_state.dart"
    - "lib/bloc/weather/weather_bloc.dart"
    - "lib/bloc/weather/weather_model.dart"
    - "lib/bloc/weather/weather_repository.dart"
    - "lib/bloc/weather/weather_page.dart"
  build_command: "flutter analyze && flutter build apk --debug"
  patterns:
    - "abstract class WeatherEvent"
    - "abstract class WeatherState"
    - "class WeatherBloc extends Bloc"
    - "class WeatherRepository"
    - "emit("
    - "on<"
    - "BlocProvider"
    - "BlocBuilder"
    - "class Weather"
---

Build a Weather feature using BLoC pattern with 6 files:

1. `lib/bloc/weather/weather_model.dart` - `Weather` class with: `String cityName`, `double temperature`, `String condition` (sunny/cloudy/rainy/snowy), `double humidity`, `double windSpeed`, `String iconCode`. Include `fromJson` factory and `toJson`.

2. `lib/bloc/weather/weather_event.dart` - Sealed/abstract class `WeatherEvent` with subclasses: `FetchWeather(String city)`, `RefreshWeather`, `ClearWeather`.

3. `lib/bloc/weather/weather_state.dart` - Sealed/abstract class `WeatherState` with subclasses: `WeatherInitial`, `WeatherLoading`, `WeatherLoaded(Weather weather)`, `WeatherError(String message)`.

4. `lib/bloc/weather/weather_repository.dart` - `WeatherRepository` class with `Future<Weather> getWeather(String city)` that returns mock data with simulated delay. Include different weather for different city names.

5. `lib/bloc/weather/weather_bloc.dart` - `WeatherBloc extends Bloc<WeatherEvent, WeatherState>` with:
   - Constructor registering handlers via `on<FetchWeather>`, `on<RefreshWeather>`, `on<ClearWeather>`
   - Store last city for refresh
   - Emit Loading then Loaded/Error states
   - Handle exceptions gracefully

6. `lib/bloc/weather/weather_page.dart` - StatelessWidget with:
   - `BlocProvider` creating WeatherBloc
   - `TextField` for city input with search icon button
   - `BlocBuilder` switching on state: initial message, loading spinner, weather display card (city, temp, condition icon, humidity, wind), error with retry
   - Weather card with gradient background based on condition
