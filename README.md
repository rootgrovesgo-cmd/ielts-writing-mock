# 雅思学术类写作 / 阅读模考与口语练习（线上 / 本地）

面向雅思教师：给学生发**一个链接**即可模考。品牌为 **Rosette Exclusive Mock Exam**，界面仿照雅思机考（computer-delivered）。中文操作提示 + 英文试题；答卷保存到服务器磁盘。写作还可选同步到 **Notion** 数据库。

**学生微信话术（可直接转发）：**  
打开链接 → 选「写作」或「阅读」模考，或点右上角「口语题库」练习 → 填姓名和老师提供的邀请码 → 开始。写作和阅读交卷后不会显示分数或答案；口语为练习，也不评分。

---

## 功能概览

- 首页 `/` 两个模考入口：Academic Writing（`/writing`）、Academic Reading（`/reading`）；右上角「口语题库」进入 Speaking 练习（`/speaking`）
- **写作**：仅 Task 1（20 分钟）/ 仅 Task 2（40 分钟）/ 完整测试 60 分钟；左侧题目，右侧答题区
- **阅读**：完整测试 60 分钟（Q1–40），或只考 Passage 1 / 2 / 3（各 20 分钟）；左文右题、底部题号面板、标记复查、文章高亮与笔记
- 倒计时、可选教师暂停、5 分钟 / 1 分钟提醒、到点自动提交
- 姓名与**邀请码**必填；没有有效邀请码无法开始或交卷；交卷后显示「Submitted. You may close this page.」——**不向学生展示分数、答案或解析**
- **口语练习**：完整练习为 Part 1 → Part 2（1 分钟准备 + 2 分钟陈述）→ Part 3，也可只练 Part 1 或只练 Part 3（Part 3 需先选定对应的 Part 2 话题）；可随机整套或自选话题；不评分、不给答案。题目依据公开回忆的 2026 年 9–12 月题季整理，并非官方材料。
- 写作内置 3 套原创题目；阅读当前为 Set A（原创练习卷，三篇 + 40 题）；口语题库见 `prompts/speaking_sept2026.json`
- 本地 JSON 落盘；写作可另同步 Notion（阅读默认只存本地，避免旧数据库缺字段）
- 教师后台 `/admin`（唯一管理员账号登录；答题情况 / 登录用户 / 进入记录 / 邀请码管理；详情 / 导出 JSON·CSV）
- 健康检查 `/health`（部署探针）

---

## 一、本地运行（教师自测）

```bash
cd ielts-writing-mock
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

或：`./run.sh`

浏览器打开：

- 首页（选科）：http://127.0.0.1:8765/
- 写作：http://127.0.0.1:8765/writing
- 阅读：http://127.0.0.1:8765/reading
- 口语练习：http://127.0.0.1:8765/speaking
- 健康检查：http://127.0.0.1:8765/health
- 教师后台：http://127.0.0.1:8765/admin

默认端口 **8765**，默认绑定 `0.0.0.0`（可用 `HOST=127.0.0.1` 限制本机）。

用 gunicorn 模拟线上：

```bash
export PORT=8765
gunicorn app:app --bind 0.0.0.0:$PORT
```

本地自测（含阅读判分、邀请码与后台登录）：

```bash
python3 -m unittest discover -s tests -v
```

---

## 二、线上部署（Render 免费 Web Service）

**无需学生安装任何东西**，教师部署一次，把网址发群即可。

### 1. 准备仓库

将本目录推到 GitHub/GitLab（或 Render 直接连本地仓库）。确保包含：`app.py`、`requirements.txt`、`Procfile`、`render.yaml`、`templates/`、`static/`、`prompts/`。

### 2. 在 Render 创建服务

1. 打开 [https://render.com](https://render.com) → **New** → **Web Service**
2. 连接含本项目的仓库；Root Directory 若在子目录则填 `ielts-writing-mock`
3. 设置（也可直接用 Blueprint：`render.yaml`）：

| 项 | 值 |
|---|---|
| Runtime | Python |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --threads 4 --timeout 120` |
| Plan | Free |
| Health Check Path | `/health` |

4. **Environment** 环境变量（见下表）保存后 Deploy
5. 部署成功后得到类似：`https://ielts-writing-mock-xxxx.onrender.com`
6. 把该链接发给学生（会先进入首页选写作或阅读）；教师用 `https://…/admin` 看卷

> Free 实例闲置会休眠，首次打开可能要等 30–60 秒。正式课前可先自己点开唤醒。

### 3. 环境变量列表

| 变量 | 必填 | 说明 |
|---|---|---|
| `PORT` | 自动 | Render 注入，勿手改 |
| `IELTS_ADMIN_USERNAME` | **生产环境必填** | 唯一教师后台用户名（请自行设置，不要把真实账号写进仓库） |
| `IELTS_ADMIN_PASSWORD` | **生产环境必填**（或改用哈希） | 唯一教师后台密码；**不设则无法登录，没有默认密码** |
| `IELTS_ADMIN_PASSWORD_HASH` | 可选 | 若设置，则用 Werkzeug 密码哈希校验，优先于明文密码 |
| `IELTS_SECRET_KEY` | 强烈建议 | Flask session 密钥；线上务必设成长随机串 |
| `NOTION_TOKEN` | 可选 | Notion Internal Integration Secret（仅写作同步） |
| `NOTION_DATABASE_ID` | 可选 | 答卷数据库 ID（与 Token 同时设置才启用写作同步） |
| `HOST` | 可选 | 仅 `python app.py` 时有效；默认 `0.0.0.0` |

---

## 三、Notion 答卷库（推荐线上写作使用）

Render 免费磁盘**不持久**，重启/重新部署后本地 JSON 可能丢失。配置 Notion 后，每次**写作**交卷会额外写入一行数据库。阅读答卷目前只保存在服务器本地 JSON（以及教师后台导出），以免旧 Notion 库缺少阅读字段导致写入失败。

### 1. 创建 Integration

1. 打开 [https://www.notion.so/my-integrations](https://www.notion.so/my-integrations)
2. **New integration** → 复制 **Internal Integration Secret** → 填到 `NOTION_TOKEN`

### 2. 建数据库并授权

新建一个 **Database（Full page）**，属性名与类型必须如下（英文名，区分大小写）：

| 属性名 | 类型 | 说明 |
|---|---|---|
| **Name** | Title | 页面标题（用考生姓名） |
| **Candidate Name** | Rich text | 考生姓名 |
| **Mode** | Select | 选项建议：`full` / `task1` / `task2` |
| **Prompt Set** | Rich text | 套卷 ID，如 `set-a` |
| **Task 1** | Rich text | Task 1 全文（Notion 单段约 2000 字上限，超长会截断） |
| **Task 2** | Rich text | Task 2 全文（同上） |
| **Task1 Words** | Number | Task 1 词数 |
| **Task2 Words** | Number | Task 2 词数 |
| **Time Used (sec)** | Number | 用时（秒） |
| **Submitted At** | Date | 提交时间（含时区） |
| **Submission ID** | Rich text | 系统 UUID |
| **Auto Submitted** | Checkbox | 是否到点自动交卷 |

然后：数据库右上角 **…** → **Connections** → 勾选你的 Integration。

### 3. 复制 Database ID

打开数据库页面，URL 形如：

`https://www.notion.so/xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx?v=…`

中间 32 位十六进制即为 `NOTION_DATABASE_ID`（可带或不带连字符）。

在 Render 填入 `NOTION_TOKEN` + `NOTION_DATABASE_ID` 后重新 Deploy。`/health` 返回 `"notion": true` 即表示已启用。

> 未配置 Notion 时，仍写入服务器 `data/submissions/`；本地自测足够，线上写作请务必配 Notion。

---

## 四、教师后台

- 地址：`/admin`
- **唯一管理员**：通过环境变量 `IELTS_ADMIN_USERNAME` 与 `IELTS_ADMIN_PASSWORD`（或 `IELTS_ADMIN_PASSWORD_HASH`）配置；二者缺一则无法登录。仓库中不含默认账号或密码。
- 登录页需同时输入用户名和密码；错误提示不会区分是用户名还是密码不对。
- 后台四个分区：
  - **答题情况**：原有答卷列表、详情与导出（写作 / 阅读）
  - **登录用户**：成功进入模考的学生（姓名、邀请码、首次/最近进入、各科开始与交卷次数，以及答卷链接）
  - **进入记录**：近期开始 / 交卷 / 被拒绝的记录
  - **邀请码**：创建、启用或停用邀请码，查看使用次数；可手填或自动生成，可选备注与次数上限
- 没有已启用的邀请码时，学生不能开始模考。请先在后台创建一枚，再发给学生。
- 列表含「科目」列（写作 / 阅读）。阅读显示成绩（如 `36/40`）与**参考分数**；写作仍显示 T1 / T2 词数
- 阅读详情为逐题对照（学生作答 / 标准答案 / ✓✗ / 中文解析），仅教师可见
- 可导出 JSON / CSV（含 `module`、阅读分数等列，不影响已有写作行）
- 「模考页」回到首页 `/`

创建第一枚邀请码：用已配置的管理员账号登录 `/admin` → 打开「邀请码」→ 填写或留空自动生成 → 点「创建邀请码」→ 把该码发给学生。

---

## 五、更换题目

- 写作：编辑 `prompts/prompts.json` 后重新部署（或本地重启）。Task 1 支持 `chart` / `table` / `process_steps`。
- 口语题库：`prompts/speaking_sept2026.json`（2026 年 9–12 月公开回忆话题，仅题目与话题卡提示，不含范文）。
- 阅读学生卷：`prompts/reading_set_a.json`（只有文章与题目，不含答案）。
- 阅读标准答案与解析（仅服务器使用）：`prompts/reading_keys.json`。切勿把该文件的内容放进学生页面或前端脚本。

---

## 六、主要路由

| 路径 | 说明 |
|---|---|
| `/` | 首页，选择写作或阅读；右上角进入口语题库 |
| `/writing` | 学术写作模考（需邀请码后才能开始） |
| `/reading` | 学术阅读模考（需邀请码后才能开始） |
| `/speaking` | 口语题库练习：完整 Part 1–3，或单项 Part 1 / Part 3（需邀请码后才能开始） |
| `/api/speaking/bank` | 口语题库 JSON（需已通过邀请码的学生会话） |
| `/api/session/start` | 校验姓名与邀请码，记录登录并建立学生会话 |
| `/api/prompts` | 写作题目 JSON（需已通过邀请码的学生会话） |
| `/api/submit` | 写作交卷（需有效学生会话或邀请码） |
| `/api/reading/submit` | 阅读交卷（服务器判分，响应中不含分数；需有效会话或邀请码） |
| `/api/reading/paper` | 阅读学生卷 JSON（无答案；需已通过邀请码的学生会话） |
| `/admin` | 教师后台 |
| `/health` | 健康检查 |

---

## 七、目录结构

```
ielts-writing-mock/
  app.py
  access.py
  reading_scoring.py
  requirements.txt
  Procfile
  render.yaml
  README.md
  run.sh
  prompts/prompts.json
  prompts/reading_set_a.json
  prompts/reading_keys.json
  tests/test_reading.py
  tests/test_access.py
  tests/test_speaking.py
  prompts/speaking_sept2026.json
  templates/
  static/
  data/submissions/    # 本地/实例磁盘备份（已 gitignore）
  data/invite_codes.json / users.json / access_log.json  # 邀请码与登录记录（已 gitignore）
```

---

## 说明

- 写作与阅读题目为教学用原创材料，非剑桥官方真题原文。口语练习题依据考生公开回忆的 2026 年 9–12 月话题整理，同样不是官方材料。
- Notion 写入失败**不会**阻断学生交卷（仍有本地 JSON）；错误记在服务日志。
- 阅读的参考分数仅供教师使用，按常见学术类阅读正确题数换算；单篇模式只记原始分，不换算总分段。
