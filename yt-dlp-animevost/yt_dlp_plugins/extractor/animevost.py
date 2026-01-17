# coding: utf-8
from typing import Any

from yt_dlp.extractor.common import InfoExtractor
import json
import re
from urllib.parse import urlparse

from yt_dlp.utils import (
    int_or_none,
    qualities,
)

# Loads episodes list
class AnimeVostShowsIE(InfoExtractor):
    # _VALID_URL = r'https?://(?:www\.)?animevost\.(org|am)/tip/.*/(?P<id>\d+)[-\w+][^/]*'
    _VALID_URL = r'https?://(?:www\.)?(animevost\.org|animevost\.am|v\d+\.vost\.pw)/tip/.*/(?P<id>\d+)[-\w+][^/]*'

    _TESTS = [
        {
            'url': 'https://animevost.org/tip/tv/179-one-piece44.html',
            'info_dict': {
                'id': '179',
                'title': 'Ван Пис',
                'description': 'Ван Пис',
            },
            'playlist_count': 992,
            'params': {
                'skip_download': True,
            },
        },
        {
            'url': 'https://animevost.org/tip/polnometrazhnyy-film/1516-gekijouban-kyoukai-no-kanata-ill-be-here-mirai-hen.html',
            'only_matching': True,
        },
        {
            'url': 'https://animevost.org/tip/ona/886-suzumiya-haruhi-no-yuuutsu.html',
            'only_matching': True,
        },
        {
            'url': 'https://animevost.am/tip/tv/385-blazblue-alter-memory.html',
            'only_matching': True,
        },
        #{
        #    'url': 'https://a110.agorov.org/tip/tv/179-one-piece44.html',
        #    'only_matching': True,
        #},
        #{
        #    'url': 'https://animevost.org/tip/tv/page,1,7,253-zetsuen-no-tempest-the-civilization-blaster1.html',
        #    'only_matching': True,
        #}
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

    def _real_extract(self, url):
        #_BASE_URL = 'https://animevost.org'
        parsed_url = urlparse(url)
        _BASE_URL = f"{parsed_url.scheme}://{parsed_url.netloc}"
        
        _SHOWS_API_URL = '/frame5.php?play='

        video_id = self._match_id(url)
        
        webpage = self._download_webpage(url, video_id, 'Downloading requested URL')

        title = self._html_search_regex(r'<h1>\s*(.+?)\s*</h1>', webpage, 'title') or \
            self._og_search_title(webpage)

        title = title[:title.find('/')]  # beautify
        title = title.strip()

        # Extract year
        release_year = self._html_search_regex(
            r'<p><strong>Год выхода:\s*</strong>(\d+?)</p>', 
            webpage, 'release_year', fatal=False
        )
        
        # Extract type
        anime_type = self._html_search_regex(
            r'<p><strong>Тип:\s*</strong>([^<]+?)</p>', 
            webpage, 'anime_type', fatal=False
        )
        if anime_type:
            anime_type = anime_type.strip()
        
        # Extract series count
        series_count_str = self._html_search_regex(
            r'<p><strong>Количество серий:\s*</strong>([^<]+?)</p>', 
            webpage, 'series_count', fatal=False
        )
        playlist_count = 0
        if series_count_str:
            # Extract number from strings like "12+", "12", "1-13 из 13"
            series_match = re.search(r'(\d+)', series_count_str)
            if series_match:
                playlist_count = int_or_none(series_match.group(1))
        
        # Extract genres
        genres_str = self._html_search_regex(
            r'<p><strong>Жанр:\s*</strong>([^<]+?)</p>', 
            webpage, 'genres', fatal=False
        )
        genres = []
        if genres_str:
            genres = [g.strip() for g in genres_str.split(',') if g.strip()]
        
        # Extract director/author
        director = self._html_search_regex(
            r'<p\s*><strong>Режиссёр:\s*</strong><span[^>]*><a[^>]*>([^<]+?)</a></span></p>', 
            webpage, 'director', fatal=False
        )
        if not director:
            # Fallback: try without link
            director = self._html_search_regex(
                r'<p\s*><strong>Режиссёр:\s*</strong>([^<]+?)</p>', 
                webpage, 'director', fatal=False
            )
        if director:
            director = director.strip()
        
        # Extract description
        description = self._html_search_regex(
            r'<p><strong>Описание:\s*</strong><span[^>]*itemprop="description"[^>]*>(.+?)</span>', 
            webpage, 'description', fatal=False, flags=re.DOTALL
        )
        if not description:
            # Fallback: try without itemprop, but with span
            description = self._html_search_regex(
                r'<p><strong>Описание:\s*</strong><span[^>]*>(.+?)</span>', 
                webpage, 'description', fatal=False, flags=re.DOTALL
            )
        if not description:
            # Fallback: try without span
            description = self._html_search_regex(
                r'<p><strong>Описание:\s*</strong>([^<]+(?:<[^>]+>[^<]*</[^>]+>)*[^<]+?)</p>', 
                webpage, 'description', fatal=False, flags=re.DOTALL
            )
        if description:
            # Clean HTML tags from description, but preserve line breaks
            description = description.replace('<br>', '\n').replace('<br />', '\n').replace('<br/>', '\n')
            description = re.sub(r'<[^>]+>', '', description)
            description = re.sub(r'\n\s*\n+', '\n\n', description)  # Normalize multiple newlines
            description = description.strip()
        else:
            description = title

        # Extract thumbnail
        thumbnail = self._og_search_thumbnail(webpage, default=None)
        if not thumbnail:
            # Fallback: try to extract from img tag with class imgRadius
            # Match img tag that has class="imgRadius" and extract src attribute
            thumbnail = self._html_search_regex(
                r'<img[^>]*class=["\']imgRadius["\'][^>]*src=["\']([^"\']+)["\']', 
                webpage, 'thumbnail', fatal=False
            )
        if not thumbnail:
            # Another fallback: try to extract any img tag with class imgRadius (more flexible)
            thumbnail_match = re.search(
                r'<img[^>]*class=["\']imgRadius["\'][^>]*>', 
                webpage, re.IGNORECASE
            )
            if thumbnail_match:
                img_tag = thumbnail_match.group(0)
                src_match = re.search(r'src=["\']([^"\']+)["\']', img_tag)
                if src_match:
                    thumbnail = src_match.group(1)
        if thumbnail:
            # Remove query parameters from thumbnail URL (like ?v2)
            thumbnail = thumbnail.split('?')[0]
            # Convert relative URL to absolute
            if thumbnail.startswith('/'):
                thumbnail = _BASE_URL + thumbnail
            elif not thumbnail.startswith('http'):
                thumbnail = _BASE_URL + '/' + thumbnail

        season = None
        season_number = 0

        season_re = re.search(r'\s+\((\w+)\s+сезон\)', title)
        if season_re:
            season = season_re[0].strip().strip('()')
            season_number = self.get_season_number(season)
            title = title.replace(season_re[0], '').strip()

        if len(title) > 90:
            print('Title too long and would be trimmed: ', title)
            title = title[:90]
            title = title[:title.rfind(' ')]

        episodes_json = self._search_regex(r'var data = \s*?(.*?);', webpage, 'data')
        episodes = json.loads(episodes_json.replace(',}', '}'))

        entries = []
        for episode in episodes:
            episode_id = episodes[episode]

            episode_player_url = _BASE_URL + _SHOWS_API_URL + episode_id

            episode_name = episode.strip()
            episode_match = re.match(r'\d+', episode_name)
            episode_num = episode_match[0] if episode_match else None

            series = title
            if season:
                series = f"{title} [{season}]"

            series_full = series
            if release_year:
                series_full = f"{series} ({release_year})"

            episode_title = f"{series} {episode_name}"

            entries.append({
                'id': episode_id,
                'title': episode_title,
                '_type': 'url_transparent',
                'url': episode_player_url,
                'ie': AnimeVostIE.ie_key(),
                'ext': 'mp4',
                'display_id': video_id + '-' + episode_name,
                'series': series_full,
                'season': season,
                'season_number': season_number,
                'episode_number': int_or_none(episode_num), # int(episode_num) if episode_num else None,
                'release_year': int_or_none(release_year) # int(release_year) if release_year else None
            })

        playlist_count = max(len(entries), int_or_none(playlist_count))
        res = {
            'id': video_id,
            'title': title,
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
        if director:
            res['director'] = director
            res['creator'] = director  # Also add as creator for compatibility
        if thumbnail:
            res['thumbnail'] = thumbnail
        
        return res

# Matches episode
class AnimeVostIE(InfoExtractor):
    IE_NAME = 'animevost:cdn'
    IE_DESC = 'animevost.org CDN'

    # _VALID_URL = r'https?://(?:www\.)?animevost\.(org|am)/frame5.php\?play=(?P<id>\d+).*'
    _VALID_URL = r'https?://(?:www\.)?(animevost\.org|animevost\.am|v\d+\.vost\.pw)/frame5.php\?play=(?P<id>\d+).*'

    _TESTS = [
        {
            'note': 'playlist',
            'url': 'https://animevost.org/frame5.php?play=2147419615',
            'info_dict': {
                'id': '2147419615',
            }
        },
    ]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(
            url,
            None, 'Episode id %s' % video_id)

        formats = self._parse_available_formats(webpage)

        self._check_formats(formats, video_id)

        print('formats:', formats)
        return {
            'id': video_id,
            'formats': formats,
            # 'title': metadata.get('podcast_name'),
            # 'series': metadata.get('series_name'),
            # 'episode': metadata.get('podcast_name'),
        }

        # return {
        #     'id': episode_id,
        #     'url': self.get_cdn_url(url, episode_id),
        # }

    def _parse_available_formats(self, webpage: str) -> list[dict]:
        formats = []
        for format_id, height in (('sd', 480), ('hd', 720)):
            pattern = rf'href=["\']([^"\']+)["\'][^>]*>\s*{height}\s*[pр]\b'
            match = re.search(pattern, webpage)
            url = match.group(1) if match else None
            if url:
                formats.append({
                    'url': url,
                    'format_id': format_id,
                    'quality': format_id,
                    'height': height,
                    'ext': 'mp4'
                })

        if not formats:
            file_list_match = re.search(
                r'["\']file["\']\s*:\s*["\']([^"\']+)["\']',
                webpage)
            file_list = file_list_match.group(1) if file_list_match else None
            if file_list:
                for match in re.finditer(r'\[(?P<label>[^\]]+)\](?P<url>https?://[^, ]+)', file_list):
                    label = match.group('label')
                    format_url = match.group('url')
                    height_match = re.search(r'(\d{3,4})\s*[pр]', label)
                    height = int(height_match.group(1)) if height_match else None
                    format_id = str(height) if height else 'http'
                    formats.append({
                        'url': format_url,
                        'format_id': format_id,
                        'quality': format_id,
                        'height': height,
                        'ext': 'mp4'
                    })
        return formats

    # def get_cdn_url(self, target_url, episode_id):
    #     response = self._download_webpage(
    #         target_url,
    #         None, 'Episode id %s' % episode_id)

    #     episode_url = self._search_regex(r'href="?(.*?)">480p', response, 'data')

    #     return episode_url