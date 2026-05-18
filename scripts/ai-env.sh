#!/usr/bin/env bash

REPO="$HOME/srv/projects/ai-codebase-explainer"

if [ ! -d "$REPO" ]; then
  echo "ERROR: Repo not found at $REPO"
  exit 1
fi

cd "$REPO"

mkdir -p "$REPO/.opencode-runtime/config"
mkdir -p "$REPO/.opencode-runtime/data"
mkdir -p "$REPO/.opencode-runtime/cache"
mkdir -p "$REPO/.opencode"
mkdir -p "$REPO/.opencode-bin"
mkdir -p "$REPO/.gentle-ai-bin"

export PATH="$REPO/.opencode-bin:$REPO/.gentle-ai-bin:$PATH"

# IMPORTANTE:
# Gentle-AI y OpenCode deben ver el mismo XDG runtime para que no trabajen con configs distintas.
export XDG_CONFIG_HOME="$REPO/.opencode-runtime/config"
export XDG_DATA_HOME="$REPO/.opencode-runtime/data"
export XDG_CACHE_HOME="$REPO/.opencode-runtime/cache"

# Config local del repo para OpenCode.
export OPENCODE_CONFIG="$REPO/opencode.json"
export OPENCODE_CONFIG_DIR="$REPO/.opencode"
