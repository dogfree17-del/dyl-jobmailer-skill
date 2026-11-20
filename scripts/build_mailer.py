"""Build the Dell Young Leaders job-mailer .docx files from a JSON data file.

Usage:
    python build_mailer.py data.json --main OUT_MAIN.docx --edu OUT_EDU.docx

It clones the first email block of assets/template.docx once per faculty, so the layout
(headings, wording, table, closing paragraphs) is exactly the template's. Only the faculty
heading and the table rows change. Links are written in full as plain text, never as hyperlinks.

data.json shape:
{
  "opportunities": [            # jobs the user shared (go in the main document)
    {"company": "...", "opportunity": "...", "location": "...",
     "link": "https://...",                       # full URL, never shortened
     "degrees": {"EMS": "BCom Finance / Accounting", "SCIENCE": "..."}}   # faculty -> degree text
  ],
  "education": [                # teaching posts (go in the education document)
    {"company": "School name", "opportunity": "...", "location": "...",
     "link": "https://www.edupstairs.org/teaching-posts/64028/",
     "phase": "Foundation Phase" | "Intermediate Phase" | "Other",
     "degree": "BEd Foundation Phase (REQV 13+), SACE-registered"}
  ]
}
Faculty keys: EMS, SCIENCE, ENGINEERING, LAW, AGRISCIENCE, SOCIAL SCIENCES.
A faculty (or education phase) with no rows is skipped. A document with no blocks is not written.
"""
import argparse
import copy
import json
import os
import re
import sys

from docx import Document
from docx.opc.constants import RELATIONSHIP_TYPE
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

TEMPLATE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "template.docx")

# (key, heading shown above the email) in the order the emails appear
FACULTIES = [
    ("EMS", "EMS / Commerce"),
    ("SCIENCE", "Science"),
    ("ENGINEERING", "Engineering"),
    ("LAW", "Law"),
    ("AGRISCIENCE", "Agriscience"),
    ("SOCIAL SCIENCES", "Social Sciences"),
]
EDU_PHASES = [
    ("Foundation Phase", "Education – Foundation Phase"),
    ("Intermediate Phase", "Education – Intermediate Phase"),
    ("Other", "Education"),
]
BLOCK_LEN = 15          # 7 paragraphs, the table, 7 paragraphs
TABLE_AT = 7
LINK_COL = 3
# short cells keep the table narrow when pasted into DYL Connect (user rule 2026-11-20)
MAX_LEN = {"company": 25, "opportunity": 40, "location": 20, "degree": 80}  # degree: 2-4 names from student_degrees.md


def die(msg):
    sys.exit("ERROR: " + msg)


def check_link(link, who):
    if not re.match(r"^(https?://|mailto:)\S+$", link or ""):
        die(f"{who}: link must be a full http(s):// or mailto: URL with no spaces, got {link!r}")
    if "..." in link or "…" in link:
        die(f"{who}: link looks shortened: {link!r}")


def display_text(link):
    if link.startswith("mailto:"):
        return link[len("mailto:"):]
    return link  # full URL as plain text (user rule 2026-11-20: no hyperlinks)


def set_cell(tc, text, link=None, part=None):
    p = tc.find(qn("w:p"))
    for r in list(p):
        if r.tag in (qn("w:r"), qn("w:hyperlink")):
            p.remove(r)
    run = OxmlElement("w:r")
    if link:
        rpr = OxmlElement("w:rPr")
        color = OxmlElement("w:color"); color.set(qn("w:val"), "0563C1"); rpr.append(color)
        under = OxmlElement("w:u"); under.set(qn("w:val"), "single"); rpr.append(under)
        run.append(rpr)
    t = OxmlElement("w:t")
    t.text = text
    t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
    run.append(t)
    if link:
        rid = part.relate_to(link, RELATIONSHIP_TYPE.HYPERLINK, is_external=True)
        h = OxmlElement("w:hyperlink")
        h.set(qn("r:id"), rid)
        h.append(run)
        p.append(h)
    else:
        p.append(run)


def make_block(template_block, heading, rows, part):
    block = [copy.deepcopy(e) for e in template_block]
    head_t = block[0].find(".//" + qn("w:t"))
    head_t.text = heading
    tbl = block[TABLE_AT]
    trs = tbl.findall(qn("w:tr"))
    proto = copy.deepcopy(trs[1])
    for tr in trs[1:]:
        tbl.remove(tr)
    for row in rows:
        tr = copy.deepcopy(proto)
        tcs = tr.findall(qn("w:tc"))
        vals = [row["company"], row["opportunity"], row["location"], display_text(row["link"]), row["degree"]]
        for name, v in zip(("company", "opportunity", "location", None, "degree"), vals):
            if name and len(v) > MAX_LEN[name]:
                print(f"WARNING: {heading}: {name} longer than {MAX_LEN[name]} characters, shorten it: {v!r}")
            if name and re.search(r"[–—‘’“”]", v):
                print(f"WARNING: {heading}: use plain - and ' instead of curly quotes / long dashes: {v!r}")
        for i, (tc, v) in enumerate(zip(tcs, vals)):
            set_cell(tc, v)  # links are plain text, never hyperlinks
        tbl.append(tr)
    return block


def sort_rows(rows):
    return sorted(rows, key=lambda r: (r["company"].lower(), r["opportunity"].lower()))


def build(out_path, blocks):
    """blocks: list of (heading, rows)."""
    doc = Document(TEMPLATE)
    body = doc.element.body
    children = [c for c in body if c.tag != qn("w:sectPr")]
    if len(children) < BLOCK_LEN or children[TABLE_AT].tag != qn("w:tbl"):
        die("assets/template.docx no longer has the expected first-block layout")
    template_block = [copy.deepcopy(c) for c in children[:BLOCK_LEN]]
    for c in children:
        body.remove(c)
    sect = body.find(qn("w:sectPr"))
    for heading, rows in blocks:
        for el in make_block(template_block, heading, rows, doc.part):
            sect.addprevious(el)
    doc.save(out_path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("data")
    ap.add_argument("--main", required=True, help="output .docx for every faculty except education")
    ap.add_argument("--edu", required=True, help="output .docx for education")
    a = ap.parse_args()
    data = json.load(open(a.data, encoding="utf-8"))

    main_blocks, edu_blocks = [], []
    seen = set()
    for o in data.get("opportunities", []):
        who = f"{o.get('company')} / {o.get('opportunity')}"
        check_link(o.get("link"), who)
        degs = o.get("degrees") or {}
        if not degs:
            print(f"WARNING: {who} has no faculty allocation and will not appear anywhere")
        seen.add(who)
    for key, heading in FACULTIES:
        rows = []
        for o in data.get("opportunities", []):
            deg = (o.get("degrees") or {}).get(key)
            if deg:
                rows.append({**{k: o[k] for k in ("company", "opportunity", "location", "link")}, "degree": deg})
        for o in data.get("opportunities", []):
            for k in (o.get("degrees") or {}):
                if k not in {f for f, _ in FACULTIES} | {"EDUCATION"}:
                    die(f"unknown faculty key {k!r} for {o.get('company')}")
        if rows:
            main_blocks.append((heading, sort_rows(rows)))
        else:
            print(f"skipped (no opportunities): {heading}")

    # Education: user-shared jobs allocated to EDUCATION go in the "Other" email,
    # phase-specific teaching posts go in their phase email.
    edu_rows = {p: [] for p, _ in EDU_PHASES}
    for o in data.get("opportunities", []):
        deg = (o.get("degrees") or {}).get("EDUCATION")
        if deg:
            edu_rows["Other"].append({**{k: o[k] for k in ("company", "opportunity", "location", "link")}, "degree": deg})
    for e in data.get("education", []):
        who = f"{e.get('company')} / {e.get('opportunity')}"
        check_link(e.get("link"), who)
        if e.get("phase") not in edu_rows:
            die(f"{who}: phase must be one of {list(edu_rows)}")
        edu_rows[e["phase"]].append({k: e[k] for k in ("company", "opportunity", "location", "link", "degree")})
    for phase, heading in EDU_PHASES:
        if edu_rows[phase]:
            edu_blocks.append((heading, sort_rows(edu_rows[phase])))
        else:
            print(f"skipped (no opportunities): {heading}")

    for path, blocks, label in ((a.main, main_blocks, "main"), (a.edu, edu_blocks, "education")):
        if blocks:
            build(path, blocks)
            print(f"wrote {path}: " + ", ".join(f"{h} ({len(r)})" for h, r in blocks))
        else:
            print(f"no {label} opportunities, {path} not written")


if __name__ == "__main__":
    main()
