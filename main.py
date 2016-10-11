from datetime import datetime,timedelta
from rpc import RPC
from xbmcswift2 import Plugin
from xbmcswift2 import actions
import HTMLParser
import os
import random
import re
import requests
import sqlite3
import time
import xbmc,xbmcaddon,xbmcvfs,xbmcgui
import xbmcplugin

from types import *

plugin = Plugin()
big_list_view = False

def log(v):
    xbmc.log(repr(v))


def get_icon_path(icon_name):
    addon_path = xbmcaddon.Addon().getAddonInfo("path")
    return os.path.join(addon_path, 'resources', 'img', icon_name+".png")


def remove_formatting(label):
    label = re.sub(r"\[/?[BI]\]",'',label)
    label = re.sub(r"\[/?COLOR.*?\]",'',label)
    return label

@plugin.route('/play/<url>')
def play(url):
    xbmc.executebuiltin('PlayMedia(%s)' % url)

@plugin.route('/execute/<url>')
def execute(url):
    xbmc.executebuiltin(url)

@plugin.route('/add_url/<id>/<label>/<path>/<thumbnail>')
def add_url(id,label,path,thumbnail):
    labels = plugin.get_storage('labels')
    thumbnails = plugin.get_storage('thumbnails')
    urls = plugin.get_storage('urls')
    urls[path] = id
    labels[path] = label
    thumbnails[path] = thumbnail
    xbmc.executebuiltin('Container.Refresh')

@plugin.route('/remove_url/<path>')
def remove_url(path):
    labels = plugin.get_storage('labels')
    thumbnails = plugin.get_storage('thumbnails')
    urls = plugin.get_storage('urls')
    del urls[path]
    del labels[path]
    del thumbnails[path]
    xbmc.executebuiltin('Container.Refresh')

@plugin.route('/add_folder/<id>/<label>/<path>/<thumbnail>')
def add_folder(id,label,path,thumbnail):
    d = xbmcgui.Dialog()
    result = d.input("Rename Shortcut",label)
    if not result:
        return
    label = result
    folders = plugin.get_storage('folders')
    labels = plugin.get_storage('labels')
    thumbnails = plugin.get_storage('thumbnails')
    folders[path] = id
    labels[path] = label
    thumbnails[path] = thumbnail
    xbmc.executebuiltin('Container.Refresh')

@plugin.route('/remove_folder/<path>')
def remove_folder(path):
    folders = plugin.get_storage('folders')
    labels = plugin.get_storage('labels')
    thumbnails = plugin.get_storage('thumbnails')
    del folders[path]
    del labels[path]
    del thumbnails[path]
    xbmc.executebuiltin('Container.Refresh')

@plugin.route('/change_image/<path>')
def change_image(path):
    d = xbmcgui.Dialog()
    result = d.browse(2, 'Choose Image', 'files')
    if not result:
        return
    thumbnail = result
    thumbnails = plugin.get_storage('thumbnails')
    thumbnails[path] = thumbnail
    xbmc.executebuiltin('Container.Refresh')

@plugin.route('/subscribe_folder/<media>/<id>/<label>/<path>/<thumbnail>')
def subscribe_folder(media,id,label,path,thumbnail):
    folders = plugin.get_storage('folders')
    urls = plugin.get_storage('urls')
    try:
        response = RPC.files.get_directory(media=media, directory=path, properties=["thumbnail"])
    except:
        return
    files = response["files"]
    dirs = dict([[remove_formatting(f["label"]), f["file"]] for f in files if f["filetype"] == "directory"])
    thumbnails = dict([f["file"], f["thumbnail"]] for f in files)
    links = {}
    for f in files:
        if f["filetype"] == "file":
            label = remove_formatting(f["label"])
            file = f["file"]
            while (label in links):
                label = "%s." % label
            links[label] = file

    items = []

    for label in sorted(dirs):
        path = dirs[label]
        file_thumbnail = thumbnails[path]
        if file_thumbnail:
            thumbnail = file_thumbnail
        context_items = []
        if path in folders:
            fancy_label = "[COLOR yellow][B]%s[/B][/COLOR] " % label
            context_items.append(("[COLOR yellow][B]%s[/B][/COLOR] " % 'Remove', 'XBMC.RunPlugin(%s)' % (plugin.url_for(remove_folder, path=path))))
        else:
            fancy_label = "[B]%s[/B]" % label
            context_items.append(("[COLOR yellow][B]%s[/B][/COLOR] " % 'Add', 'XBMC.RunPlugin(%s)' % (plugin.url_for(add_folder, id=id, label=label.encode("utf8"), path=path, thumbnail=thumbnail))))
        items.append(
        {
            'label': fancy_label,
            'path': plugin.url_for('subscribe_folder',media=media, id=id, label=label.encode("utf8"), path=path, thumbnail=thumbnail),
            'thumbnail': thumbnail,
            'context_menu': context_items,
        })

    for label in sorted(links):
        path = links[label]
        file_thumbnail = thumbnails[path]
        if file_thumbnail:
            thumbnail = file_thumbnail
        context_items = []
        if path in urls:
            fancy_label = "[COLOR yellow][B]%s[/B][/COLOR] " % label
            context_items.append(("[COLOR yellow][B]%s[/B][/COLOR] " % 'Remove', 'XBMC.RunPlugin(%s)' % (plugin.url_for(remove_url, path=path))))
        else:
            fancy_label = "[B]%s[/B]" % label
            context_items.append(("[COLOR yellow][B]%s[/B][/COLOR] " % 'Add', 'XBMC.RunPlugin(%s)' % (plugin.url_for(add_url, id=id, label=label.encode("utf8"), path=path, thumbnail=thumbnail))))

        items.append(
        {
            'label': label,
            'path': plugin.url_for('play',url=links[label]),
            'thumbnail': thumbnail,
            'context_menu': context_items,
        })

    return items


@plugin.route('/add_addons/<media>')
def add_addons(media):
    folders = plugin.get_storage('folders')
    ids = {}
    for folder in folders:
        id = folders[folder]
        ids[id] = id

    type = "xbmc.addon.%s" % media

    response = RPC.addons.get_addons(type=type,properties=["name", "thumbnail"])
    if "addons" not in response:
        return

    addons = response["addons"]

    items = []

    addons = sorted(addons, key=lambda addon: remove_formatting(addon['name']).lower())
    for addon in addons:
        label = addon['name']
        id = addon['addonid']
        thumbnail = addon['thumbnail']
        path = "plugin://%s" % id
        context_items = []
        if id in ids:
            fancy_label = "[COLOR yellow][B]%s[/B][/COLOR] " % label
            context_items.append(("[COLOR yellow][B]%s[/B][/COLOR] " % 'Remove', 'XBMC.RunPlugin(%s)' % (plugin.url_for(remove_folder, path=path))))
        else:
            fancy_label = "[B]%s[/B]" % label
            context_items.append(("[COLOR yellow][B]%s[/B][/COLOR] " % 'Add', 'XBMC.RunPlugin(%s)' % (plugin.url_for(add_folder, id=id, label=label.encode("utf8"), path=path, thumbnail=thumbnail))))
        items.append(
        {
            'label': fancy_label,
            'path': plugin.url_for('subscribe_folder',media="files", id=id, label=label, path=path, thumbnail=thumbnail),
            'thumbnail': thumbnail,
            'context_menu': context_items,
        })
    return items

@plugin.route('/add')
def add():
    items = []
    for media in ["video", "music"]:
        label = media
        id = "none"
        path = "library://%s" % media
        thumbnail = get_icon_path(media)
        items.append(
        {
            'label': "[B]%s[/B]" % media.title(),
            'path': plugin.url_for('subscribe_folder',media=media, id=id, label=label, path=path, thumbnail=thumbnail),
            'thumbnail': thumbnail,
        })

    for media in ["video", "audio"]:
        label = media
        thumbnail = get_icon_path(media)
        items.append(
        {
            'label': "[B]%s Addons[/B]" % media.title(),
            'path': plugin.url_for('add_addons',media=media),
            'thumbnail': thumbnail,
        })

    return items


@plugin.route('/')
def index():
    items = []

    folders = plugin.get_storage('folders')
    urls = plugin.get_storage('urls')
    labels = plugin.get_storage('labels')
    thumbnails = plugin.get_storage('thumbnails')

    for folder in sorted(folders, key=lambda x: labels[x]):
        path = folder
        label = labels[folder]
        thumbnail = thumbnails[folder]
        context_items = []
        context_items.append(("[COLOR yellow][B]%s[/B][/COLOR] " % 'Remove', 'XBMC.RunPlugin(%s)' % (plugin.url_for(remove_folder, path=path))))
        context_items.append(("[COLOR yellow][B]%s[/B][/COLOR] " % 'Change Image', 'XBMC.RunPlugin(%s)' % (plugin.url_for(change_image, path=path))))
        items.append(
        {
            'label': label,
            'path': folder,
            'thumbnail':thumbnail,
            'context_menu': context_items,
        })
    for url in urls:
        label = labels[url]
        thumbnail = thumbnails[url]
        path = url
        context_items = []
        context_items.append(("[COLOR yellow][B]%s[/B][/COLOR] " % 'Remove', 'XBMC.RunPlugin(%s)' % (plugin.url_for(remove_url, path=path))))
        context_items.append(("[COLOR yellow][B]%s[/B][/COLOR] " % 'Change Image', 'XBMC.RunPlugin(%s)' % (plugin.url_for(change_image, path=path))))
        items.append(
        {
            'label': label,
            'path': plugin.url_for('play',url=url),
            'thumbnail':thumbnail,
            'context_menu': context_items,
        })

    if plugin.get_setting('kodi.favourites') == 'true':
        f = xbmcvfs.File("special://profile/favourites.xml","rb")
        data = f.read()
        favourites = re.findall("<favourite.*?</favourite>",data)
        for fav in favourites:
            fav = re.sub('&quot;','',fav)
            match = re.search('<favourite name="(.*?)" thumb="(.*?)">(.*?)<',fav)
            label = match.group(1)
            thumbnail = match.group(2)
            url = match.group(3)
            items.append(
            {
                'label': label,
                'path': plugin.url_for('execute',url=url),
                'thumbnail':thumbnail,
            })

    items.append(
    {
        'label': "Add",
        'path': plugin.url_for('add'),
        'thumbnail':get_icon_path('settings'),
    })


    plugin.set_content('movies')
    return items

if __name__ == '__main__':
    plugin.run()
    if big_list_view == True:
        view_mode = int(plugin.get_setting('view_mode'))
        plugin.set_view_mode(view_mode)