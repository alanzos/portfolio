# Andres Lanzos portfolio

Source for the portfolio site, built with [Quarto](https://quarto.org/).

Live mirrors:

- Quarto Pub (primary): https://andreslanzos.quarto.pub/portfolio/
- GitHub Pages: https://alanzos.github.io/portfolio/

The site presents Andres's biomedical data-science profile, selected projects,
articles, and CV. Career facts and metrics are synchronized with the canonical
CV workspace; the reviewed website CV is stored at:

`pdf/2026-08-04_Andres_Lanzos_CV_EN_Canonical_Option_C.pdf`

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
- Navbar: brand and About / Projects / Articles / CV stay on the left; social
  icons, theme toggle, and search stay on the right. Items are **vertically
  centered** in the bar. The hamburger is hidden; the nav stays open. Icon and
  link spacing is even; the search glyph matches other icon sizes. The yellow
  portfolio focus ring is suppressed on the search input.
- Homepage uses persistent navigation and footer for Projects, Articles, CV,
  email, LinkedIn, and GitHub. No separate CTA button rows in the page body.
  The footer also links to Subscribe to my articles (Buttondown).
- Projects stay on `projects.qmd` as featured case studies. Each project heading
  includes a date (or date range) for when it was made.
- Articles live under `articles/<date-slug>/` as a Quarto listing of short notes
  adapted from LinkedIn posts. Keep the author's voice; strip platform chrome
  (hashtags, "link in comments"); avoid em dashes. Lead with the title and YAML
  description; do not add a TLDR callout.
- Write what the work **is**. Do not add disclaimer sentences or closing
  sections whose job is to list what it is not ("not a clone", "not clinical
  validation"). Scope belongs as a positive statement.
- Typography: Source Serif 4 for long-form reading and titles; Source Sans 3 for
  navigation and metadata. Body measure targets about 66 characters.
- CV page embeds the reviewed two-page Option C PDF with download and email
  controls. Because Quarto search cannot index PDF iframe content, the CV text
  is also included (visually hidden) from `includes/_cv-search-text.md` so terms
  such as employer names remain searchable. When the PDF is replaced, refresh
  that include to match. The leading underscore keeps Quarto from publishing it
  as its own page.
- Prose avoids em dashes; date ranges retain their normal range punctuation.
- One word per concept. Lock a short glossary (features, labels, genes, predictions) and use it in prose, tables, captions, and code. Do not mix synonyms (analogue scores / channels / columns / X) for variety. Keep a source's proper name (STRING combined score, Open Targets overall).
- Citations use **Vancouver / NLM numeric** (citation-sequence): in-text `[1]`, numbered list at the end, ordered by first mention. New articles use BibTeX (`references.bib` next to `index.qmd`) plus `csl/vancouver.csl`. Cite load-bearing claims (epidemiology, trials, methods, databases); skip citations on the project's own CV numbers. Older notes may keep a hand-numbered list until they are edited.

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

## Article subscriptions (RSS + Buttondown)

Articles expose an RSS feed at `articles/index.xml` (enabled via
`listing.feed` on `articles/index.qmd`). The site footer links to the
Buttondown signup page next to LinkedIn and GitHub.

Public newsletter page: <https://buttondown.com/andreslanzos>

### One-time Buttondown setup

1. Create a free Buttondown newsletter at <https://buttondown.com>.
2. Use username `andreslanzos`, or update the footer Subscribe link in
   `_quarto.yml` to match.
3. Publish/republish the site after any username change.

Readers can follow the RSS feed directly. Email delivery stays on Free by
creating drafts through the API when you publish (no paid RSS-to-email).

### Announce a new article by email (Free plan)

After the article is live on Quarto Pub, create a Buttondown draft from it:

```bash
# Preview payload only
scripts/buttondown.sh announce articles/2026-08-10-disease-independent-clocks --dry-run

# Create a draft (default; review in Buttondown, then publish there)
scripts/buttondown.sh announce articles/2026-08-10-disease-independent-clocks

# Create and send immediately
scripts/buttondown.sh announce articles/2026-08-10-disease-independent-clocks --send
```

Typical publish sequence:

```bash
rm -rf _site
quarto publish quarto-pub --no-prompt --no-browser
scripts/buttondown.sh announce articles/<date-slug>
```

The script posts subject + description + TLDR + a link to the live article. It
stores `metadata.portfolio_article=<slug>` so re-running is a no-op unless you
pass `--force`. Default site base is
`https://andreslanzos.quarto.pub/portfolio` (override with `--site-base` or
`PORTFOLIO_SITE_BASE`).

### API access (local agents / scripts)

A dedicated API key labeled **Cursor agent · portfolio** is stored outside the
repo (never commit it):

```bash
~/.config/portfolio/buttondown.env
```

Helper:

```bash
scripts/buttondown.sh ping
scripts/buttondown.sh newsletter
scripts/buttondown.sh subscribers
scripts/buttondown.sh get emails?page_size=5
scripts/buttondown.sh announce articles/<date-slug>
```

Auth header form: `Authorization: Token $BUTTONDOWN_API_KEY`  
Docs: <https://docs.buttondown.com/api-authentication>

Rotate or revoke the key at <https://buttondown.com/keys> if it leaks.
