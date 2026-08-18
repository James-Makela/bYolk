#!/bin/sh

git pull
sudo docker compose down
./start.sh
