#!/bin/bash
# Entrypoint script: fix permissions on mounted volumes, then run as langflix user.
# Runs as root initially so chown/chmod work on TrueNAS ZFS mounts.

set -e

# Fix ownership on writable mounted directories
for dir in /data/logs /data/output /app/cache /app/auth; do
    if [ -d "$dir" ]; then
        chown -R langflix:langflix "$dir" 2>/dev/null || true
        chmod -R u+rwX "$dir" 2>/dev/null || true
    fi
done

# Fix permissions on specific auth files
for f in /app/auth/youtube_credentials.json /app/auth/youtube_token.json; do
    if [ -f "$f" ]; then
        chown langflix:langflix "$f" 2>/dev/null || true
        chmod u+rw "$f" 2>/dev/null || true
    fi
done

# Fix log file permissions if they already exist
for f in /data/logs/*.log; do
    if [ -f "$f" ]; then
        chown langflix:langflix "$f" 2>/dev/null || true
        chmod u+rw "$f" 2>/dev/null || true
    fi
done

# Drop to langflix user and exec the CMD
exec gosu langflix "$@"
