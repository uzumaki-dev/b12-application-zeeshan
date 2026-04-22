import hashlib
import hmac
import json
import os
import sys
import urllib.request
from datetime import datetime, timezone


SUBMISSION_URL = "https://b12.io/apply/submission"


def build_payload() -> dict:
    """Build the JSON payload from environment variables."""
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.") + \
        f"{datetime.now(timezone.utc).microsecond // 1000:03d}Z"

    repository_link = os.environ.get("REPOSITORY_LINK", "")
    action_run_link = os.environ.get("ACTION_RUN_LINK", "")
    name = os.environ.get("APPLICANT_NAME", "")
    email = os.environ.get("APPLICANT_EMAIL", "")
    resume_link = os.environ.get("RESUME_LINK", "")

    missing = []
    for var, val in [
        ("APPLICANT_NAME", name),
        ("APPLICANT_EMAIL", email),
        ("RESUME_LINK", resume_link),
        ("REPOSITORY_LINK", repository_link),
        ("ACTION_RUN_LINK", action_run_link),
    ]:
        if not val:
            missing.append(var)

    if missing:
        print(f"ERROR: Missing required environment variables: {', '.join(missing)}")
        sys.exit(1)

    return {
        "action_run_link": action_run_link,
        "email": email,
        "name": name,
        "repository_link": repository_link,
        "resume_link": resume_link,
        "timestamp": timestamp,
    }


def canonicalize(payload: dict) -> bytes:
    """Serialize payload to compact, sorted, UTF-8-encoded JSON."""
    return json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")


def sign(body: bytes, secret: str) -> str:
    """Compute HMAC-SHA256 hex digest of the body using the given secret."""
    mac = hmac.new(secret.encode("utf-8"), body, hashlib.sha256)
    return f"sha256={mac.hexdigest()}"


def submit(body: bytes, signature: str) -> None:
    """POST the signed payload to the B12 submission endpoint."""
    req = urllib.request.Request(
        SUBMISSION_URL,
        data=body,
        headers={
            "Content-Type": "application/json",
            "X-Signature-256": signature,
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req) as resp:
            response_body = resp.read().decode("utf-8")
            print(f"Status: {resp.status}")
            print(f"Response: {response_body}")

            data = json.loads(response_body)
            if data.get("success"):
                print(f"\nSubmission successful!")
                print(f"Receipt: {data.get('receipt')}")
            else:
                print("\nSubmission was not successful.")
                sys.exit(1)

    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8")
        print(f"HTTP Error {e.code}: {e.reason}")
        print(f"Response: {error_body}")
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"Connection error: {e.reason}")
        sys.exit(1)


def main():
    signing_secret = os.environ.get("SIGNING_SECRET", "")
    if not signing_secret:
        print("ERROR: Missing SIGNING_SECRET environment variable.")
        sys.exit(1)

    payload = build_payload()
    body = canonicalize(payload)

    print("Payload:")
    print(json.dumps(payload, indent=2))
    print(f"\nCanonical body: {body.decode('utf-8')}")

    signature = sign(body, signing_secret)
    print(f"Signature: {signature}")
    print()

    submit(body, signature)


if __name__ == "__main__":
    main()
