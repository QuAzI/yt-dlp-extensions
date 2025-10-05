@if "%1"=="--batch-file" goto :list-custom

@if "%1"=="" goto :list

@if "%2"=="" goto :source


:source-from-num

yt-dlp --download-archive history.list %1 --playlist-start %2

@goto :done


:source

yt-dlp --download-archive history.list %*

@goto :done


:list-custom

yt-dlp --download-archive history.list %*

@goto :done


:list

@rem -S "+height:480"
yt-dlp --batch-file download.list -I -24: --download-archive history.list

:done
