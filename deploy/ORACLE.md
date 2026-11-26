# Oracle Cloud (Always Free) — орналастыру нұсқаулығы

Тек **тестілеу/демо** үшін. Клиенттің жұмыс сайты үшін ps.kz VPS ұсынылады.
`.kz` домені Oracle-ға жарамайды (сервер Қазақстанда болуы керек) — `.com` сияқты домен алыңыз.

## 1. Oracle аккаунты (өзіңіз жасайсыз)
1. https://www.oracle.com/cloud/free/ -> Start for free.
2. Карта растау сұралады. Home region кейін өзгертілмейді, сондықтан абайлап таңдаңыз.

## 2. Сервер құру
1. Menu -> Compute -> Instances -> Create instance.
2. Image: **Canonical Ubuntu 24.04** (ARM/aarch64 нұсқасы, A1 үшін).
3. Shape: Change shape -> Ampere -> **VM.Standard.A1.Flex**, **2 OCPU, 12 ГБ RAM** (Always Free-eligible). «Out of capacity» шықса, кейінірек қайталаңыз немесе E2.1.Micro алыңыз.
4. Networking: Public IPv4 address қосулы тұрсын.
5. SSH keys: **Save private key** басып, файлды сақтаңыз (қайта жүктелмейді).
6. Create. Дайын болған соң **Public IP** көшіріп алыңыз.

## 3. 80 және 443 порттарын ашу (Oracle панелінде)
Instance -> Subnet -> Security List -> Add Ingress Rules, екі рет:
Source CIDR `0.0.0.0/0`, IP Protocol TCP, Destination Port `80`, содан кейін `443`.
(Серверішіндегі iptables ережесін скрипт өзі ашады.)

## 4. Домен
Домен тіркеушісінде **A-жазба**: `@` (және қаласаңыз `www`) -> сервердің Public IP.

## 5. Серверге кіру (Windows PowerShell)
```
ssh -i C:\жол\ssh-key.key ubuntu@<PUBLIC_IP>
```

## 6. Кодты серверге алу
Репозиторий Private, сондықтан GitHub-та Personal Access Token жасаңыз
(Settings -> Developer settings -> Fine-grained tokens -> осы репозиторий, Contents: Read-only).
```
git clone https://github.com/ybraiymbaybagzhan-png/train_food_python.git
```
Username: GitHub логині, Password: токен.

## 7. Орнату
```
cd train_food_python
sed -i 's/\r$//' deploy/setup.sh
sudo DOMAIN=example.com EMAIL=you@mail.com bash deploy/setup.sh
```
Домен әлі жоқ болса, `DOMAIN` пен `EMAIL`-сіз іске қосыңыз: сайт `http://<PUBLIC_IP>/` бойынша ашылады.
Соңында admin / kitchen / staff құпиясөздері бір рет шығады — жазып алыңыз.

## 8. Тексеру
- Браузерде сайтты ашыңыз, `/login` арқылы admin-ға кіріңіз.
- Күй: `sudo systemctl status dar-res`
- Лог: `sudo journalctl -u dar-res -f`

## Жаңарту
```
cd ~/train_food_python && git pull && sudo bash deploy/setup.sh
```
База (`/opt/dar-res/train_food.db`) мен жүктелген суреттерге тиіспейді.

## Деректер
- Жергілікті базаңызды көшіру керек болса (GitHub-қа `*.db` жүктелмейді), өз компьютеріңізден:
  `scp -i key.key train_food.db ubuntu@<IP>:~/` содан кейін серверде:
  `sudo systemctl stop dar-res && sudo mv ~/train_food.db /opt/dar-res/ && sudo chown darres: /opt/dar-res/train_food.db && sudo systemctl start dar-res`
- Күнделікті көшірме: `/var/backups/dar-res` (соңғы 7 күн). Оны ара-тұра өз компьютеріңізге `scp` арқылы алып тұрыңыз.

## Ескертулер
- Oracle Always Free серверін жүктеме аз болса қайтарып алуы мүмкін, SLA жоқ. Көшірмені жиі алыңыз.
- Oracle-да Budget alert қойыңыз (мысалы 1 USD), ақылы ресурс таңдап алмаңыз.
- `--workers 1` өзгертпеңіз: WebSocket (/ws) қосылымдары процесс жадында сақталады.
