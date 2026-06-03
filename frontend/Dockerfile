# Archsari frontend — React (Vite) + nginx for Cloud Run / Docker.
#
# Build:
#   docker build -t archsari-web ./frontend
#
# Run (point /api at your backend):
#   docker run -p 8080:8080 -e BACKEND_URL=http://host.docker.internal:8000 archsari-web
#
# Cloud Run sets PORT=8080 automatically; set BACKEND_URL to your API service URL.

FROM node:22-alpine AS build

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .
RUN npm run build

FROM nginx:alpine

# Only substitute PORT and BACKEND_URL — leave nginx vars like $host untouched.
ENV NGINX_ENVSUBST_FILTER=PORT|BACKEND_URL \
    PORT=8080 \
    BACKEND_URL=http://127.0.0.1:8080

COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf.template /etc/nginx/templates/default.conf.template

EXPOSE 8080
