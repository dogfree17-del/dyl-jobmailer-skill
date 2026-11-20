"""Edit password for the jobmailer skill.

Claude must check the password before changing any file in this skill. Only a salted
scrypt hash is stored (assets/edit_lock.json), never the password itself.

  python edit_lock.py set      # owner: choose a password (typed hidden, asked twice)
  python edit_lock.py check    # Claude: reads the password from stdin, prints OK or WRONG

This is a guard for Claude, not real security: publishing changes to GitHub still needs
collaborator access on the repository.
"""
import getpass, hashlib, hmac, json, os, secrets, sys

LOCK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "edit_lock.json")
N, R, P = 2 ** 14, 8, 1


def digest(pw, salt):
    return hashlib.scrypt(pw.encode("utf-8"), salt=bytes.fromhex(salt), n=N, r=R, p=P, dklen=32).hex()


def cmd_set():
    pw = getpass.getpass("New edit password: ")
    if len(pw) < 8:
        sys.exit("Use at least 8 characters.")
    if getpass.getpass("Type it again: ") != pw:
        sys.exit("The two passwords are different. Nothing was changed.")
    salt = secrets.token_hex(16)
    json.dump({"scrypt": {"n": N, "r": R, "p": P}, "salt": salt, "hash": digest(pw, salt)},
              open(LOCK, "w"), indent=1)
    print("Edit password set. Tell Claude it is done.")


def cmd_check():
    if not os.path.exists(LOCK):
        sys.exit("NO PASSWORD SET")
    lock = json.load(open(LOCK))
    pw = sys.stdin.readline().rstrip("\r\n")
    ok = hmac.compare_digest(digest(pw, lock["salt"]), lock["hash"])
    print("OK" if ok else "WRONG")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    {"set": cmd_set, "check": cmd_check}.get(sys.argv[1] if len(sys.argv) > 1 else "", lambda: sys.exit(__doc__))()
