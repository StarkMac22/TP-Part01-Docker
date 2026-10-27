# Réponses aux questions — TP Discover Docker

## 1-1. Pourquoi est-il préférable de passer les variables d’environnement avec `-e` plutôt que de les mettre directement dans le Dockerfile ?

Il est préférable de passer les variables d’environnement au démarrage du conteneur avec `-e`,  parce que ça permet de séparer la configuration de l’image Docker donc mes identifiants ne sont pas directement inscrits dans le  Dockerfile qui peut être partager et la même images peut être utiliser avec plusieurs configurations 

Exemple :

```bash
docker run -d \
  --name tp-database \
  --network app-network \
  -e POSTGRES_DB=db \
  -e POSTGRES_USER=usr \
  -e POSTGRES_PASSWORD=pwd \
  tp-database:1.0
```

## 1-2. Pourquoi faut-il associer un volume au conteneur PostgreSQL ?

Un volume permet de conserver durablement les données de PostgreSQL, même si le conteneur est arrêté, supprimé ou recréé.

Sans volume, les données stockées dans le système de fichiers interne du conteneur risquent d’être perdues lors de sa suppression.

Dans ce TP, le volume est associé au répertoire de données PostgreSQL :

```yaml
volumes:
  - bafe619100dce490558644aedc03c48a90c58b84facbfe1bc28dd6b645714543:/var/lib/postgresql/data
```

Le volume permet donc de séparer les données de la durée de vie du conteneur et de retrouver les données après un redémarrage ou une recréation du service.

## 1-3. Documenter les éléments essentiels du conteneur de base de données : commandes et Dockerfile

### Dockerfile

Le Dockerfile de la base de données utilise l’image officielle PostgreSQL 17.2 Alpine :

```dockerfile
FROM postgres:17.2-alpine

ENV POSTGRES_DB=db \
    POSTGRES_USER=usr \
    POSTGRES_PASSWORD=pwd

COPY ./*.sql /docker-entrypoint-initdb.d/
```

Les scripts SQL présents dans le dossier sont copiés dans `/docker-entrypoint-initdb.d/`. PostgreSQL les exécute lors de l’initialisation d’un répertoire de données vide.


### Commandes principales

Créer le réseau Docker :

```bash
docker network create app-network
```

Construire l’image :

```bash
docker build -t tp-database:1.0 ./database
```

Démarrer le conteneur avec les variables d’environnement et un volume persistant :

```bash
docker run -d \
  --name tp-database \
  --network app-network \
  -e POSTGRES_DB=db \
  -e POSTGRES_USER=usr \
  -e POSTGRES_PASSWORD=pwd \
  -v postgres-data:/var/lib/postgresql/data \
  tp-database:1.0
```

Vérifier que le conteneur fonctionne :

```bash
docker ps
```

Consulter mes logs :

```bash
docker logs tp-database
```

**Remarque :** la commande ci-dessus illustre la création d’un volume nommé `postgres-data`. Dans ce TP, le volume externe déjà utilisé est `bafe619100dce490558644aedc03c48a90c58b84facbfe1bc28dd6b645714543`. Il faut conserver ce dernier pour préserver les données existantes.

## 1-4. Pourquoi utiliser un multistage build ? Expliquer les étapes du Dockerfile

Un multistage build permet d’utiliser plusieurs images de base dans un même Dockerfile afin de séparer la compilation de l’exécution.

Pour une application Java, la première étape utilise un JDK et Maven pour compiler le code et produire un fichier JAR. La seconde utilise uniquement un JRE pour exécuter ce fichier.

Les principaux avantages sont :

- une image finale plus légère ;
- moins d’outils de développement dans l’image d’exécution ;
- une meilleure séparation entre compilation et exécution ;
- une surface d’attaque potentiellement réduite.

Exemple de Dockerfile utilisé pour le backend :

```dockerfile
# Étape 1 : compilation de l'application
FROM eclipse-temurin:21-jdk-alpine AS myapp-build

ENV MYAPP_HOME=/opt/myapp
WORKDIR $MYAPP_HOME

RUN apk add --no-cache maven

COPY pom.xml .
COPY src ./src

RUN mvn package -DskipTests

# Étape 2 : exécution de l'application
FROM eclipse-temurin:21-jre-alpine

ENV MYAPP_HOME=/opt/myapp
WORKDIR $MYAPP_HOME

COPY --from=myapp-build $MYAPP_HOME/target/*.jar $MYAPP_HOME/myapp.jar

ENTRYPOINT ["java", "-jar", "myapp.jar"]
```

Explication des instructions :

- `FROM eclipse-temurin:21-jdk-alpine AS myapp-build` : crée l’étape de compilation avec un JDK 21.
- `ENV MYAPP_HOME=/opt/myapp` : définit le répertoire de travail de l’application.
- `WORKDIR $MYAPP_HOME` : sélectionne ce répertoire.
- `RUN apk add --no-cache maven` : installe Maven pour construire le projet.
- `COPY pom.xml .` : copie la configuration Maven.
- `COPY src ./src` : copie les sources Java.
- `RUN mvn package -DskipTests` : compile l’application et génère le JAR sans exécuter les tests.
- `FROM eclipse-temurin:21-jre-alpine` : démarre une nouvelle étape, destinée à l’exécution.
- `COPY --from=myapp-build ...` : récupère uniquement le JAR généré à l’étape précédente.
- `ENTRYPOINT` : définit la commande exécutée au démarrage du conteneur.

L’image finale ne contient donc pas Maven ni le JDK de compilation.

## 1-5. Pourquoi avons-nous besoin d’un reverse proxy ?

Un reverse proxy reçoit les requêtes des clients et les transmet au serveur applicatif approprié. Dans ce TP, Apache reçoit les requêtes HTTP puis les transmet au backend Spring Boot.

Les avantages sont les suivants :

- fournir un point d’entrée unique pour accéder à l’application ;
- masquer l’accès direct au backend ;
- centraliser certaines fonctions comme la terminaison TLS, la journalisation ou la répartition de charge ;
- faciliter l’ajout futur d’un frontend ou d’autres services.

La configuration Apache utilisée est :

```apache
LoadModule proxy_module modules/mod_proxy.so
LoadModule proxy_http_module modules/mod_proxy_http.so

<VirtualHost *:80>
    ProxyPreserveHost On
    ProxyPass / http://tp-backend:8080/
    ProxyPassReverse / http://tp-backend:8080/
</VirtualHost>
```

Les modules `mod_proxy` et `mod_proxy_http` permettent à Apache de transférer les requêtes HTTP vers le backend.

La directive `ProxyPass` transmet les requêtes, tandis que `ProxyPassReverse` adapte certains en-têtes de réponse liés aux redirections.

Le nom `tp-backend` est résolu grâce au réseau Docker partagé `app-network`.

Le fonctionnement a été vérifié avec l’URL :

http://localhost:8082/departments/IRC/students

La réponse JSON contenant Eli Copter confirme que la requête passe par Apache et atteint le backend.

## 1-6. Pourquoi Docker Compose est-il si important ?

Docker Compose permet de définir et d’orchestrer plusieurs services dans un fichier YAML unique.

Sans Docker Compose, il faut gérer manuellement les commandes de création, de démarrage, d’arrêt, les réseaux, les volumes et les ports de chaque conteneur.

Avec Docker Compose, on peut :

- centraliser la configuration des services ;
- définir leurs dépendances ;
- configurer les réseaux et les volumes ;
- démarrer ou arrêter l’application avec une seule commande ;
- faciliter la reproductibilité de l’environnement entre plusieurs machines.

Dans ce TP, Docker Compose permet de gérer ensemble PostgreSQL, le backend Java, Apache et Adminer.

## 1-7. Documenter les principales commandes Docker Compose

### Vérifier la configuration

```bash
docker compose config
```

Affiche la configuration résultante et permet de détecter certaines erreurs de syntaxe ou de configuration.

### Construire les images

```bash
docker compose build
```

Construit les images des services qui possèdent une configuration `build:`.

### Démarrer les services

```bash
docker compose up -d
```

Crée et démarre les services en arrière-plan.

### Afficher l’état des services

```bash
docker compose ps
```

Affiche les conteneurs associés au projet Compose et leur état.

### Afficher les journaux

```bash
docker compose logs
```

Affiche les journaux des services.

Pour suivre les journaux en temps réel :

```bash
docker compose logs -f
```

Pour consulter un service précis :

```bash
docker compose logs backend
```

### Arrêter les services

```bash
docker compose stop
```

Arrête les services sans supprimer les conteneurs.

### Redémarrer les services

```bash
docker compose start
```

Redémarre les conteneurs précédemment arrêtés.

### Arrêter et supprimer les conteneurs du projet

```bash
docker compose down
```

Arrête et supprime les conteneurs et le réseau créé par Compose pour le projet. Les volumes ne sont pas supprimés par défaut.

Il faut faire attention aux volumes et aux réseaux externes : ils peuvent être partagés ou contenir des données importantes.

## 1-8. Documenter le fichier docker-compose.yml

Le fichier `docker-compose.yml` décrit les services de l’application et les ressources dont ils ont besoin.

Dans ce TP, les services sont :

- `database` : serveur PostgreSQL ;
- `backend` : application Spring Boot ;
- `httpd` : serveur Apache et reverse proxy ;
- `adminer` : interface web d’administration de PostgreSQL.

### Les services

La section `services` décrit les conteneurs, leurs images ou leur mode de construction, leurs variables d’environnement, leurs ports, leurs dépendances et les réseaux auxquels ils sont connectés.

### Les dépendances

La directive `depends_on` définit l’ordre de démarrage des services. À elle seule, elle ne garantit pas que la base de données est prête à accepter des connexions.

Pour fiabiliser le démarrage, on peut ajouter un contrôle de santé (`healthcheck`) à PostgreSQL et faire dépendre le backend de l’état `service_healthy`.

### Les réseaux

La section `networks` permet aux services de communiquer entre eux. Le réseau partagé `app-network` permet notamment au backend de joindre PostgreSQL et à Apache de joindre le backend en utilisant leurs noms de conteneurs.

### Les volumes

La section `volumes` permet de conserver les données PostgreSQL indépendamment du conteneur.

Le volume utilisé dans ce TP est déclaré comme externe afin de réutiliser les données déjà présentes.

### Les ports

Apache est accessible sur le port `8082` du Mac, redirigé vers le port 80 du conteneur. Adminer est accessible sur le port `8081`, redirigé vers le port 8080 du conteneur.

Conformément au sujet, le backend et PostgreSQL ne devraient pas publier leurs ports sur l’hôte dans la configuration finale. Ils doivent être accessibles depuis les autres services via le réseau Docker.

## 1-9. Documenter les commandes de publication et les images publiées sur Docker Hub

Docker Hub est un registre en ligne permettant de stocker des images Docker et de les partager avec d’autres développeurs ou machines.

### Étape 1 : se connecter à Docker Hub

```bash
docker login
```

Cette commande permet de s’authentifier auprès du registre Docker.

### Étape 2 : taguer les images

Remplacer `VOTRE_IDENTIFIANT_DOCKERHUB` par son véritable identifiant Docker Hub.

```bash
docker tag tp-database:1.0 VOTRE_IDENTIFIANT_DOCKERHUB/tp-database:1.0

docker tag tp-backend:1.0 VOTRE_IDENTIFIANT_DOCKERHUB/tp-backend:1.0

docker tag tp-httpd:1.1 VOTRE_IDENTIFIANT_DOCKERHUB/tp-httpd:1.1
```

Le tag associe un nom de dépôt et une version à une image locale.

### Étape 3 : publier les images

```bash
docker push VOTRE_IDENTIFIANT_DOCKERHUB/tp-database:1.0

docker push VOTRE_IDENTIFIANT_DOCKERHUB/tp-backend:1.0

docker push VOTRE_IDENTIFIANT_DOCKERHUB/tp-httpd:1.1
```

### Images à documenter

| Image locale | Image à publier |
|---|---|
| `tp-database:1.0` | `VOTRE_IDENTIFIANT_DOCKERHUB/tp-database:1.0` |
| `tp-backend:1.0` | `VOTRE_IDENTIFIANT_DOCKERHUB/tp-backend:1.0` |
| `tp-httpd:1.1` | `VOTRE_IDENTIFIANT_DOCKERHUB/tp-httpd:1.1` |

Après la publication, les dépôts et les tags doivent être visibles dans le compte Docker Hub.

**État de publication :** à compléter après avoir exécuté les commandes et vérifié les images effectivement publiées. Ne pas considérer les images comme publiées tant que cette vérification n’a pas été faite.

## 1-10. Pourquoi publier les images dans un registre en ligne ?

La publication des images dans un registre en ligne permet de partager et de réutiliser les images Docker sans devoir reconstruire les applications sur chaque machine.

Les avantages sont les suivants :

- **Partage :** les membres d’une équipe peuvent récupérer les mêmes images.
- **Reproductibilité :** une version identifiée par un tag peut être utilisée sur plusieurs environnements.
- **Déploiement :** les serveurs peuvent télécharger les images depuis le registre.
- **Collaboration :** les images peuvent être intégrées dans un processus d’intégration et de déploiement continus (CI/CD).
- **Centralisation :** les versions des images sont regroupées dans un même registre.

Il faut toutefois gérer les droits d’accès et éviter de publier des secrets ou des données sensibles dans les images.



# Réponses aux questions — TP2  

## 2-1 Que sont les conteneurs de test ?

Ce sont simplement des bibliothèques Java qui vous permettent d'exécuter un tas de conteneurs Docker pendant les tests. Ici, nous utilisons le conteneur postgresql pour nous connecter à notre application lors des tests

## 2-2 Dans quel but devons-nous utiliser des variables sécurisées ?

Nous devons utiliser des variables sécurisées pour protéger les informations sensibles, comme les mots de passe, les tokens d'accès et les clés API.
Dans GitHub Actions, elles permettent de stocker ces informations dans les Secrets du dépôt et de les utiliser dans le workflow sans écrire leurs valeurs directement dans le code.


## 2-3 Pourquoi avons-nous mis les besoins : build-and-test-backend sur ce travail ? Essayez peut-être sans cela et vous verrez !

Nous avons mis needs: test-backend pour que le job de construction et de publication des images Docker ne s'exécute qu'après la réussite des tests du backend.
- Si test-backend réussit, le job build-and-push-docker-image peut démarrer.
- Si test-backend échoue, le job de construction et de publication est ignoré.

## 2-4 Dans quel but devons-nous pousser des images Docker ?

Nous devons pousser les images Docker vers un registre comme Docker Hub afin de les stocker et de pouvoir les partager et les déployer sur d'autres machines ou serveurs.


# 2- Sonarcloud ?

SonarCloud est un outil en ligne qui analyse automatiquement le code d'un projet pour détecter les bugs, les problèmes de sécurité et les erreurs de qualité.

# 2- CD ?
Le CD (Continuous Delivery ou Continuous Deployment) est une pratique qui permet d'automatiser la livraison ou le déploiement d'une application après les tests.





# Réponses aux questions — TP3 Ansible

## 3-1. Inventaire et commandes de base

### Inventaire Ansible

J'ai  créé le fichier `ansible/inventories/setup.yml` pour définir mon serveur distant Takima.

L'inventaire contient :
- Le groupe `prod`, qui représente l'environnement de production.
- L'adresse du serveur distant.
- L'utilisateur SSH `admin`.
- Le chemin vers la clé privée SSH permettant l'authentification.

Cet inventaire permet à Ansible de savoir sur quelle machine exécuter ses tâches.

### Commandes utilisées

**1. Tester la connexion au serveur**

```bash
ansible all -i inventories/setup.yml -m ping
```

Le module `ping` vérifie que la connexion SSH et l'exécution distante fonctionnent. Le résultat `SUCCESS` avec `pong` confirme que le serveur est accessible.

**2. Récupérer les informations du serveur**

```bash
ansible all -i inventories/setup.yml -m setup -a "filter=ansible_distribution*"
```

Le module `setup` récupère les informations système appelées *facts*.

Nous avons identifié un serveur Debian 12.7 (Bookworm), utilisant Python 3.11.

**3. Désinstaller Apache**

```bash
ansible all -i inventories/setup.yml -m apt -a "name=apache2 state=absent" --become
```

Le module `apt` permet de gérer les paquets Debian. `state=absent` demande la suppression d'Apache, tandis que `--become` permet d'obtenir les privilèges administrateur.

Le résultat `CHANGED` confirme que le paquet Apache a été supprimé.

### Idempotence

Ansible fonctionne selon le principe d'idempotence : si le serveur est déjà dans l'état demandé, relancer une tâche ne provoque pas de modification inutile.

Par exemple, après avoir supprimé Apache, relancer la même commande doit produire `changed: false`.



## 3-2. Utilisation des rôles Ansible

Nous avons créé un rôle Docker avec la commande :

```bash
ansible-galaxy init roles/docker
```

Un rôle Ansible permet de regrouper des tâches liées à une fonctionnalité afin de rendre le projet plus organisé, réutilisable et facile à maintenir.

Nous avons déplacé les tâches d'installation de Docker dans `roles/docker/tasks/main.yml`.

Le fichier `playbook.yml` appelle désormais ce rôle :

```yaml
- name: Configure Docker server
  hosts: all
  gather_facts: true
  become: true

  roles:
    - docker
```

Nous avons ensuite vérifié son fonctionnement avec :

```bash
ansible-playbook -i inventories/setup.yml playbook.yml
```

Résultat : `ok=12 changed=0 unreachable=0 failed=0`.

Le rôle fonctionne correctement et aucune modification supplémentaire n'a été nécessaire, ce qui démontre l'idempotence d'Ansible.





### Question 3-3 — Configuration des tâches `docker_container`

J'ai utilisé le module `community.docker.docker_container` d'Ansible pour automatiser le déploiement de mes conteneurs Docker sur mon serveur distant.

Ce module permet de créer, configurer et démarrer des conteneurs Docker sans utiliser directement la commande `docker run`.

Voici les principaux paramètres utilisés :

- **`name`** : définit le nom du conteneur (`tp-database`, `tp-backend`, `tp-httpd`).
- **`image`** : indique l'image Docker à utiliser, récupérée depuis Docker Hub.
- **`state: started`** : garantit que le conteneur est démarré.
- **`restart_policy: unless-stopped`** : permet de redémarrer automatiquement le conteneur, sauf s'il a été arrêté volontairement.
- **`published_ports`** : permet d'exposer les ports du conteneur sur le serveur.
- **`networks`** : connecte les conteneurs au réseau Docker `app-network` pour qu'ils puissent communiquer.
- **`env`** : définit les variables d'environnement nécessaires, notamment pour la connexion à PostgreSQL.
- **`volumes`** : permet de conserver les données PostgreSQL même si le conteneur est supprimé et recréé.
- **`pull: always`** : demande à Docker de vérifier et récupérer l'image depuis le registre avant le déploiement, lorsqu'il est utilisé.

Cette configuration permet d'automatiser le déploiement, de faciliter la maintenance et d'assurer l'idempotence des tâches Ansible.


### Sécurité du déploiement continu

Non, déployer automatiquement chaque nouvelle image Docker n'est pas totalement sécurisé.

Une nouvelle image peut contenir des bugs, des vulnérabilités ou du code malveillant. Son déploiement automatique pourrait provoquer une panne de l'application ou compromettre le serveur.

Pour améliorer la sécurité, il est préférable de :

- **Exécuter des tests automatiques** avant chaque déploiement.
- **Analyser les images Docker** pour détecter les vulnérabilités.
- **Utiliser des versions précises ou des digests d'images** plutôt que le tag `latest`.
- **Exiger une validation manuelle** avant le déploiement en production.
- **Protéger les secrets** avec GitHub Actions Secrets.
- **Prévoir un rollback** pour revenir rapidement à une version précédente en cas de problème.

Ainsi, le déploiement continu reste automatisé, mais seules les versions vérifiées et approuvées peuvent être déployées en production.