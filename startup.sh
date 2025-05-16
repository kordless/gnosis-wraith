#!/bin/bash
service redis-server start
exec hypercorn --bind 0.0.0.0:5678 app:app
