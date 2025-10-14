#!/usr/bin/env bash
export REQUESTS_CA_BUNDLE="$HOME/.config/rice/caldav2json/certs/custom-ca-bundle.pem"
export LD_PRELOAD=/usr/lib/libssl.so.3:/usr/lib/libcrypto.so.3
exec uv run main.py
