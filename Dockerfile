# CI runner image for the miniMe Hugo workflows: node, git, and Hugo
# extended baked in so jobs don't re-download Hugo on every run.
ARG HUGO_VERSION=0.162.1

FROM code.forgejo.org/oci/node:22-bookworm
ARG HUGO_VERSION

RUN wget -q "https://github.com/gohugoio/hugo/releases/download/v${HUGO_VERSION}/hugo_extended_${HUGO_VERSION}_linux-amd64.tar.gz" -O /tmp/hugo.tar.gz \
    && tar xzf /tmp/hugo.tar.gz -C /usr/local/bin hugo \
    && rm /tmp/hugo.tar.gz \
    && hugo version
