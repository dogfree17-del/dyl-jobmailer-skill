# Job Mailer – user manual

The Job Mailer skill turns job links into the weekly Dell Young Leaders "Explore These Career
Opportunities" emails: one email per faculty, plus an Education document with Foundation and
Intermediate Phase teaching posts. It never shares an opportunity twice, because it checks the
[shared opportunities log](https://github.com/dogfree17-del/dyl-shared-opportunities) on every run.

---

## Part 1: Set up (once per computer)

### 1. Get Claude
- You need a paid Claude plan (Pro, Max, Team or Enterprise).
- Install the **Claude desktop app** and sign in. You will use its **Code** tab.

### 2. Install the tools
Open **PowerShell** and run these one at a time:

```powershell
winget install Git.Git
winget install Python.Python.3.12
winget install GitHub.cli
```

Close and reopen PowerShell, then run:

```powershell
pip install python-docx
gh auth login
```

For `gh auth login`, choose **GitHub.com → HTTPS → Login with a web browser** and sign in.
You need a free GitHub account.

### 3. Get access
Send your GitHub username to the skill owner. They will invite you as a collaborator on:
- `dyl-jobmailer-skill` (the skill)
- `dyl-shared-opportunities` (the log)

Accept both invitations from the email GitHub sends you. Without access you can still use the skill, but your mailers won't be added to the log.

### 4. Install the skill
In PowerShell:

```powershell
git clone https://github.com/dogfree17-del/dyl-jobmailer-skill.git "$HOME\.claude\skills\jobmailer"
```

### 5. Let Claude read job adverts
- Install the **Claude in Chrome** extension in Google Chrome and connect it to the Claude app.
- Sign in to **LinkedIn** in Chrome. Claude reads LinkedIn adverts through your browser.

### 6. Test it
In the Claude app's **Code** tab, type:

```
/jobmailer https://www.linkedin.com/jobs/view/<any open job>/
```

You should get two Word files. If it doesn't work, see **Troubleshooting** below.

---

## Part 2: Make the weekly mailer

### 1. Collect links
During the week, save links to individual job adverts (LinkedIn, company careers pages, Indeed,
Careers24) and screenshots of flyers. Don't use job boards (Jooble, Agrijob, SAYouth, general list pages).

### 2. Run the skill
Paste this into the Claude app's **Code** tab, with your links:

```
/jobmailer

Mailer date: YYYY-MM-DD

Links:
[paste job links, one per line, and attach any flyer screenshots]
```

Claude will:
1. Get the latest version of the skill
2. Skip links already shared in an earlier mailer
3. Read each advert and leave out closed jobs
4. Sort the jobs into faculties
5. Add open Edupstairs teaching posts
6. Build the Word files and add this mailer to the log

### 3. Check Claude's reply
The reply lists:
- how many jobs went into each faculty,
- what was left out and why (already shared, closed, needs experience),
- anything you should double-check.

### 4. Make changes if needed
Just ask in the same chat, for example:
- "remove the Nedbank job"
- "also add https://www.linkedin.com/jobs/view/…/"
- "share the Hatch job again even though it was shared before"

Claude rebuilds the documents and updates the log.

### 5. Find the documents
Open the **Opportunities** folder in your Documents (`OneDrive\Documents\Opportunities`, or
`Documents\Opportunities` if you don't use OneDrive):
- `Career_Opportunities_YYYY-MM-DD.docx`: one email per faculty
- `Career_Opportunities_Education_YYYY-MM-DD.docx`: teaching posts

If a file was open in Word while Claude rebuilt it, the new version is saved as `-2`, `-3`.

### 6. Send the emails in DYL Connect
For each faculty:
1. Select the students for that faculty.
2. In Word, copy everything from "Dear Dell Young Leader," to "The Dell Young Leaders team".
3. Clear the DYL Connect email box, paste, then add the subject: **Explore These Career Opportunities**.
4. Send.

---

## Changing the skill

Ask Claude in plain words, for example "add this line to every email" or "keep the table shorter".
Claude edits the skill and publishes the change on GitHub, so everyone gets it on their next run.

---

## Troubleshooting

| Problem | What to do |
|---|---|
| DYL Connect says "Action failed" | Send to **one student** first. If that works, send to the rest in smaller groups. If one student also fails, contact whoever looks after DYL Connect. |
| Claude can't open LinkedIn | Check that Chrome is open, the Claude in Chrome extension is connected, and you are signed in to LinkedIn. |
| "PUSH FAILED" or "log not updated" | You don't have collaborator access yet (Part 1, step 3), or `gh auth login` was not done. |
| "Could not read the shared log" | Check your internet connection and try again. |
| A job you wanted was left out as "already shared" | Ask Claude to share it again on purpose. |
| `/jobmailer` is not recognised | The skill isn't installed in the right folder. Repeat Part 1, step 4, then restart the Claude app. |
