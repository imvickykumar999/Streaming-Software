
### 1. Installation

First, ensure you have PyInstaller installed in your environment:

```bash
pip install pyinstaller

```

### 2. The Build Command

Navigate to your `YTstream` directory and run:

```bash
pyinstaller --onefile --windowed --icon=YouTubeLiveStream.jpg YouTubeLiveStreamFolder.py

```

---

### Suno & Specterr Workflow

Since you are creating Phonk content, here is how to use that prompt effectively across both platforms:

#### **Suno.com (Audio Generation)**

Paste the prompt into the **"Style of Music"** box. If you are using **Custom Mode**, put the lyrics in the lyrics box and use the prompt below for the "Style" field:

> **Style Prompt:** Aggressive Brazilian Phonk, industrial Mandelão rhythm, rhythmic stutter 808 bass, 130 BPM, male phonk vocals, metallic percussion, sharp Memphis cowbell, distorted kick.

#### **Specterr.com (Video Generation)**

Once you upload your Suno track to Specterr, use these settings to match the "Aggressive Phonk" vibe:

* **Preset:** Choose a "Particles" or "Glitch" heavy preset.
* **Audio Reactivity:** Set the **Bass Sensitivity** to high. Since Phonk relies on the 808 "stutter" bass, you want the visuals to pulse aggressively with the kick.
* **Particles:** Increase the "Speed" and "Amount" to match the 130 BPM energy.

### A Quick Tip for your SaaS

Since you're scaling this for clients, remember that PyInstaller executables are often flagged by Windows Defender as "unrecognized apps" because they aren't digitally signed.
