r"""Log of opportunities the Dell Young Leaders careers team has already shared.

One file for the whole team: "Shared opportunities.csv" in the shared OneDrive folder
"DYL Careers Hub" (synced on every team member's PC). The weekly mailer (jobmailer skill),
the WhatsApp message skill (job-opportunity-message) and the DYL Careers Hub dashboard all
read and write it.

Two ways of sharing, kept apart on purpose:
  mailer    = weekly faculty emails (log types "job" and "teaching")
  whatsapp  = a WhatsApp message to the group (log type "whatsapp")
Sharing something again by the SAME route is a problem and gets flagged. Something that
went out by the OTHER route is only mentioned (FYI). Nothing is ever removed automatically.

Commands (all print plain text / markdown tables ready to show the user)
  status                                   Is the OneDrive folder connected? Who am I?
  whoami [--set NAME]                      Name recorded next to what you share.
  check-opps --route mailer|whatsapp --opp "Company | Opportunity | City | Link" [--opp ...]
                                           Flag opportunities that were shared before.
  check-links --route mailer|whatsapp URL [URL ...]
                                           Same, from links only (before reading the pages).
  check DATA.json --out FLAGGED.json --date YYYY-MM-DD
                                           Mailer: mark already-shared jobs / teaching posts
                                           in the data file. Nothing is removed.
  record --main MAIN.docx --edu EDU.docx --date YYYY-MM-DD
                                           Mailer: log what is really in the finished documents.
  record-whatsapp --opp "Company | Opportunity | City | Link" [--opp ...] [--date D]
                                           WhatsApp: log opportunities as shared.
  unrecord --route whatsapp|mailer --link URL [--date D]
                                           Undo a log entry made today by mistake.

Exit code 3 + "NOT CONNECTED" means this PC cannot see the OneDrive folder yet.
Set DYL_TEAM_FOLDER to point at the folder if it is somewhere unusual.
"""
import argparse
import csv
import datetime
import getpass
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.parse

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass

LOG_NAME = "Shared opportunities.csv"
HUB = "DYL Careers Hub"
FIELDS = ["date_shared", "type", "company", "opportunity", "location", "link", "faculties", "shared_by"]
SETTINGS_DIR = os.path.join(os.path.expanduser("~"), ".dyl-careers")
KEEP_QUERY = {"jk", "jobid", "job_id", "id", "gh_jid", "vacancyid", "reqid"}
FLAG_PREFIX = re.compile(r"^\[Already shared[^\]]*\]\s*", re.I)
ROUTE_LABEL = {"mailer": "weekly mailer", "whatsapp": "WhatsApp"}

NOT_CONNECTED = """NOT CONNECTED: this PC cannot see the team OneDrive folder "DYL Careers Hub", so I cannot check
what the team has already shared.
Do NOT carry on as if nothing was shared. Walk the user through references/onedrive_setup.md one step at a time
(open the shared folder link -> Add shortcut to My files -> wait for the green ticks -> run `shared_log.py status`).
Only if the user insists on going ahead without the check, continue and say clearly that nothing was checked."""


def die(msg, code=1):
    print(msg)
    sys.exit(code)


# ---------- finding the shared folder ----------
def _subdirs(p):
    try:
        return [e.path for e in os.scandir(p) if e.is_dir()]
    except OSError:
        return []


def _is_hub(p):
    return os.path.isfile(os.path.join(p, LOG_NAME)) or os.path.isfile(os.path.join(p, "DYL CV and transcript numbers.json"))


def find_team_folder():
    """Return (path, complete). complete=False when the folder exists but the log file has not synced yet."""
    env = os.environ.get("DYL_TEAM_FOLDER")
    if env and os.path.isdir(env):
        return env, os.path.isfile(os.path.join(env, LOG_NAME))
    try:
        saved = open(os.path.join(SETTINGS_DIR, "team_folder.txt"), encoding="utf-8").read().strip()
        if saved and os.path.isdir(saved):
            return saved, os.path.isfile(os.path.join(saved, LOG_NAME))
    except OSError:
        pass
    home = os.path.expanduser("~")
    roots = []
    for var in ("OneDrive", "OneDriveCommercial", "OneDriveConsumer"):
        v = os.environ.get(var)
        if v and os.path.isdir(v) and v not in roots:
            roots.append(v)
    for d in _subdirs(home):
        n = os.path.basename(d).lower()
        if (n.startswith("onedrive") or "dell" in n or "foundation" in n) and d not in roots:
            roots.append(d)
    found_incomplete = None
    for r in roots:
        for d in _subdirs(r):
            for cand in [d] + _subdirs(d):
                if HUB.lower() in os.path.basename(cand).lower():
                    if _is_hub(cand):
                        return cand, os.path.isfile(os.path.join(cand, LOG_NAME))
                    found_incomplete = found_incomplete or cand
    if found_incomplete:
        return found_incomplete, False
    return None, False


def log_path(create=False):
    folder, complete = find_team_folder()
    if not folder:
        die(NOT_CONNECTED, 3)
    p = os.path.join(folder, LOG_NAME)
    if not complete:
        if create:
            write_rows(p, [])
            return p
        die(f"NOT CONNECTED: found the folder {folder} but the file \"{LOG_NAME}\" is not in it yet. "
            "OneDrive is probably still syncing. Ask the user to wait for the green ticks on the folder in File Explorer "
            "(or to check they were given edit access), then try again.", 3)
    return p


# ---------- who is sharing ----------
def my_name():
    n = os.environ.get("DYL_NAME")
    if n:
        return n.strip()
    try:
        n = open(os.path.join(SETTINGS_DIR, "name.txt"), encoding="utf-8").read().strip()
        if n:
            return n
    except OSError:
        pass
    return ""


def cmd_whoami(a):
    if a.set:
        os.makedirs(SETTINGS_DIR, exist_ok=True)
        open(os.path.join(SETTINGS_DIR, "name.txt"), "w", encoding="utf-8").write(a.set.strip())
        print("name saved: " + a.set.strip())
    else:
        print(my_name() or "(not set)")


# ---------- matching ----------
def norm_link(url):
    url = (url or "").strip()
    if url.startswith("mailto:"):
        return url.lower()
    if not re.match(r"^https?://", url):
        url = "https://" + url
    u = urllib.parse.urlsplit(url)
    host = u.netloc.lower().removeprefix("www.")
    params = urllib.parse.parse_qsl(u.query)
    if host.endswith("linkedin.com"):
        # one LinkedIn job, many link shapes: /jobs/view/<id> or a search page with ?currentJobId=<id>
        m = re.search(r"/jobs/view/(?:[^/]*-)?(\d{6,})", u.path)
        job_id = m.group(1) if m else next((v for k, v in params if k.lower() == "currentjobid"), "")
        if job_id:
            return "linkedin.com/jobs/view/" + job_id
    path = u.path.rstrip("/")
    q = [(k, v) for k, v in params if k.lower() in KEEP_QUERY]
    return host + path + ("?" + urllib.parse.urlencode(sorted(q)) if q else "")


def norm_text(*parts):
    return "|".join(re.sub(r"[^a-z0-9]+", "", (p or "").lower()) for p in parts)


def keys(row):
    # one Edupstairs vacancy page can hold a Foundation and an Intermediate post: compare the phase too
    phase = row.get("phase") or (row.get("faculties") if row.get("type") == "teaching" else "")
    if phase in ("Other", None):
        phase = ""
    tag = "#" + norm_text(phase) if phase else ""
    ks = {"L:" + norm_link(row.get("link", "")) + tag}
    if row.get("company") or row.get("opportunity"):
        ks.add("T:" + norm_text(row.get("company"), row.get("opportunity"), row.get("location")))
    return ks


def route_of(row):
    return "whatsapp" if (row.get("type") or "").strip().lower() == "whatsapp" else "mailer"


def pretty_date(s):
    try:
        d = datetime.date.fromisoformat((s or "")[:10])
        return f"{d.day} {d:%b} {d.year}"
    except ValueError:
        return s or "?"


def describe(row):
    by = (row.get("shared_by") or "").strip()
    return f"{ROUTE_LABEL[route_of(row)]}, {pretty_date(row.get('date_shared'))}" + (f", by {by}" if by else "")


def build_index(rows, skip=None):
    idx = {}
    for r in rows:
        if skip and skip(r):
            continue
        for k in keys(r):
            idx.setdefault(k, []).append(r)
    return idx


def lookup(item, idx, route):
    """(same_route_row, other_route_row): earliest earlier share by each route, or None."""
    same = other = None
    seen = set()
    for k in keys(item):
        for r in idx.get(k, []):
            if id(r) in seen:
                continue
            seen.add(id(r))
            if route_of(r) == route:
                if same is None or (r.get("date_shared") or "") < (same.get("date_shared") or ""):
                    same = r
            else:
                if other is None or (r.get("date_shared") or "") < (other.get("date_shared") or ""):
                    other = r
    return same, other


# ---------- log I/O ----------
def read_rows(p):
    with open(p, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_rows(p, rows):
    rows = sorted(rows, key=lambda r: (r.get("date_shared", ""), r.get("type", ""), (r.get("company") or "").lower()))
    tmp = p + ".tmp"
    with open(tmp, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows({k: r.get(k, "") for k in FIELDS} for r in rows)
    try:
        os.replace(tmp, p)
    except PermissionError:
        try:
            os.remove(tmp)
        except OSError:
            pass
        die(f"ERROR: the log {p} is open in another program (Excel?). Ask the user to close it, then run this again.", 2)


# ---------- output ----------
def md_cell(s):
    return (s or "").replace("|", "/").replace("\n", " ")


def show_table(entries):
    """entries: list of dicts with label, same, other. Prints a summary and a markdown table."""
    n_same = sum(1 for e in entries if e["same"])
    n_other = sum(1 for e in entries if e["other"] and not e["same"])
    print(f"{len(entries)} checked: {n_same} ALREADY SHARED by this route (flag as a problem), "
          f"{n_other} shared by the other route only (just mention it), {len(entries) - n_same - n_other} new.")
    print()
    print("| Opportunity | Status | Shared before |")
    print("|---|---|---|")
    for e in entries:
        if e["same"]:
            status, when = "ALREADY SHARED", describe(e["same"])
            if e["other"]:
                when += "; also " + describe(e["other"])
        elif e["other"]:
            status, when = "FYI: other route", describe(e["other"])
        else:
            status, when = "New", ""
        print(f"| {md_cell(e['label'])} | {status} | {md_cell(when)} |")


def label_of(o):
    if o.get("company") or o.get("opportunity"):
        return " - ".join(x for x in (o.get("company"), o.get("opportunity")) if x) or o.get("link", "")
    return o.get("link", "")


# ---------- commands: checking ----------
def parse_opp(s):
    parts = [x.strip() for x in s.split("|")]
    if len(parts) < 4:
        die(f'ERROR: --opp needs "Company | Opportunity | City | Link", got: {s!r}', 2)
    company, opp, loc = parts[0], parts[1], parts[2]
    link = "|".join(parts[3:]).strip()
    return {"company": company, "opportunity": opp, "location": loc, "link": link}


def run_check(items, route):
    idx = build_index(read_rows(log_path()))
    entries = []
    for o in items:
        same, other = lookup(o, idx, route)
        entries.append({"label": label_of(o), "same": same, "other": other})
    show_table(entries)


def cmd_check_opps(a):
    run_check([parse_opp(s) for s in a.opp], a.route)


def cmd_check_links(a):
    run_check([{"link": u} for u in a.urls], a.route)


def cmd_check(a):
    """Mailer: annotate the data file; never remove anything."""
    rows = read_rows(log_path())
    # rebuilding the same day must not flag this mailer's own rows
    idx = build_index(rows, skip=lambda r: r.get("date_shared") == a.date and route_of(r) == "mailer")
    data = json.load(open(a.data, encoding="utf-8"))
    entries = []
    for section in ("opportunities", "education"):
        for o in data.get(section, []):
            o.pop("flag_text", None)
            o.pop("shared_before", None)
            same, other = lookup(o, idx, "mailer")
            if same:
                o["flag_text"] = "Already shared " + pretty_date(same.get("date_shared")).rsplit(" ", 1)[0]
            if same or other:
                o["shared_before"] = {k: describe(r) for k, r in (("mailer", same), ("whatsapp", other)) if r}
            entries.append({"label": label_of(o), "same": same, "other": other})
    json.dump(data, open(a.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    show_table(entries)
    print(f"\nnothing was removed; {sum(1 for e in entries if e['same'])} rows will carry an "
          f"[Already shared ...] flag in the documents -> {a.out}")


# ---------- commands: recording ----------
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
                             "company": FLAG_PREFIX.sub("", c[0].text.strip()), "opportunity": c[1].text.strip(),
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


def cmd_record(a):
    p = log_path()
    old = read_rows(p)
    new = []
    if a.main:
        new += merge_by_job(read_docx(a.main, "main"))
    if a.edu:
        new += merge_by_job(read_docx(a.edu, "edu"))
    me = my_name()
    for r in new:
        r["date_shared"] = a.date
        r["shared_by"] = me
    # re-running on the same day replaces this mailer's rows (WhatsApp rows are kept)
    kept = [r for r in old if not (r.get("date_shared") == a.date and route_of(r) == "mailer")]
    idx = build_index([r for r in kept if route_of(r) == "mailer"])
    fresh = [r for r in new if not any(k in idx for k in keys(r))]
    write_rows(p, kept + fresh)
    print(f"{a.date}: {len(fresh)} opportunities added to the shared log "
          f"({len(new) - len(fresh)} were already logged by an earlier mailer and keep their first date).")
    print("saved to: " + p)


def cmd_record_whatsapp(a):
    p = log_path()
    rows = read_rows(p)
    idx = build_index([r for r in rows if route_of(r) == "whatsapp"])
    me = my_name()
    added, skipped = [], []
    for s in a.opp:
        o = parse_opp(s)
        if any(k in idx for k in keys(o)):
            skipped.append(label_of(o))
            continue
        row = {**o, "date_shared": a.date, "type": "whatsapp", "faculties": "WhatsApp group", "shared_by": me}
        rows.append(row)
        for k in keys(row):
            idx.setdefault(k, []).append(row)
        added.append(label_of(o))
    write_rows(p, rows)
    for x in added:
        print("logged as shared on WhatsApp: " + x)
    for x in skipped:
        print("already in the log as a WhatsApp share (kept its first date): " + x)


def cmd_unrecord(a):
    p = log_path()
    rows = read_rows(p)
    target = keys({"link": a.link})
    keep, gone = [], []
    for r in rows:
        if route_of(r) == a.route and r.get("date_shared") == a.date and (keys(r) & target):
            gone.append(r)
        else:
            keep.append(r)
    write_rows(p, keep)
    print(f"removed {len(gone)} log entr{'y' if len(gone) == 1 else 'ies'} for that link dated {a.date}"
          if gone else "nothing matched (only entries from the given date and route can be removed)")


def cmd_status(a):
    folder, complete = find_team_folder()
    if not folder:
        die(NOT_CONNECTED, 3)
    if not complete:
        log_path()  # prints the "still syncing" message and exits 3
    rows = read_rows(os.path.join(folder, LOG_NAME))
    w = sum(1 for r in rows if route_of(r) == "whatsapp")
    last = max((r.get("date_shared", "") for r in rows), default="")
    print(f"CONNECTED: {folder}")
    print(f"shared log: {len(rows)} entries ({len(rows) - w} by the weekly mailer, {w} by WhatsApp), last share {pretty_date(last) if last else 'none yet'}")
    print("your name in the log: " + (my_name() or "(not set - ask the user for their first name, then run: whoami --set NAME)"))


def main():
    today = datetime.date.today().isoformat()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("status"); s.set_defaults(f=cmd_status)
    s = sub.add_parser("whoami"); s.add_argument("--set"); s.set_defaults(f=cmd_whoami)
    s = sub.add_parser("check-opps"); s.add_argument("--route", choices=["mailer", "whatsapp"], required=True)
    s.add_argument("--opp", action="append", required=True); s.set_defaults(f=cmd_check_opps)
    s = sub.add_parser("check-links"); s.add_argument("--route", choices=["mailer", "whatsapp"], required=True)
    s.add_argument("urls", nargs="+"); s.set_defaults(f=cmd_check_links)
    s = sub.add_parser("check"); s.add_argument("data"); s.add_argument("--out", required=True)
    s.add_argument("--date", default=today); s.set_defaults(f=cmd_check)
    s = sub.add_parser("record"); s.add_argument("--main"); s.add_argument("--edu")
    s.add_argument("--date", default=today); s.set_defaults(f=cmd_record)
    s = sub.add_parser("record-whatsapp"); s.add_argument("--opp", action="append", required=True)
    s.add_argument("--date", default=today); s.set_defaults(f=cmd_record_whatsapp)
    s = sub.add_parser("unrecord"); s.add_argument("--route", choices=["mailer", "whatsapp"], required=True)
    s.add_argument("--link", required=True); s.add_argument("--date", default=today); s.set_defaults(f=cmd_unrecord)
    a = ap.parse_args()
    a.f(a)


if __name__ == "__main__":
    main()
