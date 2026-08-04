# Andres Lanzos portfolio

Source for the portfolio site, built with [Quarto](https://quarto.org/).

Live mirrors:

- Quarto Pub (primary): https://andreslanzos.quarto.pub/portfolio/
- GitHub Pages: https://alanzos.github.io/portfolio/

The site presents Andres's biomedical data-science profile, selected projects,
articles, and CV. Career facts and metrics are synchronized with the canonical
CV workspace; the reviewed website CV is stored at:

`pdf/2026-07-18_Andres_Lanzos_CV_EN_Canonical_Option_C.pdf`

## Site map

| Path | Role |
| --- | --- |
| `index.qmd` | About homepage |
| `projects.qmd` | Featured project case studies (with dates) |
| `articles/` | Quarto listing of short notes under `articles/<date-slug>/` |
| `resume.qmd` | CV page (PDF embed + searchable text) |
| `styles.css` | Site theme, navbar, article/project layout |
| `includes/` | Shared HTML/Markdown includes (`gh-engagement.html`, `_cv-search-text.md`) |
| `gh-audio/` | Kokoro narration MP3s (GitHub Pages only) |
| `scripts/generate_article_audio.py` | Regenerate article listen audio |
| `writing/` | Thin redirect stub to `articles/` |

## Current site conventions

- Personal location: `Basel, Switzerland`.
- CSEM and Idorsia experience entries retain `Allschwil, Switzerland` as the
  employment location.
- Navbar: brand, About / Projects / Articles / CV, social icons, theme toggle,
  and search are **center-aligned** as one group. The hamburger is hidden; the
  nav stays open. Icon and link spacing is even; the search glyph matches other
  icon sizes. The yellow portfolio focus ring is suppressed on the search input.
- Homepage uses persistent navigation and footer for Projects, Articles, CV,
  email, LinkedIn, and GitHub. No separate CTA button rows in the page body.
- Projects stay on `projects.qmd` as featured case studies. Each project heading
  includes a date (or date range) for when it was made.
- Articles live under `articles/<date-slug>/` as a Quarto listing of short notes
  adapted from LinkedIn posts. Keep the author's voice; strip platform chrome
  (hashtags, "link in comments"); avoid em dashes. Each article starts with a
  TLDR callout.
- Typography: Source Serif 4 for long-form reading and titles; Source Sans 3 for
  navigation and metadata. Body measure targets about 66 characters.
- CV page embeds the reviewed two-page Option C PDF with download and email
  controls. Because Quarto search cannot index PDF iframe content, the CV text
  is also included (visually hidden) from `includes/_cv-search-text.md` so terms
  such as employer names remain searchable. When the PDF is replaced, refresh
  that include to match. The leading underscore keeps Quarto from publishing it
  as its own page.
- Prose avoids em dashes; date ranges retain their normal range punctuation.

## Local development

```bash
quarto preview
```

Build the complete static site with:

```bash
quarto render
```

For a GitHub Pages–shaped local build (comments, counters, listen audio):

```bash
quarto render --profile github
```

## Publishing

### Quarto Pub (primary)

Do **not** use the `github` profile here: keep `gh-audio/` out of the Quarto Pub
bundle (size limit). Clear a leftover `_site` from a GitHub-profile render first if
needed. Destination is recorded in `_publish.yml`:

```bash
rm -rf _site
quarto publish quarto-pub --no-prompt --no-browser
```

### GitHub Pages

Uses the `github` Quarto profile (`_quarto-github.yml`) so asset paths work under
`/portfolio/` and GitHub-only features are enabled. Publish from a local machine:

```bash
quarto publish gh-pages --profile github --no-prompt --no-browser
```

Or push to `main` / run **Publish to GitHub Pages** in Actions
(`.github/workflows/publish.yml`). GitHub Pages must serve from the `gh-pages`
branch.

### GitHub Pages extras (not on Quarto Pub)

The `github` profile also enables:

- **Article comments** via [Giscus](https://giscus.app) (GitHub Discussions on
  `alanzos/portfolio`)
- **Site visit and article read counts** via CounterAPI
- **Listen to this article** via pre-generated Kokoro narration
  (`gh-audio/<slug>/narration.mp3`)

Generate or refresh article audio (Python 3.12 + Kokoro + ffmpeg):

```bash
IDUNOX_KOKORO_PYTHON=/Users/ALC/Git/idunox_investor_portal/.venv-kokoro/bin/python \
  python3 scripts/generate_article_audio.py
```

One-time setup for comments: install the
[Giscus GitHub App](https://github.com/apps/giscus) on the `portfolio`
repository (Discussions are already enabled).
