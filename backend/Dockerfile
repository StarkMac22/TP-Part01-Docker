
# Étape 1 : Construire l'application avec Maven et Java 21
FROM maven:3.9-eclipse-temurin-21 AS myapp-build

ENV MYAPP_HOME=/opt/myapp
WORKDIR $MYAPP_HOME

# Copier les fichiers du projet
COPY pom.xml .
COPY src ./src

# Compiler l'application sans exécuter les tests
RUN mvn package -DskipTests

# Étape 2 : Exécuter l'application avec Java 21
FROM eclipse-temurin:21-jre-alpine

ENV MYAPP_HOME=/opt/myapp
WORKDIR $MYAPP_HOME

# Récupérer le JAR généré pendant la compilation
COPY --from=myapp-build $MYAPP_HOME/target/*.jar $MYAPP_HOME/myapp.jar

# Démarrer l'application Spring Boot
ENTRYPOINT ["java", "-jar", "myapp.jar"]
