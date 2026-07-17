# TestPilot AI — GitHub App & Webhook Integration Guide

To connect TestPilot AI with your live GitHub repositories, you need to expose your local instance to the internet (or deploy it) and configure your registered GitHub App: **`TestPilot-AI-Shikhar`**.

---

## Step 1: Set Up a Local Tunnel (For Local Development)

Since GitHub needs to send webhook payloads to your local environment, you must create a public URL pointing to your Nginx proxy (which runs on port `80`).

We recommend using **`ngrok`**:

1. Install ngrok (via npm or download):
   ```bash
   npm install -g ngrok
   ```
2. Start a tunnel pointing to port 80:
   ```bash
   ngrok http 80
   ```
3. Copy the forwarding HTTPS URL generated (e.g., `https://a1b2-34-56-78.ngrok-free.app`).

---

## Step 2: Configure Your GitHub App Settings

Go to **GitHub Developer Settings** -> **GitHub Apps** -> **`TestPilot-AI-Shikhar`**:

1. **Homepage URL**: Set to your public HTTPS URL (e.g., `https://a1b2-34-56-78.ngrok-free.app`).
2. **Identifying and authorizing users**:
   - **Callback URL**: `https://a1b2-34-56-78.ngrok-free.app/auth/callback`
3. **Webhooks**:
   - Check **Active**.
   - **Webhook URL**: `https://a1b2-34-56-78.ngrok-free.app/api/v1/webhooks/github`
   - **Webhook secret**: Copy your configured `GITHUB_WEBHOOK_SECRET` from your `.env` file (currently: `testpilot-webhook-secret-2026-7f4a91d3`).

### Repository Permissions Required:
Ensure your GitHub App has the following permissions enabled:

| Permission | Scope | Rationale |
|---|---|---|
| **Checks** | Read & Write | Posting AI test suite results and runs |
| **Contents** | Read & Write | Cloning and scanning repository code |
| **Pull Requests** | Read & Write | Reading PR diffs and posting review comments |
| **Metadata** | Read-only | Fetching repository info (mandatory) |

### Subscribe to Events:
Under **Subscribe to events**, select:
- [x] **Pull request**

---

## Step 3: Configure Your Local `.env`

Update your local `.env` file with the correct details:

```env
# GitHub App credentials
GITHUB_APP_ID=4299403
GITHUB_APP_NAME="TestPilot-AI-Shikhar"
GITHUB_CLIENT_ID=Iv23lidkcnPgeiMZ1m7Q
GITHUB_CLIENT_SECRET=af22f7d9a004170f92357251be0d610d7a4935c7
GITHUB_WEBHOOK_SECRET=testpilot-webhook-secret-2026-7f4a91d3
GITHUB_APP_PRIVATE_KEY_PATH=/app/private-key.pem
```

*Note: Make sure to copy the downloaded private key file (e.g., `testpilot-ai-shikhar.private-key.pem`) into the `backend/` folder on your host machine and name it exactly `private-key.pem` (so it sits at `backend/private-key.pem`). The updated Docker volumes will automatically map it to `/app/private-key.pem` inside the running containers.*

---

## Step 4: Installation & Triggering Analysis

1. Go to your GitHub App page and click **Install App**.
2. Install it on a test repository of your choice.
3. Open a Pull Request on that test repository.
4. GitHub will fire a `pull_request.opened` event to your ngrok URL.
5. The `testpilot-backend` will verify the signature, create records in Postgres, and dispatch the Celery task (`run_pr_analysis`).
6. Celery workers will execute the LangGraph multi-agent flow:
   - Clone the PR code
   - Build AST dependency graph
   - Run AI regression test generation
   - Post results back to the GitHub PR comments!

---

## Troubleshooting Webhooks

- Check Celery worker logs:
  ```bash
  docker compose logs celery-worker -f
  ```
- Check GitHub Developer Settings under **Advanced** -> **Recent Deliveries** to see payload delivery status and responses.
