#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# cf-token-loader.sh — resolve the Cloudflare API token at runtime.
#
# Why this file exists
# -------------------
# Both deploy scripts used to decode a hardcoded base64 token inline. This repo
# is public, so anyone who ever cloned it (and anyone with any future history
# access) can read that token. It has zone Read + DNS Records Edit +
# Zone Settings Edit on aishield.tools — enough to hijack the domain's CNAME
# and point it at an attacker's server. The token value therefore MUST NOT
# live in this repository.
#
# Resolution order (first hit wins)
# ---------------------------------
#   1. $CF_API_TOKEN        already set by the caller
#   2. $CF_TUNNEL_TOKEN     environment override (CI secret / local shell)
#   3. $CF_TOKEN_FILE       file on disk, default /root/.aishield/cf-token
#                           written once by .github/workflows/install-cf-token.yml
#
# Usage
# -----
#   . scripts/cf-token-loader.sh          # defines CF_ZONE_ID / CF_TOKEN_FILE
#   if ! load_cf_token; then
#       log "no CF token"
#       exit 2
#   fi
#
# NOTE: both callers use `set +e`, and `load_cf_token` returns 1 when nothing
# is available, so always guard it with `if ! load_cf_token; then ...` instead
# of calling it bare — otherwise a missing token is silently swallowed and the
# script spends minutes curling Cloudflare with an empty Authorization header.
# ---------------------------------------------------------------------------

# aishield.tools zone id.
: "${CF_ZONE_ID:=7625fc8ab719b3974e12aa2b6bf25489}"

# Where install-cf-token.yml writes the secret on the VPS.
: "${CF_TOKEN_FILE:=/root/.aishield/cf-token}"

# Some bash builds (MSYS2/Cygwin on Windows) resolve POSIX paths in *arguments*
# but not inside environment variables, so a Windows-style CF_TOKEN_FILE
# ("C:/tmp/x" or "C:\tmp\x") would silently fail [ -r ]. Normalise it.
#
# Two MSYS2 conventions exist for the drive prefix (/mnt/c/... on older builds,
# /c/... on newer ones), so probe which one is actually mounted instead of
# assuming. POSIX input is returned unchanged — this is a no-op on the VPS.
_cf_token_file_posix() {
    local p="$1" drv rest base
    case "$p" in
        [A-Za-z]:[\\/]*)
            drv="$(printf '%s' "${p:0:1}" | tr '[:upper:]' '[:lower:]')"
            rest="${p:2}"
            rest="${rest//\\//}"
            rest="/${rest#/}"
            if [ -d "/mnt/$drv" ]; then
                base="/mnt/$drv"
            elif [ -d "/$drv" ]; then
                base="/$drv"
            else
                base="/mnt/$drv"
            fi
            printf '%s' "$base$rest"
            ;;
        *)
            printf '%s' "$p"
            ;;
    esac
}

load_cf_token() {
    # 1. caller already supplied one
    if [ -n "${CF_API_TOKEN:-}" ]; then
        return 0
    fi
    # 2. explicit environment override
    if [ -n "${CF_TUNNEL_TOKEN:-}" ]; then
        CF_API_TOKEN="$CF_TUNNEL_TOKEN"
        return 0
    fi
    # 3. on-disk file (single line, no trailing newline/space)
    local token_file
    token_file="$(_cf_token_file_posix "$CF_TOKEN_FILE")"
    if [ -r "$token_file" ]; then
        CF_API_TOKEN="$(tr -d '[:space:]' < "$token_file")"
        if [ -n "${CF_API_TOKEN}" ]; then
            return 0
        fi
    fi
    return 1
}

# Print *where* the token came from, without printing the token.
cf_token_source() {
    local token_file
    token_file="$(_cf_token_file_posix "$CF_TOKEN_FILE")"
    if [ -n "${CF_API_TOKEN:-}" ] && [ -n "${CF_TUNNEL_TOKEN:-}" ] && [ "$CF_API_TOKEN" = "$CF_TUNNEL_TOKEN" ]; then
        echo 'env $CF_TUNNEL_TOKEN'
    elif [ -r "$token_file" ]; then
        echo "file ${token_file}"
    else
        echo 'env $CF_API_TOKEN'
    fi
}
