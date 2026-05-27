#!/usr/bin/env python3
"""Convert a RenderCV YAML file to JSON Resume (schema v1.0.0).
Usage: python3 to_jsonresume.py INPUT.yaml OUTPUT.json
"""

import json
import sys
import datetime
from pathlib import Path
from ruamel.yaml import YAML

SOCIAL_URL = {
    "LinkedIn": "https://www.linkedin.com/in/{}",
    "GitHub": "https://github.com/{}",
    "Twitter": "https://twitter.com/{}",
}


def date_str(val) -> str:
    if isinstance(val, (datetime.date, datetime.datetime)):
        return val.strftime("%Y-%m")
    return str(val) if val else ""


def map_work(entries: list) -> list:
    result = []
    for e in entries:
        item = {
            "name": e["company"],
            "position": e.get("position", ""),
            "startDate": date_str(e.get("start_date")),
            "highlights": e.get("highlights", []),
        }
        if e.get("location"):
            item["location"] = e["location"]
        end = date_str(e.get("end_date"))
        if end and end.lower() != "present":
            item["endDate"] = end
        result.append(item)
    return result


def map_education(entries: list) -> list:
    result = []
    for e in entries:
        item = {
            "institution": e["institution"],
            "area": e.get("area", ""),
            "studyType": e.get("degree", ""),
            "startDate": date_str(e.get("start_date")),
            "endDate": date_str(e.get("end_date")),
            "courses": e.get("highlights", []),
        }
        if e.get("location"):
            item["location"] = e["location"]
        result.append(item)
    return result


def map_skills(entries: list) -> list:
    return [
        {
            "name": e["label"],
            "keywords": [k.strip() for k in str(e.get("details", "")).split(",")],
        }
        for e in entries
    ]


def map_certificates(entries: list) -> list:
    return [{"name": e["label"], "date": e.get("details", "")} for e in entries]


def classify_section(name: str, entries: list) -> str:
    if not entries:
        return "unknown"
    sample = entries[0]
    if "company" in sample:
        return "work"
    if "institution" in sample:
        return "education"
    if "label" in sample and "details" in sample:
        return "certifications" if "cert" in name.lower() else "skills"
    return "unknown"


def convert(src: Path) -> dict:
    cv = YAML().load(src)["cv"]

    profiles = [
        {
            "network": s["network"],
            "username": s["username"],
            "url": SOCIAL_URL.get(s["network"], "").format(s["username"]),
        }
        for s in cv.get("social_networks", [])
    ]

    basics = {
        "name": cv.get("name", ""),
        "email": cv.get("email", ""),
        "url": cv.get("website", ""),
        "location": {"region": cv.get("location", "")},
        "profiles": profiles,
    }

    work, education, skills, certificates = [], [], [], []

    for section, entries in cv.get("sections", {}).items():
        kind = classify_section(section, entries or [])
        if kind == "work":
            work.extend(map_work(entries))
        elif kind == "education":
            education.extend(map_education(entries))
        elif kind == "skills":
            skills.extend(map_skills(entries))
        elif kind == "certifications":
            certificates.extend(map_certificates(entries))
        elif kind == "unknown":
            print(
                f"warning: skipping unrecognised section '{section}'", file=sys.stderr
            )

    if work:
        basics["label"] = work[0]["position"]

    return {
        "$schema": "https://raw.githubusercontent.com/jsonresume/resume-schema/v1.0.0/schema.json",
        "basics": basics,
        "work": work,
        "education": education,
        "skills": skills,
        "certificates": certificates,
    }


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(f"usage: {sys.argv[0]} INPUT.yaml OUTPUT.json", file=sys.stderr)
        sys.exit(1)
    out = Path(sys.argv[2])
    out.write_text(
        json.dumps(convert(Path(sys.argv[1])), ensure_ascii=False, indent=2) + "\n"
    )
    print(f"written: {out}")
