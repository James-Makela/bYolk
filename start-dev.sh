#!/bin/sh
npm install
npm run build:css
docker compose up -d
