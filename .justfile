#!/usr/bin/env -S just --justfile

set quiet
set shell := ['bash', '-euo', 'pipefail', '-c']

[doc('Render both resumes and the landing page into _site/')]
build:
    rm -rf _site && mkdir -p _site && cp -r site/. _site/
    for lang in en fr; do just render "$lang"; done
    for f in resume cv cv_en; do cp _site/resume_en.pdf "_site/$f.pdf"; done
    cp _site/resume_fr.pdf _site/cv_fr.pdf

[doc('Fail if a PDF is longer than one page or a JSON Resume is invalid')]
check:
    for f in _site/resume_??.pdf; do n=$(grep -ao '/Type/Page[^s]' "$f" | wc -l); [ "$n" -eq 1 ] || { echo "$f has $n pages"; exit 1; }; done
    uv run --locked --group dev check-jsonschema --schemafile https://raw.githubusercontent.com/jsonresume/resume-schema/v1.2.1/schema.json _site/resume_*.json

[doc('Re-render one resume on save into _site/watch/')]
watch lang:
    uv run --locked rendercv render resume/resume_{{ lang }}.yaml --watch -nopng -o ../_site/watch

[doc('Format and lint the whole repo')]
fmt:
    lefthook run pre-commit --all-files --no-stage-fixed

[doc('Lint the whole repo and fail if any formatter changes a file')]
lint:
    lefthook run pre-commit --all-files --no-stage-fixed --fail-on-changes

[private]
render lang:
    uv run --locked rendercv render resume/resume_{{ lang }}.yaml -nopng -typ ../_site/build/{{ lang }}.typ \
        -pdf ../_site/resume_{{ lang }}.pdf -md ../_site/resume_{{ lang }}.md -html ../_site/resume_{{ lang }}.html
    rm -rf _site/build
    uv run --locked scripts/to_jsonresume.py resume/resume_{{ lang }}.yaml _site/resume_{{ lang }}.json

[private]
default:
    just --list
