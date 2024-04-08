# 简介
一款基于 RSS 订阅的交互命令行式番剧更新管理器，让你摆脱追番烦恼

你是否有如下烦恼：

- 网上找不到在线观看资源？

- 单纯使用RSS订阅，不知道怎么用关键词？

- 如果关键词少，只有番剧名称，就要从一大堆制作组和一大堆参数（1080p还是720p？简体还是繁体？字幕是外挂还是内嵌？）中迷失自我，有时忘记看到哪一集了还要到处去找？

- 如果关键词精确，结果发现这个制作组这次出的较慢，别家已经出了，在是否另外添加RSS订阅中徘徊？有时一更新发现上次还是第7集，这次一下蹦出个第9集，直接跳了一集，枉我等了那么久？早知如此，当初就应该去别的制作组下了！有时制作组甚至直接把这个番剧放弃不做了，等一个月都没消息？

- 有时下载下来的资源有问题，又要翻回RSS重新搜索？

- 有时制作组也发现了资源的问题，标题末尾加个 v2 就重新上传了，你不觉得是什么大问题，或根本不觉得有问题，但软件还是自动把它下下来了，尽管原先的版本已经下好了？

气死偶咧！

那么，本程序正适合你。

本程序的搜集番剧的方法结合了 RSS 订阅与正则表达式的优点，功能强大。每个番剧都有番剧名、搜索关键词和若干过滤器属性，帮助你第一时间获取最新剧集。先使用搜索关键词从 RSS 源获取番剧列表，再使用过滤器筛选出合适的剧集，并识别对应的级数，而不用顾虑是否是看过的剧集，不用顾虑哪一个制作组，只要是新的，与任意一个过滤器匹配的，统统下载。搜索关键词只需要输入刚需，比如，番剧名，1080p，简。至于其他的，制作组，是否已经看过，都交给过滤器！下载的剧集有问题？想换其他资源？没问题！我们提供番剧搜索替换功能，包您满意。

> 注意：筛选时，程序依次遍历 RSS 内容，取第一个遍历到的匹配任意一个过滤器的新项目，因此，对于收录剧集，过滤器没有优先级之分，哪个在前哪个在后都一样。所以不喜欢的制作组不要加进过滤器。若是实在不想要，你用 `search` 命令替换吧，或者把这个过滤器删了吧。什么？你问我怎么删？任何一个文本编辑器都行，保存之后退出程序，用记事本打开 .xml 保存的文件，格式好认的很，纯文本，手动删。而对于集数的识别，程序会优先取第一个能够正确识别集数的过滤器所识别出的集数。

# Quick Start

## 准备

安装 [Python3.11](https://www.python.org/downloads/windows/)，运行以下命令：

```cmd
pip install -i https://mirror.baidu.com/pypi/simple/ pyperclip requests lxml rich
```

## 第一步：添加番剧

```cmd
add bangumi_name
```

输入上面的命令，然后就会让你设置搜索关键词和过滤器

关键词：非必填项，每个关键词之间用空格分隔

过滤器：必填项，使用正则表达式过滤，使用 `re.Match.group(1)` 识别集数（懂了伐？集数用括号括起来，最多只能有1个分组（大神不用管），标题里的括号用反斜杠转义，非要用括号就用 `(?:regex)` 格式），一次一个，会让你输入多条规则。集数不是必须的，有一条正则表达式匹配就会收录。不懂的，或者觉得不需要过滤，关键词就能够分毫不差地把需要的东西找出来，不多也不少，就输入 `.*`，搜到了就收录，不过滤，网上正则表达式教程多得很，又不难。如果要结束添加，就什么都不要输进去，直接摁回车。

起始序号：配合过滤器识别剧集集数用的，防止一集收了两次。有的字幕组或压制组在做第二季内容时序号不会重新从 1 开始算，而是从第一季末尾开始，比如第一季有 12 集，他第二季就从 13 开始，这里就填 13。这里默认就是 1，不是其他的直接摁回车。

*必填项不是说你不填就不加了，而是这个没有那更新的时候就跳过不管了。也就是说，要让它更新，番剧名和过滤器一样都不能少。*

**示例：**

> 番剧名：
> 
> > 憧憬成为魔法少女
>
> 关键词：
> 
> > 憧憬成为魔法少女 1080
>
> 过滤器1
> 
> > 正则表达式：`LoliHouse.*?- (\d+).*?简`
> >
> > 起始序号：`1`
>
> 过滤器2
> 
> > 正则表达式：`喵萌奶茶屋.*?\[(\d+)\].*?简`
> > 
> > 起始序号：`1`
>
> 过滤器3
> 
> > 正则表达式：`桜都字幕组.*?\[(\d+)\].*?简`
> > 
> > 起始序号：`1`
>
> 过滤器4
> 
> > 正则表达式：`Billion.*?\[(\d+)\].*?简`
> > 
> > 起始序号：`1`
>
> 过滤器5
> 
> > 正则表达式：`悠哈.*?\[(\d+)\].*?CHS`
> > 
> > 起始序号：`1`

## 第二步：更新&下载

直接输这个然后摁回车：

```cmd
f
```

怎么样？简单吧？更新+下载+保存一条龙服务！

这里下载的种子会保存在 torrents 文件夹里面，自己去找bt下载器吧，这就不是我的事了

完了会自动保存番剧数据文件，当然第一次会让你设置文件名，保存在相同路径下.xml文件。

## 第三步：保存&退出

虽然在第二步的一条龙服务中已经保存过了，但依然建议在退出之前手动保存一下。谁知道你会不会忘记你还运行了其它的会改变内容的指令呢？

如果只是保存一下，之后还要做其他事情，则输入以下指令。

```cmd
save
```

若还没有指定文件名，会让你设置的

如果要退出，则输入以下指令。

```cmd
exit
```

这个指令会先保存文件再退出。因此，不要直接点终端上的叉号直接关闭程序，不然辛辛苦苦输进去的番剧就又要重来一遍了哟。

## 第二次启动

第二次启动直接把上次保存的数据文件，就你输入的文件名的.xml文件，拖到脚本文件上面。哦，记得在系统里把.py文件的默认打开方式设置为 Python，而不是 pycharm 或什么其他的东西，不然你就自己进命令行打开吧。

最后按 f 更新，齐活

# 常用指令

项目有3个层级，从高到低依次是：主页，番剧，剧集

## 选择 `select` | `open`

**用法：**

```cmd
select idx1 [idx2]
open idx1 [idx2]
```

**适用范围：主页，番剧，剧集**

在主页和剧集，两者作用一致

在番剧中：

`select` 选择与当前层级相同的序号为 idx 的项目

`open` 则进入当前选择项目的序号为 idx 的子项目

## 返回 `back`

**用法：**

```cmd
back
```

**适用范围：番剧，剧集**

返回上级

## 主页 `home`

**用法：**

```cmd
home
```

**适用范围：主页，番剧，剧集**

回到主页

## 目录树 `tree`

**用法：**

```cmd
tree [new]
```

**适用范围：主页，番剧，剧集**

以树的形式展开显示全部番剧和剧集，使用参数 new 只显示新项目

## 展示 `show` | `list`

**用法：**

```cmd
show [idx]
list [idx]
```

**适用范围：主页，番剧，剧集**

show 是展示当前选择的项目，list 是展示所包含的子项目

show 不可在主页中使用，而 list 不可在剧集中使用

可使用参数，预选择序号为idx的子内容

## 展示番剧详细信息 `detail`

**用法：**

```cmd
detail [idx]
```

**适用范围：主页，番剧，剧集**

展示番剧的全部信息，包括番剧名、关键词、过滤器等

可使用参数，预选择序号为idx的子内容

## 添加项目 `add`

**用法：**

```cmd
add bangumi_name|pattern
```

**适用范围：主页，番剧**

在主页中添加番剧，在番剧中添加过滤器

## 刷新 `refresh`

**用法：**

```cmd
refresh [num]
```

**适用范围：主页，番剧**

将剧集重新过滤整理，在过滤器有所改动时使用

## 标记 `mark`

**用法：**

```cmd
mark updating|end|abandoned|pause
mark old|new
```

**适用范围：主页，番剧，剧集**

参数为 `updating`|`end`|`abandoned`|`pause` 时，只在番剧中有用，将番剧标记为：更新中|已完结|已放弃追番|暂停更新以后再看

参数为 `old`|`new` 时，全局可用，将项目标记为：已观看的旧项目|刚出锅的新项目

## 保存 `save`

**用法：**

```cmd
save
```

**适用范围：主页，番剧，剧集**

如题，保存，没设置文件名就会让你设置一下

## 退出程序 `exit`

**用法：**

```cmd
exit
```

**适用范围：主页，番剧，剧集**

保存后退出

别点终端上的叉来退出，用这个指令，带保存的

## 复制 `copy`

**用法：**

```cmd
copy [all] [idx]
```

**适用范围：主页，番剧，剧集**

idx 预选择项目

all 忽略项目状态，全部复制，默认复制所有新项目

复制所选项目所包含的磁力链接

当种子下不下来时可以复制磁力链接下载

## 更新 `update`

**用法：**

```cmd
update [all] [idx]
```

**适用范围：主页，番剧**

默认只更新正在更新的番剧，使用 all 选项无视

## RSS源 `listrss`|`setrss`|`showrss`

**用法：**

```cmd
listrss
setrss [idx]
showrss
```

**适用范围：主页，番剧，剧集**

listrss 查看 RSS 列表

setrss 切换 RSS

showrss 查看当前使用的RSS

## 下载 `download`

**用法：**

```cmd
download [all] [idx]
```

**适用范围：主页，番剧，剧集**

默认只下载新剧集，使用 all 选项无视

## 帮助 `help`

**用法：**

```cmd
help
```

**适用范围：主页，番剧，剧集**

显示所有指令与用法

## 一条龙 `f`

**用法：**

```cmd
f
```

**适用范围：主页，番剧**

熟悉不？更新+下载+保存一条龙！当然还是要自己去bt下载软件去下的

## 替换剧集 `search`

**用法：**

```cmd
search idx|[key]
```

**适用范围：主页，番剧**

在主页中，`idx` 是必填项，搜索序号为 `idx` 的番剧

在番剧中，使用额外的关键词 `key` （可选）结合番剧关键词搜索，替换或添加剧集

当你对某一集的资源不满意时，可以使用这个指令换一个资源

搜索完成后会分成两个部分，第一部分是可识别集数的，直接选就行，第二部分是识别不了集数和任何一个过滤器都匹配不上的，建议先去添加过滤器，再添加剧集，不然加进去了也不会替换掉原来的剧集，或者根本加不进去。虽然本程序允许不带集数识别字段的过滤器（就是代表集数的分组），但推荐还是加进去。

## 设置名称 `setname`

**用法：**

```cmd
setname name
```

**适用范围：主页，番剧**

设置文件名（非拖拽启动）或番剧名

## 设置关键词 `setkeys`

**用法：**

```cmd
setkeys keys
```

**适用范围：番剧**

设置番剧关键词，每个关键词之间用空格隔开

## 关于删除项目

不提供这个功能，保存文件是纯文本的 xml 格式文件，特别好认，要删的话，用记事本吧，我累了（要不要再做一个重新读取文件的重载功能？啊，好麻烦，算了）

# 我的脚本使用步骤

一个新的季度开始，上个季度的番剧已经完结差不多了，又要开始搜罗新一个季度好看的番剧了，那么，如何使用本脚本快速更新番剧呢？

1. 在网上查找新番资讯，选择并记录感兴趣的番剧。
2. 在动漫下载的网站上搜索想要的番剧，选择合适的关键词，不求能够精确到具体的制作组、字幕类型和压制参数，但求准确到这一部番剧，再加上刚需，如1080，在脚本中录入番剧名和关键词。这时候没有搜索结果也没关系。
3. 使用`export`命令，将搜索链接导出为 html 文件，用浏览器打开，查看每一个番剧的更新情况。一有更新就看看是否已经添加相应的过滤器，如若没有，且是想要的，则加入过滤器中。当然，也可以使用 `search 1` 命令查找更新，在未识别的剧集中寻找中意的，加入到过滤器中去。如果没有忌口，大可添加这两个过滤器：`\[(\d+)\]`和`- (\d+)`，加入这两个可识别大多数制作组做的资源。如果嫌两个太多，就用这个：`\b(\d+)\b`，但我不保证不出问题。如果你是死忠党，必须看某一个制作组做的资源，那么，把制作组，番剧名等参数统统塞给关键词，过滤器用这个：`.*`，脚本将来者不拒。如果发现关键词不准确，可以使用`setkeys`命令重新设置关键词，这时如果已经使用脚本更新过，用记事本检查一下，删除不想要的剧集。这个步骤每个番剧在首发一周之后就可以不做了，人家都快更下一集了，还不出就退赛吧。虽然繁琐了一点，但这都是为了之后的轻松做的准备。
4. 关键词和过滤器渐渐确定下来之后，就可以开启愉悦的追番之旅了，快使用伟大的`f`大法去更新吧！
5. 在番剧完结后，使用`mark end`将番剧标记为已完结，下次更新时就会跳过这个番剧。

# 添加RSS源

本程序提供的源已经够用，但若还想添加其他源，可在 RssSource.sources （包含 RSS 链接生成方法的 RSS 源列表）中添加 RSS。

> 本程序假设 enclosure 链接要么是磁力链接，要么是种子文件下载直链，哈希值要么在 enclosure 链接中，要么在 link 中。

# 展望

就差个GUI了吧？

谁能帮我弄个GUI出来啊啊？

