# 雅思写作 Task 1 / Task 2 限时模考（线上 / 本地）

面向雅思教师：给学生发**一个链接**即可模考。中文操作界面 + 英文学术写作题干；答卷保存到服务器磁盘，并可同步到 **Notion** 数据库（推荐线上使用）。

**学生微信话术（可直接转发）：**  
打开链接 → 填姓名 → 开始模考 → 交卷即可。

---

## 功能概览

- 仅 Task 1（20 分钟）/ 仅 Task 2（40 分钟）/ 完整测试 60 分钟
- 倒计时、可选教师暂停、5 分钟 / 1 分钟提醒、到点自动提交
- 姓名必填；交卷后显示「已提交，可以关闭页面」
- 内置 3 套原创题目（柱状图 SVG / 表格 / 流程）
- 本地 JSON 落盘 + 可选 Notion 行存储
- 教师后台 `/admin`（列表 / 详情 / 导出 JSON·CSV）
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

浏览器打开：http://127.0.0.1:8765/  
健康检查：http://127.0.0.1:8765/health  
教师后台：http://127.0.0.1:8765/admin  

默认端口 **8765**，默认绑定 `0.0.0.0`（可用 `HOST=127.0.0.1` 限制本机）。

用 gunicorn 模拟线上：

```bash
export PORT=8765
gunicorn app:app --bind 0.0.0.0:$PORT
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
6. 把该链接发给学生；教师用 `https://…/admin` 看卷（页脚也有「教师入口」）

> Free 实例闲置会休眠，首次打开可能要等 30–60 秒。正式课前可先自己点开唤醒。

### 3. 环境变量列表

| 变量 | 必填 | 说明 |
|---|---|---|
| `PORT` | 自动 | Render 注入，勿手改 |
| `IELTS_ADMIN_PASSWORD` | 强烈建议 | 教师后台密码；不设则默认 `ielts2026` |
| `IELTS_SECRET_KEY` | 强烈建议 | Flask session 密钥；线上务必设成长随机串 |
| `NOTION_TOKEN` | 可选 | Notion Internal Integration Secret |
| `NOTION_DATABASE_ID` | 可选 | 答卷数据库 ID（与 Token 同时设置才启用） |
| `HOST` | 可选 | 仅 `python app.py` 时有效；默认 `0.0.0.0` |

---

## 三、Notion 答卷库（推荐线上使用）

Render 免费磁盘**不持久**，重启/重新部署后本地 JSON 可能丢失。配置 Notion 后，每次交卷会**额外**写入一行数据库，教师在 Notion 里批改最稳妥。

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

> 未配置 Notion 时，仍写入服务器 `data/submissions/`；本地自测足够，线上请务必配 Notion。

---

## 四、教师后台

- 地址：`/admin`
- 默认密码：`ielts2026`（请用环境变量改掉）
- 可查看全文、导出 JSON / CSV
- 学生首页**不展示**后台按钮；仅页脚小字「教师入口」

---

## 五、更换题目

编辑 `prompts/prompts.json` 后重新部署（或本地重启）。Task 1 支持 `chart` / `table` / `process_steps`。

---

## 六、目录结构

```
ielts-writing-mock/
  app.py
  requirements.txt
  Procfile
  render.yaml
  README.md
  run.sh
  prompts/prompts.json
  templates/
  static/
  data/submissions/    # 本地/实例磁盘备份
```

---

## 说明

- 题目为教学用原创提示，非剑桥官方真题原文。
- Notion 写入失败**不会**阻断学生交卷（仍有本地 JSON）；错误记在服务日志。
