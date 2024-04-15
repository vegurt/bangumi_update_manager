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
    def __init__(self,name,keys:list[str] = None, patterns=None,status='updating') -> None:
        self.contains={'unrecognized':[]}
        self.name=name
        self.keys=keys if keys is not None else []
        self.patterns = patterns if patterns is not None else [[],[]] #(正则表达式, 起始序号)
        self.status=status

    def tolist(self) -> list[episode]:
        tmp=[(index,ep) for index,ep in self.contains.items() if isinstance(index,(int,float))]
        tmp.sort(key=lambda i:i[0])
        res=[ep for _,ep in tmp]
        res.extend(sorted(self.contains['unrecognized'],key=lambda ep:ep.date))
        return res

    def isavailable(self):
        return self.name and self.patterns[0]

    def clear(self):
        self.contains.clear()
        self.contains['unrecognized']=[]

    def refresh(self):
        tmp = bangumi('ep_station',self.keys,self.patterns)
        tmp.add_list(self.tolist())
        self.contains=tmp.contains

    def find(self,key=''):
        keys=self.keys[:]
        if key:
            keys.extend(key.split())
        searcher=bangumi('searcher',keys)
        searcher.addpattern('.*')
        print('正在搜索：',' '.join(keys))
        searcher.update()
        return searcher.tolist()

    def findindex(self,index):
        indexes=[]
        for ptn,begin in self.patterns[0]:
            if begin not in indexes:
                indexes.append(begin)
        keys=[str(i+index-1).rjust(2,'0') for i in indexes]
        print(f'共 {len(keys)} 个搜索任务')
        res=[]
        for k in keys:
            res.extend(self.find(k))
        return res
    
    def choose(self,eps:list[episode]):
        tmp=bangumi('reduce_repitition',self.keys)
        tmp.addpattern('.*')
        tmp.add_list(eps)
        eps = tmp.tolist()
        excluded = []
        available = []
        for ep in eps:
            if self.is_excluded_episode(ep):
                excluded.append(ep)
            else:
                available.append(ep)
        status = [self.indexofepisode(ep)[1] for ep in available]
        matched = [ep for s,ep in zip(status,available) if s==0]
        unrecognized = [ep for s,ep in zip(status,available) if s==2]
        others = [ep for s,ep in zip(status,available) if s==3]
        lastseason = [ep for s,ep in zip(status,available) if s==1]
        tochoose=matched+unrecognized+others+lastseason+excluded
        print(f'共发现 {len(tochoose)} 个项目')
        def withwarning(eplist,start,warn=''):
            i=start
            if eplist:
                if warn:
                    cs.out(warn,style='yellow')
                for ep in eplist:
                    print(f'\n序号: {i}\n{ep.datestring} {ep.dayspast}天前\n{ep.name}\n参见：{ep.source}')
                    i+=1
            return i
        start = withwarning(matched,1)
        start = withwarning(unrecognized,start,'\n警告：以下剧集无法识别集数')
        start = withwarning(others,start,'\n警告：以下剧集没有匹配的过滤器')
        start = withwarning(lastseason,start,'\n警告：以下剧集可能是上一季')
        start = withwarning(excluded,start,'\n警告：以下剧集已被排除')
        if tochoose:
            chosen=input('\n请选择序号（多个序号用空格隔开，全选输入 all ）：')
            if chosen:
                if 'all' not in chosen:
                    chosen = [int(s)-1 for s in chosen.split() if 0<int(s)<=len(tochoose)]
                    chosen = [tochoose[i] for i in chosen]
                else:
                    chosen = tochoose
                self.add_list(chosen,True)
                for ep in chosen:
                    print(f'已添加剧集：{ep.name}')

    def search(self,key:str):
        key=key.strip()
        if key.isdecimal():
            tochoose=self.findindex(int(key))
        else:
            tochoose=self.find(key)
        self.choose(tochoose)

    def showpatterns(self):
        chart = table.Table(title='')
        chart.add_column('类型',justify='center')
        chart.add_column('正则表达式',justify='left')
        chart.add_column('起始序号',justify='right')

        for pattern,index in self.patterns[0]:
            chart.add_row('正向',pattern,str(index))
        for pattern in self.patterns[1]:
            chart.add_row('反向',pattern,'-')

        cs.print(chart)

    def show(self,detail=False):
        sd={
            'updating':'更新中',
            'end':'已完结',
            'abandoned':'已放弃',
            'pause':'暂时不看',
        }
        t = '(有更新) ' if self.hasnew() else ''
        cs.out(t,style='red',end='')
        print('名称:',self.name)
        sum_matched = len(self.contains) - 1
        sum_others = len(self.contains['unrecognized'])
        sum_eps = sum_matched + sum_others
        if detail:
            print('关键词:', ' '.join(self.keys))
            if any(self.patterns):
                self.showpatterns()
            print(f'共包含 {sum_eps} 个剧集')
        if sum_eps > 0:
            if detail:
                indexes = [i for i in self.contains if isinstance(i,(int,float))]
                print(f'有 {sum_matched} 个识别到集数的剧集')
                if indexes:
                    max_index = max(indexes)
                    if int(max_index) == max_index:
                        max_index = int(max_index)
                    max_index = str(max_index).rjust(2,'0')
                    print(f'最新一集是第 {max_index} 集')
                print(f'有 {sum_others} 个未识别到集数的剧集')
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
        if not self.isavailable():
            print('==提示：请添加正向过滤器或设置番剧名==')
            
    def enum(self):
        sum_eps = len(self)
        if not sum_eps:
            print('未发现项目')
        else:
            eps = [(index,ep) for index,ep in self.contains.items() if isinstance(index,(int,float))]
            eps.sort(key=lambda x:x[0])
            for index,ep in eps:
                t = int(index)
                s = str(t if t == index else index).rjust(2,'0')
                print(f'\n第 {s} 集')
                ep.show()
            if self.contains.get('unrecognized'):
                cs.out('\n警告：以下剧集无法识别集数',style='yellow')
                for ep in sorted(self.contains['unrecognized'],key=lambda ep:ep.date):
                    print()
                    ep.show()

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
        return len(self.contains['unrecognized']) + len(self.contains) - 1

    def download(self):
        for ep in self.tolist():
            if ep.isnew:
                ep.download()

    def turnold(self):
        for ep in self.tolist():
            ep.turnold()

    @staticmethod
    def indexofepisode_singlepattern(ep,pattern):
        p,i = pattern
        index = 0
        p=re.sub(r'\{.*?\}',r'(\\d+\\.?\\d*)',p)
        tmp = re.search(p,ep.name)
        if tmp is not None:
            res=tmp.groups()
            if res and re.match(r'^\d+\.?\d*$',res[0]):
                index = float(res[0])-i+1 # 防备出现7.5集之类的合集集数
                status = 0 if index>0 else 1
            else:
                status=2
        else:
            status=3
        return index,status
            
    def indexofepisode(self,ep):
        '''\
        3: 未通过筛选
        2: 筛选通过，但未找到剧集编号
        1: 通过筛选，但编号不对
        0: 通过筛选找到了正确的剧集编号
        '''
        index,status = 0,3
        for p in self.patterns[0]:
            index_t,status_t = self.indexofepisode_singlepattern(ep,p)
            if status_t<=status:
                index,status=index_t,status_t
                if status<=2:
                    break
        return index,status


    def _add_episode(self,ep:episode,index:int|float|None,cover=False):
        if index is None:
            for i,tep in enumerate(self.contains['unrecognized']):
                if tep.isSameResource(ep):
                    if cover and tep != ep:
                        self.contains['unrecognized'][i]=ep
                    break
            else:
                self.contains['unrecognized'].append(ep)
        else:
            if cover:
                if self.contains.get(index) != ep:
                    self.contains[index]=ep
            else:
                self.contains.setdefault(index,ep)
        
    def is_excluded_episode(self,ep:episode):
        return any(re.search(p,ep.name) for p in self.patterns[1])

    def add(self,ep:episode,cover=False):
        if not self.is_excluded_episode(ep):
            index,status = self.indexofepisode(ep)
            if status in (0,2):
                self._add_episode(ep,index if status==0 else None,cover)

    def add_list(self,eps:list[episode],cover=False):
        toadd = [ep for ep in eps if not self.is_excluded_episode(ep)]
        tmp = bangumi('temp_list',self.keys,self.patterns)
        flags = [True]*len(toadd)
        for p in tmp.patterns[0]:
            for i,(flag,ep) in enumerate(zip(flags,toadd)):
                if flag:
                    index,status=tmp.indexofepisode_singlepattern(ep,p)
                    if status <= 2:
                        if status != 1:
                            tmp._add_episode(ep,index if status==0 else None)
                        flags[i]=False
        for i,ep in tmp.contains.items():
            if isinstance(i,(int,float)):
                self._add_episode(ep,i,cover)
        for ep in tmp.contains['unrecognized']:
            self._add_episode(ep,None,cover)


    def addpattern(self,pattern,begin=1,ispos=True,high_priority=True):
        if ispos:
            if high_priority:
                self.patterns[0].insert(0,[pattern,begin])
            else:
                self.patterns[0].append([pattern,begin])
        else:
            self.patterns[1].append(pattern)
        self.refresh()

    def add_pattern_interact(self,pattern=''):
        regex = pattern if pattern else input('请输入过滤器：')
        regex = regex.strip()
        if regex:
            direction = input('是否为正向过滤器？（默认为正）[Y/n]').lower() not in ('n','no')
            if regex not in (p for p,i in self.patterns[0]) if direction else self.patterns[1] or \
                   input('过滤器已存在，是否继续？（默认否）[y/N]').lower() in ('y','yes'):
                begin=1
                high_priority=True
                if direction:
                    begin = input('起始序号(默认为1)：')
                    begin = int(begin) if begin else 1
                    high_priority = input('是否添加为最高优先级（默认是）[Y/n]').lower() not in ('n','no')
                self.addpattern(regex,begin,direction,high_priority)
            return True


    @staticmethod
    def patten2text(patterns):
        res=[]
        for p,i in patterns[0]:
            res.append(f'positive: {p},{i}')
        for p in patterns[1]:
            res.append(f'negative: {p}')
        return '\n'.join(res)

    @staticmethod
    def text2pattern(text:str):
        res = [[],[]]
        if text:
            for line in text.splitlines():
                if (p:=re.search(r'positive: (.*),(\d+)',line)) is not None:
                    res[0].append((p.group(1).strip(),int(p.group(2))))
                elif (p:=re.search(r'negative: (.*)',line)) is not None:
                    res[1].append(p.group(1).strip())
        return res
    
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
        toadd = [episode.fromxml(ep) for ep in xml.iterfind('ep')]
        res.add_list([ep for ep in toadd if ep is not None])
        return res
    
    def updatefromrss(self,xml):
        toadd = [episode.fromrss(ep) for ep in xml.iterfind('item')]
        self.add_list([ep for ep in toadd if ep is not None])

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
    return layer,target

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
            print('\n'+name)
            if eps:
                for ep in eps:
                    t = '（新）' if ep.isnew else ''
                    print(f'- {t}{ep.name}')
            else:
                print('（空）')
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
        print('你走吧 (back) ，我 (episode) 只有被刷的份，你不该来这里的')
        return
    toprocess=[bm for bm in toprocess if bm.isavailable()]
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
        print('被关在这阴森的城堡里，哪还有出去的机会，感谢你的好意，但是，我 (episode) 出不去啦')
        return
    toprocess=[bm for bm in toprocess if bm.isavailable()]
    if toprocess:
        s=len(toprocess)
        for i,bm in enumerate(toprocess,1):
            print(f'\n正在更新：第{i}个，共{s}个')
            bm.show()
            bm.update()
    else:
        print('真没有了，大人，一滴都没有了，要不，换换口味？')

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
            print(f'\n正在下载：第{i}个，共{s}个')
            ep.show()
            ep.download()
        if s>0:
            print('\n大事已成，现在，只剩下最后的步骤了')
    else:
        print('这里的您都已经用过了，大部分用过一次就坏了，若是有中意的，倒是可以喊来。炉鼎难寻，需要进点货 (update) 么？还是，换点别的口味 (add) ？')    

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
        print('只我一人，空守王座，尊敬的友人啊，为我打下一处城池 (add) ，你就能拥有这至高的权利')

def add_bangumi(name):
    layer,target=selected()
    if layer==0:
        if name in (bm.name for bm in target):
            if not input('已存在该番剧，是否继续？（默认否）[y/N]').lower() in ('y','yes'):
                return
        keys=(input('请输入关键词：')).split()
        tmp = bangumi(name,keys)
        while tmp.add_pattern_interact():...
        target.add(tmp)
    else:
        print('英雄，你是否在寻找：主页 (home) ？我们的主一定会准许你的')


def add_pattern(pattern):
    layer,target=selected()
    if layer==1:
        target.add_pattern_interact(pattern)
    else:
        print('哦？我猜你要找的是番剧吧，那个喜欢搞特权的，只有他才会有这么奇怪的需求')

def search(key):
    layer,target=selected()
    if layer == 0:
        if key:
            maxnum = len(target)
            i = int(key)
            if 0<i<=maxnum:
                target[i-1].search('')
            else:
                print('再看看，是不是搞错了？')
        else:
            print('这么多材料，都没有你能看上的么？')
    elif layer == 1:
        target.search(key)
    else:
        print('什么玩意？我们这没有！')

def setname(name):
    layer,target=selected()
    if layer<2:
        target.name = name
    else:
        print('我们的一切早已不再属于我们，只有尊敬的上主才有能力修改我们的名字')

def setstatus(status):
    layer,target=selected()
    if layer==1:
        if status in ('updating','end','abandoned','pause'):
            target.status=status
    else:
        print('这是番剧的私事，我管不了')

def setkeys(keys):
    layer,target=selected()
    if layer==1:
        target.keys=keys.split()
    else:
        print('这是番剧的私事，我管不了')

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
    if layer<=1:
        l = list(target)
        if l:
            for i,item in enumerate(l,1):
                print('\n序号:',i)
                item.show()
        else:
            print('很高兴遇见你，客人，我想出去转转 (update) ，这样，我也许就能带回些特产了')
    else:
        print('回去 (back) 吧，朋友，我只是一个微末的最底层罢了，当然，你也可以找这里的主人 (home)')

def showitem(num=None):
    layer,target=selected(num)
    if layer>0:
        target.show()
    else:
        print('你想要什么？我这里有很多，但在那之前，你需要选择 (select) 一件')

def showdetail(num=None):
    layer,target=selected(num)
    if layer==1:
        target.show(True)
    else:
        print('番剧也许知道这是什么')

def enumepisode(num=None):
    layer,target=selected(num)
    if layer==1:
        target.enum()
    else:
        print('去问番剧')

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
enum [num]
  按照识别到的剧集集数列举剧集 适用于：番剧
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
  替换剧集 适用于：番剧
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
                print('是什么让你犹豫不前？快作出选择吧，少年')
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
        elif command=='enum':
            enumepisode(int(paras) if paras else None)
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
                print('啊啦啊啦，这不是我可爱的小honey么？这次是来干什么呢？是想要玩弄瓦塔西 (updating|end|abandoned|pause)，还是我的宝贝们呢 (old|new) ？')
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
                    print('我没有这个功能，我只是一介平民，不可能会有下属的，永远不会')
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
                if bm.isavailable():
                    bm.refresh()
            save()

