# eatv.0 — AI 做饭助手

> 用户上传买菜清单 / 食材图片，AI 给出菜谱方案、配图、详细教程。

## 技术栈

- **前端**：Vue 3 + Pinia + Vite
- **后端**：Python 3.12 + FastAPI + SQLite（无登录态用本地 dict，已登录态用 SQLite 持久化）
- **LLM**：MiniMax M2.5-highspeed（方案）/ M2.7-highspeed（教程）/ image-01（配图）
- **协议**：SSE 流式进度
- **鉴权**：JWT（用户名 + 密码），懒登录模式

## 功能概览

### 主功能（无需登录）
- 首页 → 上传买菜截图 / 对话输入
- 菜谱方案生成（1-3 道菜 + 碳水推荐）
- 单步教学（字号规范、倒计时、顺手做推荐）
- 结果页

### 我的（需登录）
- **历史记录**：所有生成过的菜谱方案，已登录态存 SQLite
- **收藏**：喜欢的菜一点 ★，在「我的-收藏」查看
- **退出登录**：清本地会话

### 登录机制（懒登录）
- 用户名 + 密码（≥2 字用户名，≥6 位密码）
- 主功能 / 首页完全开放，只有访问「我的」相关页面时才要求登录
- 未登录点 ★ 会自动跳登录页，登录成功后跳回

## 快速启动

### 本地开发

```bash
# 1. 装依赖
cd backend && python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cd ../frontend && pnpm install

# 2. 配后端 key
cp backend/.env.example backend/.env
# 编辑 backend/.env，填 MiniMax_API_KEY

# 3. 启动
# 终端 1：后端
cd backend && uvicorn app.main:app --reload --port 8000

# 终端 2：前端
cd frontend && pnpm dev
# 打开 http://localhost:5173
```

### 服务器部署

详见 [deploy.sh](deploy.sh)（在 Ubuntu 24.04 上跑）

## 目录结构

```
eatv.0/
├── frontend/                # Vue 3 前端
│   ├── src/
│   │   ├── views/          # 11 个页面（新增 Login / Mine / History / Favorites）
│   │   ├── components/     # TopBar / BottomTab / DishCard / TimerCard / FavoriteBtn
│   │   ├── stores/         # auth / dish / history / favorites 四个 Pinia store
│   │   ├── lib/            # api 封装（自动 JWT、401 处理）
│   │   ├── assets/         # 静态资源（含配图 Prompt 模板）
│   │   └── styles/         # Design Tokens
│   └── vite.config.ts
│
├── backend/                 # FastAPI 后端
│   ├── app/
│   │   ├── main.py         # FastAPI 入口（启动时 init_db + 自动生成 JWT_SECRET）
│   │   ├── config.py       # Settings（含 JWT_SECRET）
│   │   ├── auth.py         # 密码哈希 + JWT 编解码 + get_current_user 依赖
│   │   ├── db.py           # SQLite 封装（users / schemes / favorites 三张表）
│   │   ├── schemas.py      # Pydantic 模型
│   │   ├── prompts.py      # 三个 Agent Prompt
│   │   ├── exceptions.py
│   │   ├── logging_config.py
│   │   ├── routers/        # /api/generate/stream + /api/auth/* + /api/history + /api/favorites + /health + /ready
│   │   └── services/       # LLM client / intent / image_gen / orchestrator / cache
│   ├── data/               # SQLite 文件（自动创建，gitignore）
│   ├── .env.example
│   └── requirements.txt
│
├── docs/                    # 设计文档 + PRD + 原型图
│   └── superpowers/specs/2026-07-30-kaifan-llm-integration-design.md
│
├── deploy.sh                # 服务器一键部署脚本
├── git-init.ps1             # 本地 git 初始化脚本
└── .gitignore
```

## 关键设计

- **意图识别**：关键词 + LLM 兜底（不用否定词）
- **方案生成**：主 agent 一次出 1-3 道菜，食材安全阀门（不能编造主要食材）
- **教程生成**：每步骤拆 1-4 个 substeps，单步单屏
- **配图生成**：image-01 带 mainIngredients 一起传
- **换一批去重**：3 次上限 + history 限最近 2 轮
- **SSE 进度**：前端可流式看到阶段
- **鉴权**：JWT（HS256，7 天有效），用户名+密码，懒登录（主功能不挡）
- **数据存储**：游客态 localStorage；登录态 SQLite（历史/收藏）

## 性能

| 场景 | 端到端 |
|---|---|
| 1 道菜 | ~17s |
| 3 道菜 | ~37s |
| 配图| ~10s/张 |



## 详细 Spec

`docs/superpowers/specs/2026-07-30-kaifan-llm-integration-design.md` — 16 节设计

---

**版本**：v0.1（eatv.0 + 登录/历史/收藏）  
**更新日期**：2026-08-10
