#!/usr/bin/env bash
# Run before every push. The repo is public. Exit 1 if anything key-shaped is tracked or staged.
set -uo pipefail
cd "$(git rev-parse --show-toplevel)"
PAT='AIza[0-9A-Za-z_-]{30,}|sk-[A-Za-z0-9]{20,}|ghp_[A-Za-z0-9]{30,}|shpat_[a-f0-9]{20,}|shpca_[a-f0-9]{20,}|-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY|checkout\.shopify\.com/[0-9]+/checkouts/'
hits=$( { git grep -nIE "$PAT" -- . ':!*.md' ':!docs/*.pdf'; git diff --cached -U0 | grep -nIE "^\+.*($PAT)"; } 2>/dev/null )
if [ -n "$hits" ]; then echo "SECRET-SHAPED CONTENT FOUND:"; echo "$hits"; exit 1; fi
git ls-files | grep -qxE '\.env|device/secrets\.(h|py)' && { echo ".env or device/secrets is tracked"; exit 1; }
echo "secret scan clean"
