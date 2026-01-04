# coding: utf-8

from yt_dlp.extractor.common import InfoExtractor
import json
import re
from urllib.parse import urlparse, urljoin, unquote

from yt_dlp.utils import (
    int_or_none,
    qualities,
)

# Loads episodes list
class AnistarShowsIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?(anistar\.org|v\d+\.astar\.bz)/(?P<id>\d+)[-\w]+\.html'

    _TESTS = [
        {
            'url': 'https://anistar.org/10691-reinkarnaciya-aristokrata-blagoslovennyy-s-rozhdeniya-velichayshey-siloy-kizoku-tensei-megumareta-umare-kara-saikyou-no-chikara-wo-eru.html',
            'info_dict': {
                'id': '10691',
            },
            'params': {
                'skip_download': True,
            },
        },
    ]

    def get_season_number(self, season: str) -> int:
        if season.__contains__('первый'): return 1
        if season.__contains__('второй'): return 2
        if season.__contains__('третий'): return 3
        if season.__contains__('четвёртый'): return 4
        if season.__contains__('пятый'): return 5
        if season.__contains__('шестой'): return 6
        if season.__contains__('седьмой'): return 7
        if season.__contains__('восьмой'): return 8
        if season.__contains__('девятый'): return 9
        return 0

    def _js_to_json(self, js_string: str) -> str:
        """Convert JavaScript object/array to valid JSON"""
        # First pass: remove comments while preserving strings
        result = []
        i = 0
        in_string = False
        string_char = None
        
        # Remove comments, but preserve strings
        while i < len(js_string):
            char = js_string[i]
            prev_char = js_string[i-1] if i > 0 else None
            
            # Track string boundaries
            if char in ("'", '"'):
                # Check if this is an escaped quote
                escape_count = 0
                j = i - 1
                while j >= 0 and js_string[j] == '\\':
                    escape_count += 1
                    j -= 1
                # If even number of backslashes, quote is not escaped
                if escape_count % 2 == 0:
                    if not in_string:
                        in_string = True
                        string_char = char
                        result.append(char)
                    elif char == string_char:
                        in_string = False
                        string_char = None
                        result.append(char)
                    else:
                        result.append(char)
                else:
                    result.append(char)
            elif not in_string:
                # Outside string - check for comments
                if i < len(js_string) - 1 and js_string[i:i+2] == '//':
                    # Single-line comment - skip to end of line
                    while i < len(js_string) and js_string[i] != '\n':
                        i += 1
                    if i < len(js_string):
                        result.append('\n')  # Preserve newline
                    continue
                elif i < len(js_string) - 1 and js_string[i:i+2] == '/*':
                    # Multi-line comment - skip to */
                    i += 2
                    while i < len(js_string) - 1:
                        if js_string[i:i+2] == '*/':
                            i += 1  # Will be incremented again
                            break
                        i += 1
                    continue
                else:
                    result.append(char)
            else:
                # Inside string - preserve everything
                result.append(char)
            
            i += 1
        
        js_string = ''.join(result)
        
        # Remove trailing commas before closing braces/brackets
        js_string = re.sub(r',\s*}', '}', js_string)
        js_string = re.sub(r',\s*]', ']', js_string)
        
        # Second pass: convert to JSON (normalize quotes, fix keys, handle booleans)
        result = []
        i = 0
        in_string = False
        string_char = None
        
        while i < len(js_string):
            char = js_string[i]
            prev_char = js_string[i-1] if i > 0 else None
            
            # Handle string delimiters
            if char in ("'", '"'):
                escape_count = 0
                j = i - 1
                while j >= 0 and js_string[j] == '\\':
                    escape_count += 1
                    j -= 1
                if escape_count % 2 == 0:  # Not escaped
                    if not in_string:
                        in_string = True
                        string_char = char
                        result.append('"')  # Always use double quotes
                    elif char == string_char:
                        in_string = False
                        string_char = None
                        result.append('"')
                    else:
                        result.append(char)
                else:
                    result.append(char)
            elif in_string:
                # Inside string - preserve content and escape control characters
                if char == '"' and string_char == "'":
                    # Converting single-quoted to double-quoted, escape internal double quotes
                    result.append('\\"')
                elif char == '\\':
                    # Preserve escape sequences
                    result.append(char)
                    if i + 1 < len(js_string):
                        i += 1
                        result.append(js_string[i])
                elif ord(char) < 32:  # Control characters
                    # Escape control characters
                    if char == '\n':
                        result.append('\\n')
                    elif char == '\r':
                        result.append('\\r')
                    elif char == '\t':
                        result.append('\\t')
                    else:
                        # Other control characters - escape as \uXXXX
                        result.append(f'\\u{ord(char):04x}')
                else:
                    result.append(char)
            else:
                # Outside string - check for unquoted keys and boolean/null values
                if char == 't' and js_string[i:i+4] == 'true' and (i+4 >= len(js_string) or not (js_string[i+4].isalnum() or js_string[i+4] == '_')):
                    result.append('true')
                    i += 3
                elif char == 'f' and js_string[i:i+5] == 'false' and (i+5 >= len(js_string) or not (js_string[i+5].isalnum() or js_string[i+5] == '_')):
                    result.append('false')
                    i += 4
                elif char == 'n' and js_string[i:i+4] == 'null' and (i+4 >= len(js_string) or not (js_string[i+4].isalnum() or js_string[i+4] == '_')):
                    result.append('null')
                    i += 3
                elif (char.isalpha() or char == '_'):
                    # Check for unquoted keys
                    match = re.match(r'([a-zA-Z_][a-zA-Z0-9_]*)\s*:', js_string[i:])
                    if match:
                        lookback_pos = i - 1
                        while lookback_pos >= 0 and js_string[lookback_pos] in ' \t\n\r':
                            lookback_pos -= 1
                        
                        is_unquoted = False
                        if lookback_pos < 0:
                            is_unquoted = True
                        elif js_string[lookback_pos] == '"':
                            quote_end = lookback_pos + 1
                            while quote_end < len(js_string) and quote_end < i and js_string[quote_end] in ' \t\n\r':
                                quote_end += 1
                            if quote_end < len(js_string) and js_string[quote_end] == ':':
                                is_unquoted = False
                            else:
                                is_unquoted = True
                        elif js_string[lookback_pos] in '{[,':
                            is_unquoted = True
                        
                        if is_unquoted:
                            key = match.group(1)
                            result.append(f'"{key}"')
                            i += len(key)
                            while i < len(js_string) and js_string[i] in ' \t\n\r':
                                result.append(js_string[i])
                                i += 1
                            if i < len(js_string) and js_string[i] == ':':
                                result.append(':')
                                i += 1
                            continue
                    else:
                        result.append(char)
                else:
                    result.append(char)
            
            i += 1
        
        return ''.join(result)

    def _get_user_agent(self):
        """Get user-agent from config or use default"""
        default_ua = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:146.0) Gecko/20100101 Firefox/146.0'
        http_headers = self.get_param('http_headers', {})
        if http_headers and 'User-Agent' in http_headers:
            return http_headers['User-Agent']
        return default_ua

    def _get_headers(self, referer=None):
        """Get HTTP headers with user-agent and optional referer"""
        headers = {}
        http_headers = self.get_param('http_headers', {})
        if http_headers:
            headers.update(http_headers)
        
        # Ensure user-agent is set
        if 'User-Agent' not in headers:
            headers['User-Agent'] = self._get_user_agent()
        
        if referer:
            # Extract root URL (scheme + netloc) from referer if it's a full URL
            parsed_referer = urlparse(referer)
            referer_root = f"{parsed_referer.scheme}://{parsed_referer.netloc}"
            headers['Referer'] = referer_root
        
        return headers
    
    def _download_webpage_with_headers(self, url, video_id, note, referer=None):
        """Download webpage with proper headers"""
        headers = self._get_headers(referer=referer or url)
        # Debug: print headers before request
        print(f'[DEBUG] Requesting URL: {url}')
        print(f'[DEBUG] Headers: {headers}')
        # Use _request_webpage which accepts headers parameter
        urlh = self._request_webpage(url, video_id, note, headers=headers)
        return self._webpage_read_content(urlh, url, video_id)

    def _real_extract(self, url):
        parsed_url = urlparse(url)
        _BASE_URL = f"{parsed_url.scheme}://{parsed_url.netloc}"
        
        video_id = self._match_id(url)
        
        # Download with headers
        webpage = self._download_webpage_with_headers(url, video_id, 'Downloading requested URL', referer=url)

        print(f'[DEBUG] step 0')

        # Extract news block
        news_block = self._html_search_regex(
            r'<div[^>]*class=["\']news["\'][^>]*itemscope[^>]*>(.+?)</div>\s*</div>',
            webpage, 'news_block', fatal=False, flags=re.DOTALL
        )

        print(f'[DEBUG] step 1')

        if not news_block:
            # Try without closing div
            news_block = self._html_search_regex(
                r'<div[^>]*class=["\']news["\'][^>]*itemscope[^>]*>(.+?)(?=</div>\s*<div|$)',
                webpage, 'news_block', fatal=False, flags=re.DOTALL
            )

        print(f'[DEBUG] step 2')
        
        # Extract title from <div class="title_left"><h1 itemprop="name">...</h1>
        title = self._html_search_regex(
            r'<div[^>]*class=["\']title_left["\'][^>]*>\s*<h1[^>]*itemprop=["\']name["\'][^>]*>(.+?)</h1>',
            webpage, 'title', fatal=False
        )

        print(f'[DEBUG] step 3')

        if not title:
            # Fallback to other methods
            title = self._html_search_regex(r'<h1[^>]*>\s*(.+?)\s*</h1>', webpage, 'title', fatal=False) or \
                self._og_search_title(webpage, default=None) or \
                self._html_search_regex(r'<title[^>]*>\s*(.+?)\s*</title>', webpage, 'title')
        
        if title:
            # Clean title - take part before '/' if exists
            title = title[:title.find('/')] if '/' in title else title
            title = title.strip()

        print(f'[DEBUG] title: {title}')
        if not title:
            raise Exception('Не удалось найти название (title) тайтла на странице.')

        # Extract metadata from news block if available
        if news_block:
            # Extract year
            release_year = self._html_search_regex(
                r'<[^>]*>Год[^<]*:</[^>]*>\s*<[^>]*>(\d+?)</[^>]*>', 
                news_block, 'release_year', fatal=False
            )
            if not release_year:
                release_year = self._html_search_regex(
                    r'Год[^:]*:\s*(\d+?)', 
                    news_block, 'release_year', fatal=False
                )
            
            # Extract type
            anime_type = self._html_search_regex(
                r'<[^>]*>Тип[^<]*:</[^>]*>\s*<[^>]*>([^<]+?)</[^>]*>', 
                news_block, 'anime_type', fatal=False
            )
            if not anime_type:
                anime_type = self._html_search_regex(
                    r'Тип[^:]*:\s*([^<\n]+?)', 
                    news_block, 'anime_type', fatal=False
                )
            if anime_type:
                anime_type = anime_type.strip()
            
            # Extract series count
            series_count_str = self._html_search_regex(
                r'<[^>]*>Серий[^<]*:</[^>]*>\s*<[^>]*>([^<]+?)</[^>]*>', 
                news_block, 'series_count', fatal=False
            )
            if not series_count_str:
                series_count_str = self._html_search_regex(
                    r'Серий[^:]*:\s*([^<\n]+?)', 
                    news_block, 'series_count', fatal=False
                )
            
            # Extract genres
            genres_str = self._html_search_regex(
                r'<[^>]*>Жанр[^<]*:</[^>]*>\s*<[^>]*>([^<]+?)</[^>]*>', 
                news_block, 'genres', fatal=False
            )
            if not genres_str:
                genres_str = self._html_search_regex(
                    r'Жанр[^:]*:\s*([^<\n]+?)', 
                    news_block, 'genres', fatal=False
                )
            
            # Extract description
            description = self._html_search_regex(
                r'<[^>]*>Описание[^<]*:</[^>]*>\s*<[^>]*>(.+?)</[^>]*>', 
                news_block, 'description', fatal=False, flags=re.DOTALL
            )
            if not description:
                description = self._html_search_regex(
                    r'<div[^>]*class=["\'][^"\']*description[^"\']*["\'][^>]*>(.+?)</div>', 
                    news_block, 'description', fatal=False, flags=re.DOTALL
                )
            if not description:
                # Try itemprop="description"
                description = self._html_search_regex(
                    r'<[^>]*itemprop=["\']description["\'][^>]*>(.+?)</[^>]*>', 
                    news_block, 'description', fatal=False, flags=re.DOTALL
                )
        else:
            # Fallback: extract from full page
            release_year = self._html_search_regex(
                r'<[^>]*>Год[^<]*:</[^>]*>\s*<[^>]*>(\d+?)</[^>]*>', 
                webpage, 'release_year', fatal=False
            )
            if not release_year:
                release_year = self._html_search_regex(
                    r'Год[^:]*:\s*(\d+?)', 
                    webpage, 'release_year', fatal=False
                )
            
            anime_type = self._html_search_regex(
                r'<[^>]*>Тип[^<]*:</[^>]*>\s*<[^>]*>([^<]+?)</[^>]*>', 
                webpage, 'anime_type', fatal=False
            )
            if not anime_type:
                anime_type = self._html_search_regex(
                    r'Тип[^:]*:\s*([^<\n]+?)', 
                    webpage, 'anime_type', fatal=False
                )
            if anime_type:
                anime_type = anime_type.strip()
            
            series_count_str = self._html_search_regex(
                r'<[^>]*>Серий[^<]*:</[^>]*>\s*<[^>]*>([^<]+?)</[^>]*>', 
                webpage, 'series_count', fatal=False
            )
            if not series_count_str:
                series_count_str = self._html_search_regex(
                    r'Серий[^:]*:\s*([^<\n]+?)', 
                    webpage, 'series_count', fatal=False
                )
            
            genres_str = self._html_search_regex(
                r'<[^>]*>Жанр[^<]*:</[^>]*>\s*<[^>]*>([^<]+?)</[^>]*>', 
                webpage, 'genres', fatal=False
            )
            if not genres_str:
                genres_str = self._html_search_regex(
                    r'Жанр[^:]*:\s*([^<\n]+?)', 
                    webpage, 'genres', fatal=False
                )
            
            description = self._html_search_regex(
                r'<[^>]*>Описание[^<]*:</[^>]*>\s*<[^>]*>(.+?)</[^>]*>', 
                webpage, 'description', fatal=False, flags=re.DOTALL
            )
            if not description:
                description = self._html_search_regex(
                    r'<div[^>]*class=["\'][^"\']*description[^"\']*["\'][^>]*>(.+?)</div>', 
                    webpage, 'description', fatal=False, flags=re.DOTALL
                )
        
        playlist_count = 0
        if series_count_str:
            # Extract number from strings like "12+", "12", "1-13 из 13"
            series_match = re.search(r'(\d+)', series_count_str)
            if series_match:
                playlist_count = int_or_none(series_match.group(1))
        
        genres = []
        if genres_str:
            genres = [g.strip() for g in genres_str.split(',') if g.strip()]
        
        if description:
            # Clean HTML tags from description
            description = description.replace('<br>', '\n').replace('<br />', '\n').replace('<br/>', '\n')
            description = re.sub(r'<[^>]+>', '', description)
            description = re.sub(r'\n\s*\n+', '\n\n', description)
            description = description.strip()
        else:
            description = title or ''

        # Extract thumbnail
        thumbnail = self._og_search_thumbnail(webpage, default=None)
        if not thumbnail:
            # Try to find in news block
            if news_block:
                thumbnail = self._html_search_regex(
                    r'<img[^>]*src=["\']([^"\']+)["\']', 
                    news_block, 'thumbnail', fatal=False
                )
        if not thumbnail:
            thumbnail = self._html_search_regex(
                r'<img[^>]*class=["\'][^"\']*poster[^"\']*["\'][^>]*src=["\']([^"\']+)["\']', 
                webpage, 'thumbnail', fatal=False
            )
        if not thumbnail:
            thumbnail = self._html_search_regex(
                r'<img[^>]*src=["\']([^"\']*poster[^"\']*)["\']', 
                webpage, 'thumbnail', fatal=False
            )
        if thumbnail:
            # Convert relative URL to absolute
            if thumbnail.startswith('/'):
                thumbnail = _BASE_URL + thumbnail
            elif not thumbnail.startswith('http'):
                thumbnail = _BASE_URL + '/' + thumbnail

        season = None
        season_number = 0

        if title:
            season_re = re.search(r'\s+\((\w+)\s+сезон\)', title)
            if season_re:
                season = season_re[0].strip().strip('()')
                season_number = self.get_season_number(season)
                title = title.replace(season_re[0], '').strip()

        if title and len(title) > 90:
            print('Title too long and would be trimmed: ', title)
            title = title[:90]
            title = title[:title.rfind(' ')]

        # Try to extract episodes data from playlist
        # Playlist is returned by /test/player2/videoas.php request
        # First, find videoas.php link on the main page
        videoas_url = None
        
        # Try to find full path in iframe src in JavaScript
        videoas_match = self._search_regex(
            r'videoas\.php\?([^"\'\s\)]+)',
            webpage, 'videoas_params', fatal=False
        )
        if videoas_match:
            videoas_url = '/test/player2/videoas.php?' + videoas_match
        
        # Also try to find in iframe src attribute
        if not videoas_url:
            videoas_match = self._search_regex(
                r'<iframe[^>]*src=["\']([^"\']*videoas\.php[^"\']*)["\']',
                webpage, 'videoas_url', fatal=False
            )
            if videoas_match:
                parsed_videoas = urlparse(videoas_match)
                if parsed_videoas.path:
                    videoas_url = parsed_videoas.path
                    if parsed_videoas.query:
                        videoas_url += '?' + parsed_videoas.query
                elif parsed_videoas.query:
                    videoas_url = '/test/player2/videoas.php?' + parsed_videoas.query
        
        print(f'[DEBUG] videoas_url for playlist: {videoas_url}')
        
        episodes_list = []
        
        # Download videoas.php to get playlist
        if videoas_url:
            # Make absolute URL if relative
            if not videoas_url.startswith('http'):
                if videoas_url.startswith('/'):
                    videoas_url_full = _BASE_URL + videoas_url
                else:
                    videoas_url_full = urljoin(_BASE_URL, videoas_url)
            else:
                videoas_url_full = videoas_url
            
            # Download videoas.php page
            videoas_page = self._download_webpage_with_headers(
                videoas_url_full,
                video_id, 'Downloading videoas.php for playlist', referer=url)
            
            print(f'[DEBUG] videoas_page length: {len(videoas_page)}')
            
            # Extract playlst from videoas.php
            # Playlst format: [{title: "Серия 1", media_id: "57781", file: "url"}, ...]
            # Note: it's 'playlst' not 'playlist'
            # Find the start of the array
            playlst_match = re.search(r'var\s+playlst\s*=\s*\[', videoas_page, re.DOTALL)
            if not playlst_match:
                playlst_match = re.search(r'playlst\s*[:=]\s*\[', videoas_page, re.DOTALL)
            if not playlst_match:
                # Try 'playlist' (with 't')
                playlst_match = re.search(r'var\s+playlist\s*=\s*\[', videoas_page, re.DOTALL)
            
            if playlst_match:
                # Extract from the opening bracket to the matching closing bracket
                start_pos = playlst_match.end() - 1  # Position of '['
                bracket_count = 0
                in_string = False
                string_char = None
                i = start_pos
                
                while i < len(videoas_page):
                    char = videoas_page[i]
                    prev_char = videoas_page[i-1] if i > 0 else None
                    
                    # Track string boundaries
                    if char in ("'", '"') and prev_char != '\\':
                        if not in_string:
                            in_string = True
                            string_char = char
                        elif char == string_char:
                            in_string = False
                            string_char = None
                    elif not in_string:
                        if char == '[':
                            bracket_count += 1
                        elif char == ']':
                            bracket_count -= 1
                            if bracket_count == 0:
                                # Found matching closing bracket
                                playlist_json = videoas_page[start_pos:i+1]
                                break
                    i += 1
                else:
                    playlist_json = None
            else:
                playlist_json = None
            
            if playlist_json:
                try:
                    # Convert JavaScript object to valid JSON
                    cleaned_json = self._js_to_json(playlist_json)
                    episodes_list = json.loads(cleaned_json)
                    if not isinstance(episodes_list, list):
                        # If it's a dict, convert to list
                        if isinstance(episodes_list, dict):
                            episodes_list = list(episodes_list.values())
                    print(f'[DEBUG] Found {len(episodes_list)} episodes in playlist')
                except (json.JSONDecodeError, ValueError) as e:
                    print(f'[DEBUG] Failed to parse playlist JSON: {e}')
                    print(f'[DEBUG] playlist_json: {playlist_json}')
                    print(f'[DEBUG] cleaned_json: {cleaned_json if "cleaned_json" in locals() else "N/A"}')
        
        # Fallback: try to find playlst directly on main page
        if not episodes_list:
            # Find the start of the array using the same approach
            playlst_match = re.search(r'var\s+playlst\s*=\s*\[', webpage, re.DOTALL)
            if not playlst_match:
                playlst_match = re.search(r'playlst\s*[:=]\s*\[', webpage, re.DOTALL)
            if not playlst_match:
                # Try 'playlist' (with 't')
                playlst_match = re.search(r'var\s+playlist\s*=\s*\[', webpage, re.DOTALL)
            
            if playlst_match:
                # Extract from the opening bracket to the matching closing bracket
                start_pos = playlst_match.end() - 1  # Position of '['
                bracket_count = 0
                in_string = False
                string_char = None
                i = start_pos
                
                while i < len(webpage):
                    char = webpage[i]
                    prev_char = webpage[i-1] if i > 0 else None
                    
                    # Track string boundaries
                    if char in ("'", '"') and prev_char != '\\':
                        if not in_string:
                            in_string = True
                            string_char = char
                        elif char == string_char:
                            in_string = False
                            string_char = None
                    elif not in_string:
                        if char == '[':
                            bracket_count += 1
                        elif char == ']':
                            bracket_count -= 1
                            if bracket_count == 0:
                                # Found matching closing bracket
                                playlist_json = webpage[start_pos:i+1]
                                break
                    i += 1
                else:
                    playlist_json = None
            else:
                playlist_json = None
            
            if playlist_json:
                try:
                    # Convert JavaScript object to valid JSON
                    cleaned_json = self._js_to_json(playlist_json)
                    episodes_list = json.loads(cleaned_json)
                    if not isinstance(episodes_list, list):
                        if isinstance(episodes_list, dict):
                            episodes_list = list(episodes_list.values())
                except (json.JSONDecodeError, ValueError) as e:
                    print(f'[DEBUG] Failed to parse playlist JSON from main page: {e}')
                    pass
        
        # Fallback: try old format (var data = {...})
        if not episodes_list:
            episodes_json = self._search_regex(
                r'var\s+data\s*=\s*(\{.*?\});', 
                webpage, 'episodes', fatal=False, flags=re.DOTALL
            )
            if episodes_json:
                try:
                    episodes_dict = json.loads(episodes_json.replace(',}', '}'))
                    # Convert dict to list format
                    for episode_key, episode_value in episodes_dict.items():
                        episodes_list.append({
                            'title': episode_key,
                            'media_id': episode_value if isinstance(episode_value, str) else str(episode_value),
                            'file': None,
                            'ext': 'mp4',
                            'ie': AnistarIE.ie_key(),
                            'episode_number': int_or_none(episode_key),
                            'release_year': int_or_none(release_year)
                        })
                except (json.JSONDecodeError, ValueError):
                    pass

        entries = []
        for episode_data in episodes_list:
            if isinstance(episode_data, dict):
                episode_title = episode_data.get('title', '')
                episode_id = episode_data.get('media_id', '')
                episode_file = episode_data.get('file', '')
            else:
                # Fallback for old format
                episode_title = str(episode_data) if not isinstance(episode_data, dict) else ''
                episode_id = ''
                episode_file = None

            if not episode_title and not episode_id:
                continue

            # Extract episode number from title
            episode_num = None
            if episode_title:
                episode_match = re.search(r'(\d+)', episode_title)
                if episode_match:
                    episode_num = int_or_none(episode_match.group(1))
            
            # Use media_id as episode_id if available
            if not episode_id:
                episode_id = episode_title or str(len(entries) + 1)
            
            # Construct episode URL from file or use media_id
            episode_url = None
            if episode_file:
                episode_url = episode_file
            elif episode_id:
                # Construct URL from media_id - need to determine the pattern
                # This might need adjustment based on actual URL structure
                episode_url = f"{_BASE_URL}/player/{video_id}/{episode_id}"

            # If episode_url is relative, make it absolute
            if episode_url:
                if not episode_url.startswith('http'):
                    if episode_url.startswith('/'):
                        episode_url = _BASE_URL + episode_url
                    else:
                        episode_url = _BASE_URL + '/' + episode_url
            else:
                # Skip if no URL available
                continue

            series = title or 'Anime'
            if season:
                series = f"{title} [{season}]"

            series_full = series
            if release_year:
                series_full = f"{series} ({release_year})"

            episode_display_title = episode_title or f"{episode_num} серия" if episode_num else "серия"
            episode_full_title = f"{series} {episode_display_title}"

            entries.append({
                'id': episode_id,
                'title': episode_full_title,
                '_type': 'url_transparent',
                'url': episode_url,
                #'ie': AnistarIE.ie_key(),
                'ext': 'mp4',
                'display_id': video_id + '-' + (episode_title or episode_id),
                'series': series_full,
                'season': season,
                'season_number': season_number,
                'episode_number': episode_num,
                'release_year': int_or_none(release_year)
            })

        playlist_count = max(len(entries), int_or_none(playlist_count))
        res = {
            'id': video_id,
            'title': title or 'Anime',
            'description': description,
            'url': url,
            'entries': entries,
            'playlist_count': playlist_count,
            '_type': 'playlist',
        }
        
        # Add extracted metadata
        if release_year:
            res['release_year'] = int_or_none(release_year)
        if anime_type:
            res['type'] = anime_type
        if genres:
            res['genres'] = genres
        if thumbnail:
            res['thumbnail'] = thumbnail
        
        print(f'[DEBUG] res: {res}')
        return res

# Matches episode
class AnistarIE(InfoExtractor):
    IE_NAME = 'anistar:player'
    IE_DESC = 'anistar.org Player'

    _VALID_URL = r'https?://(?:www\.)?(anistar\.org|v\d+\.astar\.bz)/.*/playlist_hls.php/.*'

    _TESTS = [
        {
            'note': 'episode player',
            'url': 'https://anistar.org/player/10691/1',
            'info_dict': {
                'id': '10691-1',
            }
        },
    ]

    def _get_user_agent(self):
        """Get user-agent from config or use default"""
        default_ua = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:142.0) Gecko/20100101 Firefox/146.0'
        http_headers = self.get_param('http_headers', {})
        if http_headers and 'User-Agent' in http_headers:
            return http_headers['User-Agent']
        return default_ua

    def _get_headers(self, referer=None):
        """Get HTTP headers with user-agent and optional referer"""
        headers = {}
        http_headers = self.get_param('http_headers', {})
        if http_headers:
            headers.update(http_headers)
        
        # Ensure user-agent is set
        if 'User-Agent' not in headers:
            headers['User-Agent'] = self._get_user_agent()
        
        if referer:
            # Extract root URL (scheme + netloc) from referer if it's a full URL
            parsed_referer = urlparse(referer)
            referer_root = f"{parsed_referer.scheme}://{parsed_referer.netloc}"
            headers['Referer'] = referer_root
        
        return headers
    
    def _download_webpage_with_headers(self, url, video_id, note, referer=None):
        """Download webpage with proper headers"""
        headers = self._get_headers(referer=referer or url)
        # Debug: print headers before request
        print(f'[DEBUG] Requesting URL: {url}')
        print(f'[DEBUG] Headers: {headers}')
        # Use _request_webpage which accepts headers parameter
        urlh = self._request_webpage(url, video_id, note, headers=headers)
        return self._webpage_read_content(urlh, url, video_id)

    def _extract_hls_url_from_m3u8(self, m3u8_content):
        """Extract HLS stream URL from M3U8 playlist"""
        # Look for URLs in the M3U8 content
        # Usually it's a line starting with http:// or https://
        # Format: https://sfv.an-media.org/key=.../media=hls/video/...
        lines = m3u8_content.split('\n')
        for line in lines:
            line = line.strip()
            if line and (line.startswith('http://') or line.startswith('https://')):
                # Skip comments
                if not line.startswith('#'):
                    # Prefer URLs with /media=hls/ or /key= pattern
                    if '/media=hls/' in line or '/key=' in line:
                        return line
        # Fallback: return first valid URL
        for line in lines:
            line = line.strip()
            if line and (line.startswith('http://') or line.startswith('https://')):
                if not line.startswith('#'):
                    return line
        return None

    def _real_extract(self, url):
        parsed_url = urlparse(url)
        _BASE_URL = f"{parsed_url.scheme}://{parsed_url.netloc}"
        
        video_id = parsed_url.path.split('/')[-1] if parsed_url.path else 'unknown'
        
        # Try to extract from URL pattern like /player/10691/1
        path_parts = [p for p in parsed_url.path.split('/') if p]
        if len(path_parts) >= 2:
            video_id = f"{path_parts[-2]}-{path_parts[-1]}"

        # Download page with headers
        webpage = self._download_webpage_with_headers(
            url,
            video_id, 'Downloading episode page', referer=url)

        formats = []
        quality = qualities(['sd', 'hd', 'fullhd'])

        # First, find videoas.php link in JavaScript code
        # Look for: jQuery("#vid_2").html('<iframe src="/test/player2/videoas.php?id=...&hash=..." ...')
        videoas_url = None
        
        # Try to find full path in iframe src
        videoas_match = self._search_regex(
            r'<iframe[^>]*src=["\']([^"\']*videoas\.php[^"\']*)["\']',
            webpage, 'videoas_url', fatal=False
        )
        if videoas_match:
            # Extract path and query
            parsed_videoas = urlparse(videoas_match)
            if parsed_videoas.path:
                videoas_url = parsed_videoas.path
                if parsed_videoas.query:
                    videoas_url += '?' + parsed_videoas.query
            elif parsed_videoas.query:
                # Only query parameters found, construct full path
                videoas_url = '/test/player2/videoas.php?' + parsed_videoas.query
        
        if not videoas_url:
            # Try to find just query parameters in JavaScript
            videoas_params = self._search_regex(
                r'videoas\.php\?([^"\'\s\)]+)',
                webpage, 'videoas_params', fatal=False
            )
            if videoas_params:
                videoas_url = '/test/player2/videoas.php?' + videoas_params
        
        print(f'[DEBUG] videoas_url: {videoas_url}')
        
        # If found videoas.php, download it and look for playlist_hls.php there
        playlist_hls_url = None
        if videoas_url:
            # Make absolute URL if relative
            if not videoas_url.startswith('http'):
                if videoas_url.startswith('/'):
                    videoas_url_full = _BASE_URL + videoas_url
                else:
                    videoas_url_full = urljoin(_BASE_URL, videoas_url)
            else:
                videoas_url_full = videoas_url
            
            # Download videoas.php page
            videoas_page = self._download_webpage_with_headers(
                videoas_url_full,
                video_id, 'Downloading videoas.php page', referer=url)
            
            print(f'[DEBUG] videoas_page length: {len(videoas_page)}')
            
            # Now look for playlist_hls.php in videoas.php page
            playlist_hls_url = self._search_regex(
                r'file:\s*["\']([^"\']*playlist_hls\.php[^"\']*)["\']',
                videoas_page, 'playlist_hls', fatal=False
            )
            
            if not playlist_hls_url:
                # Try without file: prefix
                playlist_hls_url = self._search_regex(
                    r'["\']([^"\']*playlist_hls\.php[^"\']*)["\']',
                    videoas_page, 'playlist_hls', fatal=False
                )
            
            if not playlist_hls_url:
                # Try to find in JavaScript variables
                playlist_hls_url = self._search_regex(
                    r'(?:src|url|file)\s*[:=]\s*["\']([^"\']*playlist_hls\.php[^"\']*)["\']',
                    videoas_page, 'playlist_hls', fatal=False
                )
        
        # Fallback: try to find playlist_hls.php directly on the main page
        if not playlist_hls_url:
            playlist_hls_url = self._search_regex(
                r'file:\s*["\']([^"\']*playlist_hls\.php[^"\']*)["\']',
                webpage, 'playlist_hls', fatal=False
            )
        
        if not playlist_hls_url:
            # Try without file: prefix, but with full path
            playlist_hls_url = self._search_regex(
                r'["\']([^"\']*/(?:test/)?player2?/playlist_hls\.php[^"\']*)["\']',
                webpage, 'playlist_hls', fatal=False
            )

        print(f'[DEBUG] playlist_hls_url: {playlist_hls_url}')
        
        if playlist_hls_url:
            # Make absolute URL if relative
            if not playlist_hls_url.startswith('http'):
                if playlist_hls_url.startswith('/'):
                    playlist_hls_url = _BASE_URL + playlist_hls_url
                else:
                    playlist_hls_url = urljoin(_BASE_URL, playlist_hls_url)
            
            # First, try to extract HLS URLs from playlist_hls.php URL parameters
            # Example: /test/player2/playlist_hls.php?360=https%3A%2F%2F...&720=https%3A%2F%2F...
            hls_urls = {}
            parsed_playlist = urlparse(playlist_hls_url)
            if parsed_playlist.query:
                # Look for URLs in query parameters
                for param in parsed_playlist.query.split('&'):
                    if '=' in param:
                        key, value = param.split('=', 1)
                        # URL decode
                        decoded_value = unquote(value)
                        if decoded_value.startswith('http'):
                            # Extract quality from key (360, 720, etc.)
                            quality_match = re.search(r'(\d+)', key)
                            if quality_match:
                                quality_num = quality_match.group(1)
                                hls_urls[quality_num] = decoded_value
                            else:
                                hls_urls['default'] = decoded_value
            
            # If not found in parameters, download M3U8 playlist and extract from it
            if not hls_urls:
                m3u8_content = self._download_webpage_with_headers(
                    playlist_hls_url,
                    video_id, 'Downloading M3U8 playlist', referer=url)
                
                # Extract HLS stream URLs from M3U8 content
                # Look for different quality streams (360, 720, 1080)
                # Try to find URLs with quality indicators in the content
                for quality_name, quality_pattern in [('360', r'360[^"\'\s\)]*'), ('720', r'720[^"\'\s\)]*'), ('1080', r'1080[^"\'\s\)]*')]:
                    # Look for URLs containing quality number
                    quality_url = self._search_regex(
                        rf'(https?://[^\s"\']*{quality_pattern}[^\s"\']*)',
                        m3u8_content, f'{quality_name}p_url', fatal=False
                    )
                    if quality_url:
                        hls_urls[quality_name] = quality_url
                
                # If no quality-specific URLs found, try to extract any HLS URL
                if not hls_urls:
                    hls_url = self._extract_hls_url_from_m3u8(m3u8_content)
                    if hls_url:
                        hls_urls['default'] = hls_url
            
            # Create formats from HLS URLs
            for quality_key, hls_url in hls_urls.items():
                height = None
                if quality_key == '360':
                    height = 360
                    q = quality('sd')
                elif quality_key == '720':
                    height = 720
                    q = quality('hd')
                elif quality_key == '1080':
                    height = 1080
                    q = quality('fullhd')
                else:
                    q = None
                
                format_info = {
                    'url': hls_url,
                    'protocol': 'm3u8_native',
                    'ext': 'mp4',
                    'format_id': f'hls-{quality_key}p',
                }
                
                if height:
                    format_info['height'] = height
                if q:
                    format_info['quality'] = q
                
                # Set referer header
                format_info['http_headers'] = self._get_headers(referer=url)
                
                formats.append(format_info)

        if not formats:
            self.raise_no_formats('Could not find playlist_hls.php or HLS streams', video_id=video_id)

        return {
            'id': video_id,
            'formats': formats,
        }
