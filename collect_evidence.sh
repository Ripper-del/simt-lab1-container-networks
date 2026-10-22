#!/usr/bin/env bash
# Збір виводу всіх команд завдання у evidence/*.txt (для звіту)
cd "$(dirname "$0")"
E=evidence; mkdir -p $E
hostexec() { docker run --rm --privileged --pid=host alpine nsenter -t 1 -m -u -n -i sh -c "$*"; }
# запис команди та її виводу у файл
run() { local f="$E/$1.txt"; shift; { echo "\$ $*"; eval "$@" 2>&1; } > "$f"; }

./cleanup_cli.sh >/dev/null 2>&1
docker compose down -v >/dev/null 2>&1
# попереднє завантаження образів, щоб вивід був без шуму
for i in redis:7-alpine nginx:1.27-alpine nicolaka/netshoot python:3.12-alpine; do docker pull -q $i >/dev/null; done
docker compose build -q >/dev/null 2>&1

run 01-versions "docker version --format 'Client {{.Client.Version}} / Server {{.Server.Version}} ({{.Server.Os}}/{{.Server.Arch}})'; docker compose version; docker info --format 'Driver={{.Driver}} CgroupVersion={{.CgroupVersion}} Kernel={{.KernelVersion}} OS={{.OperatingSystem}}'"
run 02-default-net "docker network ls; docker network inspect bridge --format 'Name={{.Name}} Driver={{.Driver}} Subnet={{(index .IPAM.Config 0).Subnet}} Gateway={{(index .IPAM.Config 0).Gateway}}'"
run 03-host-docker0 "hostexec 'ip -br addr show docker0; ip route | grep docker0'"

# основне завдання: CLI-топологія
./run_cli.sh > $E/04-cli-up.txt 2>&1
run 05-user-net "docker network ls --filter name=lab1-net; docker network inspect lab1-net --format 'Subnet={{(index .IPAM.Config 0).Subnet}} Gateway={{(index .IPAM.Config 0).Gateway}} Driver={{.Driver}}'; hostexec \"ip -br addr | grep -E '^br-'\""
run 06-dns "docker exec proxy wget -qO- http://app:8000/; docker exec proxy wget -qO- http://app:8000/; docker exec app cat /etc/resolv.conf; docker run --rm --network lab1-net nicolaka/netshoot dig +short app; docker run --rm --network lab1-net nicolaka/netshoot dig +short db"
run 07-app-to-db "docker exec app python -c \"import socket;print('db ->',socket.gethostbyname('db'))\"; docker exec db redis-cli GET lab:hits"
APPIP=$(docker inspect -f '{{.NetworkSettings.Networks.lab1-net.IPAddress}}' app 2>/dev/null || docker inspect -f '{{(index .NetworkSettings.Networks "lab1-net").IPAddress}}' app)
docker run -d --name iso --network bridge nicolaka/netshoot sleep 300 >/dev/null
run 08-isolation "echo 'IP app = $APPIP'; docker exec iso ping -c 2 -W 1 app; docker exec iso ping -c 2 -W 1 $APPIP; docker exec iso curl -s -m 3 http://$APPIP:8000/ || echo 'curl: недоступно (код '\$?')'"
run 09-publish "docker port proxy; docker port app || echo 'app: портів не опубліковано'; docker port db || echo 'db: портів не опубліковано'; curl -s http://localhost:8080/; curl -s -m 3 http://localhost:8000/ || echo 'localhost:8000 недоступний'; curl -s -m 3 http://localhost:6379/ || echo 'localhost:6379 недоступний'; hostexec 'iptables -t nat -L DOCKER -n'"
run 10-inside-netns "for c in proxy app db; do echo \"=== \$c\"; docker run --rm --network container:\$c nicolaka/netshoot sh -c 'ip -br addr; ip route; ss -tlnp'; done"
for i in 1 2 3; do curl -s http://localhost:8080/ >/dev/null; done
run 11-tcp-conns "for c in proxy app db; do echo \"=== \$c\"; docker run --rm --network container:\$c nicolaka/netshoot ss -tn; done"
run 12-veth "for c in proxy app db; do echo \"=== \$c iflink=\$(docker exec \$c cat /sys/class/net/eth0/iflink)\"; done; hostexec 'ip -o link | grep veth | cut -d: -f1,2'"
run 13-host-nsenter "hostexec \"ip -br addr | grep -E '^br-|^veth'\""

# драйвери host/none/bridge на одному контейнері
run 14-drivers "for m in bridge host none; do echo \"=== --network \$m\"; docker run --rm --network \$m nicolaka/netshoot sh -c 'ip -br addr; echo -n \"internet: \"; (ping -c1 -W2 1.1.1.1 >/dev/null 2>&1 && echo OK) || echo FAIL'; done; docker run -d --rm --name pubtest --network none -p 9090:80 nginx:1.27-alpine >/dev/null; echo \"docker port (none): [\$(docker port pubtest)]\"; docker rm -f pubtest >/dev/null 2>&1"

./cleanup_cli.sh >/dev/null 2>&1

# Compose: з нуля
run 20-compose-up "docker compose up -d --wait; docker compose ps"
run 21-compose-nets "docker network inspect lab1-frontend lab1-backend --format '{{.Name}} subnet={{(index .IPAM.Config 0).Subnet}} internal={{.Internal}} containers: {{range \$id,\$c := .Containers}}{{\$c.Name}}={{\$c.IPv4Address}} {{end}}'"
run 22-segmentation "docker exec proxy wget -qO- -T 2 http://db:6379 || echo 'proxy -> db: ім’я не резолвиться (ізоляція)'; docker run --rm --network container:proxy nicolaka/netshoot ip -br addr; APP=\$(docker compose ps -q app); docker run --rm --network container:\$APP nicolaka/netshoot ip -br addr; docker run --rm --network container:\$APP nicolaka/netshoot getent hosts proxy db"
run 23-scale "docker compose up -d --scale app=2 --wait --no-recreate; docker compose ps app; docker run --rm --network lab1-frontend nicolaka/netshoot dig +short app; for i in 1 2 3 4 5 6; do curl -s http://localhost:8080/; done"
docker compose up -d --scale app=1 --no-recreate >/dev/null 2>&1
run 24-health "docker inspect --format '{{.Name}} {{if .State.Health}}{{.State.Health.Status}}{{else}}no-healthcheck{{end}}' \$(docker compose ps -q); docker compose stop db; docker compose ps -a --format '{{.Service}} {{.Status}}'; docker compose stop app proxy db; docker compose ps -a --format '{{.Service}} {{.Status}}'; docker compose up -d proxy 2>&1 | grep -E 'Waiting|Healthy|Started'; sleep 2; docker compose ps -a --format '{{.Service}} {{.Status}}'"
run 25-compose-repro "docker compose down -v; docker compose up -d --wait; docker compose ps; curl -s http://localhost:8080/; docker compose down -v"
# прибрати службові тунельні інтерфейси з виводу
sed -i '' -E '/^(tunl0|gre0|gretap0|erspan0|ip_vti0|ip6_vti0|sit0|ip6tnl0|ip6gre0|teql0|bond0|dummy0)/d' $E/*.txt
echo done
