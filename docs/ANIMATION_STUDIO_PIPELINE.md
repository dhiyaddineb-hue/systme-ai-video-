# Animation studio pipeline

This repository now has an independent animation path. The existing still-image and documentary video paths are unchanged.

## Production stages

`Creative Brief → Script → Character & Environment Bible → Storyboard → Animatic → Shot Production → Voice & Sound → Edit → QC → Export`

The first proof lives in `package_silent_valley/animation_v1/` and is intentionally isolated from `experiment_v4/` and `episode_v5/`.

## Selected method

The proof uses deterministic **2D cutout keyframe animation**. The renderer creates RGBA character/prop layers, places them at joints, interpolates keyframes with easing, and composites them over a generated background plate. It is not frame-by-frame drawn animation and it is not text-to-video or image-to-video generation.

`vtsys/animation2d.py` is the reusable renderer. `animation_v1/build.py` is the resumable proof build entry point. A future shot can be regenerated without rebuilding other shots by giving it an isolated frame range and asset directory.

## Proof acceptance gate

The current proof is a 20-second technical proof with three shots:

- A01: establish snowy cabin and character approach.
- A02: reach toward and interact with the axe/cabin area.
- A03: recoil/reaction and settle into a stable ending.

QC requires review of the first, middle, and last moments of each shot, plus natural-speed playback. The generated `qc/start.jpg`, `qc/mid.jpg`, and `qc/end.jpg` are inspection artifacts, not evidence that a longer episode is approved.

`vtsys/animation_qc.py` verifies frame/fps/duration consistency and video/audio streams. Visual review remains human/art-director work: reject identity drift, limb deformation, foot sliding, object changes, flicker, intersections, jumps, and audio/action mismatch.

## Capability and limitation record

- Image generation and Arabic speech generation are available.
- Local Pillow/ffmpeg rendering is available.
- No Arena video-generation or image-to-video tool was used.
- No lip-sync tool was used; the manifest explicitly records `lip_sync: false`.
- Narration remains external voice-over using the approved `voice-05`; it is not an imitation of the reference narrator.
- The current procedural rig is a capability prototype and must receive visual/art-direction approval before a full episode. Generated source sheets are retained as references for the next layer-segmentation pass.

## Resumability and provenance

`scene.json` retains shot function, state, action, camera, sound and continuity requirements. `manifest.json` records animation type, frame count, timing, generated assets and limitations. Build outputs are named by version and do not overwrite approved documentary deliverables.
