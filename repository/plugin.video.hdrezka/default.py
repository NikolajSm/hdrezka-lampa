# -*- coding: utf-8 -*-
import sys
import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon
import urllib.parse
import urllib.request

from resources.lib.scraper import HDRezkaScraper

_addon = xbmcaddon.Addon()
_addon_id = _addon.getAddonInfo('id')
_addon_name = _addon.getAddonInfo('name')
_addon_path = _addon.getAddonInfo('path')
_icon = _addon.getAddonInfo('icon')
_fanart = _addon.getAddonInfo('fanart')

base_url = sys.argv[0]
addon_handle = int(sys.argv[1])
args = urllib.parse.parse_qs(sys.argv[2][1:])

scraper = HDRezkaScraper()

xbmcplugin.setContent(addon_handle, 'movies')

def get_url(**kwargs):
    return '{}?{}'.format(base_url, urllib.parse.urlencode(kwargs))

def build_menu():
    url = get_url(mode='main')
    li = xbmcgui.ListItem('Головне меню')
    xbmcplugin.addDirectoryItem(addon_handle, url, li, True)

def main_menu():
    xbmcplugin.addDirectoryItem(addon_handle, get_url(mode='movies'), 
                               xbmcgui.ListItem('Фільми'), True)
    xbmcplugin.addDirectoryItem(addon_handle, get_url(mode='series'), 
                               xbmcgui.ListItem('Серіали'), True)
    xbmcplugin.addDirectoryItem(addon_handle, get_url(mode='cartoons'), 
                               xbmcgui.ListItem('Мультфільми'), True)
    xbmcplugin.addDirectoryItem(addon_handle, get_url(mode='anime'), 
                               xbmcgui.ListItem('Аніме'), True)
    xbmcplugin.addDirectoryItem(addon_handle, get_url(mode='search'), 
                               xbmcgui.ListItem('Пошук'), True)
    
    xbmcplugin.endOfDirectory(addon_handle)

def show_category(category, page=1):
    items = scraper.get_category_items(category, page)
    
    for item in items:
        list_item = xbmcgui.ListItem(label=item['title'])
        list_item.setArt({
            'thumb': item.get('thumb', _icon),
            'icon': item.get('thumb', _icon),
            'fanart': item.get('fanart', _fanart)
        })
        list_item.setInfo('video', {
            'title': item['title'],
            'plot': item.get('description', ''),
            'year': item.get('year', ''),
            'genre': item.get('genre', '')
        })
        
        url = get_url(mode='content', url=item['url'], title=item['title'])
        xbmcplugin.addDirectoryItem(addon_handle, url, list_item, True)
    
    # Додаємо пагінацію
    if len(items) >= 20:
        next_page_url = get_url(mode=category, page=str(int(page) + 1))
        next_item = xbmcgui.ListItem('Наступна сторінка →')
        xbmcplugin.addDirectoryItem(addon_handle, next_page_url, next_item, True)
    
    xbmcplugin.endOfDirectory(addon_handle)

def show_content(url, title):
    content_info = scraper.get_content_info(url)
    
    if content_info['type'] == 'movie':
        # Для фільму одразу показуємо плеєр
        play_video(url, title)
    else:
        # Для серіалу показуємо список сезонів та серій
        show_seasons(content_info['seasons'])

def show_seasons(seasons):
    for season_num, episodes in seasons.items():
        list_item = xbmcgui.ListItem(label=f'Сезон {season_num}')
        url = get_url(mode='season', season=season_num, 
                      episodes=str(list(episodes.keys())))
        xbmcplugin.addDirectoryItem(addon_handle, url, list_item, True)
    
    xbmcplugin.endOfDirectory(addon_handle)

def show_episodes(season_num, episodes):
    episodes_list = eval(episodes)  # Перетворюємо строку назад у список
    
    for episode_num in episodes_list:
        list_item = xbmcgui.ListItem(label=f'Серія {episode_num}')
        # Тут потрібно буде додати логіку для отримання посилання на конкретну серію
        xbmcplugin.addDirectoryItem(addon_handle, '', list_item, False)
    
    xbmcplugin.endOfDirectory(addon_handle)

def search_content():
    keyboard = xbmc.Keyboard('', 'Введіть назву фільму або серіалу')
    keyboard.doModal()
    
    if keyboard.isConfirmed():
        query = keyboard.getText()
        if query:
            results = scraper.search(query)
            
            for item in results:
                list_item = xbmcgui.ListItem(label=item['title'])
                list_item.setArt({
                    'thumb': item.get('thumb', _icon),
                    'icon': item.get('thumb', _icon)
                })
                
                url = get_url(mode='content', url=item['url'], title=item['title'])
                xbmcplugin.addDirectoryItem(addon_handle, url, list_item, True)
            
            xbmcplugin.endOfDirectory(addon_handle)

def play_video(url, title):
    streams = scraper.get_video_streams(url)
    
    if streams:
        # Вибираємо найкращу якість
        best_stream = max(streams, key=lambda x: x['quality'])
        
        play_item = xbmcgui.ListItem(path=best_stream['url'])
        play_item.setInfo('video', {'title': title})
        play_item.setProperty('IsPlayable', 'true')
        
        xbmcplugin.setResolvedUrl(addon_handle, True, play_item)
    else:
        xbmcgui.Dialog().notification('Помилка', 'Не вдалося отримати відео', 
                                      xbmcgui.NOTIFICATION_ERROR)

def router():
    mode = args.get('mode', ['main'])[0]
    
    if mode == 'main':
        main_menu()
    elif mode == 'movies':
        page = args.get('page', ['1'])[0]
        show_category('films', page)
    elif mode == 'series':
        page = args.get('page', ['1'])[0]
        show_category('series', page)
    elif mode == 'cartoons':
        page = args.get('page', ['1'])[0]
        show_category('cartoons', page)
    elif mode == 'anime':
        page = args.get('page', ['1'])[0]
        show_category('anime', page)
    elif mode == 'content':
        url = args.get('url', [''])[0]
        title = args.get('title', [''])[0]
        show_content(url, title)
    elif mode == 'season':
        season = args.get('season', ['1'])[0]
        episodes = args.get('episodes', [''])[0]
        show_episodes(season, episodes)
    elif mode == 'search':
        search_content()
    elif mode == 'play':
        url = args.get('url', [''])[0]
        title = args.get('title', [''])[0]
        play_video(url, title)
    else:
        main_menu()

if __name__ == '__main__':
    router()