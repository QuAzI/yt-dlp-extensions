set yt-dlp=d:\Projects\3rd-party\yt-dlp\yt-dlp.cmd

@if "%2"=="" goto :all

%yt-dlp% %1 --no-check-certificates --playlist-start %2 --download-archive c:\bin\animevost-downloaded.list
@rem -o "%%(series)s/%%(title)s.%%(ext)s"

@goto :done


:all

@if "%1"=="" goto :list

%yt-dlp% %1 --no-check-certificates --download-archive c:\bin\animevost-downloaded.list

@goto :done


:list

%yt-dlp% --batch-file c:\bin\animevost-batch.list --no-check-certificates --download-archive c:\bin\animevost-downloaded.list


:done
