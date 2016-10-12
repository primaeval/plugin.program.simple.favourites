import xbmc
import sys

xbmc.log(repr(sys.argv))
if __name__ == '__main__':
    db_type = xbmc.getInfoLabel('ListItem.DBTYPE')
    title = xbmc.getInfoLabel('ListItem.Label')
    stream_file = xbmc.getInfoLabel('ListItem.FileNameAndPath')
    iconimage = xbmc.getInfoLabel('ListItem.Art(thumb)')
    filename = xbmc.getInfoImage('ListItem.Art(thumb) ')
    content = xbmc.getInfoImage('Container.Content')
    isFolder = xbmc.getCondVisibility('ListItem.IsFolder') == 1
    xbmc.log(repr((isFolder,db_type,title,stream_file,iconimage,filename,content)))

    
