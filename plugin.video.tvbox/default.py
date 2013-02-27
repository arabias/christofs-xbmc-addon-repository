# -*- coding: utf-8 -*-

#TV Box - by Christof Torres 2012 - 2013.

import urllib,urllib2,re,datetime,xbmcplugin,xbmcgui,xbmcaddon

from xml.dom import minidom

addon = xbmcaddon.Addon(id='plugin.video.tvbox')

user_agent = 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3'

root = 'https://raw.github.com/ChristofTorres/christofs-xbmc-addon-repository/master/plugin.video.tvbox/resources/data/countries.xml'

def COUNTRIES():
        xmlfile = urllib2.urlopen(root)
        output = open(addon.getAddonInfo('path')+'/resources/data/'+root.split('/')[-1],'wb')
        output.write(xmlfile.read())
        output.close()
        xmldoc = minidom.parse(addon.getAddonInfo('path')+'/resources/data/'+root.split('/')[-1])
        country_list = xmldoc.getElementsByTagName('country')
        for country in country_list:
                xml = country.attributes['xml'].value.encode("utf-8")
                xmlfile = urllib2.urlopen(xml)
                xml = addon.getAddonInfo('path')+'/resources/data/'+xml.split('/')[-1]
                output = open(xml,'wb')
                output.write(xmlfile.read())
                output.close()
                xmldoc = minidom.parse(xml)
                channel_list = xmldoc.getElementsByTagName('channel')
                name = '[B]'+country.attributes['name'].value.encode("utf-8")+'[/B] ('+str(len(channel_list))+')'
                thumbnail = addon.getAddonInfo('path')+'/resources/media/'+country.attributes['name'].value.encode("utf-8").lower()+'.jpg'
                addDir(name, xml, 1, thumbnail, len(country_list))
                

def TVCHANNELS(xml):
        number = 0
        xmldoc = minidom.parse(xml)
        channel_list = xmldoc.getElementsByTagName('channel')
        for channel in channel_list:
                number += 1
                name = channel.attributes['name'].value.encode("utf-8")
                url = channel.attributes['url'].value.encode("utf-8")
                try:
                        epg = get_epg(channel.attributes['epg'].value.encode("utf-8"))
                except:
                        epg = ''
                try:
                        if (url.find('rtmp') == -1 and url.find('m3u8') == -1):
                                req = urllib2.Request(url)
                                req.add_header('User-Agent', user_agent)
                                response = urllib2.urlopen(req)
                                link = response.read()
                                response.close()
                                flashvars = re.compile('file=(.+?)&amp;.+?streamer=(.+?)&amp;').findall(link)
                                for playpath,rtmp in flashvars:
                                        rtmp = rtmp[0:len(rtmp)-1]
                                        rtmp = rtmp+' app=stream swfUrl=http://stream.tv-kino.net/player.swf playpath='+playpath+' live=true'
                        else:
                                rtmp = url
                        thumbnail = addon.getAddonInfo('path')+'/resources/media/'+name.lower()+'.jpg'
                        addLink(number, name, epg, rtmp, thumbnail, len(channel_list))
                except:
                        print "Unexpected error: "+url


def get_epg(url):
        req = urllib2.Request(url)
        req.add_header('User-Agent', user_agent)
        response = urllib2.urlopen(req)
        link = response.read()
        response.close()
        if (url.find('http://i.teleboy.ch') <> -1):
                now = link.split('<div id="showbox__0" class="showclass">')
                epg = re.compile('<p class="show_title">(.+?)<br /><a href="/programm/detail.php\?const_id=.+?">(.+?)</a></p>').findall(now[1])
                time = epg[0][0].decode("iso-8859-1")
                time = time.encode("utf-8")
                title = epg[0][1].decode("iso-8859-1")
                title = title.encode("utf-8") 
        elif (url.find('tele.rtl.lu') <> -1):
                now = re.compile('<TR><TD class="highlight">(.+?)</TD><TD>&nbsp;<B><A HREF=".+?>(.+?)</A>.+?</B></TD></TR>').findall(link)
                epg = re.compile('<TR><TD class="highlight">(.+?)</TD><TD>&nbsp;.*?<A HREF=".*?>(.+?)</A>.+?</TD></TR>').findall(link)
                index = -1
                for epg_time, epg_title in epg:
                        index += 1
                        if (epg_time == now[0][0] and epg_title == now[0][1]):
                                index += 1
                                time = now[0][0]+' - '+epg[index][0]
                                title = now[0][1]
                                break
        elif (url.find('portalnacional.com.pt') <> -1):
                epg = re.compile('<div class="data">(.+?)</div><div class="titulo"><a href="(.+?)" title=".+?">(.+?)</a></div>').findall(link)
                now = datetime.datetime.utcnow()
                now_dt = datetime.datetime(now.year, now.month, now.day, now.hour, now.minute, 0, 0)
                for index in range(0, len(epg)-1):
                        epg[index] = (epg[index][0],epg[index+1][0],epg[index][2])
                for epg_start_time, epg_end_time, epg_title in epg:
                        epg_start_dt = datetime.datetime(now.year, now.month, now.day, int(epg_start_time.split(':')[0]), int(epg_start_time.split(':')[1]), 0, 0)
                        epg_end_dt = datetime.datetime(now.year, now.month, now.day, int(epg_end_time.split(':')[0]), int(epg_end_time.split(':')[1]), 0, 0)
                        if (epg_start_dt.time() <= now_dt.time() and epg_end_dt.time() >= now_dt.time()):
                                time = epg_start_time+' - '+epg_end_time
                                title = epg_title
                                break
        else:
                print 'Unknown EPG: '+url       
        return title+' '+time


def get_params():
        param=[]
        paramstring=sys.argv[2]
        if len(paramstring)>=2:
                params=sys.argv[2]
                cleanedparams=params.replace('?','')
                if (params[len(params)-1]=='/'):
                        params=params[0:len(params)-2]
                pairsofparams=cleanedparams.split('&')
                param={}
                for i in range(len(pairsofparams)):
                        splitparams={}
                        splitparams=pairsofparams[i].split('=')
                        if (len(splitparams))==2:
                                param[splitparams[0]]=splitparams[1]
                                
        return param


def addLink(number,name,epg,url,iconimage,totalchannels):
        ok=True
        if (number < 10):
                name = '[B]'+'  '+str(number)+' '+name+'[/B]'+'      '+epg
        else:
                name = '[B]'+str(number)+' '+name+'[/B]'+'      '+epg
        liz=xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
        liz.setInfo( type="Video", infoLabels={ "Title": epg } )
        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=url,listitem=liz,isFolder=False,totalItems=totalchannels)
        return ok


def addDir(name,url,mode,iconimage,totalcountries):
        u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)
        ok=True
        liz=xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
        liz.setInfo( type="Video", infoLabels={ "Title": name } )
        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True,totalItems=totalcountries)
        return ok
        
              
params=get_params()
url=None
name=None
mode=None

try:
        url=urllib.unquote_plus(params["url"])
except:
        pass
try:
        name=urllib.unquote_plus(params["name"])
except:
        pass
try:
        mode=int(params["mode"])
except:
        pass

print "Mode: "+str(mode)
print "URL : "+str(url)
print "Name: "+str(name)

if mode==None or url==None or len(url)<1:
        print "COUNTRIES()"
        COUNTRIES()

elif mode==1:
        print "TVCHANNELS("+url+")"
        TVCHANNELS(url)

xbmcplugin.endOfDirectory(int(sys.argv[1]))