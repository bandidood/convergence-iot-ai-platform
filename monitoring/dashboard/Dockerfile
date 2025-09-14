FROM nginx:alpine

# Copy des fichiers web
COPY index.html /usr/share/nginx/html/

# Page de santé
RUN echo '<html><body>Dashboard OK</body></html>' > /usr/share/nginx/html/health.html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]