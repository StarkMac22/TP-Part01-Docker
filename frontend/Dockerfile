# Étape 1 : compilation du front-end Vue.js
FROM node:20-bookworm-slim AS build

WORKDIR /app

COPY package.json yarn.lock ./

RUN corepack enable \
    && yarn install --frozen-lockfile --ignore-engines

COPY . .

ENV NODE_OPTIONS=--openssl-legacy-provider

RUN yarn build

# Étape 2 : serveur Nginx
FROM nginx:stable-alpine

COPY --from=build /app/dist/ /usr/share/nginx/html/

COPY default.conf /etc/nginx/conf.d/default.conf

EXPOSE 80