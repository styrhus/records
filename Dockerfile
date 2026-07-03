# CI runner image for the miniMe Hugo workflows: node (for actions/checkout
# and the git-pages action), git, and Hugo extended baked in so fork jobs
# don't re-download the 25 MB tarball from GitHub on every run.
#
# Published as:
#   git.euh.no/tb4/hugo-runner:<version>
#   codeberg.org/tb4/hugo-runner:<version>
ARG HUGO_VERSION=0.162.1

FROM code.forgejo.org/oci/node:22-bookworm
ARG HUGO_VERSION

RUN wget -q "https://github.com/gohugoio/hugo/releases/download/v${HUGO_VERSION}/hugo_extended_${HUGO_VERSION}_linux-amd64.tar.gz" -O /tmp/hugo.tar.gz \
    && tar xzf /tmp/hugo.tar.gz -C /usr/local/bin hugo \
    && rm /tmp/hugo.tar.gz \
    && hugo version
