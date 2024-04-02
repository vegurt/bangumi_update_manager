import os
import re
import itertools
from sys import argv
from datetime import datetime
import pyperclip
import requests
from lxml import etree
from rich import console

cs=console.Console()
cookie = requests.Session()

def download(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36 QIHU 360SE'}
    res=cookie.get(url, headers=headers, timeout=(5, 15))
    res.close()
    return res

class RssSource:
    'RSS订阅与文件下载'
    def __init__(self) -> None:
        self.sources=[
            'http://kisssub.org/rss{key}.xml',
            'http://comicat.org/rss{key}.xml',
            'http://1.kisssub.115000.xyz/rss{key}.xml',
            'http://2.kisssub.115000.xyz/rss{key}.xml',
            'http://3.kisssub.115000.xyz/rss{key}.xml',
            'http://4.kisssub.115000.xyz/rss{key}.xml',
            'http://5.kisssub.115000.xyz/rss{key}.xml',
            'http://1.comicat.122000.xyz/rss{key}.xml',
            'http://2.comicat.122000.xyz/rss{key}.xml',
            'http://3.comicat.122000.xyz/rss{key}.xml',
            'http://4.comicat.122000.xyz/rss{key}.xml',
            'http://5.comicat.122000.xyz/rss{key}.xml',
            'http://1.kisssub.org/rss{key}.xml',
            'http://2.kisssub.org/rss{key}.xml',
            'http://3.kisssub.org/rss{key}.xml',
            'http://2.kisssub.net/rss{key}.xml',
            'http://3.kisssub.net/rss{key}.xml',
            'http://1.comicat.org/rss{key}.xml',
            'http://www.miobt.com/rss{key}.xml',
            # 'gg.al',
            # 'comicat.122000.xyz',
        ]
        self.index=0
        self.retry_times=3
        
    
    @property
    def source(self):
        return self.sources[self.index]

    def addsources(self,sources):
        if isinstance(sources,list):
            self.sources.extend(sources)
        elif isinstance(sources,str):
            self.sources.append(sources)
    
    def switch_source(self,num=None):
        if num is None:
            self.index+=1
            if self.index>=len(self.sources):
                self.index=0
        elif isinstance(num,int) and 0<=num<len(self.sources):
            self.index=num
            

    def rsslink(self,keys:list):
        if keys:
            keys='-'+'+'.join(' '.join(keys).split())
        else:
            keys=''
        return self.source.replace('{key}',keys)

    def download(self,keys):
        for i in range(len(self.sources)):
            t = '主站点' if self.index == 0 else f'备用站点{self.index}'
            print(f'正在使用 {t}')
            for j in range(self.retry_times):
                try:
                    print(f'第{j+1}次尝试：',end='')
                    res=download(self.rsslink(keys))
                except Exception:
                    print('失败。。。')
                else:
                    print('成功！！')
                    return res.content
            self.switch_source()


class episode:
    def __init__(self,name,source,date,downloadurl='',isnew=True) -> None:
        self.name = name
        self.source=source
        self.date:datetime=date
        self.downloadurl=downloadurl
        self.isnew:bool=isnew
        self.content=None
        self.retry_times=3

    def show(self):
        t = '(新) ' if self.isnew else ''
        print(f'{self.datestring} {self.dayspast}天前')
        cs.out(f'{t}',style='red',end='')
        print(self.name)
    
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
    def hash(self):
        hash = re.match('https?://(?:.*)/show-([0-9a-zA-Z]*)\\.html',self.source)
        if hash:
            return hash.group(1)

    @property
    def torrentlink(self):
        if self.downloadurl:
            return self.downloadurl
        else:
            hash = self.hash
            if hash:
                return episode.hash2torrent(hash)

    @property
    def magnetlink(self):
        hash = self.hash
        if hash:
            return episode.hash2magnet(hash)

    def turn_old(self):
        self.isnew=False

    def download(self):
        if not self.content is None:
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
        if res:
            name = ''.join(self.name.splitlines())
            name=re.sub(r'[\\/:*?"<>|]', ' ', name)
            if not os.path.exists('torrents'):
                os.mkdir('torrents')
            path = f'.\\torrents\\{name}.torrent'
            if os.path.exists(path):
                counter=itertools.count(2)
                for i in counter:
                    path = f'.\\torrents\\{name} {i}.torrent'
                    if not os.path.exists(path):
                        break
            with open(path,'wb') as f:
                f.write(res)
            self.turn_old()
            print('成功！！')
            return res

class bangumi:
    rss = RssSource()
    def __init__(self,name,keys,patterns=None,status='updating') -> None:
        self.contains={0:[]}
        self.name=name
        self.keys=keys
        self.patterns = patterns if patterns else [] #(正则表达式, 起始序号)
        self.status=status

    def tolist(self):
        tmp=[(index,ep) for index,ep in self.contains.items() if index>0]
        tmp.sort(key=lambda i:i[0])
        res=[ep for _,ep in tmp]
        res.extend(self.contains[0])
        return res

    def search(self,index):
        indexes=[]
        for ptn,begin in self.patterns:
            if begin not in indexes:
                indexes.append(begin)
        searcher=[bangumi('searcher',self.keys+[str(i+index-1).rjust(2,'0')],['.*']) for i in indexes]
        
        res_rough=[]
        print(f'共{len(searcher)}个搜索任务')
        for i in searcher:
            keys=' '.join(i.keys)
            print(f'正在搜索：{keys}')
            i.update()
            res_rough.extend(i.tolist())

        res_matched,res_other=[],[]
        for ep in res_rough:
            i = self.indexofepisode(ep)
            if i==index: #确定是需要的剧集
                res_matched.append(ep)
            elif i is None or i==0: #不确定是哪一集
                res_other.append(ep)
        res_all=res_matched+res_other
        print('\n找到以下项目：')
        for i,ep in enumerate(res_all,1):
            if i == len(res_matched)+1:
                print('\n警告：以下剧集无法识别，添加以下剧集建议添加相应过滤器')
            print(f'{i} {ep.name}')
        chosen=input('请选择序号：')
        if chosen:
            chosen=res_all[int(chosen)-1]
            self.add(chosen,True)

    def show(self):
        sd={
            'updating':'更新中',
            'end':'已完结',
            'abandoned':'已放弃',
            'pause':'暂时不看',
        }
        t = '(有更新) ' if self.hasnew() else ''
        cs.out(f'{t}',style='red',end='')
        print(self.name)
        if self.contains:
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
        

    def hasnew(self):
        return any([ep.isnew for ep in self])
    
    @property
    def last(self):
        return sorted(self.tolist(),key=lambda ep:ep.date)[-1]

    def __iter__(self):
        return iter(self.tolist())

    def __contains__(self,ep):
        return ep.hash in [i.hash for i in self.tolist()]

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

    def add(self,ep,cover=False):
        index = self.indexofepisode(ep)
        if not index is None and ep not in self:
            if index==0:
                self.contains[0].append(ep)
            elif index>0:
                if not (index in self.contains and not cover):
                    self.contains[index]=ep

    def addpattern(self,pattern,begin=1):
        self.patterns.append([pattern,begin])

    @staticmethod
    def patten2text(patterns):
        return '\n'.join([f'{p},{n}' for p,n in patterns])

    @staticmethod
    def text2pattern(text:str):
        if text:
            k=[i.strip() for i in text.splitlines() if i.strip()]
            k=[i.rsplit(',',maxsplit=1) for i in k]
            k=[[str(a).strip(),int(b)] for a,b  in k]
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
        for ep in xml.find('channel').iterfind('item'):
            self.add(episode.fromrss(ep))

    def update(self):
        newrss=etree.fromstring(bangumi.rss.download(self.keys))
        self.updatefromrss(newrss)

class bangumiset:
    def __init__(self,name='') -> None:
        self.name=name
        self.contains:list[bangumi]=[]

    def tolist(self):
        return self.contains

    def add(self,bm):
        self.contains.append(bm)

    def hasnew(self):
        return any([bm.hasnew() for bm in self])
    
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

def selected(num=None):
    res=sourcedata
    pre_index=index[:1]
    layer=0
    for i in index if num is None else pre_index:
        res=res[i]
        layer+=1
    if not num is None:
        if 0<num<=len(res):
            i = num-1
        elif len(index)>len(pre_index):
            i = index[len(pre_index)]
        else:
            i=None
        if not i is None:
            res=res[i]
            layer+=1
    return layer,res


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
    if any([f'&{flag};' in s for flag in fs]):
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
    text='\n'.join([ep.magnetlink for ep in tmp])
    pyperclip.copy(text)
    
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
        s = len(tmp)
        for i,ep in enumerate(tmp,1):
            print(f'正在下载：第{i}个，共{s}个')
            ep.show()
            ep.download()
            print()
    else:
        print('未发现项目')    

def auto_download():
    print('开始更新...')
    update_all()
    print('发现新项目：')
    tree()
    print('开始下载...')
    download_all()
    if sourcedata.contains:
        save()

def add_bangumi(name):
    layer,target=selected()
    if layer==0:
        keys=(input('请输入关键词：')).split()
        tmp = bangumi(name,keys)
        while True:
            pattern = input('请输入过滤器：')
            if pattern == '':
                break
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
        begin = input('起始序号(默认为1)：')
        begin = int(begin) if begin else 1
        tmp.addpattern(pattern,begin)
    else:
        print('请在番剧中使用该命令')

def search(index):
    layer,target=selected()
    if layer==1:
        target.search(index)
    else:
        print('请在番剧中使用该命令')

def setname(name):
    layer,target=selected()
    target.name = name

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

def export():
    if not sourcedata.name:
        sourcedata.name=input('请输入文件名：')
    with open(f'{sourcedata.name}.html','wt',encoding='utf8') as f:
        f.write(sourcedata.html)

def save():
    if len(argv)>1:
        filename = argv[1]
    elif sourcedata.name:
        filename = sourcedata.name
    else:
        filename = input('请输入文件名：')
    if filename:
        if not filename.endswith('.xml'):
            filename = filename + '.xml'
        sourcedata.name =os.path.splitext(os.path.split(filename)[1])[0]
        with open(filename,'wb') as f:
            f.write(etree.tostring(sourcedata.xml,pretty_print=True,encoding='utf8'))

def para(s):
    s= s.split(maxsplit=1)
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
setname 名字
  为项目命名 适用于：主页
setkeys keys
  设置番剧关键词 适用于：番剧
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
  以树的形式显示
update [all]  [num]
  更新番剧列表 适用于：主页，番剧
download [all] [num]
  下载种子文件
search [num]
  替换剧集 适用于：番剧
f
  更新下载一条龙
add 名称
  添加子项目 在主页中为添加番剧，在番剧中为添加过滤器 适用于：主页，番剧
help
  帮助
''')

sourcedata=bangumiset()
index=[]

if len(argv)>1:
    with open(argv[1],'rt',encoding='utf8') as f:
        sourcedata=bangumiset.fromxml(etree.fromstring(f.read()))


while True:
    try:
        command,paras  = para(input('>>>'))
        if command == 'exit':
            break
        elif command in ('select','open'):
            try:
                for i in [int(i) for i in paras.split()]:
                    select(i,command=='open')
            except Exception:
                print('啥玩意，听不懂')
        elif command == 'back':
            back()
        elif command == 'home':
            init()
        elif command=='show':
            showitem(int(paras) if paras else None)
        elif command=='list':
            showlist(int(paras) if paras else None)
        elif command == 'setname':
            setname(paras)
        elif command == 'setkeys':
            setkeys(paras)
        elif command == 'save':
            save()
        elif command == 'export':
            export()
        elif command == 'mark':
            if paras in ('new','old'):
                turn_all(paras)
            elif paras in ('updating','end','abandoned','pause'):
                setstatus(paras)
        elif command == 'copy':
            p1='all' not in paras
            p2=re.search('\\d+',paras)
            if p2:
                p2=int(p2.group(0))
            copy_all(p1,p2)
        elif command == 'tree':
            tree(paras=='new')
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
            search(int(paras))
        elif command == 'f':
            auto_download()
        elif command == 'add':
            if len(index)==0:
                add_bangumi(paras)
            elif len(index)==1:
                add_pattern(paras)
            else:
                print('请在主页或番剧中使用该命令')
        elif command == 'help':
            doc()
        else:
            print('你要干什么呢？啊~不要~')
    except Exception:
        print('粗错啦~~')

if sourcedata.contains:
    save()

