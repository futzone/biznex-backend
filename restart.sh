#!/bin/bash

sudo systemctl restart fastapi

echo "Service restart successfully"

sleep 3

sudo systemctl restart nginx

echo "Nginx restart successfully"
