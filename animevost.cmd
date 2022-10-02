@if "%1"=="--batch-file" goto :list-custom

@if "%1"=="" goto :list

@if "%2"=="" goto :source


:source-from-num

yt-dlp %1 --playlist-start %2 -o "%%(series)s\\%%(title)s [%%(id)s].%%(ext)s" --download-archive animevost-downloaded.list --no-check-certificates

@goto :done


:source


yt-dlp %1 -o "%%(series)s\\%%(title)s [%%(id)s].%%(ext)s" --download-archive animevost-downloaded.list --no-check-certificates

@goto :done


:list-custom

yt-dlp -o "%%(series)s\\%%(title)s [%%(id)s].%%(ext)s" --batch-file %2 --download-archive animevost-downloaded.list -I -24: --no-check-certificates

@goto :done


:list

yt-dlp -o "%%(series)s\\%%(title)s [%%(id)s].%%(ext)s" --batch-file animevost-batch.list --download-archive animevost-downloaded.list -I -24: --no-check-certificates


:done
