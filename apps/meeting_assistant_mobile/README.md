# Meeting Assistant Mobile

This is a hand-scaffolded Flutter demo focused on:

- quick meeting capture
- real-time transcription
- historical lookup

## Current State

This machine does not currently have a local Flutter toolchain, so this app has been scaffolded manually.

Already included:

- Flutter app source structure
- page layout
- local persistence
- on-device real-time transcription flow
- action item extraction demo logic

Not generated yet:

- Android and iOS platform wrappers
- Gradle and Xcode project files

## Bootstrap After Installing Flutter

After you install Flutter, run:

```bash
cd apps/meeting_assistant_mobile
flutter create .
flutter pub get
flutter run
```

## Android Note

Because the app uses microphone transcription, make sure Android includes microphone permission after platform generation:

```xml
<uses-permission android:name="android.permission.RECORD_AUDIO" />
```
