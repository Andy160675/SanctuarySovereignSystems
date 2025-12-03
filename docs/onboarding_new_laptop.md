# Onboarding a New Developer Laptop

This document describes how to onboard a new laptop into the Sovereign System development environment, using PC4 as the central bridge.

## Prerequisites

Before starting, ensure you have:

- [ ] A Tailscale account with access to the organization tailnet
- [ ] Access credentials for the PC4 SSH user (contact ops team)
- [ ] Git installed on the laptop
- [ ] Python 3.11+ installed
- [ ] Docker Desktop (optional, for local testing)

---

## 1. Join the Tailscale Network

### 1.1 Install Tailscale

**Linux:**
```bash
curl -fsSL https://tailscale.com/install.sh | sh
```

**Windows:**
Download from https://tailscale.com/download/windows

**macOS:**
```bash
brew install tailscale
```

### 1.2 Authenticate

```bash
sudo tailscale up
```

A browser window will open. Log in with your organization account.

### 1.3 Verify Connection

```bash
tailscale status
```

You should see PC4 in the list of connected machines.

---

## 2. Configure SSH Access to PC4

### 2.1 Generate SSH Key (if needed)

```bash
ssh-keygen -t ed25519 -C "dev-laptop-$(whoami)"
```

Accept the default location (`~/.ssh/id_ed25519`).

### 2.2 Send Public Key to Ops

Share your public key with the ops team:

```bash
cat ~/.ssh/id_ed25519.pub
```

The ops team will run `setup_dev_user.sh` on PC4 to create your account.

### 2.3 Configure SSH Client

Add to `~/.ssh/config`:

```ssh-config
Host pc4
    HostName pc4.your-tailnet.ts.net
    User dev_laptop_yourname
    IdentityFile ~/.ssh/id_ed25519
    StrictHostKeyChecking accept-new

# For ops access (if authorized)
Host pc4-ops
    HostName pc4.your-tailnet.ts.net
    User sovereign
    IdentityFile ~/.ssh/id_ed25519_ops
```

### 2.4 Test Connection

```bash
ssh pc4
```

You should see the Sovereign System developer welcome message.

---

## 3. Clone the Repository

### 3.1 Create Development Directory

```bash
mkdir -p ~/src
cd ~/src
```

### 3.2 Clone Repository

```bash
git clone git@github.com:YourOrg/sovereign-system.git
cd sovereign-system
```

### 3.3 Set Up Python Environment

```bash
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# or: .venv\Scripts\activate  # Windows

pip install -r requirements.txt
```

### 3.4 Verify Setup

```bash
pytest tests/ -v --ignore=tests/red_team/
```

All tests should pass.

---

## 4. Daily Development Workflow

### 4.1 Pull Latest Changes

```bash
cd ~/src/sovereign-system
git pull origin main
```

### 4.2 Run Tests Locally

```bash
# Quick test
pytest tests/ -q

# Full test with coverage
pytest tests/ -v --cov=.

# Red-team tests (if you have local services running)
pytest tests/red_team/ -v
```

### 4.3 View PC4 Status (via SSH)

```bash
# Check service status
ssh pc4 'docker ps --filter name=sovereign'

# View recent logs
ssh pc4 'docker logs --tail 50 sovereign-mesh_api-gateway'

# Check health endpoint
ssh pc4 'curl -s http://localhost:8000/health'
```

### 4.4 Push Changes

```bash
git add .
git commit -m "Description of changes"
git push origin your-branch
```

Create a PR on GitHub. CI will run automatically.

---

## 5. Access Levels

### Developer Access (Your Default)

You can:
- SSH into PC4
- Read logs and status
- Pull from git repositories
- View CI results on GitHub

You cannot:
- Run `deploy.sh`
- Execute `docker stack` commands
- Modify system configuration
- Access production secrets

### Ops Access (Requires Approval)

If you need ops access:
1. Request approval from the governance board
2. Complete security training
3. Receive a separate SSH key for the `sovereign` user

---

## 6. Troubleshooting

### Can't Connect via Tailscale

1. Check Tailscale is running: `tailscale status`
2. Re-authenticate: `sudo tailscale up`
3. Check PC4 is online in Tailscale admin console

### SSH Connection Refused

1. Verify your username with ops team
2. Check your public key was added: `ssh pc4 'cat ~/.ssh/authorized_keys'`
3. Try with verbose mode: `ssh -v pc4`

### Tests Failing Locally

1. Ensure you're in the virtual environment: `which python`
2. Update dependencies: `pip install -r requirements.txt`
3. Check for uncommitted changes: `git status`

### Can't Push to Repository

1. Check you have write access to the repo
2. Ensure your Git email is verified: `git config user.email`
3. For protected branches, create a PR instead of direct push

---

## 7. Quick Reference

| Task | Command |
|------|---------|
| Check PC4 status | `ssh pc4 'docker ps'` |
| View logs | `ssh pc4 'docker logs -f sovereign-mesh_api-gateway'` |
| Health check | `ssh pc4 'curl localhost:8000/health'` |
| Run local tests | `pytest tests/ -v` |
| Update code | `git pull origin main` |

---

## 8. Security Reminders

- Never share your SSH private key
- Don't commit secrets or credentials
- Report any security concerns to the ops team
- Log out of SSH sessions when done: `exit`

---

## Contacts

| Role | Contact |
|------|---------|
| Ops Team | ops@yourcompany.com |
| Security | security@yourcompany.com |
| Governance Board | governance@yourcompany.com |

---

*Last Updated: 2024-11-26*
