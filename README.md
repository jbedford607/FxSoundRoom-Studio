# FxSound Room Studio — Windows build

This repository is the Windows build workspace for the FxSound Room Studio source modification.

## Current status

- The original, modified source archive is **not yet uploaded**.
- The Windows CI workflow is configured to accept the source archive, execute five DSP regression tests, and compile the FxSound application using Visual Studio 2022.
- The archive contains a **source-only** advanced correction module (REW/EQ APO filter import, multichannel convolution, CamillaDSP export). Those features are not yet verified in a Windows-built installer.
- Dragonfly Reverb, Cavern QuickEQ, Eary's Spatial Expander, FluidEQ and live CamillaDSP processing are **not** bundled.

## One-time source upload

Upload **`FxSoundRoom-Advanced-Correction-Source.zip`** to the **root** of this repository, without extracting it. The file is approximately 7 MB.

This automatically triggers **Actions → Build FxSound Room Studio (Windows)**. A green build contains a compiled `FxSoundRoom.exe` artifact. Red indicates tests or compilation need fixing (open the failed step's log).

The workflow intentionally **does not install or repackage the audio driver unless all original signed driver/package assets are provided**. A compiled app without the virtual audio driver is not a standalone working audio installation.

## Technical details

- Windows Server 2022 hosted runner (Visual Studio 2022 and Windows SDK)
- Vendored JUCE modules unpacked to `C:\JUCE\modules`
- Native C++ tests: AdvancedCorrection, RoomEngine, RoomStudioEngine, Analysis and OutputLimiter
- MSBuild: `fxsound/Project/FxSound.sln` — Release, x64
- AGPL-3.0-or-later FxSound source; see `LICENSE` in the ZIP

The original FxSound virtual audio driver is separately distributed by FxSound. Windows CI cannot verify physical speakers, audio quality, installed driver behaviour, or live GUI appearance.

**Note:** The repository is currently public. GitHub repository visibility can be changed in Settings → General → Danger Zone if private storage was intended.
