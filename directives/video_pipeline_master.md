# Video Pipeline — Master Directive

> Type: **Project SOP — NON-NEGOTIABLE**
> Status: **ACTIVE**
> Last updated: 2026-03-23

---

## Purpose

Produce short-form vertical videos (6:19 aspect ratio, ~30 seconds) for Filipino parenting education content on Instagram Reels and TikTok. Every video follows an identical structure using locked assets.

---

## ⚠️ NON-NEGOTIABLE RULES

These rules CANNOT be deviated from. If a deviation is detected before generation, **STOP and report it to the user**.

### Rule Set 1: Video Structure (always 3-item listicle)

| Scene | Content | Duration | Who |
|-------|---------|----------|-----|
| 1. HOOK | Anchor character speaks the hook line | 4 seconds | Anchor |
| 2. RULE 1 LEAD | Anchor says "Number one..." + the phrase | 4 seconds | Anchor |
| 3. RULE 1 B-ROLL | Visual illustrating Rule 1 | 4 seconds | B-roll |
| 4. RULE 2 LEAD | Anchor says "Number two..." + the phrase | 4 seconds | Anchor |
| 5. RULE 2 B-ROLL | Visual illustrating Rule 2 | 3-4 seconds | B-roll |
| 6. RULE 3 LEAD | Anchor says "Number three..." + the phrase | 3-4 seconds | Anchor |
| 7. RULE 3 B-ROLL | Visual illustrating Rule 3 | 3-4 seconds | B-roll |
| 8. CTA | Anchor smiles warmly, hands together, requests sharing | 3-4 seconds | Anchor |

**Total**: ~28-34 seconds | Always exactly 3 items | Never 5, never 2, always 3.

### Rule Set 2: Tool Assignments (non-negotiable)

| Task | Tool | Notes |
|------|------|-------|
| **Steps 1-3** (concept, script, prompts) | ChatGPT 5.4 (maximum model) | Concept planning, scriptwriting, image prompt generation |
| **Image generation** | Nanobanana PRO (Higgsfield API) | All images — anchor and B-roll |
| **Anchor video generation** | Google Veo 3.1 | Native lip-sync, voice blueprint |
| **B-roll video generation** | Kling 3.0 | Motion animation, no lip-sync needed |
| **Aspect ratio** | 9:16 | Always. Standard vertical format for Reels/TikTok |

### Rule Set 3: Audio Mixing Levels

| Track | Volume Level |
|-------|-------------|
| **BGM** (background music) | 50% |
| **Anchor character speech** | 100% |
| **B-roll video original audio** | 25% |

**Locked audio assets** (use for EVERY video):
- BGM: `examples/audio_lock/bgm_track.mp3`
- SFX rule chime: `examples/audio_lock/sfx_rule_chime.mp3`
- SFX transition whoosh: `examples/audio_lock/sfx_transition_whoosh.mp3`

### Rule Set 4: Character Rules

**Anchor character**: LOCKED. Use the reference images from `examples/anchor_character_lock/` for EVERY anchor scene. Never change, never deviate.

**Locked anchor character description** (copy-paste verbatim into every anchor prompt):
```
A warm 3D-animated Pixar-style digital illustration of a Filipina grandmother 
(Lola) in her late 50s to early 60s, with grey-streaked black hair pulled back 
in a neat low bun, warm medium-brown skin with gentle smile lines and soft 
wrinkles around the eyes, kind dark brown eyes, small pearl stud earrings, a 
gentle warm smile with soft rounded cheeks, and a natural Filipino facial 
structure. She wears a cream/beige embroidered blouse with delicate vine and 
floral embroidery down the center front, small buttons, short sleeves. She 
sits in a wooden chair with a warm backrest.
```

**Locked anchor background description** (copy-paste verbatim into every anchor prompt):
```
The background is a cozy Filipino home interior with warm cream/beige walls, 
framed family photos on the walls, a potted green plant (pothos) to one side, 
a warm golden glow from natural light through a window, a tablecloth-covered 
side table with more framed photos and a vase of flowers, warm terracotta and 
wood tones throughout. The overall color palette is warm cream, amber, golden 
brown, and soft green accents.
```

**B-roll characters**: Must always be **11-13 year old students**. Not younger, not older. This is non-negotiable.

### Rule Set 5: Approval Workflow

1. **After topic + script + scene prompts are written (Steps 1-3)** → present to user for review BEFORE generating any images
2. After EVERY image generation → present to user for review
3. After EVERY video generation → present to user for review
4. If user approves → proceed to next step
5. If user does NOT approve → regenerate and ask again
6. Never proceed past any approval gate without explicit approval

### Rule Set 6: Deviation Reporting

Before generating ANY asset (image, video, audio), check all rules above. If there is ANY deviation from the locked rules:
1. **STOP immediately**
2. **Report the deviation** to the user
3. **Wait for instruction** before proceeding

### Rule Set 9: Client Critical Feedback (NON-NEGOTIABLE — 2026-03-23)

> **Source**: Direct client feedback. These are permanent production rules for ALL videos going forward. Violating any of these is a blocker for client acceptance.

#### 9.1 Language & Audio Stability
- **ALL dialogue must be in PURE ENGLISH ONLY.** No Filipino accent. No Tagalog. No code-switching.
- **CRITICAL (2026-03-23)**: Specifying "Filipino accent" or "Filipino-English accent" in Veo 3.1 voice prompts causes the model to inject Tagalog words and stutter/repeat dialogue. This is a **non-negotiable blocker**.
- Audio delivery must sound **stable and fluid** — never choppy or laggy.
- If generated audio has stuttering, repeated words, Tagalog, or choppy cadence → **reject and regenerate immediately**.
- **NEW Voice blueprint**: `"Warm maternal tone, clear English, medium pace, gentle authority. Brief pauses before key phrases as if thinking."`
- **BANNED from voice prompts**: "Filipino", "Tagalog", "accent", "dialect", any non-English language reference

#### 9.2 Typography — Premium & Cinematic
- **LOCKED FONT**: `Kalam-Bold.ttf` (handwritten/calligraphic bold) at `assets/fonts/Kalam-Bold.ttf`
- Font style must feel **high-end and cinematic** — like a professional movie or a well-told story.
- **Never use generic, basic, or "tech/startup" fonts** (including Poppins). The feel must be warm, editorial, and story-like.
- All text overlays must reinforce the premium cinematic feel.
- Font sizes: Line 1 = 44px white, Line 2 = 50px yellow (#FFD700), shadow offset 3px, alpha 200

#### 9.3 Camera Work — Very Gradual Zoom Only
- **NO noticeable zoom-in/zoom-out** on anchor scenes. The only acceptable camera movement is a **very gradual, almost imperceptible slow push-in** (dolly) over the full clip duration.
- If the zoom is noticeable to a casual viewer → **reject and regenerate**.
- Prompt wording: use "near-static", "extremely subtle push-in", "barely perceptible dolly in" — NEVER "slow dolly in" alone (Veo interprets this as too fast).
- **Gold standard**: The A3 (Rule 2) anchor video — smooth, barely-moving camera. Use this as the quality bar.
- If a generated video has any zoom oscillation (in/out/in) → **reject immediately**.
- B-roll camera: gentle, organic movement only (no rapid zooms, no whip pans).

#### 9.4 Illustration Quality — Reject Unnatural Poses
- ALL AI-generated scenes must look **natural and believable** within the art style.
- Any scene that looks "off" or unnatural must be **replaced or refined** before delivery.
- **Specific red flag**: characters performing awkward/unrealistic actions (e.g., clapping while staring at a light bulb). These must be caught during review and regenerated.
- **Rule**: After every B-roll image generation, critically evaluate: "Does this look like something a real person would naturally do?" If no → regenerate with a more natural action.

#### 9.5 Pacing & Transitions — Balanced ~4s Rhythm
- Scene transitions must occur roughly **every 4 seconds**. This is the target rhythm.
- **No scene should exceed 5 seconds** on screen. If an anchor clip is 6-8 seconds, it must be trimmed or split.
- **No scene should be shorter than 2 seconds** — if a B-roll clip is only 1-2 seconds, extend it or adjust the cut point.
- Target balance: every clip in the final timeline should be **3-5 seconds** in duration.
- Unbalanced pacing (e.g., 8s anchor then 1s B-roll) is explicitly **rejected by the client**.

#### 9.6 Veo 3.1 Anti-Stutter — NO Repeated Words (NON-NEGOTIABLE)
- Veo 3.1 sometimes causes the character to **repeat the same word/phrase multiple times** (sounds like stuttering). This is a critical defect — **reject and regenerate immediately**.
- **Root cause**: Dialogue that is too long, has complex sentence structure, or contains quoted-within-quoted speech.
- **Prevention rules**:
  1. Keep dialogue to **≤8 words per clip** (stricter than the previous ≤10 limit)
  2. Use simple, direct sentence structure — no nested quotes or parenthetical phrases
  3. Place `...` pauses between every 2-3 words to give Veo natural breathing room
  4. Avoid words that are hard to lip-sync (long multisyllabic words, tongue twisters)
  5. Test pattern: `"[2-3 words]... '[2-3 word phrase].'"` — this is the proven safe structure
- **Gold standard**: The A3 (Rule 2) video (`"Number two... 'Let them choose the book.'"`) — zero repeated words, clean delivery. Model ALL anchor prompts after this.
- **If a video has ANY word repetition** → reject, do NOT deliver to client

### Rule Set 10: Video QA Checklist (NON-NEGOTIABLE — 2026-03-23)

> **Source**: Generalized from client review feedback. Apply as standing checks for EVERY generated video before presenting for approval.

#### 10.1 Character Differentiation
- Characters in the same scene **must be visually distinct**. Avoid generating faces that look alike for different characters (e.g., mother and child must have clearly different facial features, proportions, and age-appropriate appearance).
- **Check**: After every B-roll image generation, verify that each character is immediately distinguishable.

#### 10.2 Audio Pacing & Lip-Sync Naturalness
- Speech in anchor videos must have **natural, conversational pacing**. No unnatural or unusually long pauses between words/phrases.
- If generated dialogue sounds robotic, halting, or has dead gaps → **reject and regenerate**.

#### 10.3 Anchor Eye-Line / Gaze Direction
- The anchor **must maintain direct eye contact with the camera at all times** (unless the script explicitly calls for looking elsewhere).
- Off-camera gaze breaks immersion → **reject and regenerate**.

#### 10.4 Emotional Consistency Between Characters
- Every character's facial expression **must match the emotional context of the scene**.
- If a scene depicts a child complaining, the parent must NOT be smiling. If a scene depicts an upset child being comforted, the child must NOT appear happy.
- **Check**: Review each generated frame for emotional coherence across ALL characters present.

#### 10.5 Emotional Consistency Across Scene Types
- B-roll scenes depicting conflict, sadness, or frustration **must NOT show positive expressions** (smiling, laughing) unless the narrative has shifted to resolution.
- **Check**: Cross-reference the script's intended emotion before approving any generated clip.

### Rule Set 7: Anchor Video Quality Standard (Veo 3.1)

**Reference videos**: `examples/anchor_videos/` — these 4 videos represent the **gold standard** for lip-sync quality.

| Reference Video | Scene | Quality Benchmark |
|---|---|---|
| `scene_01_anchor_video.mp4` | Hook — warm welcome smile | Perfect lip-sync, natural head movement, warm expression |
| `scene_05_anchor_video.mp4` | Speaking — explaining gesture | Fluid hand gesture, natural mouth movement, gentle authority |
| `scene_08_anchor_video.mp4` | Speaking — three-finger gesture | Natural gesture timing synced with speech |
| `scene_11_anchor_video.mp4` | CTA — warm closing smile | Gentle nod, compassionate smile, natural lip movement |

**Quality rules for ALL anchor video prompts:**
1. Always upload the corresponding anchor character lock image as starting frame
2. Prompt structure: `Camera → Motion/Action → Lighting → Camera movement → Mood → Dialogue → Voice blueprint`
3. Lip-sync must match the quality in reference videos — natural, not robotic, with expressive eyes and subtle head movement
4. Dialogue must be written as what the character SAYS (direct speech), never as narration
5. Keep dialogue ≤10 words per clip to prevent fast-speech artifacts
6. Use `...` pauses in dialogue for natural rhythm
7. Camera: always smooth slow dolly in or subtle push-in, NEVER handheld
8. Every prompt must end with the full LOCKED VOICE BLUEPRINT verbatim
9. **LIP-SYNC IS NON-NEGOTIABLE** — Veo 3.1 lip-sync must be natural and perfect (per coursework `41_Consistent_Character_Voices_in_Veo_3.1`). If the generated video has robotic, desynced, or unnatural lip movement, it MUST be rejected and regenerated. Best practices: short dialogue (≤10 words), `...` pauses, voice blueprint verbatim, upload starting frame image

---

## Pipeline Steps (per video)

### Step 1-2: Concept Plan & Script (ChatGPT 5.4)
- **Tool**: ChatGPT 5.4 (maximum model)
- Follow the exact format from `examples/step1_2_concept_and_script.md`
- Topic must be a 3-item listicle in the Filipino parenting/education niche
- Script structure: Hook → Rule 1 → Rule 2 → Rule 3 → CTA
- Lock voice blueprint: `"Filipino-English accent (speaks English with a natural Filipino accent), warm maternal tone, medium pace, gentle authority. brief pauses before key phrases as if thinking. sentences taper off slightly with reassurance."`
- Each rule follows: `"Number [X]... '[phrase].' ...This [verb]... [keyword]."`
- Total ~55 words, ~2 words/second

### Step 3: Scene Image Prompts (ChatGPT 5.4 → Nanobanana PRO)
- **Prompt writing tool**: ChatGPT 5.4 (maximum model)
- **Image generation tool**: Nanobanana PRO (Higgsfield API)
- Follow the exact format from `examples/step3_scene_prompts.md`
- Use LOCKED character description (verbatim) for all anchor prompts
- Use LOCKED background description (verbatim) for all anchor prompts
- B-roll must show 11-13 year old students (NOT younger children)
- Aspect ratio: **6:19**
- Style suffix: `"Warm 3D-animated Pixar-style, smooth digital illustration, clean lines, warm color palette, soft lighting with gentle gradients. 6:19 vertical composition with space at top and bottom for text overlays. No photorealistic, no harsh shadows, no cold tones, no text, no watermark, no extra characters."`

### Step 4: Image Upscaling
- Upscale all generated images for quality
- Tools: Nanobanana PRO upscale or Bigjpg

### Step 6: Video Prompts & Generation
- Follow the exact format from `examples/step6_video_prompts.md`
- **Anchor videos**: Veo 3.1 (upload starting image, lip-sync dialogue)
- **B-roll videos**: Kling 3.0 (motion animation from starting image, **NO DIALOGUE** — ambient animation only)
- Voice blueprint copy-pasted verbatim into every anchor video prompt
- Dialogue kept short: max 10 words per clip
- Camera movements: subtle dolly in, no handheld shake
- **⚠️ QUALITY BAR**: Every anchor video must match the lip-sync quality of the reference videos in `examples/anchor_videos/`. Review against these before presenting for approval.

### Step 7: Audio Assembly
- BGM: `examples/audio_lock/bgm_track.mp3` at **50%** volume
- Anchor speech: **100%** volume
- B-roll original video audio: **25%** volume
- SFX: use chime and whoosh from `examples/audio_lock/`

### Step 8: Final Assembly (CapCut)
- Timeline per the timing breakdown in Step 1-2
- Text overlays on every scene (rule text + keyword)
- End card with no branding for now

---

## Reference Files (read-only, never modify)

| File | Purpose |
|------|---------|
| `examples/step1_2_concept_and_script.md` | Template for concept & script |
| `examples/step3_scene_prompts.md` | Template for scene image prompts |
| `examples/step6_video_prompts.md` | Template for video prompts |
| `examples/anchor_character_lock/` | Locked anchor character reference images (4 poses) |
| `examples/anchor_videos/` | **Gold standard** Veo 3.1 anchor videos — lip-sync quality benchmark (4 videos) |
| `examples/broll_scene_examples/` | B-roll scene reference images (7 scenes) |
| `examples/audio_lock/` | Locked audio files (BGM + 2 SFX) |

---

## Execution Scripts

| Script | Purpose |
|--------|---------|
| `execution/generate_anchor_scenes.py` | Generate anchor images via Higgsfield |
| `execution/generate_anchor_chatgpt.py` | Generate anchor images via ChatGPT (backup) |
| `execution/generate_broll_chatgpt.py` | Generate B-roll images via ChatGPT (backup) |
| `execution/generate_character_options.py` | Generate character options |

---

## Self-Annealing Log

*Append new learnings below as they are discovered during execution.*

### Learning 1: Character lock updated from mid-30s mom to grandmother (2026-03-21)
- The original `step3_scene_prompts.md` described a mid-30s Filipina mom
- The actual locked character (from `examples/anchor_character_lock/`) is a Filipina grandmother (~55-60yo) with grey-streaked hair in a low bun
- **Rule**: Always use the reference images, not the text description from the old step3 file
- The locked character description in this directive has been updated to match the actual reference images

### Learning 2: B-roll age range is 11-13, not 6-7 (2026-03-21)
- The original `step3_scene_prompts.md` B-roll showed children aged 6-8
- User explicitly requires 11-13 year old students in ALL B-roll scenes
- **Rule**: Never use children younger than 11 in any B-roll scene

### Learning 3: Anchor video quality bar from reference videos (2026-03-21)
- User provided 4 reference anchor videos (`examples/anchor_videos/`) as the gold standard
- These show perfect Veo 3.1 lip-sync: natural mouth movement, expressive eyes, subtle head nods
- **Rule**: Every new anchor video prompt must follow the same prompt structure and quality level
- The prompt pattern that produces this quality: Camera movement → Motion/action description → Lighting → Camera specification → Mood → Direct dialogue → Voice blueprint

### Learning 4: ChatGPT 5.4 for Steps 1-3 (2026-03-21)
- User specifies ChatGPT 5.4 (most advanced model) for all concept planning, scriptwriting, and image prompt generation
- **Rule**: Steps 1, 2, and 3 must always use ChatGPT 5.4

### Learning 5: Higgsfield API has NO Elements/Character endpoint (2026-03-21)
- Researched `docs.higgsfield.ai` — official API only supports: `prompt`, `aspect_ratio`, `resolution`
- No "Elements", "Create a Character", or "Digital Clone" endpoint exists in the API
- Character consistency is achieved via: (1) `reference_image` field in the POST payload, (2) locked verbatim prompt descriptions
- The existing script approach (reference_image + locked character desc) is the best available method
- **Rule**: For anchor consistency, always include reference image from `examples/anchor_character_lock/` in the API call

### Learning 6: Higgsfield API aspect ratio + reference image constraints (2026-03-21)
- API only supports: `9:16`, `16:9`, `4:3`, `3:4`, `1:1`, `2:3`, `3:2`
- `6:19` is NOT supported — returns 422 error
- **Workaround**: Generate at `9:16` and crop/resize to 6:19 in post-production if needed
- Reference images in the payload are also rejected (422) for the `soul/standard` model
- **Workaround**: Character consistency relies on locked verbatim prompt descriptions only
- **Rule**: Always use `9:16` for Higgsfield API, never `6:19`

### Learning 7: Higgsfield NSFW filter — false positives and avoidance (2026-03-21)
- ALL prompts (7/7) were flagged NSFW — both anchor and B-roll — even with innocuous content
- **Triggers identified**: (1) reference images uploaded via `reference_image` field, (2) detailed physical descriptions of characters, (3) mentions of physical contact between adults and children ("arm around shoulder", "hugging", "leaning in close")
- **Fixes applied**: (a) remove `reference_image` from payload, (b) simplify character descriptions, (c) describe B-roll students independently (no adult-child physical contact), (d) add "Family-friendly, wholesome, safe for work" to every prompt
- **Rule**: Always include "family-friendly, safe for work" in Higgsfield prompts
- **Rule**: Never use `reference_image` field — Higgsfield rejects it AND it may trigger NSFW
- **Rule**: For B-roll with students, show students independently or with minimal interaction — avoid describing physical contact

### Learning 8: NEVER regenerate anchor images — reuse locked originals (2026-03-21)
- Generating new anchor images ALWAYS fails character consistency — Higgsfield produces wrong character, and text-to-image alone can never match the locked Lola exactly
- **5 locked anchor images** at `examples/anchor_character_lock/` are the ONLY source of truth
- These are already upscaled — skip upscale step for anchor images
- **Rule**: NEVER generate new anchor character images. ALWAYS copy from `examples/anchor_character_lock/`
- **Rule**: Only B-roll images need generation (via `gpt-image-1.5` with `1024x1536`)
- **Rule**: Only B-roll images need upscaling (if needed). Anchor images are pre-upscaled.

### Rule Set 8: Anchor Image Nomination (NON-NEGOTIABLE)
**This is a permanent, locked mapping. Use these EXACT images for EVERY video.**

| Slot | Source File | Scene | Description |
|------|-----------|-------|-------------|
| A1 — Hook | `scene_01_anchor_upscaled.png` | Hook (4s) | Warm gentle smile, hands on armrests |
| A2 — Rule 1 | `scene_02_anchor_upscaled.png` | Rule 1 speaking (4s) | Speaking, open palm explaining gesture |
| A3 — Rule 2 | `scene_05_anchor_upscaled.png` | Rule 2 speaking (4s) | Finger raised, teaching gesture |
| A4 — Rule 3 | `scene_08_anchor_upscaled.png` | Rule 3 speaking (3-4s) | Three fingers raised |
| A5 — CTA | `scene_11_anchor_upscaled.png` | CTA closing (3-4s) | Warm closing smile |

- **Total structure per video**: 5 anchor segments + 3 B-roll segments = 8 scenes
- **Rule**: This mapping MUST be used for every new video — no exceptions
- **Rule**: When starting a new video, copy these 5 files into the video's `images/` folder
- **Rule**: The anchor images feed directly into Veo 3.1 for video generation

### Learning 9: ChatGPT image model is gpt-image-1.5 (2026-03-21)
- `chatgpt-image-latest` requires org verification (403 error)
- The correct model to use is `gpt-image-1.5`
- Supported sizes: `1024x1024`, `1024x1536` (portrait), `1536x1024` (landscape), `auto`
- For 9:16 portrait output, use `1024x1536`
- **Rule**: B-roll image generation uses `gpt-image-1.5` at `1024x1536`

### Learning 10: Video Generation API Endpoints (PERMANENT — never re-research)

#### Veo 3.1 (Anchor Videos — Lip-Sync)
- **SDK**: `google-generativeai` Python package (`pip install google-generativeai`)
- **Env var**: `GOOGLE_AI_STUDIO_API_KEY`
- **Model**: `veo-3.1-generate-preview`
- **Python pattern**:
  ```python
  from google import genai
  from google.genai import types
  import base64, time
  client = genai.Client(api_key=API_KEY)
  # Load image as bytes
  with open("anchor.png", "rb") as f:
      image_bytes = f.read()
  image = types.Image(image_bytes=base64.standard_b64encode(image_bytes).decode(), mime_type="image/png")
  operation = client.models.generate_videos(
      model="veo-3.1-generate-preview",
      prompt="...",
      image=image,
      config=types.GenerateVideosConfig(
          aspect_ratio="9:16",
          person_generation="allow_all",
      )
  )
  while not operation.done:
      time.sleep(10)
      operation = client.operations.get(operation)
  video = operation.response.generated_videos[0]
  client.files.download(file=video.video)
  video.video.save("output.mp4")
  ```
- **Parameters**: `aspect_ratio` ("9:16"), `person_generation` ("allow_all"), `duration_seconds` (not needed — Veo auto-determines)
- **Resolution**: 720p, 1080p, or 4k
- **Async**: Returns an operation; poll with `client.operations.get(operation)` until `operation.done`

#### Kling 3.0 (B-roll Videos — Motion Animation, NO dialogue)
- **Auth**: JWT (PyJWT library). Generate token from access_key (AK) + secret_key (SK)
- **Env vars**: `KLING_ACCESS_KEY`, `KLING_SECRET_KEY`
- **Base URL**: `https://api-singapore.klingai.com`
- **Create task**: `POST /v1/videos/image2video`
- **Query task**: `GET /v1/videos/image2video/{task_id}`
- **Model**: `kling-v3`
- **Mode**: `pro` (best quality)
- **Duration**: `"5"` (seconds, string)
- **Sound**: `"off"` (no dialogue for B-roll)
- **Auth header**: `Authorization: Bearer <JWT_TOKEN>`
- **JWT generation**:
  ```python
  import jwt, time
  headers = {"alg": "HS256", "typ": "JWT"}
  payload = {"iss": ACCESS_KEY, "exp": int(time.time()) + 1800, "nbf": int(time.time()) - 5}
  token = jwt.encode(payload, SECRET_KEY, algorithm="HS256", headers=headers)
  ```
- **Image input**: Base64 encoded (raw, no `data:` prefix) or URL
- **Camera control** (optional):
  ```json
  "camera_control": {"type": "simple", "config": {"zoom": -3}}
  ```
  - `zoom`: [-10, 10]. Negative = dolly in (narrower FOV), Positive = zoom out
  - `horizontal`, `vertical`, `pan`, `tilt`, `roll` also available
- **Response**: Returns `data.task_id`. Poll until `task_status == "succeed"`. Video URL in `data.task_result.videos[0].url`
- **Rule**: URLs expire after 30 days — download immediately
- **⚠️ SELF-ANNEALED**: `camera_control` is NOT supported by `kling-v3` model (error 1201). Describe camera movement in the text prompt instead.

### Learning 11: Veo 3.1 REST API self-annealed fixes (2026-03-21)
- **`personGeneration`**: `allow_all` is NOT supported. Use `allow_adult`
- **Response format**: `predictLongRunning` returns `response.generateVideoResponse.generatedSamples[0].video.uri`
- **Download**: URI format is `https://generativelanguage.googleapis.com/v1beta/files/{id}:download?alt=media` — must append `&key=API_KEY`
- **Python 3.8 compatibility**: Cannot use `google-genai` SDK (requires 3.10+). Use REST API directly with `requests`
- **RAI audio filter**: If prompt triggers safety filter on audio, simplify dialogue or remove quoted inner dialogue
- **Rule**: The REST API approach (`predictLongRunning` → poll → download URI) is the LOCKED process for anchor video generation

### Learning 12: Final Stitching Rules (2026-03-21)
- **Anchor videos**: Speed up by **1.2x** in final stitching via ffmpeg (`setpts=PTS/1.2` + `atempo=1.2`)
- **B-roll videos**: **Trim to last 40%** of duration (keep second half, skip first 60%). No speed change.
- **BGM**: Always overlay `examples/audio_lock/bgm_track.mp3` as background music at **15% volume** beneath anchor dialogue (100% volume). Loop BGM if video is longer than track.
- **Audio bleed prevention**:
  - All clips MUST have both video + audio streams (use `anullsrc` for silent audio on B-roll)
  - All audio MUST be uniform: 44100Hz, stereo, AAC
  - Use `-t <exact_duration>` to hard-cut each clip so audio CANNOT extend beyond video duration
  - Audio from anchor clips must NEVER bleed into neighboring B-roll frames
- **Rule**: All speed/trim/BGM adjustments are applied during assembly, NOT during generation

### Learning 13: Frozen Design Choices — Transitions, Captions, Ending (2026-03-21)
- **Transitions**: Cross-dissolve (xfade=fade, 0.3s) between ALL clips. Use ffmpeg `xfade` + `acrossfade` in same filter_complex for sync safety.
- **Ending**: Fade-to-black (1.0s) on both video + audio at end of final clip
- **Captions**: Poppins SemiBold font (rendered via PIL as transparent PNG overlays, composited with ffmpeg `overlay`)
  - Line 1 (setup text): White, size 42, drop shadow (black@0.7)
  - Line 2 (key phrase/quote): Yellow (#FFD700), size 46, drop shadow (black@0.7)
  - Position: centered horizontal, **60% from top** of screen (y=1152px on 1920px height)
  - Only on anchor clips (no captions on B-roll)
- **Font location**: `assets/fonts/Poppins-SemiBold.ttf`
- **Caption rendering**: Use PIL/Pillow (NOT ffmpeg drawtext — drawtext requires libfreetype compilation)
- **Pipeline order**: xfade transitions → captions → fade-to-black → BGM overlay
- **Rule**: Each stage should be a separate ffmpeg pass for debuggability and safety

---

## 🔧 VIDEO PIPELINE ENGINE — End-to-End Summary

This section documents the **complete process** from idea to finished video, with every tool, parameter, and file location.

### Step 1: Topic & Concept (ChatGPT 5.4)
- **Input**: Content niche (Filipino parenting education), target platform (Reels/TikTok)
- **Output**: Topic + 3-item listicle structure
- **Format**: Hook → Rule 1 → Rule 2 → Rule 3 → CTA
- **Rule**: Always exactly 3 items. Never more, never less.

### Step 2: Script & Dialogue (ChatGPT 5.4)
- **Input**: Approved topic from Step 1
- **Output**: Full script with verbatim dialogue for each scene
- **Voice blueprint**: Warm Filipina grandmother "Lola" voice, Filipino-English accent
- **Duration**: ~30-35s total (4s per anchor scene, 2-3s per B-roll)

### Step 3: Image Prompts (ChatGPT 5.4)
- **Input**: Approved script from Step 2
- **Output**: One image prompt per scene (5 anchor + 3 B-roll = 8 total)
- **Anchor prompts**: Must include locked character description + background (from Rule Set 4)
- **B-roll prompts**: Must feature 11-13 year old students. No exceptions.

### Step 4: Image Generation
- **Anchor images**: Use locked images from `examples/anchor_character_lock/`
  - `scene_01_anchor_upscaled.png` → A1 Hook
  - `scene_02_anchor_upscaled.png` → A2 Rule 1
  - `scene_05_anchor_upscaled.png` → A3 Rule 2
  - `scene_08_anchor_upscaled.png` → A4 Rule 3
  - `scene_11_anchor_upscaled.png` → A5 CTA
- **B-roll images**: Generate fresh per-video using `gpt-image-1.5` (OpenAI)
  - Size: 1024x1792 (portrait, 9:16)
  - Stored in `assets/video_XX/images/bN_name/broll_image.png`

### Step 5: Video Prompts (ChatGPT 5.4)
- **Anchor prompts**: Include dialogue verbatim, specify lip-sync, warm Filipino-English accent
- **B-roll prompts**: Motion description only, NO dialogue, specify camera movement in text

### Step 6: Video Generation
#### 6a. Anchor Videos — Veo 3.1 REST API
- **Script**: `execution/generate_video01_anchor_videos.py`
- **Model**: `veo-3.1-generate-preview`
- **API**: `generativelanguage.googleapis.com/v1beta/models/veo-3.1-generate-preview:predictLongRunning`
- **Auth**: `GOOGLE_AI_STUDIO_API_KEY` (from `.env`)
- **Parameters**: image (base64), aspect ratio `9:16`, personGeneration `allow_adult`
- **Lip-sync**: Enabled via voice description in prompt
- **Flow**: POST → get operation ID → poll until `done=true` → download video from URI
- **Self-annealed**: `allow_all` → `allow_adult`, response parsing fixed for `generateVideoResponse.generatedSamples[0].video.uri`

#### 6b. B-Roll Videos — Kling 3.0 API
- **Script**: `execution/generate_video01_broll_videos.py`
- **Model**: `kling-v3`
- **API**: `https://api-singapore.klingai.com/v1/videos/image2video`
- **Auth**: JWT (PyJWT) from `KLING_ACCESS_KEY` + `KLING_SECRET_KEY` (from `.env`)
- **Parameters**: image (URL), duration `5`, aspect ratio `9:16`, sound `off`
- **⚠️ NO camera_control**: Not supported by kling-v3. Describe camera movement in prompt text instead.
- **Flow**: POST → get task_id → poll until `task_status == "succeed"` → download video URL

### Step 7: Assembly — `execution/assemble_video01.py`
- **Clip order**: A1 → A2 → B1 → A3 → B2 → A4 → B3 → A5
- **Anchor speed**: 1.2x (`setpts=PTS/1.2` + `atempo=1.2`)
- **B-roll trim**: Last 40% only (skip first 60% with `-ss`, then `-t` for duration)
- **Audio alignment**: All clips get both video + audio streams
  - Anchors: native audio from Veo
  - B-roll: silent audio via `anullsrc=r=44100:cl=stereo`
  - Hard-cut with `-t <exact_duration>` to prevent bleed
  - Uniform: 44100Hz, stereo, AAC, 192k across all clips
- **Output**: `assets/video_01/videos/` (individual clips in `.tmp/assembly_v3/`)

### Step 8: Polish — `execution/polish_video01.py` (4 stages)
- **Stage 1** — Cross-dissolve transitions
  - ffmpeg `xfade=transition=fade:duration=0.3` + `acrossfade=d=0.3` in single filter_complex
  - Video + audio processed together for guaranteed sync
  - Output cached: `.tmp/polish/s1_xfade.mp4`
- **Stage 2** — Poppins SemiBold captions
  - Rendered as transparent PNGs via PIL/Pillow
  - Composited with ffmpeg `overlay` filter with `enable=between(t,start,end)`
  - White setup line (42px) + Yellow keyword line (#FFD700, 46px)
  - Position: centered, 60% from top
  - Only on anchor clips (5 captions total)
- **Stage 3** — Fade-to-black (1.0s)
  - `fade=t=out` on video + `afade=t=out` on audio
- **Stage 4** — BGM overlay
  - `examples/audio_lock/bgm_track.mp3` looped at 15% volume
  - Mixed with `amix=inputs=2:duration=first`
- **Final output**: `assets/video_01/videos/video_01_final.mp4`

### Environment Variables (`.env`)
```
GOOGLE_AI_STUDIO_API_KEY=...   # Veo 3.1
KLING_ACCESS_KEY=...            # Kling 3.0
KLING_SECRET_KEY=...            # Kling 3.0
```

### Directory Structure
```
03_Video_Pipeline_03/
├── directives/
│   └── video_pipeline_master.md          # This file — all rules + learnings
├── execution/
│   ├── generate_video01_anchor_videos.py  # Veo 3.1 anchor generation
│   ├── generate_video01_broll_videos.py   # Kling 3.0 B-roll generation
│   ├── assemble_video01.py                # Assembly (speed, trim, concat)
│   └── polish_video01.py                  # Polish (transitions, captions, fade, BGM)
├── assets/
│   ├── fonts/
│   │   └── Poppins-SemiBold.ttf
│   └── video_01/
│       ├── images/                        # Source images per scene
│       └── videos/                        # Generated videos + final output
├── examples/
│   ├── anchor_character_lock/             # Locked anchor reference images
│   └── audio_lock/
│       └── bgm_track.mp3                  # Locked BGM track
└── .env                                   # API keys
```

### Replication: How to Create Video 02, 03, etc.
1. Run Steps 1-3 with ChatGPT → approve topic, script, prompts
2. Generate B-roll images (anchor images are LOCKED, same for all videos)
3. Copy and adapt the `generate_video01_*` scripts for the new video number
4. Update prompts/dialogue in the script for the new content
5. Run anchor generation → B-roll generation → assembly → polish
6. Review at each gate per Rule Set 5

### Learning 14: Security — API Keys & Git (2026-03-21)
- **NEVER commit API keys** to git — even in `.md` files
- `.env` is in `.gitignore` but `env.md` was NOT — it contained all keys in plaintext
- GitHub secret scanning blocked the push (detected OpenAI key)
- Fix: `git filter-branch --force --index-filter 'git rm --cached --ignore-unmatch env.md'` to purge from history
- **Rule**: Add ALL env/key files to `.gitignore` before first commit. Currently excluded: `.env`, `env.md`, `credentials.json`, `token.json`
- **Git repo**: `kaushiks27/Reel_Pipeline_V1`

### Learning 15: Parameterize scripts — don't duplicate per video (2026-03-23)
- Creating separate `generate_video02_*.py` scripts for each video is not scalable
- **Future refactor**: Create a single set of pipeline scripts that accept a config file (JSON/YAML) containing topic, dialogue, B-roll prompts, and scene mappings
- Config-driven approach: `python3 execution/generate_broll.py --config assets/video_02/config.json`
- **Rule**: When refactoring, ensure output quality is identical to per-video scripts. Config changes only — no logic changes.
- **Priority**: Do this refactor before Video 03

### Learning 16: Caption font — Kalam Bold (handwritten cinematic) (2026-03-23)
- Client provided screenshot reference showing a **bold handwritten/calligraphic italic** font style
- Poppins SemiBold was too clean/corporate — doesn't match the cinematic storytelling feel
- **New font**: `Kalam-Bold.ttf` (Google Fonts) — warm, handwritten, story-like
- **Location**: `assets/fonts/Kalam-Bold.ttf`
- **Rule**: ALL future videos use Kalam Bold for captions, not Poppins SemiBold
- Font sizes: Line 1 = 44px white, Line 2 = 50px yellow (#FFD700), stronger shadow (3px offset, alpha 200)

### Learning 17: NEVER prompt specific finger counts (2026-03-23)
- AI video models (both Veo 3.1 and Kling 3.0) **cannot reliably render a specific number of fingers held up**
- A4 was prompted with "holds up three fingers" but rendered 2 fingers while saying "number three" — visual/audio mismatch
- **Rule**: NEVER include finger-counting instructions in prompts. Use generic hand gestures instead: "open hand gesture", "gestures warmly", "hands clasped", "explaining gesture"
- This is a universal AI limitation — apply to ALL video generation prompts

### Learning 18: Anchor character MUST look directly at camera (2026-03-23)
- A1 (Hook) is the **gold standard** — character looks directly at the camera throughout
- A2 and A3 had the character occasionally looking away — breaks the intimate storytelling feel
- **Rule**: Every anchor prompt MUST include "looks directly at the camera" or "maintains eye contact with the camera" as a mandatory instruction
- **Prompt pattern**: Start every anchor prompt with "Near-static camera, medium close-up, eye-level. The character looks directly at the camera."

### Learning 19: Kling 3.0 is now the PRIMARY anchor video engine (2026-03-23)
- Veo 3.1 issues: Filipino accent caused Tagalog bleed, word stuttering/repetition, and quota limits (429)
- Kling 3.0 with `sound: "on"` provides cleaner lip sync with pure English TTS
- **Rule**: Use Kling 3.0 (`kling-v3`, mode `pro`, sound `on`) as the **primary** engine for anchor videos
- Veo 3.1 is demoted to backup only
- API: `POST /v1/videos/image2video` with `sound: "on"` for native TTS lip sync

### Learning 20: REUSE scripts — NEVER duplicate per video (NON-NEGOTIABLE) (2026-03-23)
- The same execution scripts MUST be reused across all video productions. Creating `generate_video02_*.py`, `generate_video03_*.py`, etc. is **explicitly prohibited**.
- **How to reuse**: Parameterize scripts via config files (JSON/YAML) or CLI arguments:
  - `python3 execution/generate_anchor_videos_kling.py --config assets/video_03/config.json`
  - Config file contains: topic, scenes, prompts, dialogue, output paths
- **Reason**: Duplicating scripts creates maintenance debt, makes bug fixes harder, and violates the 3-layer architecture (directives → orchestration → deterministic scripts)
- **Migration plan**: Rename current scripts to generic names (drop `video02_` prefix), add config file support, validate output quality is identical
- **Priority**: MUST be done before Video 03 production begins

### Learning 21: Parameterized orchestrator must be validated against ALL directive rules (2026-03-24)
- When creating `run_pipeline.py` (parameterized master orchestrator), the first version had **9 violations** of locked directive rules:
  1. **Generated anchor images** instead of copying from `examples/anchor_character_lock/` (violates Learning 8 + Rule Set 8)
  2. **Used Veo 3.1 as primary** instead of Kling 3.0 (violates Learning 19)
  3. **Included "Filipino-English accent"** in voice blueprint (violates Rule Set 9.1 — causes Tagalog bleed + stuttering)
  4. **No word count limit** on dialogue (violates Rule Set 9.6 — must be ≤8 words)
  5. **Used "slow dolly in"** for camera (violates Rule Set 9.3 — must be "near-static", "extremely subtle push-in")
  6. **Prompted specific finger counts** (violates Learning 17 — AI can't reliably render finger counts)
  7. **Missing eye-contact directive** (violates Learning 18 — "looks directly at camera" is mandatory)
  8. **Wrong BGM volume** (used 50% instead of 15%, violates Learning 12)
  9. **Wrong image model** for B-roll in prompt descriptions (used gpt-image in step 2 prompts but didn't properly flag anchor images as locked-only)
- **Root cause**: The orchestrator was written from memory/summary instead of reading the full directive line-by-line
- **Rule**: When creating ANY new execution script, read `video_pipeline_master.md` in FULL first. Cross-check every decision against the Self-Annealing Log (Learnings 1-20). Do NOT rely on memory.
- **Rule**: Script headers should list which rules they comply with (e.g., `# Compliant with: Learning 8, Rule Set 9.1, ...`)
- **Script**: `execution/run_pipeline.py` — the corrected parameterized orchestrator

### Learning 22: Kling API requires RAW base64 — no data URI prefix (2026-03-24)
- Kling `/v1/videos/image2video` expects `"image": "<raw_base64>"` — NOT `"image": "data:image/png;base64,<b64>"`
- The data URI prefix causes silent rejection (every request fails, no useful error message)
- JWT tokens MUST be refreshed on each poll call (they expire after 30 min)
- Always include `negative_prompt` field: `"blurry, distorted, text, watermark, ugly, deformed, zoom in, zoom out, Tagalog, non-English"`
- Always check `data.get("code") == 0` in API responses, not just HTTP 200
- **Reference**: The proven working script is `execution/generate_video02_anchor_videos_kling.py` — any Kling code must match it line-by-line

### Learning 23: Pipeline MUST gate on step failures — never proceed past a broken step (2026-03-24)
- If Step 5 (video gen) produces 2/8 videos, Step 6 (assembly) MUST NOT run — it will fail on missing files
- If Step 6 fails, Step 7 (polish) MUST NOT run
- **Pattern**: Each step returns a success/fail status. On failure: log to Google Sheets "Error Log" tab, mark remaining steps as "blocked", halt pipeline
- **Dashboard**: Blocked steps show gray with "Blocked by Step N failure" detail text

### Learning 24: Modularize execution scripts — orchestrator must be a thin coordinator (2026-03-24)
- Proven working scripts (assemble_video01.py, polish_video01.py, etc.) contain complex, tested ffmpeg logic. NEVER inline this into the orchestrator
- **Pattern**: Orchestrator calls modules via `import` or `subprocess.run()`. Each module owns its domain logic
- **Extracted modules**: `video_engines.py` (Kling/Veo), `error_logger.py` (Sheets error tab), `drive_uploader.py` (Google Drive date/topic folders)
- Keep orchestrator under 300 lines — if it grows beyond that, extract another module

### Learning 25: Assembly/Polish scripts need dynamic scene config for parameterization (2026-03-24)
- Assembly script has hardcoded SCENES list (`a2_rule1_speaking`, `b1_safety`, etc.) specific to Video 01
- New videos generate different scene IDs (e.g., `a2_rule1`, `b1_rule1`)
- **Fix**: Add `--config scene_config.json` flag to assembly/polish scripts
- Config JSON contains: scene order, file paths, captions, clip types
- Without `--config`, scripts default to original hardcoded scenes (backward compatible)
- **Critical**: All existing ffmpeg filter chains (1.2x anchor, last-40% B-roll, xfade, BGM) MUST remain byte-identical

### Learning 26: Video prompts MUST follow Kling shot-by-shot structure (2026-03-24)
- Per `36_Kling_3.0_UPDATE_2026.md`: every video prompt needs 4 sections: **Shot**, **Details**, **Camera**, **Mood**
- Anchor prompts: `Shot: Medium close-up, near-static, eye-level. Details: [character action, lighting, texture]. Camera: 50mm lens, subtle push-in. Mood: Warm, maternal.`
- B-roll prompts: `Shot: Medium shot, slow pan. Details: [scene description]. Camera: 35mm lens, smooth pan. Mood: Studious, cozy.`
- Per `33_KlingCameraPDF.pdf.md`: "Always start your prompt with the camera angle and build from there"
- Include **lens reference** (35mm, 50mm, 85mm) — this triggers Kling to treat it as camera footage, not animation
- **Reference**: `video_expert_baseline.md` Section 4 (Video Generation) and Section 5 (Camera Movement Toolkit)

### Learning 27: Voice blueprint MUST include punctuation pauses and tapering (2026-03-24)
- Per `41_Consistent_Character_Voices_in_Veo_3.1.md`: use `...` and punctuation for natural pauses
- Blueprint format: `'tone, accent, pace, authority. Pauses before key words... as if thinking. Sentences taper off slightly.'`
- Copy-paste the EXACT same blueprint into EVERY anchor prompt — never paraphrase
- Dialogue lines must also use `...` pauses: `"Number one... 'the phrase.'"`
- **16 tone presets available** in Lesson 41 — current pipeline uses "Confident" variant

### Learning 28: Script generation MUST include few-shot JSON example (2026-03-24)
- Per `11_how_to_write_prompts.md` Step 6: provide weak → upgraded prompt example
- System prompt for script generation (Step 1) must include a complete JSON example showing ideal output
- This prevents GPT from inventing field names, using wrong dialogue lengths, or missing caption entries
- Example topic used: "Signs your teen is struggling" with full rules+captions structure
- **Critical**: The few-shot example must demonstrate the `...` pause pattern and ≤8 word limit

### Learning 29: Flat file structure + auto-cleanup after Drive upload (2026-03-24)
- **Images**: `assets/video_XX/images/scene_id.png` (flat, no nested per-scene folders)
- **Videos**: `assets/video_XX/videos/scene_id.mp4` (flat)
- **JSONs**: `assets/video_XX/pipeline/` subfolder (script.json, image_prompts.json, video_prompts.json, image_results.json, video_results.json)
- **Final**: `assets/video_XX/final/` subfolder (assembled + polished output)
- **After confirmed Drive upload**: `cleanup_local_assets()` deletes `images/`, `videos/`, `.tmp/assembly_v3/`, `.tmp/polish/`
- **Preserved**: `pipeline/` (lightweight JSONs for reference) and `final/` (reference copy)
- **If upload fails**: local files are NOT deleted — error message says "local files preserved"

