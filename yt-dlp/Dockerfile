FROM python:3.13

VOLUME /downloads

RUN pip install --upgrade yt-dlp
RUN python -m pip install "yt-dlp-animevost @ git+https://github.com/QuAzI/yt-dlp-extensions.git#subdirectory=yt-dlp-animevost"

WORKDIR /app
COPY ./yt-dlp.conf ./

ENTRYPOINT ["/usr/local/bin/yt-dlp"]
