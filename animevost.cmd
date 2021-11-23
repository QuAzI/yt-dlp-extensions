@if "%2"=="" goto :all

yt-dlp %1 --no-check-certificates --download-archive c:\bin\animevost-downloaded.list --playlist-start %2

@goto :done


:all

@if "%1"=="" goto :list

yt-dlp %1 --no-check-certificates --download-archive c:\bin\animevost-downloaded.list

@goto :done


:list

yt-dlp --batch-file c:\bin\animevost-batch.list --no-check-certificates --download-archive c:\bin\animevost-downloaded.list -o "%%(series)s\\%%(title)s [%%(id)s].%%(ext)s"
@rem default template: %(title)s [%(id)s].%(ext)s

:done
