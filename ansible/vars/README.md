This directory must contain `vault.yml`, encrypted with Ansible Vault and loaded
by `playbook.yml`. Create it with `scripts/init-vault.py`; see `../VAULT.md`.

Required variables: `vault_postgres_db`, `vault_postgres_user`,
`vault_postgres_password`. Do not add a plaintext template with real values.
The encrypted `vault.yml` is intended to be versioned; the password is not.
