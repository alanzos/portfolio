# Andres Lanzos portfolio

Source for [andreslanzos.quarto.pub](https://andreslanzos.quarto.pub/), built and published with [Quarto](https://quarto.org/).

The site presents Andres's biomedical data-science profile, selected impact,
current CV and project portfolio. Career facts and metrics are synchronized
with the canonical CV workspace; the reviewed website CV is stored at:

`pdf/2026-07-18_Andres_Lanzos_CV_EN_Canonical_Option_B.pdf`

## Current site conventions

- The personal location is `Basel, Switzerland`.
- CSEM and Idorsia experience entries retain `Allschwil, Switzerland` as the
  employment location.
- The homepage uses the persistent navigation and footer for CV, project,
  email, LinkedIn, and GitHub access. It intentionally has no separate CTA
  button rows in the page body.
- The CV page embeds the reviewed two-page Option B PDF and keeps its download
  and email controls.
- Prose avoids em dashes; date ranges retain their normal range punctuation.

## Local development

```bash
quarto preview
```

Build the complete static site with:

```bash
quarto render
```

## Publishing

The existing Quarto Pub destination is recorded in `_publish.yml`. After reviewing the rendered `_site/` output, publish with:

```bash
quarto publish quarto-pub --no-prompt --no-browser
```

## Contact

[andreslanzos@gmail.com](mailto:andreslanzos@gmail.com)

## License

GNU Affero General Public License v3.0 (AGPL-3.0).
