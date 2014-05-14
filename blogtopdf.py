#!/usr/bin/env python
"""
Example:
  framecapture qt.nokia.com trolltech.png
"""

import sys
import time
import platform
from PyQt5.QtCore import pyqtSignal, QObject, QSize, Qt, QUrl
from PyQt5.QtGui import QImage, QPainter, QPagedPaintDevice, QPdfWriter
from PyQt5.QtWidgets import QApplication
from PyQt5.QtWebKitWidgets import QWebPage
from PyQt5.QtNetwork import QNetworkProxyFactory, QNetworkProxy, QTcpSocket

def cout(s):
    sys.stdout.write(s)
    sys.stdout.flush()

def cerr(s):
    sys.stderr.write(s)
    sys.stderr.flush()


def FinderFinished(key):
#     global g_finders
#     del g_finders[key]
    print ("FinderFinished start!!!!!!!!!!!!!")
    global g_urls
    for url in g_urls:
        if g_urls[url] == 0:
            g_urls[url] = FrameCapture(url)
            g_urls[url].load(url)

def CaptureFinished(key):
    global g_urls
    del g_urls[key]
    
class WebLoader(QObject):
    
    _finished = pyqtSignal(str)
    
    def __init__(self, key):
        super(WebLoader, self).__init__()

#         if platform.python_version() < '3.0.0':
#             self._key = unicode(key)
  
        self._key = key
        self._percent = 0
        self._page = QWebPage()
        self._page.mainFrame().setScrollBarPolicy(Qt.Vertical,  Qt.ScrollBarAlwaysOff)
        self._page.mainFrame().setScrollBarPolicy(Qt.Horizontal, Qt.ScrollBarAlwaysOff)
        self._page.loadProgress.connect(self.printProgress)
        
        
    def printProgress(self, percent):
        if self._percent >= percent:
            cout("\n")
            return
        else:
            cout('#' * (percent - self._percent))
            self._percent = percent
            
    def load(self, url):
        self._percent = 0
        self._url = QUrl.fromUserInput(url)
        self._page.mainFrame().load(self._url)
        self._page.setViewportSize(QSize(1280, 800))  
        print("Loading... %s" % url)
                        
                        
class UrlFinder(WebLoader):
    
    def __init__(self, key):
        super(UrlFinder, self).__init__(key)
        self._page.loadFinished.connect(self.findUrls)
        self._finished.connect(FinderFinished)

    def findUrls(self, ok):
        if ok == False:
            print("Load %s failed", self._url.toString())
            self._finished.emit(self._key)
            return
        print('load finished, start parse urls')
        
        start = 0
        allStr = self._page.mainFrame().documentElement().toInnerXml() #allStr = allStr.encode('utf-8-sig')
        while True: 
            strs = allStr.find('http://coolshell.cn/articles/', start)
            if strs == -1:
                break
            stre = allStr.find('.html"', strs)
            if stre == -1 or stre - strs > 38:
                start = strs + 30
                continue
            
            surl = allStr[strs : stre + 5] #surl = str(surl)
            global g_urls
            g_urls.setdefault(surl, 0)   
            start = stre
        print ("\nfinished!!!!!!!!!!!!!")
#         self._finished.emit(self._key) 
        FinderFinished(self._key)
        
                        
class FrameCapture(WebLoader):
    
    def __init__(self, key):
        super(FrameCapture, self).__init__(key)
        self._page.loadFinished.connect(self.saveResult)
        self._finished.connect(CaptureFinished)

    def saveResult(self, ok):
        # Crude error-checking.
        if not ok:
            cerr("Failed loading %s\n" % self._url.toString())
            #self._finished.emit(self._key)
            CaptureFinished(self._key)
            return

        # Save each frame in different image files.
        self._frameCounter = 0
        self.saveImage(self._page.mainFrame())
        #self.savePdf(self._page.mainFrame())   
        #self._finished.emit(self._key)
        CaptureFinished(self._key)
        
    def getName(self, element):
        num = element.attribute("id")[5:]
        title = element.firstChild().toPlainText()
        return num + '-' + title + '.png'
    
    def getPostElement(self, parentElement):
        element = parentElement.firstChild();
        while not element.isNull():
            print element.tagName()
            if element.tagName() == "DIV" and element.hasAttribute("class") and element.attribute("class") == "post":
                return element
            child = self.getPostElement(element)
            if child != None:
                return child
            element = element.nextSibling()
        return None    

    def saveImage(self, frame):
        element = self.getPostElement(frame.documentElement())
        if element is not None:
            rect = element.geometry()
            image = QImage(rect.size(), QImage.Format_ARGB32_Premultiplied)
            image.fill(Qt.transparent)
            painter = QPainter(image)
            painter.setRenderHint(QPainter.Antialiasing, True)
            painter.setRenderHint(QPainter.TextAntialiasing, True)
            painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
            element.render(painter)
            painter.end()
            image.save(self.getName(element))

    def savePdf(self, frame):
        element = self.getPostElement(frame.documentElement())
        if element is not None:
            rect = element.geometry()
            pdf = QPdfWriter(self.getName(element))
            pdf.setPageSize(QPagedPaintDevice.A4)
            painter = QPainter(pdf)
            painter.setRenderHint(QPainter.Antialiasing, True)
            painter.setRenderHint(QPainter.TextAntialiasing, True)
            painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
            element.render(painter)
            painter.end()  
    
if __name__ == '__main__':
    #sys.argv = ['', 'http://coolshell.cn/articles/11235.html', 'xx.png']
    #if len(sys.argv) != 3:
    #    cerr(__doc__)
    #    sys.exit(1)


    app = QApplication(sys.argv)
    
    proxy = QNetworkProxy(QNetworkProxy.HttpProxy, 'proxy.bei.gameloft.org', 3128)
    proxy.setUser('qifeng.wang')
    proxy.setPassword('Gameloft1')
    QNetworkProxy.setApplicationProxy(proxy)
    #QNetworkProxyFactory.setUseSystemConfiguration(True)
    
    global g_urls
    global g_finders
    g_urls = {}
    g_finders = {}
    urlBase = 'http://coolshell.cn/page/'    
    for ipage in range(1, 2):
        page = str(ipage)
        pageurl = urlBase + page
        g_finders[page] = UrlFinder(page)
        g_finders[page].load(pageurl)
        #finder.load(pageurl)

    app.exec_()
