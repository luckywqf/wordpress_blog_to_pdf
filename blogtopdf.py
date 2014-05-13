#!/usr/bin/env python
"""
Example:
  framecapture qt.nokia.com trolltech.png
"""

import sys
import time

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


def FinderFinished(obj):
    del obj
    for url in g_urls:
        if g_urls[url] == 0:
            capture = FrameCapture()
            capture.load(url)

def CaptureFinished(obj):
    del obj
    
class WebLoader(QObject):
    
    def __init__(self):
        super(WebLoader, self).__init__()
        
        self._percent = 0
        self._page = QWebPage()
        self._page.mainFrame().setScrollBarPolicy(Qt.Vertical,  Qt.ScrollBarAlwaysOff)
        self._page.mainFrame().setScrollBarPolicy(Qt.Horizontal, Qt.ScrollBarAlwaysOff)
        self._page.loadProgress.connect(self.printProgress)
        self._finished = pyqtSignal(self)
        
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
        self._page.mainFrame().load(url)
        self._page.setViewportSize(QSize(1280, 800))  
        print("Loading... %s" % url)
                        
                        
class UrlFinder(WebLoader):
    
    def __init__(self):
        super(UrlFinder, self).__init__()
        self._page.loadFinished.connect(self.findUrls)
        self._finished.connect(FinderFinished)

    def findUrls(self, ok):
        if ok == False:
            print("Load %s failed", self._url.toString())
            self.finished.emit()
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
            
            str = allStr[strs : stre + 5]
            g_urls.setdefault(str, 0)   
            start = stre
        
        self.finished.emit() 
        
                        
class FrameCapture(QObject):
    
    def __init__(self):
        super(FrameCapture, self).__init__()
        self._page.loadFinished.connect(self.saveResult)
        self._finished.connect(CaptureFinished)

    def saveResult(self, ok):
        # Crude error-checking.
        if not ok:
            cerr("Failed loading %s\n" % self._url.toString())
            self.finished.emit()
            return

        # Save each frame in different image files.
        self._frameCounter = 0
        self.saveImage(self._page.mainFrame())
        self.savePdf(self._page.mainFrame())   
        self.finished.emit()
        
    def getName(self, element):
        num = element.attribute("id")[5:]
        title = element.firstChild().toPlainText()
        return num + '-' + title + '.png'
    
    def getPostElement(self, parentElement):
        element = parentElement.firstChild();
        while not element.isNull():
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

    #proxy = QNetworkProxy(QNetworkProxy.HttpProxy, 'proxy.bei.gameloft.org', 3128)
    #proxy.setUser('qifeng.wang')
    #proxy.setPassword('Gameloft1')
    #QNetworkProxy.setApplicationProxy(proxy)
    #QNetworkProxyFactory.setUseSystemConfiguration(True)
    
    app = QApplication(sys.argv)
    
    g_urls = {}
    urlBase = 'http://coolshell.cn/page/'
    for page in range(1, 67):
        pageurl = urlBase + str(page)
        finder = UrlFinder()
        finder.load(pageurl)

    app.exec_()
    print(g_urls)
