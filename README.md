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


## Ambience Focus upgrade (17 November 2026)

Latest verified workflow: [Windows build 43904341402](../../actions/runs/43904341402). The build passed **eight** native DSP regression suites and produced a Windows x64 application artifact.

The **7.1 ambience** page has four additional native audio functions:

- **Stereo ambience extraction:** Uses adjustable stereo difference information to emphasize spatial/background material. It is not machine-learning source separation.
- **Reverb ducking:** A real-time envelope follower reduces only the wet late-reflection signal during strong direct sound.
- **Frequency-based ambience:** Independent low-cut (40–4000 Hz) and high-cut (1000–18000 Hz) controls operate on the reverb input.
- **Wet-only 7.1:** When the source appears to be stereo-derived 7.1, suppresses synthesized direct side/rear content and routes late reverb to the four ambient speakers. Preserves native side/rear channels when genuine multichannel input is detected.

The upmix algorithm, stereo hall, subtle chorus, speaker-specific side/rear send levels, and imported correction options remain.

The modified application includes persistent settings and a larger scrollable 7.1 page. The original driver is retained unchanged in the separately distributed NSIS installer; it is not re-signed or replaced.

**Testing:** Automated DSP unit tests and Windows Visual Studio build passed; live audio playback on physical 7.1 hardware and visual GUI inspection remain unverified.



## Live Stem Matrix (17 November 2026)

Latest **passing** Windows CI run: [43913561369](../../actions/runs/43913561369). Nine native DSP regression test executables passed, followed by Windows x64 MSBuild. New source: `upgrade/LiveStemMatrix.h`, `upgrade/LiveStemMatrixTest.cpp`, `upgrade/ApplyLiveStemMatrix.py`.

The **Live stems** GUI tab provides:
- Four *DSP-estimated*, not AI-isolated, music groups: bass/low end, centered (vocal-like) audio, percussive transients, stereo-side details.
- A true **4 × 8 speaker matrix**: assign any subset of FL, FR, center, LFE, rear-left/right, side-left/right to each group.
- Independent gain sliders, live signal-level meters, center/drum sensitivity and bass cutoff.
- Three useful routing presets (Studio band, Rhythm in surround, Gentle overlay), a full reset, and Solo audition modes that mute the original to reveal exactly what the estimator extracted.
- Optional replacement of existing synthetic side/rear content, without clearing genuine native discrete 7.1 source channels.
- Saved routing state, initially disabled. Operates only when audio is rendered in Windows 7.1 layout from an L/R source.

**What it is not:** there is no bundled neural instrument-separation model, and these four groups are **not isolated vocals, drums, guitar or bass stems** in the Demucs sense. A center-panned instrument can be included in the vocal-like group; kicks and bass may overlap; stereo-difference details may include ambience and effects. No extra algorithmic sample-buffer/lookahead is introduced by this processor; Windows audio buffers still contribute latency.

The original signed FxSound driver remains untouched in the separately packaged NSIS installer. Automated DSP tests and compiler build passed; GUI interaction and live speaker playback have not been verified on a physical Windows 7.1 system.
