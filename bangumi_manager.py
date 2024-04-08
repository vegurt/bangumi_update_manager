import os
import re
import base64
import itertools
import copy
from sys import argv
from datetime import datetime
import pyperclip
import requests
from lxml import etree
from rich import console,table

cs=console.Console()
cookie = requests.Session()

def download(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36 QIHU 360SE'}
    res=cookie.get(url, headers=headers, timeout=(5, 15))
    res.close()
    return res

class RssGenerator:
    def __init__(self,name,func,source=None) -> None:
        '''\
        name: RSS源名称
        func: 参数为RSS源、关键词列表和页数，输出为RSS链接的函数
        source: 传递到func函数作为RSS源参数的参数
        '''
        self.name = name
        self.source = source
        self.func=func

    def toRss(self,keys,page=1):
        # 看到某些站点搜索结果第一页和第二页点进去的RSS的URL不一样，我满怀兴奋地加入了页码参数
        # 结果等我哐哐哐一顿写完才发现，没什么软用，就是URL不一样而已，内容一模一样
        # 我还说这是不是可以打破RSS展示数量的限制，把所有搜索结果都收集起来，结果就这？
        # 我也不改了，算是弥补脚本里面一个番剧只能存一组关键词的缺陷吧
        # 也算是希冀未来有网站能够和网页一样RSS也能翻页
        # 反正也浪费不了多少系统资源
        # 如果要使用多组关键词进行整合，那就不同页码返回不同链接吧
        # 但需保证除了最后一页，前面的都返回至少一个项目
        # 脚本从1开始遍历页码，直到搜不到为止，然后把所有结果合并
        return self.func(self.source,keys,page)


class RssSource:
    'RSS订阅与文件下载'
    def __init__(self) -> None:
        func1 = lambda source,keys,page:(source.format(key='-'+'+'.join(' '.join(keys).split()) if keys else '') if page==1 else '')
        func2 = lambda source,keys,page:(source.format(key='?keyword='+'+'.join(' '.join(keys).split()) if keys else '') if page==1 else '')
        self.sources=[
            RssGenerator('爱恋动漫 主站',func1,'http://kisssub.org/rss{key}.xml'),
            RssGenerator('漫猫动漫 主站',func1,'http://comicat.org/rss{key}.xml'),
            RssGenerator('爱恋动漫 站点1',func1,'http://1.kisssub.115000.xyz/rss{key}.xml'),
            RssGenerator('爱恋动漫 站点2',func1,'http://2.kisssub.115000.xyz/rss{key}.xml'),
            RssGenerator('爱恋动漫 站点3',func1,'http://3.kisssub.115000.xyz/rss{key}.xml'),
            RssGenerator('爱恋动漫 站点4',func1,'http://4.kisssub.115000.xyz/rss{key}.xml'),
            RssGenerator('爱恋动漫 站点5',func1,'http://5.kisssub.115000.xyz/rss{key}.xml'),
            RssGenerator('漫猫动漫 站点1',func1,'http://1.comicat.122000.xyz/rss{key}.xml'),
            RssGenerator('漫猫动漫 站点2',func1,'http://2.comicat.122000.xyz/rss{key}.xml'),
            RssGenerator('漫猫动漫 站点3',func1,'http://3.comicat.122000.xyz/rss{key}.xml'),
            RssGenerator('漫猫动漫 站点4',func1,'http://4.comicat.122000.xyz/rss{key}.xml'),
            RssGenerator('漫猫动漫 站点5',func1,'http://5.comicat.122000.xyz/rss{key}.xml'),
            RssGenerator('爱恋动漫 站点6',func1,'http://1.kisssub.org/rss{key}.xml'),
            RssGenerator('爱恋动漫 站点7',func1,'http://2.kisssub.org/rss{key}.xml'),
            RssGenerator('爱恋动漫 站点8',func1,'http://3.kisssub.org/rss{key}.xml'),
            RssGenerator('爱恋动漫 站点9',func1,'http://2.kisssub.net/rss{key}.xml'),
            RssGenerator('爱恋动漫 站点10',func1,'http://3.kisssub.net/rss{key}.xml'),
            RssGenerator('漫猫动漫',func1,'http://1.comicat.org/rss{key}.xml'),
            RssGenerator('喵喵喵',func1,'http://www.miobt.com/rss{key}.xml'),
            RssGenerator('末日动漫',func2,'https://share.acgnx.se/rss.xml{key}'),
            RssGenerator('动漫花园',func2,'https://share.dmhy.org/topics/rss/rss.xml{key}'),
            # 'gg.al',
            # 'comicat.122000.xyz',
        ]
        self.index=0
        self.retry_times=3
        
    
    @property
    def source(self):
        return self.sources[self.index]
    
    @property
    def name(self):
        return self.source.name
    
    def switch_source(self,num=None):
        if num is None:
            self.index+=1
            if self.index>=len(self.sources):
                self.index=0
        elif isinstance(num,int) and 0<=num<len(self.sources):
            self.index=num
    
    @staticmethod
    def extractRss(rss):
        '提取RSS内容'
        rss = rss.find('channel')
        if rss is not None:
            res = etree.Element('channel')
            rss = copy.deepcopy(rss)
            for item in rss.iterfind('item'):
                res.append(item)
            return res

    @staticmethod
    def extendRss(rss1,rss2,inplace=True):
        'rss2的内容加到rss1里去'
        if not inplace:
            rss1 = copy.deepcopy(rss1)
        rss2 = copy.deepcopy(rss2)
        rss1.extend(rss2)
        return rss1

    def rsslink(self,keys:list,page=1):
        return self.source.toRss(keys,page)

    def getrss(self,keys,page=1,sourcetest=True):
        for i in range(len(self.sources)):
            link = self.rsslink(keys,page)
            if link:
                print(f'正在使用 {self.name} 下载第 {page} 页')
                for j in range(self.retry_times):
                    try:
                        print(f'第{j+1}次尝试：',end='')
                        res=download(link)
                        res = self.extractRss(etree.fromstring(res.content))
                    except Exception:
                        print('失败。。。')
                    else:
                        print('成功！！')
                        return res
            else:
                return
            if not sourcetest:
                return
            self.switch_source()

    def download(self,keys):
        res = None
        for page in itertools.count(1):
            try:
                tmp = self.getrss(keys,page,page==1)
                if tmp is not None:
                    if res is None:
                        res = etree.Element('channel')
                    if len(tmp)>0:
                        self.extendRss(res,tmp)
                    else:
                        break
                else:
                    break
            except Exception:
                break
        return res


class episode:
    def __new__(cls,name,source,date,downloadurl,isnew=True):
        if name and source:
            if not downloadurl:
                tmp = cls.findhash(source)
                if tmp is None or cls.tohashv1(tmp) is None:
                    return # 不带下载链接，就别来了
            return super().__new__(cls)

    def __init__(self,name,source,date,downloadurl,isnew=True) -> None:
        self.name = name
        self.source=source
        self.date:datetime=date
        if downloadurl:
            self.downloadurl=downloadurl
        else:
            h = self.findhash(source)
            h = self.tohashv1(h)
            self.downloadurl=self.hash2torrent(h)
        self.isnew:bool=isnew
        self.content=None
        self.retry_times=3

    @staticmethod
    def findhash(s):
        res=re.search(r'\b[A-Za-z0-9]{32}(?:[A-Za-z0-9]{8})?\b',s)
        if res:
            res = res.group(0)
            if len(res)==32:
                return res.upper()
            elif len(res)==40:
                return res.lower()
                
    @staticmethod
    def tohashv1(torrenthash:str):
        if len(torrenthash)==32:
            try:
                return base64.b16encode(base64.b32decode(torrenthash.upper())).decode().lower() # 种子短哈希转长哈希
            except Exception:
                return
        elif len(torrenthash)==40:
            return torrenthash.lower()

    def isSameResource(self, ep) -> bool:
        # 只代表指向同一个资源，来源不一定相同
        if not isinstance(ep,episode):
            return False
        h1,h2=self.hash,ep.hash
        return ((h1 or h2) and h1==h2) or self.name==ep.name or \
               self.source==ep.source or self.downloadurl==ep.downloadurl

    def __eq__(self, ep) -> bool:
        if not isinstance(ep,episode):
            return False
        return self.name==ep.name and self.date==ep.date and \
               self.source==ep.source and self.downloadurl==ep.downloadurl

    def show(self):
        t = '(新) ' if self.isnew else ''
        print(f'{self.datestring} {self.dayspast}天前')
        cs.out(f'{t}',style='red',end='')
        print(self.name)
        print(f'参见：{self.source}')
    
    @property
    def xml(self):
        return etree.Element('ep',
                            name = self.name,
                            source=self.source,
                            date=self.datestring,
                            downloadurl=self.downloadurl,
                            isnew=str(self.isnew))
    
    @classmethod
    def fromrss(cls,xml):
        def str2date(datestr):
            fs={
            'Jan': 1,
            'Feb': 2,
            'Mar': 3,
            'Apr': 4,
            'May': 5,
            'Jun': 6,
            'Jul': 7,
            'Aug': 8,
            'Sep': 9,
            'Oct': 10,
            'Nov': 11,
            'Dec': 12
        }
            tmp  = re.search(r'\w+, (\d+) (\w+) (\d+) (\d+):(\d+):(\d+)', datestr)
            day,mounth,year,hour,minute,second = tmp.groups()
            return datetime(int(year),fs[mounth[:3]],int(day),int(hour),int(minute),int(second))
        name = trans(xml.find('title').text)
        source = trans(xml.find('link').text)
        date = str2date(trans(xml.find('pubDate').text))
        downloadurl = trans(xml.find('enclosure').get('url',''))
        return cls(name,source,date,downloadurl)

    @classmethod
    def fromxml(cls,xml):
        def str2date(datestr):
            tmp = re.search(r'(\d+)-(\d+)-(\d+) (\d+):(\d+):(\d+)', datestr)
            year,mounth,day,hour,minute,second = tmp.groups()
            return datetime(int(year),int(mounth),int(day),int(hour),int(minute),int(second))
        name=trans(xml.get('name',''))
        source=trans(xml.get('source',''))
        date=trans(xml.get('date',''))
        downloadurl=trans(xml.get('downloadurl',''))
        isnew=eval(trans(xml.get('isnew','True')))

        date = str2date(date) if date else datetime.min
        return cls(name,source,date,downloadurl,isnew)

    @property
    def dayspast(self):
        return (datetime.now()-self.date.replace(hour=0,
                        minute=0, second=0, microsecond=0)).days

    @property
    def datestring(self):
        date = self.date.isoformat(' ')
        week = dict(enumerate(('周一', '周二', '周三', '周四', '周五', '周六', '周日'), 1))[self.date.isoweekday()]
        return f'{date} {week}'

    @staticmethod
    def hash2magnet(hash):
        return f'magnet:?xt=urn:btih:{hash}&tr=http://open.acgtracker.com:1096/announce'

    @staticmethod
    def hash2torrent(hash):
        return f'http://v2.uploadbt.com/?r=down&hash={hash}'

    @property
    def hash(self): # 40位哈希值
        hash = self.findhash(self.downloadurl) or self.findhash(self.source)
        if hash:
            return self.tohashv1(hash)

    @property
    def torrentlink(self):
        if self.downloadurl.startswith('magnet'):
            hash = self.hash
            if hash and len(hash)==40:
                return episode.hash2torrent(hash)
        else:
            return self.downloadurl

    @property
    def magnetlink(self):
        if self.downloadurl.startswith('magnet'):
            return self.downloadurl
        else:
            hash = self.hash
            if hash:
                return episode.hash2magnet(hash)

    def turn_old(self):
        self.isnew=False

    def download(self,path=None):
        if self.content is not None:
            res = self.content
        else:
            res=None
            for i in range(self.retry_times):
                try:
                    print(f'第{i+1}次尝试：',end='')
                    res=download(self.torrentlink)
                except Exception:
                    print('失败。。。')
                else:
                    res = res.content
                    self.content=res
                    break
            else:
                print('下不了，用磁链下吧')
        if res:
            pathname = path or 'torrents'
            if not os.path.exists(pathname):
                os.makedirs(pathname)
            name = ''.join(self.name.splitlines())
            name=re.sub(r'[\\/:*?"<>|]', ' ', name)
            fullpath=os.path.join(pathname,f'{name}.torrent')
            if os.path.exists(fullpath):
                counter=itertools.count(2)
                for i in counter:
                    fullpath=os.path.join(pathname,f'{name} {i}.torrent')
                    if not os.path.exists(fullpath):
                        break
            with open(fullpath,'wb') as f:
                f.write(res)
            self.turn_old()
            print('成功！！')
            return res

class bangumi:
    rss = RssSource()
    def __init__(self,name,keys:list[str],patterns=None,status='updating') -> None:
        self.contains={0:[]}
        self.name=name
        self.keys=keys
        self.patterns = patterns if patterns else [] #(正则表达式, 起始序号)
        self.status=status

    def tolist(self) -> list[episode]:
        tmp=[(index,ep) for index,ep in self.contains.items() if index>0]
        tmp.sort(key=lambda i:i[0])
        res=[ep for _,ep in tmp]
        res.extend(self.contains[0])
        return res

    def refresh(self):
        l = self.tolist()
        self.contains.clear()
        self.contains[0]=[]
        for ep in l:
            self.add(ep)

    def find(self,key=''):
        keys=self.keys[:]
        if key:
            keys.extend(key.split())
        searcher=bangumi('searcher',keys,[['.*',1]])
        print('正在搜索：',' '.join(keys))
        searcher.update()
        return searcher.tolist()

    def findindex(self,index):
        indexes=[]
        for ptn,begin in self.patterns:
            if begin not in indexes:
                indexes.append(begin)
        keys=[str(i+index-1).rjust(2,'0') for i in indexes]
        print(f'共 {len(keys)} 个搜索任务')
        res=[]
        for k in keys:
            res.extend(self.find(k))
        return res
    
    def choose(self,eps:list[episode]):
        indexes = [self.indexofepisode(ep) for ep in eps]
        matched = [ep for index,ep in zip(indexes,eps) if index is not None and index>0]
        others = [ep for index,ep in zip(indexes,eps) if index is None or index==0]
        available=matched+others
        print(f'共发现 {len(available)} 个项目')
        for i,ep in enumerate(available,1):
            if i == len(matched)+1:
                cs.out('\n警告：以下剧集无法识别，添加以下剧集建议添加相应过滤器',style='yellow')
            print(f'\n{i}\n{ep.datestring}\n{ep.name}')
        if available:
            chosen=input('\n请选择序号（多个序号用空格隔开）：')
            if chosen:
                for i in (int(s) for s in chosen.split()):
                    if 0<i<=len(available):
                        self.add(available[i-1],True)
                        print(f'已添加剧集：{available[i-1].name}')
                    else:
                        print(f'超出范围的序号：{i}')

    def search(self,key:str):
        key=key.strip()
        if key.isdecimal():
            tochoose=self.findindex(int(key))
        else:
            tochoose=self.find(key)
        self.choose(tochoose)

    def showpatterns(self):
        chart = table.Table(title='')
        chart.add_column('正则表达式',justify='left')
        chart.add_column('起始序号',justify='right')

        for pattern,index in self.patterns:
            chart.add_row(pattern,str(index))

        cs.print(chart)

    def show(self,detail=False):
        sd={
            'updating':'更新中',
            'end':'已完结',
            'abandoned':'已放弃',
            'pause':'暂时不看',
        }
        t = '(有更新) ' if self.hasnew() else ''
        cs.out(f'{t}',style='red',end='')
        print(self.name)
        if detail:
            print('关键词:', ' '.join(self.keys))
            if self.patterns:
                self.showpatterns()
        if self.tolist():
            l=self.last
            d=l.dayspast
            style = 'white'
            if self.status=='updating':
                if d>7:
                    style='rgb(255,0,0)'
                elif d==7:
                    style='rgb(0,0,255)'
                else:
                    style='rgb(255,255,255)'
            elif self.status=='end':
                style='rgb(0,255,0)'
            else:
                style='rgb(128,128,128)'
            print('最近更新：',end='')
            l.show()
        else:
            style='rgb(0,255,255)'
        cs.out(f'状态：{sd[self.status]}',style=style)
        if not (self.name and self.patterns):
            print('==提示：请添加过滤器或设置番剧名==')
        

    def hasnew(self):
        return any(ep.isnew for ep in self)
    
    @property
    def last(self):
        l=self.tolist()
        if l:
            return sorted(l,key=lambda ep:ep.date)[-1]

    def __iter__(self):
        return iter(self.tolist())

    def hasResource(self,ep:episode):
        return any(item.isSameResource(ep) for item in self.tolist())

    def __getitem__(self,i):
        return self.tolist()[i]
    
    def __len__(self):
        return len(self.tolist())

    def download(self):
        for ep in self.tolist():
            if ep.isnew:
                ep.download()

    def turnold(self):
        for ep in self.tolist():
            ep.turnold()
            
    def indexofepisode(self,ep):
        '''\
        None: 未找到匹配的过滤器，或未通过筛选
        =0: 筛选通过，但未找到剧集编号
        <0: 通过筛选找到了剧集编号，但小于起始集数
        >0: 通过筛选找到的剧集编号
        '''
        index = None
        for p,i in self.patterns:
            tmp = re.search(p,ep.name)
            if tmp:
                if index is None:
                    index=0
                res=tmp.groups()
                if res:
                    index = int(res[0])-i+1
                    if index<=0:
                        index-=1
                    else:
                        break
        return index

    def add(self,ep:episode|None,cover=False):
        if ep is None:
            return
        index = self.indexofepisode(ep)
        if index is not None:
            if index==0:
                for i,tep in enumerate(self.contains[0]):
                    if tep.isSameResource(ep):
                        if cover and tep != ep:
                            self.contains[0][i]=ep
                        break
                else:
                    self.contains[0].append(ep)
            elif index>0:
                if cover:
                    if self.contains.get(index) != ep:
                        self.contains[index]=ep
                else:
                    self.contains.setdefault(index,ep)

    def addpattern(self,pattern,begin=1):
        self.patterns.append([pattern,begin])

    @staticmethod
    def patten2text(patterns):
        return '\n'.join([f'{p},{n}' for p,n in patterns])

    @staticmethod
    def text2pattern(text:str):
        if text:
            k=[i.strip() for i in text.splitlines() if i.strip()] # 删除空白行
            k=[i.rsplit(',',maxsplit=1) for i in k] # 分离正则表达式与起始序号
            k=[[str(a).strip(),int(b)] for a,b  in k] # 最后的转换
            return k
        else:
            return []
    
    @property
    def xml(self):
        res = etree.Element('bm',name=self.name,keys=' '.join(self.keys),status=self.status)
        ptn = etree.SubElement(res,'ptn')
        ptn.text=bangumi.patten2text(self.patterns)
        for ep in self.tolist():
            res.append(ep.xml)
        return res
    
    @classmethod
    def fromxml(cls,xml:etree.Element):
        patterns=bangumi.text2pattern(trans(xml.find('ptn').text))
        res = cls(name=trans(xml.get('name','')),keys=trans(xml.get('keys','')).split(),patterns=patterns,status=trans(xml.get('status','updating')))
        for ep in xml.iterfind('ep'):
            res.add(episode.fromxml(ep))
        return res
    
    def updatefromrss(self,xml):
        for ep in xml.iterfind('item'):
            newep = episode.fromrss(ep)
            if newep is not None:
                self.add(newep)

    def update(self):
        newrss=bangumi.rss.download(self.keys)
        if newrss is not None:
            self.updatefromrss(newrss)
        else:
            print('完蛋！网络崩了')

class bangumiset:
    def __init__(self,name='') -> None:
        self.name=name
        self.contains:list[bangumi]=[]

    def tolist(self):
        return self.contains

    def add(self,bm):
        self.contains.append(bm)

    def hasnew(self):
        return any(bm.hasnew() for bm in self)
    
    @property
    def html(self):
        tostr = lambda k:' '.join(k)
        text='\n        '.join([f'<p><a href=\"http://kisssub.org/search.php?keyword={tostr(bm.keys)}\" target="_blank">{bm.name}</a></p>' for bm in self.contains])
        return f'''\
<!DOCTYPE HTML>
<html>
    <head>
        <meta charset="utf-8" />
        <title>{self.name}</title>
    </head>
    <body>
        {text}
    </body>
</html>'''
    
    def download(self):
        for bm in self.contains:
            bm.download()

    def turnold(self):
        for bm in self.contains:
            bm.turnold()

    @property
    def xml(self):
        res=etree.Element('xml',name=self.name)
        for bm in self.contains:
            res.append(bm.xml)
        return res
    
    @classmethod
    def fromxml(cls,xml):
        res=cls(name=trans(xml.get('name','')))
        for bm in xml.iterfind('bm'):
            res.add(bangumi.fromxml(bm))
        return res


    def __getitem__(self,i):
        return self.contains[i]
    
    def __contains__(self,o):
        return o in self.contains

    def __len__(self):
        return len(self.contains)

    def __iter__(self):
        return iter(self.contains)

def currenttarget():
    res=sourcedata
    for i in index[:2]:
        res=res[i]
    return res

def packwithlayer(item):
    if isinstance(item,bangumiset):
        layer = 0
    elif isinstance(item,bangumi):
        layer = 1
    elif isinstance(item,episode):
        layer = 2
    else:
        layer = None
    return layer,item

def selected(num=None):
    cur = currenttarget()
    if num is None:
        return packwithlayer(cur)
    if len(index)<2:
        tmp = cur
    else:
        tmp = sourcedata[index[0]]
    maxnum=len(tmp)
    if 0<num<=maxnum:
        return packwithlayer(tmp[num-1])
    else:
        print('不行了，不要，太多了，要被榨干了，不要再把陌生的东西插进来啊，要坏掉了')
        raise Exception('索引不在范围内')


def collect(filt=True,num=None):
    layer,target=selected(num)
    if layer==2:
        return [target]
    else:
        toprocess=[]
        if layer==1:
            toprocess.extend(target.tolist())
        elif layer==0:
            for i in target:
                toprocess.extend(i.tolist())
        if filt:
            toprocess = [ep for ep in toprocess if ep.isnew]
        return toprocess
    
def trans(s:str):
    if not s:
        return ''
    fs = {
        'lt': '<',
        'gt': '>',
        'amp': '&',
        'apos': '\'',
        'quot': '\"'
    }
    for flag, sym in fs.items():
        s = re.sub(f'&({flag};)+', sym, s)
    if any(f'&{flag};' in s for flag in fs):
        return trans(s)
    else:
        return s
    
def select(num, getin = True):
    if len(index)==0:
        maxnum=len(sourcedata)
        if 0<num<=maxnum:
            index.append(num-1)
    else:
        if len(index)==1:
            maxnum=len(sourcedata[index[0]]) if getin else len(sourcedata)
        else:
            maxnum=len(sourcedata[index[0]])
        if 0<num<=maxnum:
            if getin:
                if len(index)==1:
                    index.append(num-1)
                else:
                    index[1]=num-1
            else:
                index[-1]=num-1
    showselected()

def showselected(num=None):
    layer,target=selected(num)
    layer=['home','bangumi','episode'][layer]
    print(f'{layer} {target.name} selected')

def back():
    if index:
        index.pop()
    showselected()

def init():
    index.clear()
    showselected()

def turn_all(status):
    s = {'new':True,'old':False}
    tmp = collect()
    for ep in tmp:
        ep.isnew=s.get(status,ep.isnew)

def copy_all(filt=True,num=None):
    tmp = collect(filt,num)
    links = [ep.magnetlink for ep in tmp]
    if not all(links):
        rest = [ep for link,ep in zip(links,tmp) if not link]
        print(f'警告！{len(rest)} 个项目找不到磁力链接')
        for ep in rest:
            print(ep.name)
    text='\n'.join([i for i in links if i])
    if text:
        pyperclip.copy(text)
        print('已复制：')
        print(text)
    else:
        print('未发现项目')
    
def tree(filt=True):
    if filt:
        tmp=[(bm.name, [ep for ep in bm if ep.isnew]) for bm in sourcedata if bm.hasnew()]
    else:
        tmp=[(bm.name, [ep for ep in bm]) for bm in sourcedata]
    if tmp:
        for name,eps in tmp:
            print(name)
            for ep in eps:
                print(f'- {ep.name}')
            print()
    else:
        print('未发现项目')

def refresh(num=None):
    layer,target=selected(num)
    toprocess=[]
    if layer == 0:
        toprocess.extend(target.contains)
    elif layer == 1:
        toprocess.append(target)
    else:
        print('该命令不适用于剧集')
        return
    toprocess=[bm for bm in toprocess if bm.name and bm.patterns]
    for bm in toprocess:
        bm.refresh()
    

def update_all(filt=True,num=None):
    layer,target=selected(num)
    toprocess=[]
    if layer == 0:
        toprocess.extend(target.contains)
        if filt:
            toprocess=[bm for bm in toprocess if bm.status=='updating']
    elif layer == 1:
        toprocess.append(target)
    else:
        print('该命令不适用于剧集')
        return
    toprocess=[bm for bm in toprocess if bm.name and bm.patterns]
    if toprocess:
        s=len(toprocess)
        for i,bm in enumerate(toprocess,1):
            print(f'正在更新：第{i}个，共{s}个')
            bm.show()
            bm.update()
            print()
    else:
        print('未发现项目')

def download_all(filt=True,num=None):
    tmp = collect(filt,num)
    if tmp:
        print(f'共找到 {len(tmp)} 个项目')
        todo = [ep for ep in tmp if ep.torrentlink]
        tocopy = [ep for ep in tmp if not ep.torrentlink and ep.magnetlink]
        if tocopy:
            print(f'{len(tocopy)} 个项目因未找到种子链接，已为您复制磁力链接，下载完成需手动标记为旧项目')
            for ep in tocopy:
                print(ep.name)
            magnetlinks='\n'.join([ep.magnetlink for ep in tocopy])
            pyperclip.copy(magnetlinks)
        rest = len(tmp) - len(todo) - len(tocopy)
        if rest > 0:
            print(f'警告！{rest} 个项目找不到下载链接！') # 尽管不可能，但总要把所有情况都考虑清楚
            rest = [ep for ep in tmp if not ep.torrentlink and not ep.magnetlink]
            for ep in rest:
                print(ep.name)
        s = len(todo)
        for i,ep in enumerate(todo,1):
            print(f'正在下载：第{i}个，共{s}个')
            ep.show()
            ep.download()
            print()
    else:
        print('未发现项目')    

def auto_download():
    if sourcedata.contains:
        print('开始更新...')
        update_all()
        print('发现新项目：')
        tree()
        print('开始下载...')
        download_all()
        save()
    else:
        print('请先添加番剧')

def add_bangumi(name):
    layer,target=selected()
    if layer==0:
        if name in (bm.name for bm in target):
            if not input('已存在该番剧，是否继续？（默认否）[y/N]').lower() in ('y','yes'):
                return
        keys=(input('请输入关键词：')).split()
        tmp = bangumi(name,keys)
        while True:
            pattern = input('请输入过滤器：')
            if pattern == '':
                break
            if pattern in (p for p,i in tmp.patterns):
                if not input('过滤器已存在，是否继续？（默认否）[y/N]').lower() in ('y','yes'):
                    continue
            begin = input('起始序号(默认为1)：')
            begin = int(begin) if begin else 1
            tmp.addpattern(pattern,begin)
        target.add(tmp)
    else:
        print('请在主页中使用该命令')


def add_pattern(pattern):
    layer,target=selected()
    if layer==1:
        tmp = target
        if pattern in (p for p,i in tmp.patterns):
            if not input('过滤器已存在，是否继续？（默认否）[y/N]').lower() in ('y','yes'):
                return
        begin = input('起始序号(默认为1)：')
        begin = int(begin) if begin else 1
        tmp.addpattern(pattern,begin)
    else:
        print('请在番剧中使用该命令')

def search(key):
    layer,target=selected()
    if layer == 0:
        if key:
            maxnum = len(target)
            i = int(key)
            if 0<i<=maxnum:
                target[i-1].search('')
        else:
            print('请选择搜索内容')
    elif layer == 1:
        target.search(key)
    else:
        print('请在主页或番剧中使用该命令')

def setname(name):
    layer,target=selected()
    if layer<2:
        target.name = name
    else:
        print('勿要随便改动剧集名称')

def setstatus(status):
    layer,target=selected()
    if layer==1:
        if status in ('updating','end','abandoned','pause'):
            target.status=status
    else:
        print('请在番剧中使用该命令')

def setkeys(keys):
    layer,target=selected()
    if layer==1:
        target.keys=keys.split()
    else:
        print('请在番剧中使用该命令')

def setRSS(num):
    bangumi.rss.switch_source(num-1)
    showRSS()

def listRSS():
    for i,rss in enumerate(bangumi.rss.sources,1):
        print(f'{i} {rss.name}')

def showRSS():
    print(f'using RSS {bangumi.rss.name}')

def showlist(num=None):
    layer,target=selected(num)
    showselected(num)
    if layer<=1:
        for i,item in enumerate(target,1):
            print(i)
            item.show()
            print()
    else:
        print('请在非剧集中使用该命令')

def showitem(num=None):
    layer,target=selected(num)
    if layer>0:
        target.show()
    else:
        print('请在非主页中使用该命令')

def showdetail(num=None):
    layer,target=selected(num)
    if layer==1:
        target.show(True)
    else:
        print('请在番剧中使用该命令')

def export():
    filename = getFilename()
    if filename:
        path = filename+'.html'
        with open(path,'wt',encoding='utf8') as f:
            f.write(sourcedata.html)
        print(f'已保存到：{os.path.abspath(path)}')

def save():
    if filepath:
        path = filepath
    else:
        path = getFilename()
        if path:
            path+='.xml'
    if path:
        with open(path,'wb') as f:
            f.write(etree.tostring(sourcedata.xml,pretty_print=True,encoding='utf8'))

def para(s:str):
    s= s.strip().split(maxsplit=1)
    if len(s)==2:
        return s[0],s[1]
    elif len(s)==1:
        return s[0],''
    else:
        return '',''

def doc():
    print('''\
层级名称：主页(home)，番剧(bangumi)，剧集(episode)

exit
  退出程序
open num [num]
  选择子内容
select num [num]
  选择相同层级内容
back
  返回上一层级
home
  主页
show [num]
  查看项目详情 适用于：番剧，剧集
list [num]
  查看子内容列表 适用于：主页，番剧
detail [num]
  查看番剧详细信息 适用于：番剧
setname 名字
  为项目命名 适用于：主页，番剧
setkeys keys
  设置番剧关键词 适用于：番剧
listrss
  查看RSS源列表
setrss num
  设置当前使用的RSS源
showrss
  查看当前使用的RSS源
save
  保存项目
export
  导出为html方便浏览器查看
mark old|new|updating|end|abandoned|pause
  old|new 标记新旧
  updating|end|abandoned|pause 设置番剧状态 适用于：番剧
copy [all] [num]
  复制磁力链接
tree [new]
  以树的形式显示，使用参数 new 只显示新项目
refresh [num]
  重新过滤整理剧集 适用于：主页，番剧
update [all]  [num]
  更新番剧列表 适用于：主页，番剧
download [all] [num]
  下载种子文件
search idx|[key]
  替换剧集 适用于：主页，番剧
f
  更新下载一条龙 适用于：主页，番剧
add 名称
  添加子项目 在主页中为添加番剧，在番剧中为添加过滤器 适用于：主页，番剧
help
  帮助
''')

def load_from_file(path):
    global filepath
    path=os.path.abspath(path)
    with open(path,'rt',encoding='utf8') as f:
        sourcedata=bangumiset.fromxml(etree.fromstring(f.read()))
    filepath=path
    os.chdir(os.path.dirname(filepath))
    return sourcedata

def getFilename():
    if filepath:
        return os.path.splitext(os.path.basename(filepath))[0]
    elif sourcedata.name:
        return re.sub(r'[\\/:*?"<>|]', ' ', sourcedata.name)
    else:
        name = input('请输入文件名:')
        name=re.sub(r'[\\/:*?"<>|]', ' ', name)
        if name:
            sourcedata.name=name
        return name


index=[]
filepath=argv[1] if len(argv)>1 else ''

try:
    sourcedata=load_from_file(filepath) if filepath else bangumiset()
except Exception:
    print('文件有误，请检查文件格式是否正确')
    input('按回车键退出...')
    exit()

while True:
    try:
        command,paras  = para(input('>>>'))
        if command == 'exit':
            break
        elif command in ('select','open'):
            if paras:
                try:
                    for i in [int(i) for i in paras.split()]:
                        select(i,command=='open')
                except Exception:
                    print('啥玩意，听不懂')
            else:
                print('未选择项目')
        elif command == 'back':
            back()
        elif command == 'home':
            init()
        elif command=='show':
            showitem(int(paras) if paras else None)
        elif command=='list':
            showlist(int(paras) if paras else None)
        elif command=='detail':
            showdetail(int(paras) if paras else None)
        elif command == 'setname':
            if paras:
                setname(paras)
            else:
                print('未设置名称')
        elif command == 'setkeys':
            if paras:
                setkeys(paras)
            else:
                print('未设置关键词')
        elif command == 'listrss':
            listRSS()
        elif command == 'setrss':
            if paras:
                setRSS(int(paras))
            else:
                print('未设置RSS')
        elif command == 'showrss':
            showRSS()
        elif command == 'save':
            save()
        elif command == 'export':
            export()
        elif command == 'mark':
            if paras in ('new','old'):
                turn_all(paras)
            elif paras in ('updating','end','abandoned','pause'):
                setstatus(paras)
            else:
                print('请输入正确的标志：old|new|updating|end|abandoned|pause')
        elif command == 'copy':
            p1='all' not in paras
            p2=re.search('\\d+',paras)
            if p2:
                p2=int(p2.group(0))
            copy_all(p1,p2)
        elif command == 'tree':
            tree(paras=='new')
        elif command=='refresh':
            refresh(int(paras) if paras else None)
        elif command == 'update':
            p1='all' not in paras
            p2=re.search('\\d+',paras)
            if p2:
                p2=int(p2.group(0))
            update_all(p1,p2)
        elif command == 'download':
            p1='all' not in paras
            p2=re.search('\\d+',paras)
            if p2:
                p2=int(p2.group(0))
            download_all(p1,p2)
        elif command == 'search':
            search(paras)
        elif command == 'f':
            auto_download()
        elif command == 'add':
            if paras:
                if len(index)==0:
                    add_bangumi(paras)
                elif len(index)==1:
                    add_pattern(paras)
                else:
                    print('请在主页或番剧中使用该命令')
            else:
                print('未添加内容')
        elif command == 'help':
            doc()
        else:
            print('你要干什么呢？啊~不要~')
    except KeyboardInterrupt:
        print('555，你知道干得正起劲突然被打断是什么感觉吗？')
    except Exception as e:
        print('粗错啦~~')
        # raise
    finally:
        if sourcedata.contains:
            for bm in sourcedata:
                if bm.name and bm.patterns:
                    bm.refresh()
            save()

