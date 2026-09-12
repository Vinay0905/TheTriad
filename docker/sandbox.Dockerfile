# Sandbox image for TriadCouncil approved-code execution.
#
# pytest is baked in rather than installed at run time, because the container
# runs with --network=none and a read-only root filesystem. That also lets us
# emit JUnit XML as machine-readable evidence of the test run.
#
# Build once:
#   docker build -t triadcouncil-sandbox:py312 -f docker/sandbox.Dockerfile docker/
#
# Override the tag with AI_TEAM_SANDBOX_IMAGE if you build your own.

FROM python:3.12-slim

# Pinned so an approved bundle runs against the same test runner every time.
RUN pip install --no-cache-dir pytest==8.3.4

# Containers run as a non-root user (see AI_TEAM_SANDBOX_UID, default 65534).
# Bytecode writing is disabled because the root filesystem is read-only.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /workspace

# The runner always supplies an explicit argv from the allowlist; this default
# only exists so a bare `docker run` of the image is inert rather than a shell.
CMD ["python", "-c", "print('TriadCouncil sandbox image. The runner supplies the command.')"]
