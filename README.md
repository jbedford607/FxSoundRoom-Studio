# FxSound Room Studio — Windows build workspace

Customized FxSound Room Studio with two simplified audio-effects pages:

## Stereo ambience
- Stereo hall reverb with real decay, predelay, high-frequency damping, and wet mix
- Soft chorus for subtle depth, without panning, orbiting, or ping-pong movement

## 7.1 ambience
- Dedicated late/diffuse reverb feeding **only** side and rear speakers
- Four independent wet-only speaker sends (side left/right, rear left/right)
- The reverb stage leaves front L/R, centre, and LFE unchanged
- Original room feedback / 8-line FDN algorithm / imported WAV convolution remain selectable
- Existing 7.1 upmix, room correction, microphone calibration, and speaker-room configuration retained

Removed from the active effects interface: orbit echo, ping-pong echo, moving phaser, manual stereo width, fake rear decay spread, and tuned-note send controls. Older tuned-note sends are disabled when settings load.

## Windows build

The repository contains a source archive and **[GitHub Actions Windows build workflow](../../actions)**.
On a Windows Server 2022 runner, the workflow:
1. Extracts the source archive
2. Applies the advanced surround, legacy Stereo/7.1, and latest ambience replacement patches
3. Runs the native DSP regression tests
4. Builds the GUI with Visual Studio 2022 and JUCE
5. Uploads a compiled application artifact and an exact source ZIP

The latest passing workflow run is [Ambience Cleanup](../../actions/runs/43901620697). The compiled app by itself requires the original signed FxSound virtual audio driver. The separate NSIS installer handed to the user bundles unchanged original driver files.

**Verification limits:** automated DSP tests and Windows compilation passed. Live Windows audio, GUI layout and speaker hardware playback were not tested.

## License

The FxSound-derived code is governed by its AGPL-3.0-or-later license, included in the bundled source. No third-party VST plugin binaries are included.
