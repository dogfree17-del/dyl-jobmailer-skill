---
name: jobmailer
description: Turns job links the user shares (LinkedIn, Indeed, Careers24, careers pages, flyer images) into the Dell Young Leaders "Explore These Career Opportunities" email bodies, one email per faculty (EMS, Science, Engineering, Law, Agriscience, Social Sciences), and builds a separate Education document with Foundation Phase and Intermediate Phase teaching posts from Edupstairs. Produces two .docx files in a fixed template with full links as plain text (no hyperlinks). Use whenever the user says /jobmailer, "job mailer", "mailer", "make the faculty emails", "put these jobs into the email document", or shares job links and wants them split by faculty into email bodies, even if they don't name the skill. Not for the all-faculties table with "similar" jobs (opportunity-scout) or WhatsApp blurbs (job-opportunity-message).
---

# Job Mailer

The user shares job links. You read each one, allocate it strictly to faculties, and fill a fixed email template so the user can paste each faculty's email straight into their mailer. Two Word files come out:

1. **Main document**: one email body per faculty, for every faculty except Education.
2. **Education document**: Foundation Phase and Intermediate Phase teaching posts (from Edupstairs), plus any user-shared jobs allocated to Education.

## Step 0: Get the latest version of this skill

This skill is shared through GitHub (https://github.com/dogfree17-del/dyl-jobmailer-skill) so that everyone uses the same version. At the start of every run, pull the latest version:

```bash
git -C "<skill-folder>" pull --ff-only
```

If the pull changed `SKILL.md`, re-read it before continuing. The scripts, template and references take effect straight away. If the pull fails (no internet, or local edits that are not pushed), tell the user and carry on with the local copy.

**Output folder** (`<Opportunities folder>` below): `~/OneDrive/Documents/Opportunities` if the user has OneDrive Documents, otherwise `~/Documents/Opportunities`. Create it if it does not exist.

## Step 0b: Check the shared log is connected

```bash
python "<skill-folder>/scripts/shared_log.py" status
```

- `CONNECTED`: carry on. If it says your name in the log is **(not set)**, ask the user for their first name once and run `python "<skill-folder>/scripts/shared_log.py" whoami --set "<first name>"`. The name is shown next to what they share, so teammates see who sent it.
- `NOT CONNECTED`: stop. This PC cannot see the team OneDrive folder, so nothing can be checked. Walk the user through `references/onedrive_setup.md` one step at a time (wait for their answer after each step), then run `status` again. Only if the user says to go ahead without the check, continue and say clearly in the reply that nothing could be checked against what the team already shared.

## Editing this skill

**Ask for the edit password first. No password, no edit.** Before changing ANY file in `<skill-folder>` (SKILL.md, references, template, scripts), ask the user for the skill's edit password, then check it:

```bash
printf '%s\n' "<password the user typed>" | python "<skill-folder>/scripts/edit_lock.py" check
```

- `OK`: go ahead with the edit.
- `WRONG`: don't edit. Tell the user the password is wrong; they can try again. After 3 wrong tries, stop and tell them to ask the skill owner.
- `NO PASSWORD SET`: don't edit; tell the user the owner must set one with `python "<skill-folder>/scripts/edit_lock.py" set`.

Never write the password into any file, commit message, or reply, and never change or delete `assets/edit_lock.json` or `scripts/edit_lock.py` unless the password check passed in this conversation. Ask again in each new conversation. Making the weekly mailer (building documents, updating the shared log) is not an edit and needs no password.

When the password check has passed, edit the files in `<skill-folder>`, then publish the change so everyone gets it on their next run:

```bash
git -C "<skill-folder>" add -A
git -C "<skill-folder>" commit -m "<short description of the change>"
git -C "<skill-folder>" push
```

Pull first if the push is rejected. If the push fails because this GitHub account has no write access, tell the user the change only applies on this computer and that the repo owner can add them as a collaborator.

## The template

The look is fixed. `assets/template.docx` is the user's own document and `scripts/build_mailer.py` clones its first email block for each faculty. The user said "exactly this is fine", so never restyle the template, add columns, add sections, or add summary text inside the documents. Notes for the user go in your chat reply, not in the files.

## Hard rules

- **Only the jobs the user gave you.** Do not search for "similar" jobs and do not pad faculties. The only extra jobs allowed are the Edupstairs teaching posts, because the user asked for those explicitly.
- **Skip a faculty that has no opportunities.** The script does this automatically and tells you which were skipped.
- **Links must be complete and working.** Full `https://` URLs, never shortened with "...", no tracking parameters (`&from=shareddesktop_copy`, `?trk=`, `?utm_`). The script refuses links that look shortened and writes each link as the full URL in plain text. **No hyperlinks** (user rule, 2026-11-20).
- **Never apply.** Only read pages. Never click Apply or Send, sign in, or submit anything. Careers24 `/jobs/apply/ID` links are application forms that already contain the user's uploaded CV, so open the public advert page instead (see below).
- **Flag what the team already shared. Never remove it.** Everything that has gone out (in a mailer, or on WhatsApp through the job-opportunity-message skill or the dashboard) is logged in "Shared opportunities.csv" in the team OneDrive folder **DYL Careers Hub**, which every team member syncs (Step 0 checks it is connected). Two routes are kept apart:
  - Already sent **in a mailer** = a real problem. Keep the job in the documents, but flag it: the script writes the row highlighted yellow with `[Already shared 20 Nov]` in front of the company, and you list it first in your reply, with the date and who shared it. The user decides whether to delete the row before sending.
  - Only sent **on WhatsApp** = not a problem. Mention it in the reply table as FYI, with the date and who shared it. No flag in the documents.
  Never drop a flagged job yourself, and never hide a flag.
- **Don't silently drop a job the user gave you.** If a link is dead or closed, tell the user in the reply and leave it out of the document. If it is open but has a red flag (asks for 1+ years of experience, commission-only, closes within 2 days), include it and flag it in the reply.

## Step 1: Get the links

Use the links in the user's message. Images (flyers) count as jobs: read them and transcribe company, opportunity, location, how to apply, qualification. If there are no links, ask for them and stop. Don't start browsing without links.

Before browsing, check which links the team already shared:

```bash
python "<skill-folder>/scripts/shared_log.py" check-links --route mailer URL1 URL2 ...
```

Read every link anyway, because flagged jobs stay in the documents. Remember which ones the table marked **ALREADY SHARED** (sent in an earlier mailer) and which **FYI** (only on WhatsApp); Step 5 repeats the check once the details are filled in.

## Step 2: Read each job

| Field | What goes in the cell |
|---|---|
| Company | Employer's short name: "Faurecia", not "Faurecia South Africa (FORVIA)" (for a recruiter ad with no named employer: the recruiter name) |
| Opportunity | Short title, max ~40 characters, e.g. "Finance Graduate", "Graduate Programme 2027". Drop suffixes like "(12 Month Fixed Term Contract)" and the location. |
| Location | City only, e.g. "Cape Town", "Gqeberha". Province only when no city is given; "Nationwide" for national programmes. |
| Application Link | The URL the user gave (cleaned) or the company's own application page. Full URL. |
| Preferred Course/Degree | Degrees **from `references/student_degrees.md`** (the degrees our students study) that relate to what the ad asks for, written per faculty (see Step 3). Use the list's "Mailer name", 2–4 of them, max ~80 characters, e.g. "BAccounting / BCom (Financial Accounting)" |

**Keep the table short (user rule, 2026-11-20).** The emails are pasted into DYL Connect, and long cells make the table too wide and the email too heavy. Use plain characters: "-" not "–", "'" not "’". The script prints a WARNING for any cell over the limits; shorten it and rebuild.

Which browser:
- **LinkedIn**: Claude in Chrome (`mcp__claude-in-chrome__*`), because the user's Chrome is signed in. Read `anthropic-skills:chrome-browser` first, load the tools in one ToolSearch call, open a new tab, and close it at the end. Use `get_page_text` after `navigate`; batch several navigate + get_page_text pairs in one `browser_batch` call.
- **Indeed** (`za.indeed.com/viewjob?jk=ID`): Chrome works and shows the full description. Use `https://za.indeed.com/viewjob?jk=ID` as the link (drop `&from=...`).
- **Careers24**: the pasted link is usually `/jobs/apply/ID`. The public page is `https://www.careers24.com/jobs/adverts/ID-title-in-lowercase-hyphens-location` (e.g. `2398439-graduate-intern-bloemfontein`). If the slug is wrong the site redirects to a job list, so check that the page you read shows the right job, and use WebSearch to find the real slug if not. Use the advert URL as the link and as the source of details.
- **Other sites**: WebFetch (or the web-fetch agent) first; Chrome if the page is JavaScript-only.
- LinkedIn "About the job" sometimes cuts off before the requirements. Say so in your reply and infer the degree from the title, marking it as inferred in the reply (the document cell just carries your best short wording).

Check each job's closing date. A closed job, or one closing today, stays out.

## Step 3: Allocate strictly by faculty

Read `references/faculties.md` and `references/student_degrees.md`. For each job decide which faculties' graduates the ad actually asks for, going by the degrees named first and the work second. Then translate the ad's degree wording into **our students' degrees** from `student_degrees.md`: the ad may say "Finance degree" or "Supply Chain", and the cell shows the related degrees from the list (e.g. "BAccounting / BCom (Financial Sciences)", "BCom (Management Sciences)"). Each faculty gets its own degree text, so the same job appears in several tables with different "Preferred Course/Degree" wording. For example BMW's graduate programme is "BAccounting / BCom (Financial Accounting) / BCom (Management Sciences)" under EMS, "BSc (Computer Science) / BDatSci (Data Science)" under Science, and "LLB / BAccLLB" under Law. If no degree in the list relates, use the ad's wording and flag it in the reply. If the ad asks for a health or veterinary degree (MBChB, Nursing, Physiotherapy, etc.), tell the user: there is no faculty email for those yet.

Strictness rules the user has set:
- A faculty needs a named degree in the ad, or work that clearly belongs to it. "Any degree" ads go only to the faculties whose graduates plausibly do the work (analytical / quantitative ads: Science, Engineering, Law; use wording like "Any quantitative / analytical degree").
- IT-support and data-processing roles are Science only, even if "Information Systems" is listed.
- Don't put a job in EMS only because it is a corporate graduate programme. EMS needs a commerce degree or commerce work.
- Inferred degrees (the ad lists none) go to as few faculties as the duties justify.
- A job can use several faculties; Education gets a job only if the ad names BEd / PGCE / teaching.

Faculty keys for the JSON: `EMS`, `SCIENCE`, `ENGINEERING`, `LAW`, `AGRISCIENCE`, `SOCIAL SCIENCES`, `EDUCATION`.
Order of emails in the main document: EMS / Commerce, Science, Engineering, Law, Agriscience, Social Sciences.

## Step 4: Education (Foundation and Intermediate Phase)

Do this on every run, because the user asked for the Education document each time.

1. Open `https://www.edupstairs.org/south-african-teaching-posts/` in Chrome. It is a search page. The phase lists are at:
   - `https://www.edupstairs.org/teaching-posts/?sa_tp_phase=Foundation%20Phase`
   - `https://www.edupstairs.org/teaching-posts/?sa_tp_phase=Intermediate%20Phase`
   The default view hides closed vacancies; leave it that way.
2. `get_page_text` only returns the first card. Read the whole list with JavaScript on the page and return only text, never `href`s, because the JS tool blocks output that contains URLs with query strings:
   `[...document.querySelectorAll('article')].map(a=>a.innerText.split('\n').filter(s=>s.trim()).join(' ; ')).join('\n')`
   Long lists get cut off at about 1,000 characters, so read it in slices of four (`.slice(0,4)`, `.slice(4,8)`, ...). Each card gives school, location, subjects and grades, phase, permanent or temporary, number of posts and closing date. The vacancy link is `https://www.edupstairs.org/teaching-posts/ID/`; the ID is in the card's link (`a.pathname`).
3. Open each vacancy page (`/teaching-posts/ID/`) and read `document.querySelector('main').innerText` from "Requirements" to "Safety reminder" for requirements and how to apply. All school posts need REQV 13+ and SACE registration; some also need First Aid or a police clearance.
4. A card can contain posts for different phases (for example "Post 1 All subjects Gr R–3, Post 2 Intermediate Phase Gr 4–6"). Split it: one row in Foundation, one in Intermediate, each with that post's subjects.
5. Leave out posts that are closed or close today. Keep posts closing in 1–2 days and flag them in the reply.
6. Rows go in the `education` array with `phase` set to `Foundation Phase` or `Intermediate Phase`. Company is the school, Opportunity is short subjects and grades plus "(Perm)" or "(Temp)", e.g. "All subjects Gr 1-3 (Perm)"; abbreviate subjects (Maths, NS & Tech, SS, LS, Eng HL, Afr FAL) and say "2 posts" instead of listing each. Location is the town. Application Link is the vacancy page (or `mailto:` for a flyer that only gives an email address). Degree is "BEd Foundation Phase, SACE" (or Intermediate), plus a short extra from the post if needed (", police clearance", ", First Aid").
7. Teaching jobs the user shared themselves (flyers or links) go in the `education` array under the phase they belong to.
8. Non-teaching jobs the user shared that you allocated to EDUCATION in Step 3 (for example a BEd-accepting graduate programme) appear automatically as an extra "Education" email (phase `Other`).

## Step 5: Build

Write the data to a JSON file in the scratchpad (shape is in the docstring of `scripts/build_mailer.py`; `examples/2026-11-12.json` is a full example). Then flag everything the team already shared, including Edupstairs posts and any job posted again under a new link (same company + title + location):

```bash
python "<skill-folder>/scripts/shared_log.py" check data.json --out data_flagged.json --date YYYY-MM-DD
```

It prints the table you show the user (Step 6) and adds a flag to every job already sent in a mailer. **Nothing is removed.** `--date` is today's mailer date; rows logged on that date are ignored, so rebuilding on the same day doesn't flag this mailer's own jobs. Then build from `data_flagged.json`:

```bash
python "<skill-folder>/scripts/build_mailer.py" data_flagged.json \
  --main "<Opportunities folder>/Career_Opportunities_YYYY-MM-DD.docx" \
  --edu  "<Opportunities folder>/Career_Opportunities_Education_YYYY-MM-DD.docx"
```

Add `-2`, `-3` to the file names if they already exist. The script prints which faculties were written and which were skipped. Fix any ERROR it reports (usually a shortened or malformed link).

Then record the mailer in the shared log (it reads the finished documents, ignores the `[Already shared ...]` flags, and saves them to the OneDrive log with the user's name):

```bash
python "<skill-folder>/scripts/shared_log.py" record --main MAIN.docx --edu EDU.docx --date YYYY-MM-DD
```

Run `record` again after every rebuild or after the user edits the documents the same day (for example removing a job): it replaces that date's mailer rows with what is in the documents now (WhatsApp rows are kept). Jobs an earlier mailer already logged keep their first date. If it says the file is open, ask the user to close it in Excel and run `record` again.

## Step 6: Deliver

Send both files with `SendUserFile` (display `attach`). Then reply briefly:
- Rows per faculty and per phase, and which faculties were skipped.
- Jobs that need attention: closing within 2 days (name the date), asks for 1+ years of experience, commission-only, degree inferred because the ad gave none, link that was a form and was swapped for the advert page, anything you could not open.
- **The already-shared table**, first, before the other notes. Paste the table `check` printed (Opportunity | Status | Shared before). Say plainly which jobs were **already sent in an earlier mailer** (kept in the documents but highlighted yellow with `[Already shared ...]`; the user should delete those rows before sending, unless sharing again on purpose) and which were only on WhatsApp (FYI, no flag in the documents). Give the date and who shared each one. If nothing was shared before, say so in one line.
- The shared log in OneDrive was updated.
- Say that no jobs were added beyond the ones shared plus the Edupstairs posts.

## Files

- `assets/template.docx`: the user's template. Do not edit it casually; the script clones its first block (7 paragraphs, the table, 7 paragraphs). The 7th paragraph (just above the table) holds the green WhatsApp opt-out line the user asked for on 2026-11-20 (the version without it is in the git history).
- `scripts/build_mailer.py`: builds both documents.
- `scripts/edit_lock.py` + `assets/edit_lock.json`: the edit password check (only a scrambled hash is stored).
- `scripts/shared_log.py`: checks and updates "Shared opportunities.csv" in the team OneDrive folder **DYL Careers Hub** (`status`, `whoami`, `check-links`, `check-opps`, `check`, `record`, `record-whatsapp`, `unrecord`). Finds the folder automatically on each PC; set `DYL_TEAM_FOLDER` to override. The job-opportunity-message (WhatsApp) skill uses the same script.
- `references/onedrive_setup.md`: the simple steps for a teammate to connect the shared OneDrive folder.
- `references/faculties.md`: faculty mapping and strictness rules.
- `references/student_degrees.md`: the degrees our students study, grouped by faculty; the "Preferred Course/Degree" column uses these names.
- `examples/2026-11-12.json`: a complete data file from the first run.
