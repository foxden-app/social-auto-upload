#!/usr/bin/env bash
set -euo pipefail

account="${1:?usage: tencent_commands.sh <account>}"

sau tencent check --account "$account" --json
# First login requires the user to scan the QR code:
# sau tencent login --account "$account" --headed
