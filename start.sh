#!/bin/sh
npm install
npm run build:css
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
