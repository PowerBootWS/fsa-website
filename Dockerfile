FROM nginx:alpine

# Template is rendered at container start via envsubst (built into nginx:alpine entrypoint)
COPY nginx.conf.template /etc/nginx/templates/default.conf.template
COPY index.html /usr/share/nginx/html/index.html
COPY how-it-works.html /usr/share/nginx/html/how-it-works.html
COPY coming-soon.html /usr/share/nginx/html/coming-soon.html
COPY privacy-policy.html /usr/share/nginx/html/privacy-policy.html
COPY terms-of-use.html /usr/share/nginx/html/terms-of-use.html
COPY affiliate.html /usr/share/nginx/html/affiliate.html
COPY affiliate-confirmation.html /usr/share/nginx/html/affiliate-confirmation.html
COPY enrollment-confirmation.html /usr/share/nginx/html/enrollment-confirmation.html
COPY enroll.html /usr/share/nginx/html/enroll.html
COPY jobs.html /usr/share/nginx/html/jobs.html
COPY exit-intent.js /usr/share/nginx/html/exit-intent.js
COPY styles.css /usr/share/nginx/html/styles.css
COPY styles-v2.css /usr/share/nginx/html/styles-v2.css
COPY assets/ /usr/share/nginx/html/assets/
COPY sitemap.xml /usr/share/nginx/html/sitemap.xml
COPY robots.txt /usr/share/nginx/html/robots.txt
COPY articles/ /usr/share/nginx/html/articles/

EXPOSE 80
