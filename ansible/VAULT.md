# Déploiement Docker et Ansible Vault

Le contrôleur Ansible s'exécute dans Docker, puis administre le serveur par SSH.
Le socket Docker de l'hôte n'est pas monté dans le contrôleur. Les dépendances
Docker du serveur restent installées par le rôle `docker` existant.

## Initialisation locale indispensable

Depuis la racine du dépôt :

```sh
docker build -t tp-ansible:local ./ansible/controller
docker run --rm -it --user "$(id -u):$(id -g)" \
  -e HOME=/tmp \
  --mount "type=bind,src=$PWD/ansible,dst=/work" \
  --entrypoint python tp-ansible:local /work/scripts/init-vault.py
```

Aux trois premières invites, saisir les valeurs PostgreSQL **actuellement en
service**, inchangées : nom de base, utilisateur, mot de passe. Toutes les saisies
sont masquées. Choisir ensuite un nouveau mot de passe Vault et le confirmer.
Le script chiffre directement en mémoire et crée `ansible/vars/vault.yml` avec
des permissions `0600` ; aucun fichier contenant les valeurs en clair ou le mot
de passe Vault n'est créé. Il refuse d'écraser un coffre-fort existant.

Conserver le mot de passe Vault dans un gestionnaire de mots de passe. Il sera
nécessaire de versionner **uniquement le fichier chiffré** avant d'utiliser la CI.
Ne jamais versionner de fichier contenant ce mot de passe ni déchiffrer le
coffre-fort sur place dans le dépôt. Les patterns `.gitignore` sont une protection
complémentaire, pas une validation du chiffrement.

Pour modifier ensuite le coffre-fort en saisissant son mot de passe :

```sh
ansible-vault edit --ask-vault-pass ansible/vars/vault.yml
```

Cette commande utilise Ansible et un éditeur local sécurisé. Désactiver les
sauvegardes, fichiers swap et extensions de synchronisation de l'éditeur.

## Configuration GitHub

Dans l'environnement GitHub Actions `production` (ou les secrets du dépôt si
c'est la configuration existante), ajouter `ANSIBLE_VAULT_PASSWORD` avec
exactement le mot de passe choisi à l'initialisation. Ne pas le fournir ici ni
dans une ligne de commande. Les secrets existants `SSH_PRIVATE_KEY`, `SSH_HOST`,
`DOCKERHUB_USERNAME`, `DOCKERHUB_TOKEN` et `SONAR_TOKEN` restent inchangés.

Le job de déploiement refuse un coffre-fort absent ou non chiffré. Il construit
l'image du contrôleur, écrit la clé SSH et le mot de passe dans un répertoire
temporaire privé du runner, puis les monte en lecture seule sous `/run/secrets`.
Le projet est monté en lecture seule sous `/work`. Les secrets ne sont jamais
passés en arguments de build ou copiés dans l'image. La vérification des clés
SSH reste active ; `known_hosts` est constitué par `ssh-keyscan` comme auparavant.
Cette collecte initiale doit être effectuée depuis un réseau de confiance ; elle
ne constitue pas une vérification indépendante de l'empreinte du serveur.
Le répertoire temporaire est supprimé par une étape `if: always()`.

Les quatre images applicatives restent taguées avec le SHA du commit. Les tests
Maven, SonarQube, les conditions de publication et de déploiement, ainsi que le
test de santé via `/api/actuator/health` sont conservés.

## Vérification locale sans déploiement

Après initialisation du coffre-fort :

```sh
docker run --rm -it \
  --mount "type=bind,src=$PWD/ansible,dst=/work,readonly" \
  tp-ansible:local -i inventories/setup.yml playbook.yml \
  --ask-vault-pass --syntax-check
```

Cette commande ne contacte pas le serveur. Pour une future exécution réelle,
utiliser la commande `docker run` du workflow avec quatre variables d'images et
un répertoire privé contenant `id_rsa`, `known_hosts` et `vault-password`, monté
en lecture seule sous `/run/secrets`. Le mot de passe peut aussi être saisi avec
`--ask-vault-pass` et `-it` au lieu d'utiliser le fichier `vault-password`.
Ne pas activer le traçage shell (`set -x`) ni le débogage Ansible des secrets.

## Compatibilité et limites

Les rôles, le volume `tp-postgres-data`, les ports et les routes Apache sont
conservés. Les tâches des conteneurs PostgreSQL et backend et la validation des
variables utilisent `no_log: true`. Le backend reçoit les mêmes valeurs par
variables d'environnement. Les variables d'initialisation de PostgreSQL ne
changent pas les utilisateurs d'une base déjà persistée : conserver exactement
les valeurs actuelles pour cette migration, sans supprimer le volume.

Vault protège les fichiers au repos ; les administrateurs du serveur/Docker
peuvent toujours lire les variables d'environnement des conteneurs. Des
identifiants étaient déjà suivis dans Git, notamment dans les rôles et dans
`backend/src/main/resources/application.yml`. Vault n'efface ni l'historique Git,
ni ces valeurs par défaut du backend ou celles d'anciennes images. Cette
migration ne constitue pas une rotation des identifiants ; une rotation et un
éventuel nettoyage de l'historique demandent une opération distincte coordonnée.

Sans `vars/vault.yml` chiffré et le secret GitHub correspondant, le déploiement
est volontairement bloqué. Aucun coffre-fort de production n'est fourni avec
un mot de passe inventé.

Référence : [chiffrement des fichiers avec Ansible Vault](https://docs.ansible.com/projects/ansible/latest/vault_guide/vault_encrypting_content.html).
