# The records product as a container: the kit plus Hugo, serving the site.
FROM codeberg.org/tb4/hugo-runner:latest

COPY . /records
WORKDIR /records/hugo
EXPOSE 1313
CMD ["hugo", "server", "--bind", "0.0.0.0", "--baseURL", "http://localhost:1313/"]
