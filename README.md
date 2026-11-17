# Pulse Studio v0.5 — Android piano roll with automatic C64 Serum reference

A standalone Android app with a piano roll, keyboard, play/pause/stop/rewind/loop, project save/load, sound controls and effects, and WAV/MP3 export.

## Automatic sound initialization
On first launch, the app fetches the public A/B comparison's **original Serum rendering** for **LD C64 Lead [AS]**, decodes it and stores the MP3 in app-private storage. It then uses short note regions from that recording as a multisampled sound bank. No user-provided Serum binary, preset files, PC rendering, file selection, or manual conversion are required.

Public recording: https://btesser.github.io/serum2vital/factory-leads/ (author's paired original Serum vs Vital sound comparison). Direct retrieval: https://raw.githubusercontent.com/btesser/serum2vital/gh-pages/factory-leads/LD%20C64%20Lead%20%5BAS%5D%20-%20serum.mp3

**Important limitations**: The reference is a short phrase (notes C3 / E♭3 / F3 / G3) rather than an exhaustive note-by-note multisample library. The app pitch-shifts those notes across the piano roll, so the timbre and built-in effects can change as they are transposed. This is closer to the original recording than the generic oscillator used in v0.4, but does **not** run the proprietary Serum engine. The first launch needs internet to retrieve the reference, then the cached reference can play offline. If the external recording becomes unavailable, it cannot be loaded by the app.

Other Serum 1 .fxp presets continue to use an approximate parameter mapping, and Serum 2 presets parse metadata only. These features are not equivalent to full Serum compatibility. The app does not package or redistribute the original comparison audio; the user fetches it from the publisher's public URL in-app.

## Build
Requires Java 17, Android SDK 35, Gradle 8.10.2 and lamejs 1.2.1. Build `gradle assembleDebug` or use the included GitHub Actions workflow; the workflow verifies app startup, button visibility, WAV/MP3 export, automatic reference loading and non-silent reference note rendering in an Android emulator.

Not affiliated with Xfer Records, Serum, Adam Szabo, or Image-Line.
