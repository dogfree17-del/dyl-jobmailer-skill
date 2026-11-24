# Connect the team's shared OneDrive folder (once per computer)

The careers team keeps one list of everything already shared (weekly mailers and WhatsApp messages) in a
shared OneDrive folder called **DYL Careers Hub**. Each skill reads it before sharing, so nobody sends the
same opportunity twice. Your computer needs a synced copy of that folder. It takes about 5 minutes.

**For Claude, when guiding a user:** give ONE step at a time in plain words, wait for them to say it is done,
then give the next. Never paste all the steps at once. After step 4, run
`python "<skill-folder>/scripts/shared_log.py" status` yourself and tell them the result.

## Before you start (the folder owner, once)

Anokunda opens the **DYL Careers Hub** folder in OneDrive (work account) -> **Share** -> adds each teammate's
work email -> permission **Can edit** -> **Send**. Each teammate then gets an email.

## Steps for each teammate

1. **Check OneDrive is running with your work account.**
   Look at the bottom-right of the screen (click the little arrow `^` if you can't see it). You should see a
   blue cloud icon named **OneDrive - Michael & Susan Dell Foundation**. If there is no cloud: press the
   Windows key, type **OneDrive**, open it, and sign in with your work email.

2. **Open the invitation and add the folder to your OneDrive.**
   Open the email "... shared the folder DYL Careers Hub with you" and click **Open**. In the page that opens,
   click **Add shortcut to My files** at the top (if you can't see it, click the three dots **...** first).

3. **Wait for it to appear on your computer.**
   Open File Explorer (yellow folder icon) -> **OneDrive - Michael & Susan Dell Foundation**. Within a few minutes
   a folder **DYL Careers Hub** appears. Wait until it shows a green tick. If it doesn't appear after 5 minutes:
   right-click the OneDrive cloud -> **Pause syncing** -> **Resume syncing**.

4. **Keep it on this computer.**
   Right-click the **DYL Careers Hub** folder -> **Always keep on this device**. This makes sure the list is
   really on your laptop, not just online.

5. **Check it works.**
   Tell Claude "check the shared log". It should say **CONNECTED**.

## If something goes wrong

| What you see | What to do |
|---|---|
| No "Add shortcut to My files" button | Use the **Sync** button on the same page instead, or ask Anokunda to confirm you were given **Can edit**. |
| Claude says NOT CONNECTED after step 3 | The folder has a different name or location on your PC. Tell Claude where it is, or set it once: `setx DYL_TEAM_FOLDER "C:\full\path\to\DYL Careers Hub"`, then restart the Claude app. |
| "The log is open in another program" | Close **Shared opportunities.csv** if it is open in Excel, then try again. |
| Two people shared at the same moment and a file called "Shared opportunities-<name>.csv" appeared | Tell Anokunda. It means two edits collided and the two lists need merging. |
