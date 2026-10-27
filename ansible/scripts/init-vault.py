"""Create an encrypted Vault directly in memory, with hidden interactive input."""

import getpass
import os
from pathlib import Path
import sys

import yaml
from ansible.parsing.vault import VaultLib, VaultSecret


def main():
    if not sys.stdin.isatty():
        raise SystemExit("An interactive terminal is required; run docker with -it.")
    target = Path(__file__).resolve().parents[1] / "vars" / "vault.yml"
    if target.exists():
        raise SystemExit("Vault already exists; use ansible-vault edit to update it.")

    print("Enter the CURRENT PostgreSQL values to preserve the existing database.")
    values = {
        name: getpass.getpass(prompt)
        for name, prompt in (
            ("vault_postgres_db", "Current database name (hidden): "),
            ("vault_postgres_user", "Current PostgreSQL user (hidden): "),
            ("vault_postgres_password", "Current PostgreSQL password (hidden): "),
        )
    }
    if not all(values.values()):
        raise SystemExit("All PostgreSQL values are required; nothing was written.")
    password = getpass.getpass("Choose a new Vault password: ")
    confirmation = getpass.getpass("Confirm Vault password: ")
    if not password or password != confirmation:
        raise SystemExit("Vault passwords empty or different; nothing was written.")

    secret = VaultSecret(password.encode())
    encrypted = VaultLib().encrypt(yaml.safe_dump(values).encode(), secret=secret)
    target.parent.mkdir(parents=True, exist_ok=True)
    # Exclusive creation, restrictive permissions; only ciphertext reaches disk.
    fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "wb") as output:
        output.write(encrypted)
    print("Encrypted Vault created. Store its password in your password manager")
    print("and in the GitHub secret ANSIBLE_VAULT_PASSWORD.")


if __name__ == "__main__":
    main()
