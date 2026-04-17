FROM nginx:alpine

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY index.html /usr/share/nginx/html/index.html
COPY home.html /usr/share/nginx/html/home.html
COPY privacy-policy.html /usr/share/nginx/html/privacy-policy.html
COPY terms-of-use.html /usr/share/nginx/html/terms-of-use.html
COPY affiliate.html /usr/share/nginx/html/affiliate.html
COPY styles.css /usr/share/nginx/html/styles.css
COPY assets/ /usr/share/nginx/html/assets/
COPY sitemap.xml /usr/share/nginx/html/sitemap.xml

EXPOSE 80
