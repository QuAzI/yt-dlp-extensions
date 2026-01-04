# yt-dlp-extensions

Плагин для yt-dlp, позволяющий скачивать аниме с сайта [animevost.org](https://animevost.org) и его зеркал (animevost.am, vost.pw).

## Описание

Проект включает:
- **Плагин для yt-dlp** - кастомный экстрактор для animevost.org
- **Docker-контейнер** - автоматизированное скачивание через Docker Compose
- **Скрипты для ручного использования** - для Windows и Linux

Плагин поддерживает:
- Скачивание целых сериалов (плейлистов) по URL страницы аниме
- Скачивание отдельных эпизодов
- Автоматическое определение сезонов
- Поддержка качества 480p и 720p
- Сохранение метаданных: название сериала, номер эпизода, год выпуска, тип, жанры, режиссёр, описание, миниатюра

## Структура проекта

```
yt-dlp-extensions/
├── yt-dlp/                          # Docker-контейнер и конфигурация
│   ├── Dockerfile                   # Образ с yt-dlp и плагином
│   └── yt-dlp.conf                  # Конфигурация yt-dlp
├── yt-dlp-animevost/                # Плагин для установки через pip
│   ├── pyproject.toml               # Конфигурация пакета
│   └── yt_dlp_plugins/
│       ├── __init__.py
│       └── extractor/
│           └── animevost.py         # Основной код плагина
├── docker-compose.yml               # Docker Compose конфигурация
├── deployment.yml                   # Ansible playbook для развертывания
├── download.cmd                     # Скрипт для ручного скачивания (Windows)
└── README.md
```

## Установка и использование

### Установка через pip (рекомендуется)

Самый простой способ установки - через pip. Плагин будет автоматически зарегистрирован и готов к использованию:

```shell
python -m pip install "yt-dlp-animevost @ git+https://github.com/QuAzI/yt-dlp-extensions.git#subdirectory=yt-dlp-animevost"
```

После установки просто используйте yt-dlp как обычно - плагин будет автоматически загружен для URL animevost.org.

### Установка через Docker Compose

1. **Создайте необходимые файлы:**
   ```bash
   # Список URL для скачивания (по одному URL на строку)
   touch download.list
   
   # История скачанных эпизодов (может быть пустым, но файл обязателен)
   touch history.list
   ```

2. **Добавьте URL в `download.list`:**
   ```
   https://animevost.org/tip/tv/179-one-piece44.html
   https://animevost.org/tip/tv/385-blazblue-alter-memory.html
   ```

3. **Настройте путь для скачивания в `docker-compose.yml`:**
   ```yaml
   volumes:
     - /путь/к/папке/скачивания:/downloads
   ```

4. **Запустите скачивание:**
   ```bash
   docker-compose up
   ```

5. **Автоматический запуск по расписанию (crontab):**
   ```bash
   crontab -e
   ```
   Добавьте строку:
   ```crontab
   42 6,13,18,20,22 * * *  cd ~/server/animevost-downloader && docker-compose up
   ```

### Ручной запуск (Windows)

1. **Установите yt-dlp** (например, в `C:\bin\yt-dlp.exe`)

2. **Скопируйте плагин:**
   - Создайте папку `C:\bin\ytdlp_plugins\extractor`
   - Скопируйте файл `yt-dlp-animevost\yt_dlp_plugins\extractor\animevost.py` в `C:\bin\ytdlp_plugins\extractor\`

3. **Используйте скрипт `download.cmd`:**
   ```cmd
   download.cmd                    # Скачать из download.list
   download.cmd URL                # Скачать конкретный URL
   download.cmd URL номер_эпизода # Скачать с определенного эпизода
   ```

### Ручной запуск (Linux/Mac)

1. **Установите yt-dlp:**
   ```bash
   pip install --upgrade yt-dlp
   ```

2. **Скопируйте плагин:**
   ```bash
   mkdir -p ~/.local/share/yt-dlp/plugins/extractor
   cp yt-dlp-animevost/yt_dlp_plugins/extractor/animevost.py ~/.local/share/yt-dlp/plugins/extractor/
   ```

3. **Используйте yt-dlp:**
   ```bash
   yt-dlp --download-archive history.list "https://animevost.org/tip/tv/179-one-piece44.html"
   ```

## Развертывание через Ansible

Для автоматического развертывания на сервере используйте `deployment.yml`:

```bash
ansible-playbook deployment.yml
```

Playbook автоматически:
- Установит Docker
- Скопирует конфигурацию
- Настроит cron для автоматического скачивания

## Формат сохранения файлов

Файлы сохраняются в следующем формате:
```
/downloads/[Название сериала]/[Название сериала] [Номер эпизода] [ID].mp4
```

Например:
```
/downloads/Ван Пис/Ван Пис 1 [2147419615].mp4
```

## Поддерживаемые домены

- animevost.org
- animevost.am
- vost.pw (v*.vost.pw)

## Примечания

- Файл `history.list` обязателен для работы Docker Compose (даже если пустой), иначе будет создана директория вместо файла
- Плагин автоматически пропускает уже скачанные эпизоды благодаря `--download-archive`

