# Public web entrypoint for Google Cloud Run.
# Serves the React build and proxies /api to the API service (BACKEND_URL).

FROM node:22-alpine AS build

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .
RUN npm run build

FROM nginx:alpine

RUN apk add --no-cache gettext

COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf.template /etc/nginx/templates/default.conf.template
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

ENV PORT=8080 \
    BACKEND_URL=http://127.0.0.1:8080

EXPOSE 8080

ENTRYPOINT ["/docker-entrypoint.sh"]
