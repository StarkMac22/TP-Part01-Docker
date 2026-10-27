FROM python:3.13-slim-bookworm

ENV PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    ANSIBLE_HOST_KEY_CHECKING=True \
    ANSIBLE_SSH_ARGS="-o UserKnownHostsFile=/run/secrets/known_hosts -o StrictHostKeyChecking=yes"

RUN apt-get update \
    && apt-get install -y --no-install-recommends openssh-client ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt requirements.yml /opt/controller/
RUN pip install -r /opt/controller/requirements.txt \
    && ansible-galaxy collection install -r /opt/controller/requirements.yml -p /usr/share/ansible/collections

WORKDIR /work
ENTRYPOINT ["ansible-playbook"]
