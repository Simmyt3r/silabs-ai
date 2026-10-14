from __future__ import annotations

import argparse
import json
import secrets

from silabs_ai.auth import hash_api_key


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate a Silabs AI product API key and its server-side SHA-256 digest."
    )
    parser.add_argument("client_id", help="Product/client name, e.g. unixpress")
    args = parser.parse_args()

    client_id = args.client_id.strip()
    if not client_id:
        raise SystemExit("client_id cannot be blank")

    raw_key = "silabs_" + secrets.token_urlsafe(32)
    digest = hash_api_key(raw_key)

    print("CLIENT ID:")
    print(client_id)
    print("\nRAW API KEY (show once; store only in the client secret manager):")
    print(raw_key)
    print("\nSERVER HASH:")
    print(digest)
    print("\nSILABS_API_KEY_HASHES JSON:")
    print(json.dumps({client_id: digest}))


if __name__ == "__main__":
    main()
