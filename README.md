# jobmailer – Dell Young Leaders weekly career mailer skill

A Claude skill that turns job links into the weekly "Explore These Career Opportunities"
emails, one per faculty, plus an Education document with Edupstairs teaching posts.
It checks [dyl-shared-opportunities](https://github.com/dogfree17-del/dyl-shared-opportunities)
so an opportunity is never shared twice.

**New here? Read the [user manual](MANUAL.md)** for setup and weekly use.

## Install (once per computer)

Clone this repository into your Claude skills folder:

```bash
git clone https://github.com/dogfree17-del/dyl-jobmailer-skill.git ~/.claude/skills/jobmailer
```

You also need Python 3 with `python-docx` (`pip install python-docx`), and the GitHub CLI (`gh`)
signed in if you want the shared log to be updated after each mailer.

## Use

Type `/jobmailer` in Claude Code followed by the job links.

## Staying up to date

The skill pulls the latest version from this repository at the start of every run, so
everyone always uses the same rules, template and scripts. When you ask Claude to change
the skill, it commits and pushes the change here. To push changes you need to be added as a
collaborator on this repository.
