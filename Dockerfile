# This file is meant for deploying the MCP server using Docker Compose. This, together with
# the Docker Compose file, makes it possible to create a localhost deployment of the MCP server,
# which can be used for testing and development purposes or for running on a server.
#
# No API keys are needed. The database is downloaded on first use and cached in
# FINANCEDATABASE_CACHE_DIR (a volume in docker-compose.yml), then checked for updates at
# most once a day.

FROM python:3.12-slim

WORKDIR /app

RUN pip install uv

# Dependencies first (cached unless pyproject.toml or uv.lock change), then the package.
COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --extra mcp --no-dev --no-install-project

COPY financedatabase/ financedatabase/
RUN uv sync --frozen --extra mcp --no-dev

ENV MCP_TRANSPORT=streamable-http
ENV MCP_HOST=0.0.0.0
ENV MCP_PORT=8000
ENV FINANCEDATABASE_CACHE_DIR=/data/financedatabase

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

CMD ["uv", "run", "--no-sync", "financedatabase-mcp"]
