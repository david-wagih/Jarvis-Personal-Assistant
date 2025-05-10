#!/bin/sh
if [ -n "$TOKEN_PICKLE_B64" ]; then
  echo "$TOKEN_PICKLE_B64" | base64 -d > /app/token.pickle
fi
exec python setup_gmail_pubsub.py