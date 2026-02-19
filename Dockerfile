FROM nginx:alpine

COPY index.html /usr/share/nginx/html/index.html
COPY privacy-policy.html /usr/share/nginx/html/privacy-policy.html
COPY terms-of-use.html /usr/share/nginx/html/terms-of-use.html
COPY styles.css /usr/share/nginx/html/styles.css
COPY assets/ /usr/share/nginx/html/assets/
COPY sitemap.xml /usr/share/nginx/html/sitemap.xml

EXPOSE 80
