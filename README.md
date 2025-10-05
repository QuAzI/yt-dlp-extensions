Плагин для скачивания с animevost.org и Docker Compose

Обязательно создайте
- download.list - список для скачивания (просто список url)
- history.list - история id уже скачанных серий. Хотя бы пустой файл обязателен, иначе Docker Compose создаст директорию

Для ручного скачивания нужно скопировать `ytdlp_plugins\animevost\yt_dlp_plugins\extractor`
в `ytdlp_plugins` которая должна быть размещена рядом с yt-dlp
Например, для `c:\bin\yt-dlp.exe` создать `c:\bin\ytdlp_plugins` и скопировать `extractor` внутрь
