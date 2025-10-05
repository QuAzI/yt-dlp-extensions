FROM python:3.13

VOLUME /downloads

RUN pip install --upgrade yt-dlp

WORKDIR /app
COPY ./yt-dlp.conf ./
COPY ./ytdlp_plugins /etc/yt-dlp/plugins

CMD ["/usr/local/bin/yt-dlp"]
