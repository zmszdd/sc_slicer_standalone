#!/usr/bin/env bash
# Push the prepared local commit to a private GitHub repository.
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "usage: $0 <github-repo-url> [branch]" >&2
  echo "example: $0 git@github.com:OWNER/sc_slicer_standalone.git main" >&2
  exit 2
fi

url="$1"
branch="${2:-main}"
key="/root/.ssh/id_ed25519_github_sc_slicer"

if [[ ! -f "$key" ]]; then
  echo "missing SSH key: $key" >&2
  exit 2
fi

if [[ "$url" == https://github.com/* ]]; then
  path="${url#https://github.com/}"
  path="${path%.git}"
  url="git@github.com:${path}.git"
fi

git remote remove github 2>/dev/null || true
git remote add github "$url"

isolated_home="$(mktemp -d "${TMPDIR:-/tmp}/sc-gh-push.XXXXXX")"
trap 'rm -rf "$isolated_home"' EXIT
mkdir -p "$isolated_home/.ssh"

HOME="$isolated_home" \
GIT_SSH_COMMAND="ssh -i $key -o IdentitiesOnly=yes -o StrictHostKeyChecking=accept-new" \
  git push -u github "HEAD:${branch}"
