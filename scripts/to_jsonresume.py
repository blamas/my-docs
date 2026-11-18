#!/usr/bin/env python3
"""Convert a RenderCV YAML file to JSON Resume (schema v1.2.1).
Usage: to_jsonresume.py INPUT.yaml OUTPUT.json
"""

import datetime
import json
import re
import sys
from pathlib import Path

from ruamel.yaml import YAML

SCHEMA = "https://raw.githubusercontent.com/jsonresume/resume-schema/v1.2.1/schema.json"

SOCIAL_URL = {
    "LinkedIn": "https://www.linkedin.com/in/{}",
    "GitHub": "https://github.com/{}",
    "GitLab": "https://gitlab.com/{}",
    "X": "https://x.com/{}",
}

LANGUAGE_LABELS = {"languages", "langues"}
CERTIFICATE_LABELS = {"certifications"}


def date_str(val) -> str:
    if isinstance(val, (datetime.date, datetime.datetime)):
        return val.strftime("%Y-%m")
    return str(val) if val else ""


def split_top_level(text: str) -> list[str]:
    """Split on commas outside parentheses: "GitOps (Flux, ArgoCD), Helm" -> 2 items."""
    items, depth, current = [], 0, ""
    for char in text:
        depth += {"(": 1, ")": -1}.get(char, 0)
        if char == "," and depth == 0:
            items.append(current.strip())
            current = ""
        else:
            current += char
    items.append(current.strip())
    return [i for i in items if i]


def strip_markdown(text: str) -> str:
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", str(text))
    return text.replace("**", "").replace("*", "")


def with_dates(item: dict, e: dict) -> dict:
    if start := date_str(e.get("start_date") or e.get("date")):
        item["startDate"] = start
    end = date_str(e.get("end_date"))
    if end and end.lower() != "present":
        item["endDate"] = end
    return item


def map_work(entries: list) -> list:
    return [
        with_dates(
            {
                "name": e["company"],
                "position": e.get("position", ""),
                **({"location": e["location"]} if e.get("location") else {}),
                **({"summary": strip_markdown(e["summary"])} if e.get("summary") else {}),
                "highlights": [strip_markdown(h) for h in e.get("highlights", [])],
            },
            e,
        )
        for e in entries
    ]


def map_education(entries: list) -> list:
    return [
        with_dates(
            {
                "institution": e["institution"],
                "area": e.get("area", ""),
                "studyType": e.get("degree", ""),
                "courses": [strip_markdown(h) for h in e.get("highlights", [])],
            },
            e,
        )
        for e in entries
    ]


def map_projects(entries: list) -> list:
    return [
        with_dates(
            {
                "name": strip_markdown(e["name"]),
                **({"description": strip_markdown(e["summary"])} if e.get("summary") else {}),
                "highlights": [strip_markdown(h) for h in e.get("highlights", [])],
            },
            e,
        )
        for e in entries
    ]


def map_one_line(entries: list, kind: str) -> tuple[list, list, list]:
    skills, languages, certificates = [], [], []
    for e in entries:
        details = strip_markdown(e.get("details", ""))
        if e["label"].lower() in LANGUAGE_LABELS:
            for lang in split_top_level(details):
                name, _, fluency = lang.partition("(")
                name, fluency = name.strip(), fluency.rstrip(")").strip()
                languages.append({"language": name[:1].upper() + name[1:], **({"fluency": fluency} if fluency else {})})
        elif kind == "certificates":
            certificates.append({"name": strip_markdown(e["label"]), "date": details})
        elif e["label"].lower() in CERTIFICATE_LABELS:
            for cert in split_top_level(details):
                if m := re.fullmatch(r"(.+?)\s*\((\d{4}(?:-\d{2}){0,2})\)", cert):
                    certificates.append({"name": m[1], "date": m[2]})
                else:
                    certificates.append({"name": cert})
        else:
            skills.append({"name": strip_markdown(e["label"]), "keywords": split_top_level(details)})
    return skills, languages, certificates


def classify_section(name: str, entries: list) -> str:
    sample = entries[0] if entries else None
    if isinstance(sample, str):
        return "summary"
    if not isinstance(sample, dict):
        return "unknown"
    if "company" in sample:
        return "work"
    if "institution" in sample:
        return "education"
    if "name" in sample:
        return "projects"
    if "label" in sample:
        return "certificates" if "cert" in name.lower() else "skills"
    return "unknown"


def convert(src: Path) -> dict:
    cv = YAML(typ="safe").load(src)["cv"]

    profiles = []
    for s in cv.get("social_networks", []):
        profile = {"network": s["network"], "username": s["username"]}
        if s["network"] in SOCIAL_URL:
            profile["url"] = SOCIAL_URL[s["network"]].format(s["username"])
        profiles.append(profile)

    basics = {
        "name": cv.get("name", ""),
        "label": cv.get("headline", ""),
        "email": cv.get("email", ""),
        "url": cv.get("website", ""),
        "location": {"region": cv.get("location", "")},
        "profiles": profiles,
    }

    out: dict[str, list] = {k: [] for k in ("work", "projects", "education", "skills", "certificates", "languages")}
    summary_parts: list[str] = []

    for section, entries in (cv.get("sections") or {}).items():
        kind = classify_section(section, entries or [])
        if kind == "summary":
            summary_parts.extend(strip_markdown(e) for e in entries)
        elif kind == "work":
            out["work"] += map_work(entries)
        elif kind == "education":
            out["education"] += map_education(entries)
        elif kind == "projects":
            out["projects"] += map_projects(entries)
        elif kind in ("skills", "certificates"):
            items, languages, certificates = map_one_line(entries, kind)
            out["skills"] += items
            out["languages"] += languages
            out["certificates"] += certificates
        else:
            print(f"warning: skipping unrecognised section '{section}'", file=sys.stderr)

    if summary_parts:
        basics["summary"] = "\n\n".join(summary_parts)
    if not basics["label"] and out["work"]:
        basics["label"] = out["work"][0]["position"]

    return {"$schema": SCHEMA, "basics": basics, **{k: v for k, v in out.items() if v}}


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(f"usage: {sys.argv[0]} INPUT.yaml OUTPUT.json", file=sys.stderr)
        sys.exit(1)
    out = Path(sys.argv[2])
    out.write_text(json.dumps(convert(Path(sys.argv[1])), ensure_ascii=False, indent=2) + "\n")
    print(f"written: {out}")
