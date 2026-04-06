# Flutter App Design

## Product Goal

The mobile app should make this project useful in daily work, not just in demos. The core value is:

- capture meeting content quickly
- review historical records anytime
- track action items without opening a terminal

For the first mobile demo, the app focuses on:

1. real-time speech transcription on device
2. one-tap save of meeting notes
3. fast history lookup
4. meeting detail review
5. action item status tracking

## Why Flutter

Flutter is the most practical choice for this stage because:

- one codebase can target Android first and still stay ready for iOS
- UI iteration is fast for form, list, and detail based product flows
- plugin ecosystem is mature for microphone, local storage, and network
- it fits the current product stage better than building separate native apps

## MVP Scope

### Included

- live transcription page
- local meeting history
- meeting detail page
- local action item extraction
- action item status updates

### Deferred

- backend sync
- account system
- cloud history sync
- multi-device sync
- background long-duration recording
- LLM extraction inside the app

## Information Architecture

### App Shell

- `Record`
- `History`

### Navigation

- bottom navigation for primary entry points
- detail page opens from history list item tap

## Page Structure

### 1. Record Page

Purpose:

- instant capture entry
- real-time transcript display
- quick save into local history

Main sections:

- title input
- live status strip
- transcript editor
- primary controls
- extraction preview

### 2. History Page

Purpose:

- search and browse all saved meetings

Main sections:

- search field
- recent meeting cards
- metadata chips

### 3. Meeting Detail Page

Purpose:

- review what happened in one meeting
- manage action items

Main sections:

- title and created time
- transcript block
- action item checklist

## State and Data Flow

### Core Models

- `MeetingRecord`
- `MeetingActionItem`

### Service Layer

- `MeetingRepository`
- `LiveTranscriptionService`
- `LocalActionItemExtractor`

### Data Flow

1. user opens `Record`
2. user starts transcription
3. `LiveTranscriptionService` streams partial transcript updates
4. transcript is shown live in the editor
5. user saves the meeting
6. `LocalActionItemExtractor` creates action items from transcript
7. `MeetingRepository` stores the full meeting locally
8. `History` renders the updated list
9. `Meeting Detail` shows transcript and toggles action item status

## Persistence Strategy

For the demo, local persistence uses `shared_preferences`.

Recommended later upgrade:

- move to `drift` or `isar`

## Real-Time Transcription Strategy

The demo uses device speech recognition through `speech_to_text`.

Recommended later evolution:

1. demo stage: `speech_to_text` on device
2. beta stage: upload audio to backend for better transcript quality
3. production stage: hybrid flow with local live captions plus server refinement

## Suggested Folder Layout

```text
apps/meeting_assistant_mobile/
├── pubspec.yaml
├── README.md
└── lib/
    ├── main.dart
    ├── app.dart
    ├── core/
    ├── models/
    ├── services/
    └── screens/
```

## Next Technical Steps

1. install Flutter locally
2. run `flutter create .` inside the app directory to generate platform wrappers
3. run the demo on Android
4. connect the app to the Python backend after the local-only flow feels right
