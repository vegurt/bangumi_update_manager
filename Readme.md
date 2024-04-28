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

本程序的搜集番剧的方法结合了 RSS 订阅与正则表达式的优点，功能强大。每个番剧都有番剧名、搜索关键词和若干过滤器属性，帮助你第一时间获取最新剧集。先使用搜索关键词从 RSS 源获取番剧列表，再使用过滤器筛选出合适的剧集，并识别对应的级数，而不用顾虑是否是看过的剧集，不用顾虑哪一个制作组，只要是新的，与任意一个过滤器匹配的，统统下载。搜索关键词只需要输入刚需，比如，番剧名，1080p，简。至于其他的，制作组，是否已经看过，都交给过滤器！下载的剧集有问题？想换其他资源？没问题！我们提供番剧搜索替换功能。

# Quick Start

## 准备

安装 [Python3.11](https://www.python.org/downloads/windows/)，运行以下命令：

```cmd
pip install -i https://mirror.baidu.com/pypi/simple/ pyperclip requests lxml rich opencc-python-reimplemented
```

双击脚本文件

当然，也可以直接运行 releases 里发布的 .exe 可执行文件。

## 添加番剧

```
>>>add bangumi_name
```

输入上面的命令，然后就会让你设置搜索关键词和过滤器

关键词：非必填项，每个关键词之间用空格分隔

过滤器：必填项，使用正则表达式过滤，如果要结束添加，就什么都不要输进去，直接摁回车。使用 `re.Match.group(1)` 识别集数（懂了伐？集数用括号括起来，最多只能有1个分组（大神不用管），标题里的括号用反斜杠转义，非要用括号就用 `(?:regex)` 格式），一次一个，会让你输入多条规则。可以使用 `{index}` 代替集数，脚本会把它自动替换成集数的正则，也推荐使用这种方式，内置的正则考虑了有时会出现的7.5集这种集数。集数识别不是必须的，正则表达式匹配就会收录。不懂的，或者觉得不需要过滤，关键词就能够分毫不差地把需要的东西找出来，不多也不少，就输入 `.*`，搜到了就收录，不过滤，网上正则表达式教程多得很，又不难。

起始序号：配合过滤器识别剧集集数用的，防止一集收了两次。有的字幕组或压制组在做第二季内容时序号不会重新从 1 开始算，而是从第一季末尾开始，比如第一季有 12 集，他第二季就从 13 开始，这里就填 13。这里默认就是 1，不是其他的直接摁回车。

- 必填项不是说你不填就不加了，而是这个没有那更新的时候就跳过不管了。也就是说，要让它更新，番剧名和过滤器一样都不能少。
- 如果一个番剧暂时还没有资源，可以在添加该番剧时设置完番剧名后让你设置过滤器时直接摁回车退出，待以后有资源了再添加，详见 `add` 命令。

> 过滤器分为正向过滤器、反向过滤器和剧集过滤器。脚本将搜集匹配正向过滤器但不匹配反向过滤器的剧集，使用剧集过滤器识别集数，过滤器全部用正则表达式表示。在本脚本中，正向过滤器就是剧集过滤器，由正则表达式和起始集数构成，反向过滤器为若干个正则表达式。将与任意一个反向过滤器匹配的剧集排除，优先匹配排在前面的正向过滤器，集数取匹配到的过滤器所识别出的集数，不论该过滤器是否能识别集数，尽管后面有过滤器能够识别此剧集集数，只取第一个匹配到的过滤器识别的集数。因此，需要将能够识别集数的过滤器放在前面，如果要用万能过滤器 `.*` 就放最后面。

**示例：**

下面以 转生为第七王子，随心所欲的魔法学习之路 这部番剧为例。

先在动漫网站上搜索这部番剧，注意搜索关键词的选择，要准确到搜索结果里只有这一部番剧。

这里我用 `转生 七王子 1080`

然后观察搜索到的剧集，取感兴趣的那一个写成过滤器。这里以 Lolihouse 为例。

这个制作组的剧集名称如下：

`[LoliHouse] 转生为第七王子，随心所欲的魔法学习之路 / Dainana Ouji - 01 [WebRip 1080p HEVC-10bit AAC][简繁内封字幕]`

重要的特征有：LoliHouse，简

再加上剧集集数识别字段，观察集数周围具有标志性的符号，这里集数的左边有一横杠加一空格，因此集数过滤器如下：

`- {index}`

最后将重要的特征与集数过滤器按照前后顺序摆放，中间用 `.*?` 连接，得到最终的过滤器：

`LoliHouse.*?- {index}.*?简`

这个番剧本身就是第一季，也没有序章之类的第0集，因此第一集序号都是从1开始，不需要管

进入软件，添加番剧：

```
>>>add 转生为第七王子，随心所欲的魔法学习之路
请输入关键词：转生 七王子 1080

请输入过滤器（不输入任何内容直接按回车取消本次添加）:
Lilith-Raws.*?- {index}
是否为正向过滤器？（默认为正）[Y/n]
起始序号(默认为1)：
是否添加为最高优先级（默认是）[Y/n]

请输入过滤器（不输入任何内容直接按回车取消本次添加）:
沸羊羊.*?- {index}.*?简
是否为正向过滤器？（默认为正）[Y/n]
起始序号(默认为1)：
是否添加为最高优先级（默认是）[Y/n]

请输入过滤器（不输入任何内容直接按回车取消本次添加）:
芝士动物朋友.*?\[{index}\].*?简
是否为正向过滤器？（默认为正）[Y/n]
起始序号(默认为1)：
是否添加为最高优先级（默认是）[Y/n]

请输入过滤器（不输入任何内容直接按回车取消本次添加）:
LoliHouse.*?- {index}.*?简
是否为正向过滤器？（默认为正）[Y/n]
起始序号(默认为1)：
是否添加为最高优先级（默认是）[Y/n]

请输入过滤器（不输入任何内容直接按回车取消本次添加）:

请输入文件名:example
```

因为是第一个番剧，最后会让你设置文件名并自动保存文件。软件每次执行命令之后，如果存在至少一个番剧，都会自动保存。

这里我最看好LoliHouse做的番剧，因此最后添加它的过滤器，具有最高优先级，而最不希望下载 Lilith-Raws 的资源，它的资源是繁体，因此第一个添加，作为后备选择。

当一个剧集有多个制作组发布时，软件取优先级较高的那个。

再添加第二部番剧：

```
>>>add 约会大作战 第五季
请输入关键词：约会大作战 1080

请输入过滤器（不输入任何内容直接按回车取消本次添加）:

```

这里假设这部番剧还没有任何资源，添加过滤器时直接按回车退出，等以后有资源了再添加。

使用`list`指令查看已添加番剧：

```
>>>list

序号: 1
名称: 转生为第七王子，随心所欲的魔法学习之路
状态：更新中

序号: 2
名称: 约会大作战 第五季
状态：更新中
==提示：请添加正向过滤器或设置番剧名==
```

第二部番剧没有添加任何正向过滤器，弹出提示，不符合更新条件，只有番剧名、正向过滤器皆备才能更新。

查看到刚才添加的第一个番剧序号为1，使用 `detail` 命令查看详细信息：

```
>>>detail 1
名称: 转生为第七王子，随心所欲的魔法学习之路
关键词: 转生 七王子 1080
┏━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━┓
┃ 类型 ┃ 正则表达式                      ┃ 起始序号 ┃
┡━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━┩
│ 正向 │ LoliHouse.*?- {index}.*?简      │        1 │
│ 正向 │ 芝士动物朋友.*?\[{index}\].*?简 │        1 │
│ 正向 │ 沸羊羊.*?- {index}.*?简         │        1 │
│ 正向 │ Lilith-Raws.*?- {index}         │        1 │
└──────┴─────────────────────────────────┴──────────┘
共包含 0 个剧集
状态：更新中

tip: 剧集详细信息可使用 enum 命令查看
```

番剧的名称已设置，关键词已设置，过滤器已添加，下面就可以更新了

## 更新&下载

**方法一：**

直接输这个然后摁回车：

```
>>>f
```

怎么样？简单吧？更新+下载+保存一条龙服务！

这里下载的种子会保存在 torrents 文件夹里面，自己去找bt下载器吧，这就不是我的事了

完了会自动保存番剧数据文件，当然第一次会让你设置文件名，保存在相同路径下.xml文件。

**方法二：**

如果单独更新某一部番剧，也可以这样

```
>>>select idx
>>>update
>>>tree --new
>>>download
```

先使用 `select` 命令选择某一部番剧

再使用 `update` 更新

使用 `tree new` 查看更新之后多了哪些新项目

最后 `download` 下载种子文件

**方法三：**

如果你的时间充裕，时不时就想来更新一下，那么就没必要逐个番剧去更新了，这里提供一种快速更新的方法

```
>>>fq
```

这个命令将不适用任何关键词搜索番剧，然后由番剧在搜索到的剧集列表中自行找到与自己关键词与过滤器匹配的剧集并添加

之后自动下载种子文件

如果不希望自动下载，也可以这样

```
>>>qupdate
```

与一般的更新方法不同，这个不需要每个番剧都拉一个RSS，而是将最新发布的资源一起下载，在本地分配，更加快速。

然而，受限于RSS最大项目的限制，据我观察，不带任何关键词搜索得到的项目发布时间的跨度（最早与最晚的时间差）大概是一天左右，因此至少12小时要更新一次，不然就有可能错过了。

## 保存&退出

虽然在第二步的一条龙服务中已经保存过了，软件还会自动保存，但依然建议在退出之前手动保存一下。谁知道你会不会忘记你还运行了其它的会改变内容的指令呢？

如果只是保存一下，之后还要做其他事情，则输入以下指令。

```
>>>save
```

若还没有指定文件名，会让你设置的

如果要退出，则输入以下指令。

```
>>>exit
```

这个指令会先保存文件再退出。因此，不要直接点终端上的叉号直接关闭程序，不然辛辛苦苦输进去的番剧就又要重来一遍了哟。

## 第二次启动

第二次启动直接把上次保存的数据文件，就你输入的文件名的.xml文件，拖到脚本文件上面。哦，记得在系统里把.py文件的默认打开方式设置为 Python，而不是 pycharm 或什么其他的东西，不然你就自己进命令行打开吧。

然后想干嘛就干嘛

## 追加设置

若干天之后，某一步番剧有资源了，可使用 `add` 命令添加过滤器。

**示例：**

先使用`list`查看一下番剧编号：

```
>>>list
```

输出结果见[添加番剧](##添加番剧)。

这里我们需要设置的是第二部番剧，因此先选择第二部

```
>>>select 2
bangumi 约会大作战 第五季 selected
```

再添加过滤器：

```
>>>add Lilith.*?S05 - {index}
是否为正向过滤器？（默认为正）[Y/n]
起始序号(默认为1)：
是否添加为最高优先级（默认是）[Y/n]
```

查看一下详细信息：

```
>>>detail
名称: 约会大作战 第五季
关键词: 约会大作战 1080
┏━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━┓
┃ 类型 ┃ 正则表达式             ┃ 起始序号 ┃
┡━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━┩
│ 正向 │ Lilith.*?S05 - {index} │        1 │
└──────┴────────────────────────┴──────────┘
共包含 0 个剧集
状态：更新中

tip: 剧集详细信息可使用 enum 命令查看
```

这里已经选择了一部番剧，因此 detail 命令之后不需要再跟一个序号。

如果之前忘了设置关键词，或者有更好的关键词，这里也可以使用 `setkeys` 命令设置：

```
>>>setkeys 约会大作战 1080
```

然后回到主页更新：

```
>>>home
home example selected
>>>f
```

这里不回到主页直接 f 的话，只会自动更新当前选择的番剧，回到主页会更新所有番剧。

## 结束更新

又过了若干天，你对某个番剧不感兴趣了，又或者某个番剧完结了，就可以使用 `mark` 命令标记一下。软件只会更新状态为 `updating` 的番剧，其他的都跳过。

**示例：**

```
>>>select 1
bangumi 转生为第七王子，随心所欲的魔法学习之路 selected
>>>mark abandoned
>>>select 2
bangumi 约会大作战 第五季 selected
>>>mark end
>>>home
home example selected
>>>list

序号: 1
名称: 转生为第七王子，随心所欲的魔法学习之路
状态：已放弃

序号: 2
名称: 约会大作战 第五季
状态：已完结
```

# 指令大全

项目有3个层级，从高到低依次是：主页，番剧，剧集

## 选择 `select` | `open`

**用法：**

```
select idx
open idx
```

**别名：**

`select`: `sl`
`open`: `opn`

**适用范围：主页，番剧，剧集**

`select` 将当前项目的子项目设为活动项目

`open` 将当前项目的子项目设为当前项目

注意：无法将剧集设为当前项目

## 返回 `back`

**用法：**

```
back
```

**别名：** `bk`

**适用范围：番剧，剧集**

返回上级

## 主页 `home`

**用法：**

```
home
```

**别名：** `hm`

**适用范围：主页，番剧，剧集**

回到主页

## 清屏 `cls`

**用法：**

```
cls
```

**适用范围：主页，番剧，剧集**

清除终端显示内容

## 当前 `current`

**用法：**

```
current
```

**别名：** `cwd`

**适用范围：主页，番剧，剧集**

查看当前项目与活动项目

可以这样理解：除了不带预选择参数的 `list` 命令（作用于当前项目） 外，所有命令都是作用于活动项目。而 `select` 命令设置了一个全局的预选择序号，命令中的预选择序号是一个临时的预选择序号。

如果存在**临时**预选择序号，那么**活动项目**就是**当前项目**中序号为**临时**预选择序号的**子项目**；

否则，如果存在**全局**预选择序号，那么**活动项目**就是**当前项目**中序号为**全局**预选择序号的**子项目**；

如果还没有，那么**活动项目**就是**当前项目**。

## 目录树 `tree`

**用法：**

```
tree [--new] [idx]
```

**适用范围：主页，番剧**

以树的形式展开显示全部番剧和剧集

使用参数 `new` 只显示新项目

使用 idx 参数预选择子项目

## 展示 `show` | `list`

**用法：**

```
show [idx]
list [idx]
```

**别名：**

`list`: `ls`

**适用范围：主页，番剧，剧集**

`show` 是展示活动项目，`list` 是展示当前项目（不带 idx 参数）或活动项目（带 idx 参数）所包含的子项目

`show` 不可在主页中使用，而 `list` 不可在剧集中使用

可使用参数，预选择序号为 idx 的子内容

## 展示番剧详细信息 `detail`

**用法：**

```
detail [idx]
```

**别名：** `dt`

**适用范围：番剧**

展示番剧的全部信息，包括番剧名、关键词、过滤器等

可使用参数，预选择序号为 idx 的子内容

## 展示番剧详细信息 `enum`

**用法：**

```
enum [idx]
```

**适用范围：番剧**

按照识别到的剧集集数列举剧集

可使用参数，预选择序号为 idx 的子内容

## 添加项目 `add`

**用法：**

```
add bangumi_name|regex
```

**适用范围：主页，番剧**

在主页中添加番剧，在番剧中添加过滤器

## 刷新 `refresh`

**用法：**

```
refresh [--deep] [idx]
```

**别名：** `rf`

**适用范围：主页，番剧**

将剧集重新过滤整理，在过滤器有所改动时使用

`--deep` 先使用关键词过滤一遍

## 标记 `mark`

**用法：**

```
mark updating|end|abandoned|pause
mark old|new
```

**别名：** `mk`

**适用范围：主页，番剧，剧集**

参数为 `updating`|`end`|`abandoned`|`pause` 时，只在番剧中有用，将番剧标记为：更新中|已完结|已放弃追番|暂停更新以后再看

参数为 `old`|`new` 时，全局可用，将项目标记为：已观看的旧项目|刚出锅的新项目

## 保存 `save`

**用法：**

```
save
```

**别名：** `s`

**适用范围：主页，番剧，剧集**

如题，保存，没设置文件名就会让你设置一下

## 退出程序 `exit`

**用法：**

```
exit
```

**别名：** `quit`, `q`

**适用范围：主页，番剧，剧集**

保存后退出

别点终端上的叉来退出，用这个指令，带保存的

## 复制 `copy`

**用法：**

```
copy [--force] [idx]
```

**别名：** `cp`

**适用范围：主页，番剧，剧集**

idx 预选择项目

`--force` 忽略项目状态，全部复制，默认复制所有新项目

复制所选项目所包含的磁力链接

当种子下不下来时可以复制磁力链接下载

## 更新 `update`

**用法：**

```
update [--force] [idx]
```

**别名：** `up`

**适用范围：主页，番剧**

默认只更新正在更新状态的番剧，使用 `--force` 选项无视

## 快速更新 (quick update) `updateq`

**用法：**

```
updateq [--force] [opt]
    opt:
        -k key1 key2 ...
```

**别名：** `upq`

**适用范围：主页**

把最近发布的剧集一股脑全拿回来，至于是谁的，让番剧自己来认

默认只更新正在更新状态的番剧，使用 `--force` 选项无视

使用参数 k 可附加关键词

**示例：**

```
updateq -k lolihouse 1080
```

## RSS源 `listrss`|`setrss`|`showrss`

**用法：**

```
listrss
setrss [idx]
showrss
```

**别名：**

`listrss`: `lr`

`setrss`: `sr`

`showrss`: `rss`

**适用范围：主页，番剧，剧集**

`listrss` 查看 RSS 列表

`setrss` 切换 RSS

`showrss` 查看当前使用的 RSS

## 下载 `download`

**用法：**

```
download [--force] [idx]
```

**别名：** `dl`

**适用范围：主页，番剧，剧集**

默认只下载新剧集，使用 `--force` 选项无视

## 帮助 `help`

**用法：**

```
help
```

**别名：** `h`

**适用范围：主页，番剧，剧集**

显示所有指令与用法

## 一条龙 `f`

**用法：**

```
f [--force] [idx]
```

**适用范围：主页，番剧**

熟悉不？更新+下载+保存一条龙！当然还是要自己去bt下载软件去下的

## 快速自动更新下载 `fq`

**用法：**

```
fq [--force] [opt]
    opt:
        -k key1 key2 ...
```

**适用范围：主页**

使用参数 k 可附加关键词

解决了普通更新慢的问题

增加了需要频繁更新的问题

但这是小问题，相信大部分人都是闲着没事就 `f` 一下，那不如改成 `fq`，还能减轻一点服务器负担

## 替换剧集 `search`

**用法：**

```
search idx
search [key] [opt]
    opt:
        -i idx1,idx2,...
        --index=idx1,idx2,...
```

**别名：** `sch`

**适用范围：番剧**

当前项目是主页时，idx 是必填项，搜索序号为 idx 的番剧

当前项目是番剧时，使用额外的关键词 key（可选）结合番剧关键词搜索，替换或添加剧集

使用可选参数 index 可搜索集数为 idx1, idx2,... 的剧集

参数 index 只能放在最前面或最后面，不能放中间

当你对某一集的资源不满意时，可以使用这个指令换一个资源

搜索完成后会分成两个部分，第一部分是可识别集数的，直接选就行，第二部分是识别不了集数和任何一个过滤器都匹配不上的，建议先去添加过滤器，再添加剧集，不然加进去了也不会替换掉原来的剧集，或者根本加不进去。虽然本程序允许不带集数识别字段的过滤器（就是代表集数的分组），但推荐还是加进去。

**示例：**

```
search 1
search lolihouse -i 7,8,9
search lolihouse --index=7,8,9
```

## 快速搜索 (quick search) `searchq`

**用法：**

```
searchq [key] [opt]
    opt:
        -i idx1,idx2,...
        --index=idx1,idx2,...
```

**别名：** `schq`

**适用范围：主页**

不需要指定具体番剧，让选定的剧集自己找路回去

**示例：**

```
searchq 七王子 1080 -i 7,8,9
searchq 七王子 1080 --index=7,8,9
```

## 高级搜索 (expert search) `searche`

**用法：**

```
searche|sche [key] [opt1] [opt2] ...
  opt:
    -k idx
    -i idx1,idx2,...
    -o idx
    --force
    --cover
    --no-reset
    --enable-keys
    --disable-keys
    --choose
    -a key1_1 key1_2 ... -a key2_1 key2_2 ... -a ...
```

**别名：** `sche`

**适用范围：主页，番剧**

`key` 搜索关键词 **\*这个选项必须写在最前面\***

`-k` 从番剧获取关键词 默认：活动项

`-i` 集数 支持多个

`-o` 添加到哪个番剧 默认：活动项

`--force` 不考虑番剧状态

`--cover` 当存在相同剧集，但来源、制作组、字幕类型、压制参数等不完全相同时，覆盖剧集

`--no-reset` 覆盖剧集时不重置为新项目 仅 `--cover` 存在时有效

`--enable-keys` 添加番剧时是否自动查找匹配关键词的剧集 仅添加到单个番剧时有效，添加到主页必须使用关键词筛选

> **什么情况下应该使用 `--enable-keys` ？**
>
> 搜索关键词很模糊，不确定搜索结果是否有什么乱七八糟的东西，而过滤器在编写时默认搜索结果全部是这一部番剧对应的剧集，且活动项目是番剧或存在 `-o` 选项时
>
> 简单来说：
> 
> 1. 没使用 `-k` 选项，但使用了 `-o` 选项，关键词又很模糊时，应使用
> 
> 2. `-k` 选项与 `-o` 选项的值不同时，应使用
>

`--choose` 自行从搜索结果中挑选剧集

`-a` 附加关键词 支持多个 **\*这个选项必须写在最后面\***

有了这个命令，不管是更新单个番剧 (`update` 命令)，还是快速更新所有番剧 (`updateq` 命令)，亦或搜索替换 (`search` 命令)，快速搜索替换 (`searchq` 命令)，快速自动更新下载 (`fq` 命令)，还有其他骚操作，都能用这个命令实现，就问你牛不牛？（叉会腰）

**示例：**

**要更新单个剧集，就酱紫：**

在主页中：

```
searche -k 1 -o 1
```

在番剧中：

```
searche
```

**要使用快速更新方法，就在主页中酱紫：**

```
searche
```

**要使用关键词搜索，就酱紫：**

如果并非在番剧原有关键词上附加关键词搜索，可在主页中这样：

```
searche 转生 七王子 1080 -o 1 --force --cover --choose
```

在使用 `--choose` 选项自行挑选剧集时，你想做的大概就是选一个替换掉已有剧集，因此使用 `--cover` 选项

自己选择的剧集，自己难道还不清楚对应的番剧是否正在更新，还是已经放弃了？既然是自己选的，那一定给我加进去，因此使用 `--force` 选项

这里虽然在主页中使用了 `-o` 选项而没有使用 `-k` 选项，但关键词足够清晰，因此不需要 `--enable-keys` 选项

如果是附加关键词搜索，也可在主页中：

```
searche lolihouse -k 1 -o 1 --force --cover --choose
```

或在番剧中：

```
searche lolihouse --force --cover --choose
```

上面的在主页中使用，就是快速搜索

**一个使用 `--enable-keys` 选项的例子**

在主页中：

```
searche lolihouse -o 1 --enable-keys
```

这里搜索关键词没有指定一部番剧，搜索结果不一定是选定番剧的剧集，因此要用 `--enable-keys` 自行使用番剧内关键词先筛选一下

**一个使用了全部选项的命令：**

```
searche lolihouse -k 1 -i 7,8,9 -o 1 --force --cover --no-reset --enable-keys --choose -a 1080 简体 -a 1080 简繁
```

看到这个命令，你一定就能知道所有指令的具体用法

## 设置名称 `setname`

**用法：**

```
setname name
```

**别名：** `name`, `nm`

**适用范围：主页，番剧**

设置文件名（非拖拽启动）或番剧名

## 设置关键词 `setkeys`

**用法：**

```
setkeys keys
```

**别名：** `keys`, `ks`

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

