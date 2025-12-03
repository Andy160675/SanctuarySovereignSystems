# Collaborator Access Instructions

**Repo:** `PrecisePointway/sovereign-system` (PRIVATE)
**Commit:** `f991e27`

---

## Step 1: Create GitHub Account (if needed)

Go to https://github.com/join and sign up using your email:
- `johnrustywell@aol.com`
- `jackhardaker19@gmail.com`

**Write down your GitHub username** - you'll need to share it with Andy.

---

## Step 2: Accept Invitation

Once Andy adds you, you'll receive an email:
> "You've been invited to collaborate on PrecisePointway/sovereign-system"

Click **"View invitation"** and accept.

---

## Step 3: Clone the Repository (Read-Only)

```powershell
# Install Git if needed
winget install Git.Git

# Clone (requires GitHub login)
git clone https://github.com/PrecisePointway/sovereign-system.git
cd sovereign-system

# Verify you have the latest
git log -1 --oneline
# Should show: f991e27 [Release] Open-source preparation...
```

---

## Step 4: Stay Updated

```powershell
cd sovereign-system
git pull origin master
```

---

## What You Can Do (Read-Only)

| Action | Allowed |
|--------|---------|
| View all code | Yes |
| View all docs | Yes |
| Clone repo | Yes |
| Pull updates | Yes |
| Create issues | Yes |
| Push changes | **No** |
| Merge PRs | **No** |

---

## Key Files to Review

| File | Purpose |
|------|---------|
| `README.md` | Project overview |
| `docs/AUTOMATION_CANON.md` | CI-as-constitution |
| `docs/ST_MICHAEL_AUTOMATION.md` | Adjudication layer |
| `CONTRIBUTING.md` | How changes are made |
| `LICENSE` | Apache 2.0 |

---

## Questions?

Contact Andy or open a GitHub issue.

---

*Last updated: 2025-12-03*
*Commit: f991e27*
