# my-docs

[![Site](https://github.com/blamas/my-docs/actions/workflows/site.yml/badge.svg)](https://github.com/blamas/my-docs/actions/workflows/site.yml)

Resume of Théo Rey, published at [docs.reyth.dev](https://docs.reyth.dev) in English and French as PDF, HTML, Markdown
and [JSON Resume](https://jsonresume.org). Rendered with [RenderCV](https://github.com/rendercv/rendercv).

| Path | Content |
| --- | --- |
| `resume/resume_{en,fr}.yaml` | Resume sources |
| `site/` | Static files copied as is (landing page) |
| `scripts/to_jsonresume.py` | RenderCV YAML to JSON Resume |

```sh
mise run build        # renders everything into _site/, checks one page per PDF and the JSON Resume schema
mise run watch en     # re-renders on save into _site/watch/
```

Every PR builds the site; `main` deploys it to GitHub Pages.
