# Baserow gateway: the official Caddy image (pinned by tag and digest) with a
# Caddyfile that routes /api, /ws, /mcp and /assistant to the backend and the
# rest to the web frontend.
FROM caddy:2.11.9-alpine@sha256:003a97808e781aa9f7e75cc2f43d34d461099031faf5e20faefb9f61126836f0

COPY Caddyfile /etc/caddy/Caddyfile

# Fail the build rather than the deploy on a Caddyfile error.
RUN PORT=8080 caddy validate --config /etc/caddy/Caddyfile --adapter caddyfile

EXPOSE 8080
CMD ["caddy", "run", "--config", "/etc/caddy/Caddyfile", "--adapter", "caddyfile"]
