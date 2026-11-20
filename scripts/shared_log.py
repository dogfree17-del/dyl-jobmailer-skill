"""Log of opportunities already shared in the weekly mailer, kept in a public GitHub repo.

Repo: https://github.com/dogfree17-del/dyl-shared-opportunities  (file: shared_opportunities.csv)
Anyone can read it (the raw file is public). Recording needs push access to the repo.

Commands
  python shared_log.py check-links URL [URL ...]
      Before browsing: says which of the user's links were already shared (and when).
  python shared_log.py check data.json --out data_new.json --date YYYY-MM-DD
      After filling data.json: drops every job / teaching post already in the log
      (same link, or same company + opportunity + location) and writes data_new.json.
      Rows logged on --date itself are ignored, so rebuilding on the same day works.
  python shared_log.py record --main MAIN.docx --edu EDU.docx --date YYYY-MM-DD
      After the final build: reads what is really in the documents (including the user's
      own edits), replaces that date's rows in the log, commits and pushes.

The local clone lives at ~/develop/dyl-shared-opportunities (cloned on first use).
"""
import argparse, csv, io, json, os, re, shutil, subprocess, sys, tempfile, urllib.parse, urllib.request

OWNER_REPO = "dogfree17-del/dyl-shared-opportunities"
CSV_NAME = "shared_opportunities.csv"
RAW_URL = f"https://raw.githubusercontent.com/{OWNER_REPO}/main/{CSV_NAME}"
CLONE_DIR = os.path.expanduser("~/develop/dyl-shared-opportunities")
FIELDS = ["date_shared", "type", "company", "opportunity", "location", "link", "faculties"]
KEEP_QUERY = {"jk", "jobid", "job_id", "id", "gh_jid", "vacancyid", "reqid"}


# ---------- matching ----------
def norm_link(url):
    url = (url or "").strip()
    if url.startswith("mailto:"):
        return url.lower()
    if not re.match(r"^https?://", url):
        url = "https://" + url
    u = urllib.parse.urlsplit(url)
    host = u.netloc.lower().removeprefix("www.")
    path = u.path.rstrip("/")
    q = [(k, v) for k, v in urllib.parse.parse_qsl(u.query) if k.lower() in KEEP_QUERY]
    return host + path + ("?" + urllib.parse.urlencode(sorted(q)) if q else "")


def norm_text(*parts):
    return "|".join(re.sub(r"[^a-z0-9]+", "", (p or "").lower()) for p in parts)


def keys(row):
    # one Edupstairs vacancy page can hold a Foundation and an Intermediate post: compare the phase too
    phase = row.get("phase") or (row.get("faculties") if row.get("type") == "teaching" else "")
    if phase in ("Other", None):
        phase = ""
    tag = "#" + norm_text(phase) if phase else ""
    return {"L:" + norm_link(row["link"]) + tag, "T:" + norm_text(row["company"], row["opportunity"], row["location"])}


# ---------- log I/O ----------
def git(*args, check=True):
    return subprocess.run(["git", "-C", CLONE_DIR, *args], capture_output=True, text=True, check=check)


def ensure_clone():
    if not os.path.isdir(os.path.join(CLONE_DIR, ".git")):
        os.makedirs(os.path.dirname(CLONE_DIR), exist_ok=True)
        subprocess.run(["gh", "repo", "clone", OWNER_REPO, CLONE_DIR], check=True)
    else:
        git("pull", "--ff-only", "--quiet", check=False)


def read_log(prefer_local=True):
    text = None
    if prefer_local and os.path.isdir(os.path.join(CLONE_DIR, ".git")):
        git("pull", "--ff-only", "--quiet", check=False)
        p = os.path.join(CLONE_DIR, CSV_NAME)
        if os.path.exists(p):
            text = open(p, encoding="utf-8").read()
    if text is None:
        try:
            text = urllib.request.urlopen(RAW_URL, timeout=20).read().decode("utf-8")
        except Exception as e:
            sys.exit(f"ERROR: could not read the shared log ({e}). Check {RAW_URL}")
    return list(csv.DictReader(io.StringIO(text)))


def index(rows, skip_date=None):
    idx = {}
    for r in rows:
        if skip_date and r["date_shared"] == skip_date:
            continue
        for k in keys(r):
            idx.setdefault(k, r)
    return idx


# ---------- docx reading ----------
def read_docx(path, kind):
    from docx import Document
    from docx.oxml.ns import qn
    from docx.table import Table
    from docx.text.paragraph import Paragraph
    tmp = os.path.join(tempfile.mkdtemp(), "f.docx")
    shutil.copyfile(path, tmp)          # works even while the file is open in Word
    d = Document(tmp)
    rows, heading, prev = [], "", ""
    for el in d.element.body:
        if el.tag == qn("w:p"):
            t = Paragraph(el, d._body).text.strip()
            if t.startswith("Subject:"):
                heading = prev
            if t:
                prev = t
        elif el.tag == qn("w:tbl"):
            for tr in Table(el, d._body).rows[1:]:
                c = tr.cells
                link = c[3].text.strip()
                h = c[3]._tc.find(".//" + qn("w:hyperlink"))
                if h is not None and h.get(qn("r:id")) in d.part.rels:
                    link = d.part.rels[h.get(qn("r:id"))].target_ref
                if not re.match(r"^(https?://|mailto:)", link):
                    link = ("mailto:" if "@" in link and "/" not in link else "https://") + link
                rows.append({"type": "teaching" if kind == "edu" and heading.startswith("Education") and "Phase" in heading else "job",
                             "company": c[0].text.strip(), "opportunity": c[1].text.strip(),
                             "location": c[2].text.strip(), "link": link,
                             "faculties": heading.replace("Education – ", "").replace("Education - ", "")})
    return rows


def merge_by_job(rows):
    out = {}
    for r in rows:
        k = norm_link(r["link"]) + "#" + norm_text(r["company"], r["opportunity"])
        if k in out:
            if r["faculties"] not in out[k]["faculties"].split("; "):
                out[k]["faculties"] += "; " + r["faculties"]
        else:
            out[k] = dict(r)
    return list(out.values())


# ---------- commands ----------
def cmd_check_links(a):
    idx = index(read_log())
    for url in a.urls:
        hit = idx.get("L:" + norm_link(url))
        print(f"ALREADY SHARED {hit['date_shared']}: {hit['company']} - {hit['opportunity']}  {url}" if hit else f"new: {url}")


def cmd_check(a):
    idx = index(read_log(), skip_date=a.date)
    data = json.load(open(a.data, encoding="utf-8"))
    removed = []
    for section in ("opportunities", "education"):
        keep = []
        for o in data.get(section, []):
            hit = next((idx[k] for k in keys(o) if k in idx), None)
            if hit:
                removed.append(f"{o['company']} - {o['opportunity']} (shared {hit['date_shared']})")
            else:
                keep.append(o)
        data[section] = keep
    json.dump(data, open(a.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"{len(removed)} already shared, removed:" if removed else "nothing was shared before")
    for r in removed:
        print("  - " + r)
    print(f"kept {len(data.get('opportunities', []))} jobs and {len(data.get('education', []))} teaching posts -> {a.out}")


def cmd_record(a):
    ensure_clone()
    p = os.path.join(CLONE_DIR, CSV_NAME)
    old = list(csv.DictReader(open(p, encoding="utf-8"))) if os.path.exists(p) else []
    new = []
    if a.main:
        new += merge_by_job(read_docx(a.main, "main"))
    if a.edu:
        new += merge_by_job(read_docx(a.edu, "edu"))
    for r in new:
        r["date_shared"] = a.date
    kept = [r for r in old if r["date_shared"] != a.date]
    idx = index(kept)
    fresh = [r for r in new if not any(k in idx for k in keys(r))]
    rows = sorted(kept + fresh, key=lambda r: (r["date_shared"], r["type"], r["company"].lower()))
    with open(p, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows({k: r.get(k, "") for k in FIELDS} for r in rows)
    print(f"{a.date}: {len(fresh)} opportunities recorded ({len(new) - len(fresh)} skipped as already shared on an earlier date)")
    git("add", CSV_NAME)
    if git("diff", "--cached", "--quiet", check=False).returncode == 0:
        print("log unchanged, nothing to push")
        return
    git("commit", "-q", "-m", f"Record mailer {a.date}: {len(fresh)} opportunities\n\n"
        "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>")
    r = git("push", "-q", check=False)
    print("pushed to github.com/" + OWNER_REPO if r.returncode == 0 else "PUSH FAILED: " + r.stderr.strip())


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("check-links"); s.add_argument("urls", nargs="+"); s.set_defaults(f=cmd_check_links)
    s = sub.add_parser("check"); s.add_argument("data"); s.add_argument("--out", required=True)
    s.add_argument("--date", required=True); s.set_defaults(f=cmd_check)
    s = sub.add_parser("record"); s.add_argument("--main"); s.add_argument("--edu")
    s.add_argument("--date", required=True); s.set_defaults(f=cmd_record)
    a = ap.parse_args()
    a.f(a)


if __name__ == "__main__":
    main()
