from xbmcswift2 import Plugin
from xbmcswift2 import actions
import xbmc,xbmcaddon,xbmcvfs,xbmcgui
import re
from rpc import RPC
import requests
import random
import sqlite3
from datetime import datetime,timedelta
import time
#import urllib
import HTMLParser
import xbmcplugin
#import xml.etree.ElementTree as ET
#import sqlite3
import os
#import shutil
#from rpc import RPC
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
 
@plugin.route('/add_url/<id>/<label>/<path>')
def add_url(id,label,path):
    folders = plugin.get_storage('urls')
    labels = plugin.get_storage('labels')
    #ids = plugin.get_storage('ids')
    urls[path] = id
    labels[path] = label
    #ids[id] = id
    xbmc.executebuiltin('Container.Refresh')

@plugin.route('/remove_url/<id>/<label>/<path>')
def remove_url(id,label,path):
    urls = plugin.get_storage('urls')
    labels = plugin.get_storage('labels')
    del urls[path]
    del labels[path]
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
    #ids = plugin.get_storage('ids')
    folders[path] = id
    labels[path] = label
    thumbnails[path] = thumbnail
    #ids[id] = id
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

@plugin.route('/subscribe_folder/<id>/<label>/<path>/<thumbnail>')
def subscribe_folder(id,label,path,thumbnail):
    folders = plugin.get_storage('folders')
    urls = plugin.get_storage('urls')
    response = RPC.files.get_directory(media="files", directory=path, properties=["thumbnail"])
    files = response["files"]
    dirs = dict([[remove_formatting(f["label"]), f["file"]] for f in files if f["filetype"] == "directory"])
    thumbnails = dict([f["file"], f["thumbnail"]] for f in files)
    links = {}
    #thumbnails = {}
    for f in files:
        if f["filetype"] == "file":
            label = remove_formatting(f["label"])
            file = f["file"]
            while (label in links):
                label = "%s." % label
            links[label] = file
            #thumbnails[label] = f["thumbnail"]

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
            'path': plugin.url_for('subscribe_folder',id=id, label=label.encode("utf8"), path=path, thumbnail=thumbnail),
            #'thumbnail': get_icon_path('tv'),
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
            context_items.append(("[COLOR yellow][B]%s[/B][/COLOR] " % 'Remove', 'XBMC.RunPlugin(%s)' % (plugin.url_for(remove_url, id=id, label=label.encode("utf8"), path=path))))
        else:
            fancy_label = "[B]%s[/B]" % label
            context_items.append(("[COLOR yellow][B]%s[/B][/COLOR] " % 'Add', 'XBMC.RunPlugin(%s)' % (plugin.url_for(add_url, id=id, label=label.encode("utf8"), path=path))))
    
        items.append(
        {
            'label': label,
            'path': plugin.url_for('play',url=links[label]),
            #'thumbnail': thumbnails[label],
            'thumbnail': thumbnail,
        })
    
    return items


@plugin.route('/subscribe')
def subscribe():
    folders = plugin.get_storage('folders')
    ids = {}
    for folder in folders:
        id = folders[folder]
        ids[id] = id
    all_addons = []
    for type in ["xbmc.addon.video", "xbmc.addon.audio"]:
        response = RPC.addons.get_addons(type=type,properties=["name", "thumbnail"])
        if "addons" in response:
            found_addons = response["addons"]
            all_addons = all_addons + found_addons

    seen = set()
    addons = []
    for addon in all_addons:
        if addon['addonid'] not in seen:
            addons.append(addon)
        seen.add(addon['addonid'])

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
            'path': plugin.url_for('subscribe_folder',id=id, label=label, path=path, thumbnail=thumbnail),
            'thumbnail': thumbnail,
            #'thumbnail': get_icon_path('tv'),
            #'context_menu': context_items,
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
        items.append(
        {
            'label': label,
            'path': folder,
            #'thumbnail':get_icon_path('tv'),
            'thumbnail':thumbnail,
            'context_menu': context_items,
        })
    for url in urls:
        label = labels[url]
        items.append(
        {
            'label': label,
            'path': url,
            'thumbnail':get_icon_path('tv'),
        })

    items.append(
    {
        'label': "Add",
        'path': plugin.url_for('subscribe'),
        'thumbnail':get_icon_path('settings'),
    })
    return items

if __name__ == '__main__':
    plugin.run()
    if big_list_view == True:
        view_mode = int(plugin.get_setting('view_mode'))
        plugin.set_view_mode(view_mode)