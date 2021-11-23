# coding: utf-8

from yt_dlp.extractor.common import InfoExtractor
import json
import re


class AnimeVostShowsIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?animevost\.(org|am)/tip/.*/(?P<id>\d+)[-\w+][^/]*'

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
        return 0

    def _real_extract(self, url):
        _BASE_URL = 'https://animevost.org'
        _SHOWS_API_URL = '/frame5.php?play='

        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id, 'Downloading requested URL')

        title = self._html_search_regex(r'<h1>\s*(.+?)\s*</h1>', webpage, 'title') or \
            self._og_search_title(webpage)

        title = title[:title.find('/')]  # beautify
        title = title.strip()

        season = None
        season_number = 0

        season_re = re.search(r'\s+\((\w+)\s+сезон\)', title)
        if season_re:
            season = season_re[0].strip().strip('()')
            season_number = self.get_season_number(season)
            title = title.replace(season_re[0], '').strip()

        # description = self._html_search_meta(
        #     ['og:description', 'description', 'twitter:description'],
        #     webpage, 'description', default=None)

        description = title

        episodes_json = self._search_regex(r'var data = \s*?(.*?);', webpage, 'data')
        episodes = json.loads(episodes_json.replace(',}', '}'))

        entries = []
        for episode in episodes:
            episode_id = episodes[episode]

            episode_player_url = _BASE_URL + _SHOWS_API_URL + episode_id

            episode_match = re.match(r'\d+', episode)
            episode_num = episode_match[0] if episode_match else None

            episode_title = f"{title} {episode}"
            if season:
                episode_title = f"{title} [{season}] {episode}"

            entries.append({
                'id': episode_id,
                'title': episode_title,
                '_type': 'url_transparent',
                'url': episode_player_url,
                'ie': AnimeVostIE.ie_key(),
                'ext': 'mp4',
                'display_id': video_id + '-' + episode,
                'series': title,
                'season': season,
                'season_number': season_number,
                'episode_number': int(episode_num) if episode_num else None
            })

        res = {
            'id': video_id,
            'title': title,
            'description': description,
            'url': url,
            'entries': entries,
            'playlist_count': len(entries),
            '_type': 'playlist',
        }
        return res


class AnimeVostIE(InfoExtractor):
    IE_NAME = 'animevost:cdn'
    IE_DESC = 'animevost.org CDN'

    _VALID_URL = r'https?://(?:www\.)?animevost\.(org|am)/frame5.php\?play=(?P<id>\d+).*'

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
        episode_id = self._match_id(url)
        return {
            'id': episode_id,
            'url': self.get_cdn_url(url, episode_id),
        }

    def get_cdn_url(self, target_url, episode_id):
        response = self._download_webpage(
            target_url,
            None, 'Episode id %s' % episode_id)

        episode_url = self._search_regex(r'href="?(.*?)">480p', response, 'data')

        return episode_url