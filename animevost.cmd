@if "%1"=="--batch-file" goto :list-custom

@if "%1"=="" goto :list

@if "%2"=="" goto :source


:source-from-num

@rem -S "+height:480"
yt-dlp %1 --playlist-start %2

@goto :done


:source

yt-dlp %*

@goto :done


:list-custom

yt-dlp %*

@goto :done


:list

yt-dlp --batch-file animevost-batch.list -I -24:

:done
