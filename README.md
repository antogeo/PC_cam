# PC Cam

A simple desktop camera app for the PC: record videos and take photos from
your webcam, and choose the camera, resolution and output size.

## Why this project exists

I got tired of the apps crashing on my system, and I found it faster to
vibe code a video recorder.

## Features

- Live preview, photo and video capture
- Choose the camera, the supported resolution and the output size
- Record as many videos as you like; each clip appears with a thumbnail in a
  clips panel at the bottom of the window
- Choose which clips to keep: untick the ones you don't want, then save the
  rest or discard them
- Double-click a clip to play it back; closing the preview never deletes it
- Save to `~/Videos/PC Cam` by default, or pick any folder (your last choice is
  remembered)
- Option to keep the clips panel always visible
- Microphone audio in videos

## Install and run

    conda create -n pc_cam python=3.11
    conda activate pc_cam
    pip install -r requirements.txt
    python main.py

Videos are saved to `~/Videos/PC Cam` and photos to `~/Pictures/PC Cam`.

## Tests

    pytest
