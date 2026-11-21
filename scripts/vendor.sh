#!/usr/bin/env bash
# Re-clone the reference repos the skills came from (gitignored).
set -e; mkdir -p _vendor; cd _vendor
[ -d skills ] || git clone --depth 1 -q https://github.com/mattpocock/skills.git
[ -d kun ] || git clone --depth 1 -q https://github.com/kunchenguid/kun.git
echo vendored
