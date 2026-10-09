"""
Método Grid — 4 prompts for consistent AI character across all video scenes.
Based on: PERSONAGENS CONSISTENTES em Vídeos de IA: Método Grid (VEO 3 e Nano Banana 2)

Flow:
  1. REFERENCE_SHEET  -> 5-panel contact sheet with front/side/back views
  2. SCENE_GRID       -> 2x2 storyboard (4 camera angles A/B/C/D)
  3. FRAME_EXTRACTION -> isolate one panel (A/B/C/D) to standalone 4K image
  4. VEO_ANIMATION    -> animate the extracted frame with Veo 3
"""

REFERENCE_SHEET_PROMPT = """\
– TOP PRIORITY: Every panel must show the exact same person as the reference image.
Identical face structure, skin tone, hair color, hair style, and clothing. No variation between panels.
Create a 5-panel character contact sheet.
Format: 16:9 landscape. Solid light gray background (#CCCCCC) throughout.
Remove all original background — character appears only against flat gray in all panels.
Layout — two columns side by side:
  LEFT COLUMN (35% of total width, full height): Two stacked panels of equal height:
    Panel 1 (top): Head close-up, front view — face and neck only, looking directly at camera
    Panel 2 (bottom): Head close-up, side profile — face and neck only, 90 degree turn, left profile
  RIGHT COLUMN (65% of total width, full height): Three equal vertical panels side by side:
    Panel 3: Full body front — head to toe, neutral standing pose
    Panel 4: Full body side — head to toe, left side view
    Panel 5: Full body back — head to toe, facing away from camera
Lighting: Soft, flat, even studio lighting across all panels. No shadows, no dramatic lighting.
Style: Photorealistic, hyperrealistic, 8K resolution, thin clean borders separating all panels.
CHARACTER DESCRIPTION: {character_description}
"""

SCENE_GRID_PROMPT = """\
CONSISTENCY – TOP PRIORITY: Extract character appearance exclusively from the attached reference \
images and contact sheets.
Every panel must show the exact same person. Identical face, skin tone, hair, clothing in every panel.
Act as a Lead Storyboard Artist and Cinematographer for a high-budget film production.
Generate a 4-panel (2x2 grid) storyboard sequence showing the same scene from four different \
camera angles.
PANEL LABELING: Each panel must be clearly labeled with an alphanumeric identifier in its \
top-left corner: A, B, C, D.
CINEMATIC VARIETY: Mix Wide Shots (WS) for scale, Medium Shots (MS) for action, Close-Ups (CU) \
for emotion, and at least one dynamic angle (low angle, Dutch angle, or aerial).
USER SCENE INPUT: {scene_description}
8K resolution, 16:9 format.
"""

FRAME_EXTRACTION_PROMPT = """\
1. FRAME SELECTION: Isolate exactly the composition, camera angle, and framing corresponding \
to panel: {panel_letter} from the provided 2x2 storyboard grid.
2. CHARACTER CONSISTENCY – TOP PRIORITY: Extract character appearance exclusively from the \
attached character contact sheets.
   Replicate exact facial features, skin tone, hair color and style, body proportions, and \
clothing colors/textures.
3. SCENE, LIGHTING & TECHNICAL ACCURACY: Use the scene grid panel exclusively to capture \
environment, lighting conditions, atmospheric mood, color palette, time of day and weather effects.
4. FINAL OUTPUT: Single standalone image, ultra-high resolution, 4K cinematic standard. \
Photorealistic.
   Remove all panel labels and grid lines from the output.
"""

VEO_ANIMATION_PROMPT = """\
ANIMATION INSTRUCTIONS – READ BEFORE GENERATING:
Animate exactly the scene shown in the attached scene image.
The scene image is the sole reference for environment, lighting, atmosphere, camera angle, \
composition and all visual elements.
The attached character contact sheets are used exclusively to anchor the physical appearance \
of characters in the scene.
Extract facial features, skin tone, hair color, hair style, body proportions and clothing \
details from the contact sheets.
SCENE TO ANIMATE: {scene_description}
Camera movement: {camera_movement}
Duration: {duration_seconds} seconds
Style: Cinematic, photorealistic, smooth motion
"""

GRID_PROMPTS = {
    "reference_sheet": REFERENCE_SHEET_PROMPT,
    "scene_grid": SCENE_GRID_PROMPT,
    "frame_extraction": FRAME_EXTRACTION_PROMPT,
    "veo_animation": VEO_ANIMATION_PROMPT,
}

CAMERA_MOVEMENTS = {
    "static":    "Static camera, no movement",
    "slow_zoom": "Slow cinematic zoom in, subtle",
    "pan_left":  "Slow pan left",
    "pan_right": "Slow pan right",
    "pull_back": "Slow pull back reveal",
    "push_in":   "Slow push in toward subject",
    "orbit":     "Slow orbital movement around subject",
}

PANEL_ANGLES = {
    "A": "Wide Shot (WS) — full environment visible",
    "B": "Medium Shot (MS) — subject waist up",
    "C": "Close-Up (CU) — face and emotion",
    "D": "Dynamic angle — low angle, Dutch tilt, or aerial",
}
