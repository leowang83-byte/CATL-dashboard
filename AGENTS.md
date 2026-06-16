\# CATL Resource Intelligence Platform



\## AGENTS.md



本文件用于指导 Codex / AI coding agent 修改本项目。

所有代码修改、页面重构、数据接入和视觉优化，都必须遵守本文件与 `DESIGN.md`。



\---



\# 1. Project Purpose



本项目是面向 CATL 资源事业部的全球锂资源投研与决策支持系统。



系统目标不是简单展示数据，而是将：



\* 全球资源新闻

\* 公司公告

\* 交易所披露

\* 价格信号

\* 供需预测

\* 项目成本

\* 国家风险

\* 投资优先级



转化为管理层可理解、可跟踪、可执行的资源战略信号。



核心目标：



1\. 资源安全

2\. 资源成本

3\. 资源投资

4\. 资源风险



本系统不是：



\* 新闻网站

\* 普通行情终端

\* 矿山ERP

\* 单纯可视化展示页

\* 图表堆叠型Dashboard



\---



\# 2. Key Users



目标用户：



\* 董事长

\* 资源事业部总经理

\* 资源投资负责人

\* 高级研究员



表达方式必须偏管理层语言：



\* 先结论

\* 再依据

\* 最后行动建议



避免：



\* 原始数据堆砌

\* 过长解释

\* 研究员式堆指标

\* 无结论图表

\* 新闻门户式排版



\---



\# 3. Core Information Architecture



本系统的页面分工如下：



```text

周报页 = 本周情报

核心驾驶舱 = 战略总览

其他标签页 = 分析依据

```



任何页面修改都必须遵守该分工。



禁止将所有内容都堆入核心驾驶舱。



禁止让周报页和核心驾驶舱重复展示同一类信息。



\---



\# 4. Dashboard Pages



当前顶部标签页包括：



1\. CATL资源事业部周报

2\. 核心驾驶舱

3\. LCE走势预测

4\. 全球资源地图与AISC成本

5\. 政策与新闻风险

6\. 投资优先级与AI策略

7\. Market Monitor 市场监测中心

8\. 数据与模型说明



\---



\# 5. Page Responsibilities



\## 5.1 CATL资源事业部周报



定位：



周度资源战略情报简报。



该页面只回答三件事：



1\. 本周发生了什么

2\. 对 CATL 有什么影响

3\. 管理层需要做什么



允许展示：



\* 本周重大事件 TOP5

\* 单条事件影响

\* 市场是否验证重大事件

\* AI研判与决策建议

\* 本周建议动作

\* 原文链接

\* 数据来源和更新时间



禁止展示：



\* 长篇新闻全文

\* 复杂图表

\* 全球地图

\* AISC成本曲线

\* 投资矩阵

\* 长表格

\* 长期供需预测

\* 与核心驾驶舱重复的战略状态灯



周报页的关键词：



```text

事件

影响

验证

行动

```



\---



\## 5.2 核心驾驶舱



定位：



管理层战略总览页。



核心驾驶舱不是所有模块的拼接页，而是整个系统的战略状态入口。



核心驾驶舱只允许展示：



1\. 全球锂资源战略状态

2\. 核心状态灯

3\. 资源配置状态

4\. 结构性约束与机会

5\. 数据更新状态



核心驾驶舱应尽量控制在一屏到一屏半内读完。



\---



\### 5.2.1 核心驾驶舱必须保留的内容



\#### 一、全球锂资源战略状态



用于一句话总结当前资源战略环境。



示例：



```text

当前全球锂资源处于价格低位修复、供给扰动上升、低成本资源窗口期阶段。

```



\---



\#### 二、核心状态灯



建议展示 5 个状态：



```text

资源安全

资源成本

市场验证

投资窗口

资源国风险

```



状态值建议使用：



```text

稳定

观察

上升

承压

打开

部分验证

```



不要在核心驾驶舱展示过多详细解释。



\---



\#### 三、资源配置状态



建议展示：



```text

低成本资源配置

资源国集中度

高风险项目敞口

权益资源覆盖

```



该模块体现 CATL 资源事业部视角，区别于周报页的新闻视角。



\---



\#### 四、结构性约束与机会



用于替代“本周关键变化”。



建议展示：



```text

价格约束

供应约束

投资机会

风险约束

```



示例：



```text

价格约束：当前价格仍接近边际成本支撑区。

供应约束：中期 APS 情景仍存在缺口压力。

投资机会：低价周期有利于锁定低成本资源。

风险约束：高风险资源国政策不确定性仍在上升。

```



\---



\#### 五、数据更新状态



建议展示：



```text

新闻采集

公司公告

价格数据

库存数据

```



库存数据未接入时，必须明确显示：



```text

库存数据：待接入 SMM / Mysteel / Fastmarkets / Benchmark

```



\---



\### 5.2.2 核心驾驶舱禁止展示的内容



核心驾驶舱必须删除或禁止展示以下内容：



```text

02 LCE走势预测

03 中期供需平衡

长期三情景预测

全球资源地图

AISC成本曲线

政策新闻详细列表

投资优先级矩阵

AI策略详细表

数据与模型说明长文本

```



这些内容应保留在各自独立标签页中。



\---



\### 5.2.3 核心驾驶舱与周报页的边界



| 内容           | 周报页 | 核心驾驶舱  |

| ------------ | --- | ------ |

| 本周重大事件TOP5   | 是   | 否      |

| 单条新闻影响       | 是   | 否      |

| AI行动建议       | 是   | 否      |

| 市场是否验证TOP5事件 | 是   | 仅保留状态灯 |

| 资源战略总状态      | 否   | 是      |

| 资源配置状态       | 否   | 是      |

| 中长期结构性约束     | 否   | 是      |

| 数据更新状态       | 可有  | 可有     |



核心原则：



```text

周报页讲本周发生了什么。

核心驾驶舱讲当前战略状态是什么。

```



\---



\## 5.3 LCE走势预测



定位：



价格、供需、短中长期情景预测页。



允许展示：



\* LCE价格走势

\* 未来半年预测区间

\* 中期供需平衡

\* STEPS / APS / NZE 情景

\* 长期三情景预测

\* 价格中枢情景面积图



禁止：



\* 重复周报页新闻

\* 重复核心驾驶舱状态灯

\* 展示无数据来源的预测



\---



\## 5.4 全球资源地图与AISC成本



定位：



全球项目分布、资源结构、AISC成本曲线和项目库分析页。



允许展示：



\* 全球资源地图

\* 项目明细

\* AISC成本曲线

\* 项目库90% AISC成本线

\* 资源类型结构

\* 成本分层

\* 项目明细表



注意：



行业边际价格支撑带与项目库90% AISC成本线不是同一个口径，必须明确区分。



```text

行业边际价格支撑带 = 用于判断价格底部

项目库90% AISC成本线 = 用于判断项目库成本分层

```



\---



\## 5.5 政策与新闻风险



定位：



资源战略事件池，不是新闻中心。



优先展示：



\* 事件

\* 国家

\* 公司

\* 事件状态

\* CATL影响

\* 市场验证

\* 行动建议



禁止：



\* 大量原始新闻堆叠

\* 长篇新闻摘要

\* 重复新闻

\* 无结论新闻列表

\* 新闻门户式排版



未来优化方向：



新闻应聚合为事件链，支持：



```text

新发生

跟踪中

已落地

已解除

```



该页面应从“新闻列表”升级为“资源风险监控中心”。



\---



\## 5.6 投资优先级与AI策略



定位：



项目排序、投资优先级和资源配置建议页。



允许展示：



\* Priority项目

\* 投资评分

\* AISC

\* 国家风险

\* 资源类型

\* 产能规模

\* 项目阶段

\* 推荐动作



禁止：



\* 用AI自由生成投资结论

\* 不基于结构化字段直接推荐项目

\* 将新闻热度直接等同于投资优先级



投资建议必须基于：



\* AISC

\* 国家风险

\* 资源类型

\* 产能规模

\* 项目阶段

\* CATL战略相关性



\---



\## 5.7 Market Monitor 市场监测中心



定位：



市场验证系统，不是普通行情终端。



重点关注：



\* GFEX碳酸锂主力

\* 碳酸锂现货

\* SC6锂辉石价格

\* 期货-现货价差



Market Monitor 可以展示详细图表。



周报页只接入 Market Monitor 的结论信号。



核心驾驶舱只保留市场验证状态灯。



禁止将 Market Monitor 变成复杂金融终端。



库存信号规则：



\* 当前只预留接口

\* 不允许用不可靠数据生成库存判断

\* 不允许编造库存趋势

\* 后续可接入 SMM / Mysteel / Fastmarkets / Benchmark



\---



\## 5.8 数据与模型说明



定位：



解释数据来源、模型逻辑、CSV关系和更新机制。



允许展示：



\* 数据来源

\* 模型流程

\* CSV调用关系

\* 更新命令

\* 数据缺口

\* 模型限制

\* 数据更新时间



\---



\# 6. Design System



所有页面必须遵守 `DESIGN.md`。



特别注意：



\* 字体整体偏大

\* 最小字体不得低于 14px

\* 正文字体建议 16px

\* 表格字体建议 15px

\* KPI 数值建议 32px

\* 页面标题建议 36px

\* 不使用默认 Plotly 彩虹色

\* 不使用大面积红色或绿色背景

\* 不使用透明柱状图

\* 卡片、标签、图表风格必须统一



\---



\# 7. Engineering Principles



\## 7.1 dashboard.py



`dashboard.py` 只应负责：



\* 页面导航

\* 页面渲染

\* 调用模块函数

\* 展示已有 CSV 输出



不应负责：



\* 复杂数据抓取

\* 新闻爬取

\* LLM调用

\* 大量数据清洗

\* 大量评分逻辑

\* 复杂事件聚类



如需要新增复杂逻辑，应拆分为独立文件。



\---



\## 7.2 Recommended Module Structure



推荐结构：



```text

dashboard.py

ui\_components.py

data\_loader.py

market\_data.py

market\_signal\_engine.py

news\_ingestion.py

company\_disclosure\_ingestion.py

weekly\_intelligence\_engine.py

event\_cluster\_engine.py

quality\_checks.py

```



\---



\## 7.3 Module Responsibilities



\### dashboard.py



负责：



\* 顶部导航

\* 页面调用

\* Streamlit渲染

\* 图表展示



禁止：



\* 大量业务逻辑

\* 爬虫

\* 复杂评分

\* 生成假数据



\---



\### ui\_components.py



负责统一 UI 组件：



\* section\_header

\* kpi\_card

\* signal\_card

\* event\_card

\* risk\_badge

\* status\_pill

\* data\_status\_card



所有页面应优先复用统一组件，避免重复手写 HTML。



\---



\### data\_loader.py



负责：



\* load\_csv

\* safe\_num

\* get\_latest\_record

\* file\_update\_status

\* required\_columns\_check

\* 数据缺失兜底



\---



\### market\_data.py



负责：



\* AkShare 数据抓取

\* 市场价格数据获取

\* 汇率和宏观数据

\* GFEX 相关价格



\---



\### market\_signal\_engine.py



负责生成：



```text

reports/weekly\_market\_signals.csv

```



重点输出：



\* 价格信号：偏强 / 偏弱 / 中性

\* 是否验证 TOP5 事件

\* 期货-现货价差

\* SC6 价格变化



禁止：



\* 生成假库存数据

\* 将库存新闻当库存数据

\* 在无数据时强行判断库存趋势



\---



\### news\_ingestion.py



负责：



\* RSS

\* Google News RSS

\* Mining.com

\* 公开新闻采集



输出：



```text

reports/raw\_news\_events.csv

```



\---



\### company\_disclosure\_ingestion.py



负责：



\* 公司公告

\* 交易所披露

\* IR新闻

\* 年报 / 季报 / 公告入口



输出：



```text

reports/raw\_disclosure\_events.csv

```



\---



\### weekly\_intelligence\_engine.py



负责：



\* 新闻事件筛选

\* 事件评分

\* CATL影响评估

\* 决策建议

\* 周报 CSV 生成



输出：



```text

reports/weekly\_critical\_events.csv

reports/weekly\_catl\_impact.csv

reports/weekly\_decision\_actions.csv

reports/weekly\_ai\_brief.csv

```



\---



\### event\_cluster\_engine.py



未来负责：



\* 新闻去重

\* 事件聚类

\* 事件生命周期

\* 事件状态更新

\* 新闻到战略事件的转换



事件状态包括：



```text

新发生

跟踪中

已落地

已解除

```



\---



\### quality\_checks.py



负责：



\* CSV字段校验

\* 缺失数据提示

\* 异常值提示

\* 文件更新时间检查

\* 数据源完整性检查



\---



\# 8. Data Rules



\## 8.1 CSV First



Dashboard 页面应优先读取 `reports/` 目录中的 CSV。



不要在页面渲染时直接爬取数据。



\---



\## 8.2 No Fake Data



禁止：



\* 为了让页面好看而生成假数据

\* 库存数据未接入时输出库存趋势

\* 新闻缺失时编造事件

\* 价格缺失时强行判断偏强或偏弱



如果数据缺失，应明确显示：



```text

数据待接入

等待自动采集更新

```



\---



\## 8.3 Data Source Transparency



所有关键信号必须可追溯到：



\* CSV文件

\* source字段

\* source\_url字段

\* updated\_at字段

\* published\_at字段



\---



\# 9. Core CSV Files



常用 CSV 包括：



```text

reports/dynamic\_cost\_curve.csv

reports/investment\_recommendations.csv

reports/country\_event\_risk.csv

reports/news\_event\_summary.csv

reports/policy\_price\_impact.csv

reports/lce\_price\_forecast.csv

reports/lce\_price\_timeseries.csv

reports/weekly\_price\_inputs.csv

reports/lce\_supply\_demand\_forecast.csv

reports/raw\_news\_events.csv

reports/raw\_disclosure\_events.csv

reports/weekly\_critical\_events.csv

reports/weekly\_catl\_impact.csv

reports/weekly\_decision\_actions.csv

reports/weekly\_ai\_brief.csv

reports/weekly\_market\_signals.csv

```



如新增 CSV，必须同步更新：



```text

DATA\_SCHEMA.md

CSV\_RELATIONSHIP.md

数据与模型说明页面

```



\---



\# 10. Coding Style



\## 10.1 General



\* 使用 Python 3

\* 遵守 PEP8

\* 函数命名使用 snake\_case

\* 常量命名使用 UPPER\_CASE

\* 页面函数统一使用 `render\_section\_xx\_name()`



\---



\## 10.2 Streamlit



\* 页面逻辑保持清晰

\* 不在循环中频繁读取 CSV

\* 不在页面中执行耗时爬取

\* 所有 `st.markdown(..., unsafe\_allow\_html=True)` 应尽量复用组件



\---



\## 10.3 Plotly



\* 必须使用统一色系

\* 禁止默认调色板

\* 图表必须有清晰标题、图例和单位

\* 首页不要放复杂图表

\* 深度标签页可以放复杂图表



\---



\## 10.4 Error Handling



所有数据读取必须容错：



\* 文件不存在 → 返回空 DataFrame

\* 字段不存在 → 使用默认值或提示

\* 日期解析失败 → 显示 N/A

\* 数值解析失败 → 显示 N/A



不要因为一个 CSV 缺失导致整个 Dashboard 崩溃。



\---



\# 11. Navigation Rules



顶部标签页是主导航。



禁止在核心驾驶舱重复设置“深度分析入口”。



核心驾驶舱不承担导航功能，只承担战略状态总览功能。



页面导航分发必须保持完整 `if / elif` 链，不能在中间插入无关代码。



\---



\# 12. Weekly Workflow



标准运行顺序：



```bash

python news\_ingestion.py

python company\_disclosure\_ingestion.py

python weekly\_intelligence\_engine.py

python market\_signal\_engine.py

python weekly\_update.py

streamlit run dashboard.py

```



如果某个文件不存在，应跳过或提示，不应中断整个系统。



\---



\# 13. Decision Logic Principles



系统决策逻辑应遵循：



```text

事件 → 影响 → 市场验证 → 行动建议

```



而不是：



```text

新闻 → 展示

```



核心驾驶舱决策逻辑应遵循：



```text

数据 → 状态 → 约束 → 战略判断

```



而不是：



```text

图表 → 堆叠

```



所有 AI 建议必须来自结构化字段，不允许凭空生成。



LLM 如果接入，只能用于：



\* 归纳

\* 润色

\* 管理层语言压缩



不能直接决定：



\* 投资哪个项目

\* 是否收购

\* 是否退出

\* 是否套保



\---



\# 14. Manual Editing Caution



当前 `dashboard.py` 较长，手动修改时必须注意缩进。



如果函数定义在 `main()` 内：



```python

&#x20;   def render\_section\_xxx():

&#x20;       ...

```



函数名前面为 4 个空格，函数体为 8 个空格。



如果函数定义在文件顶层：



```python

def render\_section\_xxx():

&#x20;   ...

```



函数名前面为 0 个空格，函数体为 4 个空格。



\---



\# 15. Forbidden Changes



未经明确要求，禁止：



\* 删除已有标签页

\* 删除已有 CSV 读取逻辑

\* 删除已有核心函数

\* 修改项目基础路径

\* 引入无法安装的依赖

\* 使用假数据填充页面

\* 把周报页改成新闻门户

\* 把核心驾驶舱改成图表合集

\* 把 Market Monitor 改成复杂金融终端

\* 把其他标签页内容重新塞回核心驾驶舱



\---



\# 16. Preferred Codex Output



当 Codex 修改代码时，应优先输出：



1\. 修改了哪些文件

2\. 修改了哪些函数

3\. 新增了哪些 CSV 字段

4\. 是否影响已有页面

5\. 如何运行验证



验证命令：



```bash

python -m py\_compile dashboard.py

streamlit run dashboard.py

```



如新增模块：



```bash

python -m py\_compile 新模块.py

```



\---



\# 17. Long-Term Direction



本项目长期目标不是做一个普通 Dashboard，而是形成：



```text

CATL全球资源战略情报系统

```



核心能力：



1\. 全球资源事件监控

2\. 市场价格验证

3\. 项目成本与风险评估

4\. 投资优先级排序

5\. 管理层决策信号输出

6\. 数据来源与模型可追溯



最终系统应从：



```text

数据展示工具

```



升级为：



```text

资源战略预警与决策支持系统

```



