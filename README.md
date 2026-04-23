# B12 Application Submission

Automated, cryptographically signed job application submission powered by GitHub Actions.

---

## Overview

This repository fulfills the B12 application task: **build a CI/CD pipeline that submits a signed JSON payload to `https://b12.io/apply/submission`** on every push to `main` (or via manual trigger).

The solution is intentionally **zero-dependency** — it uses only Python's standard library, keeping the pipeline fast, auditable, and free of supply-chain risk.

## Architecture

```
push to main ──▶ GitHub Actions ──▶ submit.py ──▶ B12 API
                                       │
                          ┌─────────────┼─────────────┐
                          ▼             ▼             ▼
                    Build Payload   Canonicalize    Sign & POST
                    (env vars →     (sorted keys,   (HMAC-SHA256,
                     JSON dict)      compact JSON)   X-Signature-256)
```

### Pipeline Flow

| Step | What happens |
|------|-------------|
| **1. Trigger** | A push to `main` or a manual `workflow_dispatch` starts the workflow. |
| **2. Environment** | GitHub Actions provisions `ubuntu-latest` with Python 3.12. |
| **3. Build payload** | `submit.py` reads secrets from environment variables and generates an ISO 8601 UTC timestamp. |
| **4. Canonicalize** | The payload is serialized to compact JSON with alphabetically sorted keys — this guarantees a deterministic byte sequence for signing. |
| **5. Sign** | An HMAC-SHA256 signature is computed over the canonical body using the shared `SIGNING_SECRET`. |
| **6. Submit** | The payload is POSTed with `Content-Type: application/json` and the `X-Signature-256` header. The script prints the receipt on success or exits with a non-zero code on failure. |

## Project Structure

```
.
├── .github/
│   └── workflows/
│       └── submit.yml      # GitHub Actions workflow definition
├── submit.py               # Application submission script
└── README.md
```

| File | Purpose |
|------|---------|
| [`submit.py`](submit.py) | Core script — payload construction, HMAC signing, and HTTP submission. |
| [`submit.yml`](.github/workflows/submit.yml) | CI/CD workflow — triggers, environment setup, and secret injection. |

## Setup & Configuration

### 1. Fork / clone this repository

### 2. Add the required repository secrets

Navigate to **Settings → Secrets and variables → Actions** and add:

| Secret | Description |
|--------|-------------|
| `SIGNING_SECRET` | Shared HMAC key provided in the application instructions |
| `APPLICANT_NAME` | Your full name |
| `APPLICANT_EMAIL` | Your email address |
| `RESUME_LINK` | Public URL to your resume/CV |

> **Note:** `REPOSITORY_LINK` and `ACTION_RUN_LINK` are derived automatically from GitHub context variables — no manual setup needed.

### 3. Push to `main` (or trigger manually)

The workflow runs automatically on push. You can also trigger it manually from the **Actions** tab using `workflow_dispatch`.

## Design Decisions

| Decision | Rationale |
|----------|-----------|
| **Zero external dependencies** | `urllib.request`, `hmac`, `hashlib`, and `json` are all stdlib. This eliminates `pip install` steps, reduces attack surface, and makes the pipeline faster. |
| **Canonical JSON serialization** | `json.dumps(sort_keys=True, separators=(",", ":"))` produces a deterministic byte-for-byte representation, which is essential for HMAC verification on the server side. |
| **Fail-fast on missing config** | The script validates all required environment variables upfront and exits with a clear error message before attempting any network call. |
| **Structured error handling** | `HTTPError` and `URLError` are caught separately with descriptive output, making CI logs easy to debug. |
| **Secrets via environment** | Sensitive values never appear in code or logs — they're injected by GitHub Actions from encrypted repository secrets. |

## Running Locally (for testing)

```bash
export SIGNING_SECRET="your-secret"
export APPLICANT_NAME="Your Name"
export APPLICANT_EMAIL="you@example.com"
export RESUME_LINK="https://example.com/resume.pdf"
export REPOSITORY_LINK="https://github.com/your-user/your-repo"
export ACTION_RUN_LINK="https://github.com/your-user/your-repo/actions/runs/0"

python submit.py
```

No virtual environment or `pip install` required — Python 3.10+ is all you need.

## Security Considerations

- **HMAC-SHA256** ensures the payload has not been tampered with in transit and proves the sender holds the signing secret.
- **Repository secrets** are encrypted at rest by GitHub and masked in workflow logs.
- **No third-party actions** beyond GitHub's official `actions/checkout` and `actions/setup-python` — minimizing supply-chain exposure.
