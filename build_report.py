"""Формує звіт ЛР1 (PDF + DOCX) з файлів evidence/."""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "common"))
from report_lib import Report

E = "evidence/"
AUTHOR = os.environ.get("LAB_AUTHOR", "Прізвище_Ім'я")
GROUP = os.environ.get("LAB_GROUP", "ІО-00")
r = Report(1, "Контейнерні мережі. Мережева модель Docker та взаємодія контейнеризованих сервісів",
           AUTHOR, GROUP, "асистент кафедри ОТ Назар МЕЛЬНИК", "report")

r.h1("1. Мета і завдання лабораторної роботи")
r.p("Мета: ознайомитися з мережевою моделлю Docker, побудувати ізольовану користувацьку bridge-мережу, "
    "розгорнути в ній проксі, застосунок і базу даних, перевірити взаємодію, ізоляцію та публікацію портів, "
    "описати топологію у docker-compose.yml.")
r.p("Завдання (високий рівень): основна частина (CLI-топологія nginx → Flask → Redis у мережі lab1-net, DNS, ізоляція, "
    "NAT, дослідження netns, Compose) та додаткова (сегментація frontend/backend, порівняння host/none/bridge, veth-пари, "
    "псевдоніми та балансування, healthcheck з depends_on).")

r.h1("2. Результати виконання")
r.h2("2.1. Схема спроєктованої мережевої топології")
r.img(E + "topology.png", "Рис. 1. Топологія: хост, мости, veth-пари, контейнери, IP-адреси, порти", 15.5)
r.p("Єдина точка входу — proxy (порт 8080 на хості). Застосунок app підключений до двох мереж: frontend "
    "(172.28.1.0/24) для зв'язку з проксі та backend (172.28.2.0/24, internal) для зв'язку з БД. "
    "У CLI-частині (основне завдання) усі три контейнери працюють в одній мережі lab1-net 172.28.0.0/24.")
r.table(["Сервіс", "Образ", "Порт", "Мережі", "Публікація"],
        [["proxy", "nginx:1.27-alpine", "80", "frontend", "8080:80"],
         ["app", "lab1-app:1.0 (python:3.12-alpine, Flask, gunicorn)", "8000", "frontend, backend", "ні"],
         ["db", "redis:7-alpine", "6379", "backend", "ні"]], [2.2, 6, 1.5, 3.3, 2.5])

r.h2("2.2. Середовище виконання")
r.step("Версії", "docker version; docker compose version; docker info", E + "01-versions.txt",
       "Використано Docker Engine 28.5.2 і Compose v2.40.3 на Docker Desktop (Linux VM, ядро 6.12, cgroup v2). "
       "Команди рівня хоста (ip, iptables, nsenter) виконуються у мережевому просторі цієї VM через привілейований контейнер.")

r.h2("2.3. Структура проєкту")
r.bullets(["docker-compose.yml — опис топології (мережі, сервіси, healthcheck, depends_on);",
           "app/Dockerfile, app/app.py, app/requirements.txt — сервіс застосунку;",
           "nginx.conf — конфігурація проксі;",
           "run_cli.sh, cleanup_cli.sh — розгортання через Docker CLI (основне завдання);",
           "collect_evidence.sh — автоматичний збір виводів команд для звіту (evidence/)."])

r.h2("2.4. Основне завдання")
r.step("Пункт 2. Стандартні мережі Docker", "docker network ls; docker network inspect bridge", E + "02-default-net.txt",
       "Мережа bridge має підмережу 172.17.0.0/16, шлюз 172.17.0.1, драйвер bridge; поряд існують host і none.")
r.step("Інтерфейс docker0 на хості", "ip -br addr show docker0; ip route | grep docker0", E + "03-host-docker0.txt",
       "Інтерфейс docker0 має адресу шлюзу 172.17.0.1/16, а маршрут до 172.17.0.0/16 іде через цей міст.")
r.step("Пункт 3. Користувацька мережа і контейнери", "bash run_cli.sh  (network create, run db/app/proxy)", E + "04-cli-up.txt",
       "Створено мережу lab1-net 172.28.0.0/24 і запущено db, app, proxy; відповідь {\"hits\":1,...} підтверджує "
       "роботу ланцюжка proxy → app → db.", 12)
r.step("Мережа lab1-net і міст br-<id>", "docker network inspect lab1-net; ip -br addr | grep br-", E + "05-user-net.txt",
       "Підмережа й шлюз збігаються із заданими, а на хості з'явився інтерфейс br-<id> з адресою 172.28.0.1/24.")
r.step("Пункт 4. Взаємодія та вбудований DNS", "docker exec proxy wget -qO- http://app:8000/; docker exec app cat /etc/resolv.conf; dig app", E + "06-dns.txt",
       "Проксі звертається до app за іменем, лічильник зростає; у контейнері nameserver 127.0.0.11 — це вбудований DNS Docker; dig повертає IP-адреси app і db.")
r.step("З'єднання app → db за іменем", "docker exec app python -c \"gethostbyname('db')\"; docker exec db redis-cli GET lab:hits", E + "07-app-to-db.txt",
       "Ім'я db резолвиться в 172.28.0.2, а значення лічильника в Redis збігається з кількістю запитів — застосунок реально звертається до БД.")
r.step("Пункт 5. Ізоляція", "docker run --network bridge ... ping app / ping <IP app> / curl", E + "08-isolation.txt",
       "Контейнер у мережі bridge не резолвить ім'я app і не досягає його за IP (100% втрат, тайм-аут curl): різні мережі ізольовані.")
r.step("Пункт 6. Публікація портів і NAT", "docker port; curl localhost:8080/8000/6379; iptables -t nat -L DOCKER -n", E + "09-publish.txt",
       "Опубліковано лише 8080 → proxy:80; порти 8000 і 6379 з хоста недоступні. Правило DNAT перенаправляє tcp/8080 на 172.28.0.x:80.")
r.step("Пункт 7. Мережевий стан зсередини контейнерів", "docker run --network container:<name> nicolaka/netshoot ip addr; ip route; ss -tlnp", E + "10-inside-netns.txt",
       "Кожен контейнер має eth0 з адресою з lab1-net, маршрут за замовчуванням через 172.28.0.1 і слухає свій порт (80, 8000, 6379); збігається з docker network inspect.", 40)
r.step("Встановлені TCP-з'єднання", "ss -tn у просторах proxy, app, db", E + "11-tcp-conns.txt",
       "Видно ESTABLISHED-з'єднання app ↔ db (порт 6379): це підтверджує, що застосунок підтримує з'єднання з БД.")
r.step("Пункт 8. Compose з нуля", "docker compose up -d --wait; docker compose ps", E + "20-compose-up.txt",
       "Усі три сервіси піднялися одним командою, db і app у стані healthy, опубліковано лише порт proxy.")
r.step("Відтворюваність", "docker compose down -v; docker compose up -d --wait; curl localhost:8080", E + "25-compose-repro.txt",
       "Після повного видалення (-v) конфігурація відтворюється з нуля, застосунок відповідає.", 40)
r.p("Пункт 9 (схема топології) виконано на рис. 1. Висновок за схемою: bridge-міст виконує роль L2-комутатора, "
    "кожен контейнер приєднаний до нього через veth-пару, а вихід назовні та публікація портів реалізовані через NAT (iptables).")

r.h2("2.5. Додаткове завдання")
r.step("Сегментація frontend/backend", "docker network inspect lab1-frontend lab1-backend", E + "21-compose-nets.txt",
       "У frontend є proxy та app, у backend — app та db (internal=true). Мережі мають різні підмережі.")
r.step("Проксі не бачить БД, app бачить обидва сегменти", "wget db з proxy; ip addr у netns proxy та app; getent hosts", E + "22-segmentation.txt",
       "Із proxy ім'я db не резолвиться; у proxy один інтерфейс (frontend), а в app два: eth0 (backend) і eth1 (frontend).", 40)
r.step("veth-пари", "cat /sys/class/net/eth0/iflink; ip link | grep veth", E + "12-veth.txt",
       "Значення iflink у контейнері (87 для proxy, 86 для app, 85 для db) дорівнює номеру veth-інтерфейсу на хості — так зіставляються кінці пари; на схемі це лінії «veth».")
r.step("Псевдоніми та балансування", "docker compose up -d --scale app=2; dig +short app; curl localhost:8080 ×6", E + "23-scale.txt",
       "DNS повертає дві адреси репліки app, а в відповідях з'являються різні instance. Розподіл нерівномірний: це DNS round-robin, а не балансувальник; "
       "nginx для цього перерезолвить ім'я (resolver 127.0.0.11).", 40)
r.step("Healthcheck і depends_on", "docker compose stop; docker compose up -d proxy", E + "24-health.txt",
       "Після зупинки всіх сервісів запуск proxy автоматично піднімає db, чекає healthy, потім app, і тільки потім proxy: працює depends_on з condition: service_healthy.", 40)

r.h2("Порівняння мережевих режимів bridge, host, none")
r.step("Один і той самий контейнер у трьох режимах", "docker run --network bridge|host|none nicolaka/netshoot ip addr; ping 1.1.1.1", E + "14-drivers.txt",
       "У bridge є eth0 з адресою підмережі і вихід назовні; у host контейнер бачить інтерфейси хоста; у none лише lo і немає зовнішньої мережі.", 45)
r.table(["Режим", "Інтерфейси", "IP-адреса", "Доступ назовні", "Публікація портів"],
        [["bridge", "lo, eth0 (veth)", "з підмережі моста", "так (NAT)", "так (-p, DNAT)"],
         ["host", "усі інтерфейси хоста", "адреса хоста", "так", "не потрібна (порт відкривається на хості)"],
         ["none", "тільки lo", "немає", "ні", "ні (docker port порожній)"]], [2, 3.5, 3, 3, 4.5])

r.h1("3. Конфігураційні файли та код")
for name in ["docker-compose.yml", "app/Dockerfile", "app/app.py", "nginx.conf", "run_cli.sh"]:
    r.code(open(name, encoding="utf-8").read().rstrip(), name)

r.h1("4. Висновки")
r.p("Побудовано ізольовану bridge-мережу з проксі, застосунком і БД; доведено роботу вбудованого DNS Docker, ізоляцію "
    "між мережами та публікацію лише одного порту через NAT. Дослідження netns, veth-пар і мосту br-<id> показало, що контейнерна "
    "мережа базується на Linux namespaces, veth і bridge. Сегментація frontend/backend ховає БД від проксі, "
    "healthcheck із depends_on задає правильний порядок запуску, а DNS-псевдонім дозволяє масштабувати app без зміни конфігурації. "
    "Топологія повністю відтворюється командою docker compose up -d.")
r.p("Підпис виконавця: ____________      Підпис викладача: ____________")
print(r.build())
