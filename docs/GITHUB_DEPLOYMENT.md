# GitHub deployment guide

## 1. Create the repository

Create a new public GitHub repository named:

```text
J07-VIREO
```

Recommended description:

```text
Award-winning offline edge-AI assistive navigation prototype using Raspberry Pi 5, Hailo, Vosk, audio feedback and a directional haptic belt.
```

Do not ask GitHub to generate a README, licence or `.gitignore`; they are already included.

## 2. Replace placeholders

Replace `Jivyzn` in:

- `README.md`
- `CITATION.cff`

with your actual GitHub username.

## 3. Push the repository

From the extracted folder:

```bash
git init
git branch -M main
git add .
git commit -m "Release JØ7 Vireo v1.0.0"
git remote add origin https://github.com/Jivyzn/JO7-Vireo.git
git push -u origin main
```

The included HEF is approximately 30 MB and can be committed directly. Avoid repeatedly replacing large binaries in Git history. For future model versions, prefer GitHub Releases or Git LFS.

## 4. Configure the GitHub page

Under **About**, set:

- Website: a project/demo page when available
- Topics:
  - `assistive-technology`
  - `accessibility`
  - `edge-ai`
  - `computer-vision`
  - `raspberry-pi`
  - `hailo`
  - `vosk`
  - `embedded-systems`
  - `offline-ai`
  - `south-africa`

Use `assets/images/vireo-final-enclosure.jpg` or a later high-resolution project image as the social preview.

## 5. Repository settings

Recommended settings:

- enable Issues;
- enable Discussions for build questions;
- keep Actions enabled so CI runs;
- enable private vulnerability reporting;
- enable Dependabot alerts;
- add branch protection after the first successful CI run;
- require pull requests and passing CI for future collaborators.

## 6. Create the first release

Create tag and release **`v1.0.0`**. Use the contents of `docs/RELEASE_NOTES_v1.0.0.md` as the release description.

Attach the repository ZIP if desired. The HEF is already included in the source tree.

## 7. Verify the public result

Check that:

- README images render;
- the architecture Mermaid diagram renders;
- the licence is detected as AGPL-3.0;
- GitHub displays the citation option;
- Actions pass on Python 3.10–3.12;
- no `.env`, credentials, WAV recordings or personal contact details were committed;
- all public recognition links work;
- the model checksum matches `docs/MODEL_CARD.md`.
