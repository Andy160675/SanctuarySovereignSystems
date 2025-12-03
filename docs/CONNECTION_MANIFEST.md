# SOVEREIGN SYSTEM - CONNECTION MANIFEST

## API Keys & Tokens (DO NOT COMMIT TO GIT)

Store these in your password manager or GitHub Secrets. This file documents WHERE to set them, not the values.

---

## 1. GITHUB

### Repository Access

```
Repo: https://github.com/PrecisePointway/sovereign-system
Org:  https://github.com/Blade2AI (if applicable)
```

### GitHub CLI Authentication

```bash
# On any new machine:
gh auth login
# Choose: GitHub.com → HTTPS → Login with browser
```

### GitHub Actions Secrets (set in repo settings)

| Secret Name | Purpose | Where to Get |
|-------------|---------|--------------|
| `GITHUB_TOKEN` | Auto-provided by Actions | Automatic |
| `DOCKERHUB_USERNAME` | Container registry | hub.docker.com |
| `DOCKERHUB_TOKEN` | Container registry | hub.docker.com → Security |

### Webhooks (Repo → Settings → Webhooks)

| Webhook | URL Pattern | Events |
|---------|-------------|--------|
| CI Status | Discord/Slack webhook URL | Push, PR, Workflow |
| Deploy | Your deploy endpoint | Release published |

---

## 2. SSH ACCESS

### Generate Key (if needed)

```bash
ssh-keygen -t ed25519 -C "andyj@sovereign-system"
# Save to: ~/.ssh/id_ed25519_sovereign
```

### SSH Config (~/.ssh/config)

```
# Core PC (this machine)
Host pc-core-1
    HostName 100.x.x.x  # Tailscale IP - get from: tailscale ip -4
    User andyj
    IdentityFile ~/.ssh/id_ed25519_sovereign

# NAS
Host nas-01
    HostName 100.x.x.x  # Tailscale IP
    User admin
    IdentityFile ~/.ssh/id_ed25519_sovereign

# Other PCs
Host pc-core-2
    HostName 100.x.x.x
    User andyj
    IdentityFile ~/.ssh/id_ed25519_sovereign
```

### Add Public Key to GitHub

```bash
cat ~/.ssh/id_ed25519_sovereign.pub
# Copy output to: GitHub → Settings → SSH Keys → New SSH Key
```

---

## 3. TAILSCALE

### Install & Login

```bash
# Windows
winget install Tailscale.Tailscale

# Then:
tailscale up
# Login via browser
```

### Get Machine IPs

```bash
tailscale status
# Lists all machines on your tailnet with their IPs
```

### MagicDNS Hostnames

If MagicDNS enabled, use hostnames like:
- `pc-core-1.tailnet-name.ts.net`
- `nas-01.tailnet-name.ts.net`

---

## 4. CONTAINER REGISTRY

### Docker Hub

```bash
docker login
# Username: your-dockerhub-username
# Password: Access token from hub.docker.com → Security
```

### GitHub Container Registry (GHCR)

```bash
echo $GITHUB_TOKEN | docker login ghcr.io -u USERNAME --password-stdin
```

---

## 5. CLOUD PROVIDERS (if applicable)

### Azure (optional)

```bash
az login
az account set --subscription "your-sub-id"
```

### AWS (optional)

```bash
aws configure
# Access Key ID: from IAM
# Secret Access Key: from IAM
# Region: eu-west-2 (or your region)
```

---

## 6. ENVIRONMENT VARIABLES

Create `.env` file (NEVER commit this):

```bash
# GitHub
GITHUB_TOKEN=ghp_xxxxxxxxxxxx

# Tailscale (if using API)
TAILSCALE_API_KEY=tskey-api-xxxx

# Blockchain (if applicable)
OPTIMISM_RPC_URL=https://mainnet.optimism.io
PRIVATE_KEY=0x... (NEVER commit)

# Monitoring
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
```

### GitHub Actions Secrets Setup

```bash
# Add secrets via CLI:
gh secret set DISCORD_WEBHOOK_URL --body "https://discord.com/api/webhooks/..."
gh secret set TAILSCALE_AUTHKEY --body "tskey-auth-..."
```

---

## 7. AUTO-LINK SETUP SCRIPT

Run this on any new machine after cloning the repo:

```bash
#!/bin/bash
# setup_connections.sh

# 1. GitHub CLI
if ! command -v gh &> /dev/null; then
    echo "Install GitHub CLI first: winget install GitHub.cli"
    exit 1
fi
gh auth login

# 2. SSH key
if [ ! -f ~/.ssh/id_ed25519_sovereign ]; then
    ssh-keygen -t ed25519 -C "andyj@sovereign" -f ~/.ssh/id_ed25519_sovereign -N ""
    echo "Add this key to GitHub:"
    cat ~/.ssh/id_ed25519_sovereign.pub
fi

# 3. Tailscale
if ! command -v tailscale &> /dev/null; then
    echo "Install Tailscale: winget install Tailscale.Tailscale"
    exit 1
fi
tailscale status || tailscale up

# 4. Verify GitHub connection
gh auth status
gh repo view PrecisePointway/sovereign-system --json name

echo "Setup complete. Test with: ssh pc-core-1 'echo connected'"
```

---

## 8. WEBHOOK ENDPOINTS (for CI notifications)

### Discord (optional)

1. Server Settings → Integrations → Webhooks → New Webhook
2. Copy URL
3. Add to GitHub: Repo → Settings → Webhooks → Add webhook
   - Payload URL: Discord webhook URL + `/github`
   - Content type: `application/json`
   - Events: Push, PR, Workflow runs

### Slack (optional)

1. Create Slack App → Incoming Webhooks
2. Add to channel
3. Same process as Discord

---

## 9. VERIFICATION CHECKLIST

After setting up a new node, verify:

```bash
# GitHub
gh auth status                          # Should show logged in
gh repo view PrecisePointway/sovereign-system  # Should show repo info

# SSH
ssh -T git@github.com                   # Should greet you

# Tailscale
tailscale status                        # Should list your machines
ping pc-core-1                          # Should respond (if online)

# Git remote
git remote -v                           # Should show GitHub URLs
```

---

## 10. SECURITY NOTES

- **NEVER** commit `.env`, `secrets.*`, `*.pem`, `id_rsa*` to git
- **NEVER** share this file with actual credentials filled in
- **ALWAYS** use GitHub Secrets for CI/CD sensitive values
- **ROTATE** tokens if you suspect compromise

---

*This manifest documents connection patterns, not credentials.*
*Credentials belong in password managers and GitHub Secrets.*
