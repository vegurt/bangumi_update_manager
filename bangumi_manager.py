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
from rich import tree as rtree
import opencc

cs=console.Console()
cookie = requests.Session()

def download(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36 QIHU 360SE'}
    res=cookie.get(url, headers=headers, timeout=(5, 15))
    res.close()
    return res

class UserError(Exception):...

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
                    except Exception:
                        print('失败。。。')
                    else:
                        try:
                            res = self.extractRss(etree.fromstring(res.content))
                        except Exception:
                            res = None
                        if res is None:
                            print('网站返回了非RSS数据')
                            if sourcetest:
                                break
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
        print(self.detaildatestring)
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
        str2bool = lambda s:{'True' :True,  'true' :True, 'T':True,  't':True, '1':True,
                             'False':False, 'false':False,'F':False, 'f':False,'0':False}.get(s,True)
        isnew=str2bool(trans(xml.get('isnew','True')))

        date = str2date(date) if date else datetime.min
        return cls(name,source,date,downloadurl,isnew)

    @property
    def dayspast(self):
        return (datetime.now().date()-self.date.date()).days
    
    @property
    def pastdaysstring(self):
        match self.dayspast:
            case -2:
                return '（后天）'
            case -1:
                return '（明天）'
            case 0:
                return '（今天）'
            case 1:
                return '（昨天）'
            case 2:
                return '（前天）'
            case int(t) if t>0:
                return f'（{t}天前）'
            case int(t) if t<0:
                return f'（{t}天后）'
            case _:
                return ''

    @property
    def datestring(self):
        date = self.date.isoformat(' ')
        week = dict(enumerate(('周一', '周二', '周三', '周四', '周五', '周六', '周日'), 1))[self.date.isoweekday()]
        return f'{date} {week}'

    @property
    def detaildatestring(self):
        return f'{self.datestring} {self.pastdaysstring}'

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
                print('下载失败，可尝试使用 copy|cp 命令复制磁力链接下载')
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
    def __init__(self,name,keys:list[str]|None = None, patterns=None,status='updating') -> None:
        self.contains={'unrecognized':[]}
        self.name=name
        self.keys=keys if keys is not None else []
        self.patterns = patterns if patterns is not None else [[],[]] #(正则表达式, 起始序号)
        self.status=status

    def tolist(self) -> list[episode]:
        res = self.contains['unrecognized'][:]
        res.extend([ep for ep in self.contains.values() if isinstance(ep,episode)])
        res.sort(key=lambda ep:ep.date,reverse=True)
        return res

    def isavailable(self):
        return self.name and self.patterns[0]

    def isupdatable(self,filt=True):
        return self.isavailable() and (not filt or self.status == 'updating')

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
        print('正在搜索:',' '.join(keys))
        searcher.update()
        return searcher.tolist()

    def findindex(self,index:list[int|float],key=''):
        if self.patterns[0]:
            keys=[i+j-1 if i>0 else j for j in index for p,i in self.patterns[0]]
        else:
            keys=index
        keys = [int(i) if int(i)==i else round(i,2) for i in keys]
        keys=sorted(list(set(keys)))
        keys=[str(i).rjust(2,'0') for i in keys]
        _key = key.split()
        keys = [' '.join(_key+[i]) for i in keys]
        print(f'共 {len(keys)} 个搜索任务')
        res=[]
        for k in keys:
            for ep in self.find(k):
                if ep not in res:
                    res.append(ep)
        res.sort(key=lambda ep:ep.date,reverse=True)
        return res
    
    def find_advanced(self,key=''):
        _keys = key.split()
        start,end=0,len(_keys)
        index = None
        def tonum(s:str):
            res=[]
            s=[i for i in s.split(',') if i]
            for i in s:
                num = re.match(r'^[+-]?\d+\.?\d*$',i)
                if num is not None:
                    num=float(num.group())
                    res.append(int(num) if int(num) == num else num)
                else:
                    return
            return res
        if end>=1 and _keys[0].startswith('--index='):
            num = tonum(_keys[0][len('--index='):])
            if num is not None:
                index=num
                start+=1
        elif end>=1 and _keys[-1].startswith('--index='):
            num = tonum(_keys[-1][len('--index='):])
            if num is not None:
                index=num
                end-=1
        elif end>=2 and _keys[0] == '-i':
            num = tonum(_keys[1])
            if num is not None:
                index=num
                start+=2
        elif end>=2 and _keys[-2] == '-i':
            num = tonum(_keys[-1])
            if num is not None:
                index=num
                end-=2
        keys=' '.join(_keys[start:end])
        if index:
            return self.findindex(index,keys)
        else:
            return self.find(keys)

    def packeps(self,eps:list[episode]):
        tmp=bangumi('reduce_repitition',self.keys)
        tmp.addpattern('.*')
        tmp.add_list(eps)
        eps = tmp.tolist()
        status = [self.indexofepisode(ep)[1] for ep in eps]
        return list(zip(status,eps))

    @staticmethod
    def choose(eps:list[tuple[int,episode]]):
        code_description={
            0:'',
            1:'\n警告：以下剧集可能是上一季',
            2:'\n警告：以下剧集无法识别集数',
            3:'\n警告：以下剧集没有匹配的过滤器',
            4:'\n警告：以下剧集已被排除',
            5:'\n以下剧集不在追番列表中',
        }
        code_order=(0,2,3,1,4,5)
        block_size=10
        total_num=len(eps)
        print(f'共发现 {total_num} 个项目')
        if total_num>0:
            tochoose=[(i,s,ep) for i,(s,ep) in enumerate(sorted(eps,key=lambda i:code_order.index(i[0])),1)]
            def letchoose(command:str):
                command=command.strip()
                if command:
                    if 'q' in command:
                        return [] # 退出
                    else:
                        ep_all = [i[2] for i in tochoose]
                        if 'all' in command:
                            chosen = sorted(ep_all,key=lambda ep:ep.date,reverse=True)
                        else:
                            chosen = [int(s)-1 for s in command.split() if s.isdecimal() and 0<int(s)<=total_num]
                            chosen = [ep_all[i] for i in chosen]
                        return chosen
                else:
                    return None # 展示更多
            blocks=[tochoose[i:i+block_size] for i in range(0,total_num,block_size)]
            for block in blocks:
                status=None
                for i,s,ep in block:
                    if s!=status:
                        status=s
                        warn=code_description[status]
                        if warn:
                            cs.out(warn,style='yellow')
                    print(f'\n序号: {i}\n{ep.detaildatestring}\n{ep.name}\n参见：{ep.source}')
                chosen = letchoose(input('\n请选择序号（多个序号用空格隔开，全选输入 all ），或按回车显示更多，q退出：\n'))
                if chosen is not None:
                    return chosen
            print('\n没有更多项目了')
            chosen = letchoose(input('\n请选择序号（多个序号用空格隔开，全选输入 all ）：\n'))
            if chosen is not None:
                return chosen
        return []

    def search(self,key:str):
        key=key.strip()
        tochoose=self.find_advanced(key)
        chosen = self.choose(self.packeps(tochoose))
        if chosen:
            method = input('\na. 添加\nb. 下载\nc. 全部\nd. 取消\n选择需要的操作: ').strip().lower()
            if method in ('a','c'):
                self.add_list(chosen,True)
                for ep in chosen:
                    print(f'\n已处理:\n{ep.name}')
            if method in ('b','c'):
                bangumi.downloadlist(chosen)
        

    def showpatterns(self):
        chart = table.Table()
        chart.add_column('类型',justify='center')
        chart.add_column('正则表达式',justify='left')
        chart.add_column('起始序号',justify='right')

        for pattern,index in self.patterns[0]:
            chart.add_row('正向',pattern,str(index))
        for pattern in self.patterns[1]:
            chart.add_row('反向',pattern,'-')

        cs.print(chart,markup=False)

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

    @staticmethod
    def downloadlist(eps:list[episode]):
        s = len(eps)
        links=[]
        for i,ep in enumerate(eps,1):
            print(f'\n正在下载：第{i}个，共{s}个')
            ep.show()
            if ep.torrentlink:
                t=ep.download()
                if not t:
                    if ep.magnetlink:
                        links.append(ep.magnetlink)
                    else:
                        print('未找到磁力链接')
            elif ep.magnetlink:
                links.append(ep.magnetlink)
                print('未找到下载链接，但找到了磁力链接')
            else:
                print('未找到下载方式')
        if links:
            pyperclip.copy('\n'.join(links))
            print('已复制磁力链接')

    def turnold(self):
        for ep in self.tolist():
            ep.turnold()

    @staticmethod
    def indexofepisode_singlepattern(ep,pattern):
        p,i = pattern
        index = 0
        p=re.sub(r'\{[A-Za-z]*?\}',r'([+-]?\\d+\\.?\\d*)',p)
        tmp = re.search(p,ep.name)
        if tmp is not None:
            res=tmp.groups()
            if res and re.match(r'^[+-]?\d+\.?\d*$',res[0]):
                _index = float(res[0]) # 防备出现7.5集之类的合集集数
                index = _index-i+1 if i>0 else _index
                status = 0 if _index>=i else 1
            else:
                status=2
        else:
            status=3
        return index,status
            
    def indexofepisode(self,ep):
        '''\
        4: 被反向过滤器排除
        3: 未通过筛选
        2: 筛选通过，但未找到剧集编号
        1: 通过筛选，但编号不对
        0: 通过筛选找到了正确的剧集编号
        '''
        if self.is_excluded_episode(ep):
            return 0,4
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

    def match_episode(self,ep:episode):
        # 不区分大小写与简繁字体
        cc = opencc.OpenCC('t2s')
        return all(cc.convert(key).lower() in cc.convert(ep.name).lower() for key in self.keys)

    def match_list(self,eps:list[episode]):
        return [ep for ep in eps if self.match_episode(ep)]

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
        regex = pattern if pattern else input('\n请输入过滤器（不输入任何内容直接按回车取消本次添加）: \n')
        regex = regex.strip()
        if regex:
            direction = input('是否为正向过滤器？（默认为正）[Y/n]').lower() not in ('n','no')
            if regex not in (p for p,i in self.patterns[0]) if direction else self.patterns[1] or \
                   input('过滤器已存在，是否继续？（默认否）[y/N]').lower() in ('y','yes'):
                begin=1
                high_priority=True
                if direction:
                    begin = input('起始序号(请输入一个整数，默认为1)：').strip()
                    p=re.match(r'^[+-]?\d+\.?\d*$',begin)
                    if p is not None:
                        begin = round(float(p.group()))
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
                if (p:=re.search(r'positive: (.*),([+-]?\d+)',line)) is not None:
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
            print('网络似乎崩了')

class bangumiset:
    def __init__(self,name='') -> None:
        self.name=name
        self.contains:list[bangumi]=[]

    def searcher(self, keys=None, activate=True):
        tmp = bangumi('searcher',keys)
        if activate:
            tmp.addpattern('.*')
        return tmp

    def quick_add_list(self,eps,filt=True,cover=False):
        for bm in self:
            if bm.isupdatable(filt):
                bm.add_list(bm.match_list(eps),cover)

    def quick_update(self, keys=None, filt=True):
        tmp = self.searcher(keys)
        if keys is not None:
            print('正在查找:',' '.join(keys))
        tmp.update()
        self.quick_add_list(tmp.tolist(),filt)

    def quick_search(self,key:str,filt=False):
        key=key.strip()
        tmp = self.searcher(activate=False)
        tochoose=tmp.find_advanced(key)
        bms = [bm for bm in self if bm.isupdatable(filt)]
        def status_single(ep:episode,bm:bangumi):
            if bm.match_episode(ep):
                return bm.indexofepisode(ep)[1]
            else:
                return 5
        def statusvalue(ep):
            status = [status_single(ep,bm) for bm in bms]
            return min(status) if status else 5
        status = [statusvalue(ep) for ep in tochoose]
        toadd = tmp.choose(list(zip(status,tochoose)))
        if toadd:
            method = input('\na. 添加\nb. 下载\nc. 全部\nd. 取消\n选择需要的操作: ').strip().lower()
            if method in ('a','c'):
                self.quick_add_list(toadd,filt,True)
                for bm in bms:
                    for ep in bm.match_list(toadd):
                        print(f'\n{bm.name} 已处理:\n{ep.name}')
            if method in ('b','c'):
                bangumi.downloadlist(toadd)

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
    for i in index[0][:1]:
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
    maxnum=len(cur)
    if num is not None:
        num = num-1
    else:
        num = index[1]
    if num is not None:
        if 0<=num<maxnum:
            tmp = cur[num]
        else:
            print(f'当前项目只包含 {maxnum} 个子项目')
            raise UserError('索引不在范围内')
    else:
        tmp=cur
    return packwithlayer(tmp)

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
    cur = currenttarget()
    maxnum=len(cur)
    num-=1
    if 0<=num<maxnum:
        if getin:
            if len(index[0])<1:
                index[0].append(num)
                index[1]=None
            else:
                print(f'剧集不存在打开操作')
        else:
            index[1]=num
    else:
        print(f'当前项目只包含 {maxnum} 个子项目')
    showselected()
    
def showselected(num=None):
    def item_brief(layer,item):
        layer=['主页','番剧','剧集'][layer]
        return f'{layer} {item.name}'
    tc=f'序号{index[0][-1]+1} ' if index[0] else ''
    ta = f'序号{index[1]+1} ' if index[1] is not None else tc
    print(f'当前项目:\n{tc}{item_brief(*packwithlayer(currenttarget()))}')
    print(f'活动项目:\n{ta}{item_brief(*selected(num))}')

def back():
    if index[0]:
        t=index[0].pop()
        if index[1] is not None:
            index[1]=t
    else:
        index[1] = None
    showselected()

def init():
    index[0].clear()
    index[1] = None
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
    
def tree(filt=True,num=None):
    layer,target=selected(num)
    if layer<=1:
        toptree=rtree.Tree(target.name if target.name else '（未命名）')
        if layer == 0:
            tmp=[(bm.name, [ep for ep in bm if not filt or ep.isnew]) for bm in target if not filt or bm.hasnew()]
            if tmp:
                for name,eps in tmp:
                    _t = toptree.add(name)
                    if eps:
                        for ep in eps:
                            t = '（新）' if ep.isnew else ''
                            _t.add(f'{t}{ep.name}')
                    else:
                        _t.add('（空）')
            else:
                toptree.add('未发现项目')
        elif layer == 1:
            tmp = [ep for ep in target if not filt or ep.isnew]
            if tmp:
                for ep in tmp:
                    t = '（新）' if ep.isnew else ''
                    toptree.add(f'{t}{ep.name}')
            else:
                toptree.add('未发现项目')
        cs.print(toptree,markup=False)
    else:
        print('本命令只作用于主页和番剧')

def refresh(num=None):
    layer,target=selected(num)
    toprocess=[]
    if layer == 0:
        toprocess.extend(target.contains)
    elif layer == 1:
        toprocess.append(target)
    else:
        print('剧集不存在刷新操作')
        return
    toprocess=[bm for bm in toprocess if bm.isavailable()]
    for bm in toprocess:
        bm.refresh()
    
def quick_update(keys=None,filt=True):
    layer,target=selected()
    if layer == 0:
        target.quick_update(keys,filt)
    elif layer == 1:
        print('快速更新只用于主页\n更新单个番剧请使用一般更新命令 update|up')
    else:
        print('剧集不存在更新操作')

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
        print('剧集不存在更新操作')
        return
    toprocess=[bm for bm in toprocess if bm.isavailable()]
    if toprocess:
        s=len(toprocess)
        for i,bm in enumerate(toprocess,1):
            print(f'\n正在更新：第{i}个，共{s}个')
            bm.show()
            bm.update()
    else:
        print('未发现需要更新的项目')

def download_all(filt=True,num=None):
    tmp = collect(filt,num)
    if tmp:
        bangumi.downloadlist(tmp)
    else:
        print('未发现需要下载的项目')    

def auto_download_quick(keys=None,filt=True):
    layer,target=selected()
    if layer==0:
        print('\n开始更新...')
        quick_update(keys,filt)
        print('\n发现新项目：')
        tree()
        print('\n开始下载...')
        download_all()
        auto_save()
    elif layer == 1:
        print('快速自动更新下载只用于主页\n对单个番剧自动更新下载请使用一般自动更新命令 f')
    else:
        print('本命令只作用于主页')

def auto_download(filt=True,num=None):
    layer,target=selected(num)
    if layer<=1:
        print('\n开始更新...')
        update_all(filt,num)
        print('\n发现新项目：')
        tree(num=num)
        print('\n开始下载...')
        download_all(num=num)
        auto_save()
    else:
        print('本命令只作用于主页和番剧')

def add_bangumi(name):
    layer,target=selected()
    if layer==0:
        if name in (bm.name for bm in target):
            if input('已存在该番剧，是否继续？（默认否）[y/N]').lower() not in ('y','yes'):
                return
        keys=(input('请输入关键词：')).split()
        tmp = bangumi(name,keys)
        while tmp.add_pattern_interact():...
        target.add(tmp)
    else:
        print('请在 主页 添加番剧，可使用 home|hm 命令返回主页')


def add_pattern(pattern):
    layer,target=selected()
    if layer==1:
        target.add_pattern_interact(pattern)
    else:
        print('先选择一个番剧，而不是主页或剧集，再添加过滤器')

def quick_search(key):
    layer,target=selected()
    if layer == 0:
        target.quick_search(key)
    elif layer == 1:
        print('快速搜索只用于主页\n搜索单个番剧请使用一般搜索命令 search|sch')
    else:
        print('剧集不存在搜索操作')

def search(key:str):
    layer,target=selected()
    if layer<=1:
        if layer == 0:
            if key.isdecimal():
                num = int(key)
                layer,target=selected(num)
                key = ''
            else:
                print('在主页使用搜索命令，必须搭配番剧序号使用\n要在主页搜索，可尝试快速搜索命令 searchq|schq')
        if layer == 1:
            target.search(key)
    else:
        print('本命令只作用于主页和番剧')

def setname(name):
    layer,target=selected()
    if layer<2:
        target.name = name
    else:
        print('对于剧集，名称是判断两个剧集是否相同的重要信息，不可更改')

def setstatus(status):
    layer,target=selected()
    if layer==1:
        if status in ('updating','end','abandoned','pause'):
            target.status=status
    else:
        print('本命令只作用于番剧')

def setkeys(keys):
    layer,target=selected()
    if layer==1:
        target.keys=keys.split()
    else:
        print('本命令只作用于番剧')

def setRSS(num):
    bangumi.rss.switch_source(num-1)
    showRSS()

def listRSS():
    for i,rss in enumerate(bangumi.rss.sources,1):
        print(f'{i} {rss.name}')

def showRSS():
    print(f'using RSS {bangumi.rss.name}')

def showlist(num=None):
    layer,target=selected(num) if num is not None else packwithlayer(currenttarget())
    if layer<=1:
        l = list(target)
        if l:
            for i,item in enumerate(l,1):
                print('\n序号:',i)
                item.show()
        else:
            print('未发现任何子项目')
    else:
        print('本命令只作用于主页和番剧')

def showitem(num=None):
    layer,target=selected(num)
    if layer>0:
        target.show()
    else:
        print('本命令只作用于番剧和剧集，要查看所有番剧可使用 list|ls 命令')

def showdetail(num=None):
    layer,target=selected(num)
    if layer==1:
        target.show(True)
        print('\ntip: 剧集详细信息可使用 enum 命令查看')
    else:
        print('本命令只作用于番剧')

def enumepisode(num=None):
    layer,target=selected(num)
    if layer==1:
        target.enum()
    else:
        print('本命令只作用于番剧')

def doc():
    print('''\
层级名称：主页(home)，番剧(bangumi)，剧集(episode)

exit|quit|q
  退出程序
cls
  清屏
open|opn idx
  将当前项目的子项目设为当前项目
  适用于：番剧
select|sl idx
  将当前项目的子项目设为活动项目
back|bk
  返回上一层级
home|hm
  主页
current|cwd
  查看当前项目与活动项目
show [idx]
  查看项目详情 适用于：番剧，剧集
list|ls [idx]
  查看子内容列表 适用于：主页，番剧
detail|dt [idx]
  查看番剧详细信息 适用于：番剧
enum [idx]
  按照识别到的剧集集数列举剧集 适用于：番剧
setname|name|nm name
  为项目命名 适用于：主页，番剧
setkeys|keys|ks keys
  设置番剧关键词 适用于：番剧
listrss|lr
  查看RSS源列表
setrss|sr idx
  设置当前使用的RSS源
showrss|rss
  查看当前使用的RSS源
save|s
  保存项目
export|p
  导出为html方便浏览器查看
mark|mk old|new|updating|end|abandoned|pause
  old|new 标记新旧
  updating|end|abandoned|pause 设置番剧状态 适用于：番剧
copy|cp [all] [idx]
  复制磁力链接
tree [new] [idx]
  以树的形式显示，使用参数 new 只显示新项目 适用于：主页，番剧
refresh|rf [idx]
  重新过滤整理剧集 适用于：主页，番剧
updateq|upq [all] [opt]
  opt:
    -k key1 key2 ...
  使用参数 k 可附加关键词 快速更新番剧 适用于：主页
update|up [all]  [idx]
  更新番剧列表 适用于：主页，番剧
download|dl [all] [idx]
  下载种子文件
searchq|schq [key] [opt]
  opt:
    -i idx1,idx2,...
    --index=idx1,idx2,...
  快速替换剧集 使用 index 参数可搜索特定剧集 适用于：主页
search|sch 替换剧集
  search idx
     适用于：主页
  search [key] [opt]
     opt:
       -i idx1,idx2,...
       --index=idx1,idx2,...
     使用 index 参数可搜索特定剧集 适用于：番剧
f [all] [idx]
  更新下载一条龙 适用于：主页，番剧
fq [all] [opt]
  opt:
    -k key1 key2 ...
  快速自动更新下载 使用参数 k 可附加关键词 适用于：主页
add name|regex
  添加子项目 在主页中为添加番剧，在番剧中为添加过滤器 适用于：主页，番剧
help|h
  帮助

中括号[]中的是非必要内容，不带[]的是必要内容
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

def export():
    filename = getFilename()
    if filename:
        path = filename+'.html'
        with open(path,'wt',encoding='utf8') as f:
            f.write(sourcedata.html)
        print(f'已保存到：{os.path.abspath(path)}')

def save():
    global filepath
    if filepath:
        path = filepath
    else:
        path = getFilename()
        if path:
            path+='.xml'
    if path:
        path=os.path.abspath(path)
        with open(path,'wb') as f:
            f.write(etree.tostring(sourcedata.xml,pretty_print=True,encoding='utf8'))
        filepath=path

def auto_save():
    if filepath or sourcedata.name or sourcedata.contains:
        save()

def parse_paras(s:str):
    s= s.strip().split(maxsplit=1)
    if len(s)==2:
        return s[0],s[1]
    elif len(s)==1:
        return s[0],''
    else:
        return '',''

def extract_paras(s:str,key=''):
    ps = s.split()
    p=None
    switch=False
    for k in ps:
        if p is None and k.isdecimal():
            p=int(k)
        elif k==key:
            switch=True
        else:
            print(f'未知参数: {k}')
    return switch, p

def extract_keys(s:str):
    ps = s.split()
    start=0
    filt=True
    for i,k in enumerate(ps):
        if k=='all':
            filt=False
        elif k=='-k':
            start=i+1
            break
        else:
            print(f'未知参数: {k}')
    return ps[start:] if start > 0 else None, filt

index=[[],None]

filepath=argv[1] if len(argv)>1 else ''

try:
    sourcedata=load_from_file(filepath) if filepath else bangumiset()
except Exception:
    print('文件有误，请检查文件格式是否正确')
    input('按回车键退出...')
    exit()

while True:
    try:
        command,paras  = parse_paras(input('>>> '))
        match command:
            case 'exit'|'quit'|'q':
                break
            case 'cls':
                os.system('cls')
            case 'select'|'sl'|'open'|'opn':
                p1,p2=extract_paras(paras)
                if p2 is not None:
                    try:
                        select(p2, command in ('open','opn'))
                    except Exception:
                        print('请使用正确的序号')
                else:
                    print('请搭配序号使用')
            case 'back'|'bk':
                back()
            case 'home'|'hm':
                init()
            case 'current'|'cwd':
                showselected()
            case 'show':
                showitem(extract_paras(paras)[1])
            case 'list'|'ls':
                showlist(extract_paras(paras)[1])
            case 'detail'|'dt':
                showdetail(extract_paras(paras)[1])
            case 'enum':
                enumepisode(extract_paras(paras)[1])
            case 'setname'|'name'|'nm':
                if paras:
                    setname(paras)
                else:
                    print('未设置名称')
            case 'setkeys'|'keys'|'ks':
                if paras:
                    setkeys(paras)
                else:
                    print('未设置关键词')
            case 'listrss'|'lr':
                listRSS()
            case 'setrss'|'sr':
                p1,p2=extract_paras(paras)
                if p2 is not None:
                    setRSS(p2)
                else:
                    print('未设置RSS')
            case 'showrss'|'rss':
                showRSS()
            case 'save'|'s':
                save()
            case 'export'|'p':
                export()
            case 'mark'|'mk':
                if paras in ('new','old'):
                    turn_all(paras)
                elif paras in ('updating','end','abandoned','pause'):
                    setstatus(paras)
                else:
                    print('在番剧中，使用 updating|end|abandoned|pause 设置番剧状态，在任意地方使用 old|new 标记所有包含剧集的新旧')
            case 'copy'|'cp':
                p1,p2=extract_paras(paras,'all')
                copy_all(not p1, p2)
            case 'tree':
                p1,p2=extract_paras(paras,'new')
                tree(p1,p2)
            case 'refresh'|'rf':
                refresh(extract_paras(paras)[1])
            case 'updateq'|'upq':
                quick_update(*extract_keys(paras))
            case 'update'|'up':
                p1,p2=extract_paras(paras,'all')
                update_all(not p1, p2)
            case 'download'|'dl':
                p1,p2=extract_paras(paras,'all')
                download_all(not p1, p2)
            case 'searchq'|'schq':
                quick_search(paras)
            case 'search'|'sch':
                search(paras)
            case 'fq':
                auto_download_quick(*extract_keys(paras))
            case 'f':
                p1,p2=extract_paras(paras,'all')
                auto_download(not p1, p2)
            case 'add':
                if paras:
                    layer = selected()[0]
                    if layer==0:
                        add_bangumi(paras)
                    elif layer==1:
                        add_pattern(paras)
                    else:
                        print('本命令只作用于主页和番剧，主页中添加番剧，番剧中添加过滤器')
                else:
                    print('请搭配添加内容使用，例如：add 憧憬成为魔法少女')
            case 'help'|'h':
                doc()
            case _:
                print('请输入命令，或使用 help|h 命令查看所有命令')
    except KeyboardInterrupt:
        print('操作被用户中断')
    except UserError:
        ...
    except Exception:
        print('粗错啦~~')
        # raise
    finally:
        for bm in sourcedata:
            if bm.isavailable():
                bm.refresh()
        auto_save()

