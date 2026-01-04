FROM python:3.13

VOLUME /downloads

RUN pip install --upgrade yt-dlp

WORKDIR /app
COPY ./yt-dlp.conf ./

#was yt-dlp/ytdlp_plugins/animevost/yt_dlp_plugins/extractor/*
#COPY ./ytdlp_plugins /etc/yt-dlp/plugins

ENTRYPOINT ["/usr/local/bin/yt-dlp"]
