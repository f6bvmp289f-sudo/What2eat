# eatv.0 — AI 做饭助手

> 用户上传买菜清单 / 食材图片，AI 给出菜谱方案、配图、详细教程。

## 技术栈

- **前端**：Vue 3 + Pinia + Vite
- **后端**：Python 3.12 + FastAPI
- **LLM**：MiniMax M2.5-highspeed（方案）/ M2.7-highspeed（教程）/ image-01（配图）
- **协议**：SSE 流式进度
- **缓存**：内存 dict（MVP 阶段）

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
│   │   ├── views/          # 7 个页面
│   │   ├── components/     # TopBar / DishCard / TimerCard
│   │   ├── stores/         # Pinia 状态
│   │   ├── assets/         # 静态资源（含配图 Prompt 模板）
│   │   └── styles/         # Design Tokens
│   └── vite.config.ts
│
├── backend/                 # FastAPI 后端
│   ├── app/
│   │   ├── main.py         # FastAPI 入口
│   │   ├── config.py       # Settings
│   │   ├── schemas.py      # Pydantic 模型
│   │   ├── prompts.py      # 三个 Agent Prompt
│   │   ├── exceptions.py
│   │   ├── logging_config.py
│   │   ├── routers/        # /api/generate/stream + /health + /ready
│   │   └── services/       # LLM client / intent / image_gen / orchestrator
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

- **意图识别**：关键词 + LLM 兜底（不用否定词，图片噪音容忍）
- **方案生成**：主 agent 一次出 1-3 道菜，食材安全阀门（不能编造主要食材）
- **教程生成**：每步骤拆 1-4 个 substeps，单步单屏
- **配图生成**：image-01 带 mainIngredients 一起传
- **换一批去重**：3 次上限 + history 限最近 2 轮
- **SSE 进度**：前端可流式看到阶段

## 性能

| 场景 | 端到端 |
|---|---|
| 1 道菜 | ~17s |
| 3 道菜 | ~37s |
| 配图（硬瓶颈）| ~10s/张 |

## 部署到生产

⚠️ **生产部署前必做**：
1. 在 [MiniMax 控制台](https://platform.minimaxi.com/user-center/basic-information/secret-key) **撤销当前 key**（对话里已泄露）+ 重新生成
2. 服务器上 `nano backend/.env` 填新 key
3. 申请 ICP 备案
4. 配置 HTTPS（`certbot --nginx`）

## 详细 Spec

`docs/superpowers/specs/2026-07-30-kaifan-llm-integration-design.md` — 16 节设计

---

**版本**：v0（eatv.0）  
**更新日期**：2026-07-31
