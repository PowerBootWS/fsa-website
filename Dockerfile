# Stage 1: stitch shared nav/footer partials into every page (scripts/build_pages.py)
FROM python:3.11-slim AS build
WORKDIR /build
COPY . .
RUN python3 scripts/build_pages.py --out dist

# Stage 2: serve the built output
FROM nginx:alpine

# Template is rendered at container start via envsubst (built into nginx:alpine entrypoint)
COPY nginx.conf.template /etc/nginx/templates/default.conf.template
COPY --from=build /build/dist/ /usr/share/nginx/html/

EXPOSE 80
