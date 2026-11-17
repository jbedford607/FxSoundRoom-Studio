# Pulse Studio — Android synthesizer prototype

Offline Android music sequencer. Piano roll, touch keyboard, WAV/MP3 export, JSON project saving, Serum 1 FXP parameter reader, Serum 2 metadata reader, 10 functioning WebAudio effects, and WAV multisample playback.

**Not the proprietary Serum engine.** FXP import maps supported oscillator/envelope/FX parameter values; unsupported wavetables, Serum-specific DSP and modulations are not accurately reproduced. Serum 2 file import presently uses only metadata (experimental approximation). For original timbre import a WAV sample exported from your own synth, tuned to C4. External Serum wavetables not bundled.

Build with Java 17, Android SDK 35, Gradle 8.10.2 and lamejs 1.2.1. Run `gradle assembleDebug`. Debug APK is at `app/build/outputs/apk/debug/app-debug.apk`.
