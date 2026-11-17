# Pulse Studio v0.5 — Android piano roll with automatic C64 Serum reference

A standalone Android app with a piano roll, keyboard, play/pause/stop/rewind/loop, project save/load, sound controls and effects, and WAV/MP3 export.

## Automatic sound initialization
The APK build automatically retrieves and bundles the public A/B comparison's **original Serum rendering** for **LD C64 Lead [AS]**, then the app loads it locally on startup. If the bundled asset isn't present, the app can also fetch and privately cache the recording. It then uses short note regions from that recording as a multisampled sound bank. No user-provided Serum binary, preset files, PC rendering, file selection, or manual conversion are required.

Public recording: https://btesser.github.io/serum2vital/factory-leads/ (author's paired original Serum vs Vital sound comparison). Direct retrieval: https://raw.githubusercontent.com/btesser/serum2vital/gh-pages/factory-leads/LD%20C64%20Lead%20%5BAS%5D%20-%20serum.mp3

**Important limitations**: The reference is a short phrase (notes C3 / E♭3 / F3 / G3) rather than an exhaustive note-by-note multisample library. The app pitch-shifts those notes across the piano roll, so the timbre and built-in effects can change as they are transposed. This is closer to the original recording than the generic oscillator used in v0.4, but does **not** run the proprietary Serum engine. The published sound recording is bundled into the APK, so normal playback works offline without user setup. Source credit is retained below; redistribution permissions of the sound recording have not been independently verified.

Other Serum 1 .fxp presets continue to use an approximate parameter mapping, and Serum 2 presets parse metadata only. These features are not equivalent to full Serum compatibility. The app bundle includes a copy of the short comparison recording; do not assume this grants unrestricted rights to redistribute the recording commercially.

## Build
Requires Java 17, Android SDK 35, Gradle 8.10.2 and lamejs 1.2.1. Build `gradle assembleDebug` or use the included GitHub Actions workflow; the workflow verifies app startup, button visibility, WAV/MP3 export, automatic reference loading and non-silent reference note rendering in an Android emulator.

Not affiliated with Xfer Records, Serum, Adam Szabo, or Image-Line.
