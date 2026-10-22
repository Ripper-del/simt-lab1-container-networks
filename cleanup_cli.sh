#!/usr/bin/env bash
# прибирання ресурсів CLI-частини
docker rm -f proxy app db iso 2>/dev/null
docker network rm lab1-net 2>/dev/null
exit 0
