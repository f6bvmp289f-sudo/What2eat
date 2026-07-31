# 开饭 · MiniMax LLM 接入设计 Spec

> 版本：v1.0
> 日期：2026-07-30
> 状态：待审批
> 关联文档：[PRD.md §3.1-3.5](../../PRD.md)、[Design.md §2-§6](../../Design.md)、[实施计划](../../../.claude/plans/virtual-skipping-hare.md)

---

## 1. Context（为什么做这件事）

当前项目（"开饭"）的前端用户流程已完整：Home → Chat（图片+文字输入）→ Loading → Result → DishDetail → Tutorial → Done。

但 `Loading.vue` 内的菜谱生成是**前端 mock**（`mockGenerateScheme()` 写死两道菜）。这导致：

- 用户看到的菜谱永远是固定的（番茄土豆炖牛腩 + 青椒肉丝），没有真实个性化
- 无法验证食材识别、菜谱设计、营养均衡等核心产品逻辑
- PRD §3.1.3 食材安全阀门无法被真实测试
- PRD §3.2.5 加载动画只是装饰，没有真实"思考"

**目标**：接入真实 LLM，让前端在用户上传买菜截图 + 输入文字意图后，调用后端服务，拿到真实生成的菜谱方案、菜品配图、详细教程。

**预期产出**：用户从 Chat 发送后，在 Loading 页看到「识别食材 → 出方案 → 画配图 → 写教程」实时进度，约 30 秒后跳转到 Result 页，看到带真实配图 + 真实教程的完整方案。

---

## 2. Goals & Non-Goals

### Goals

- ✅ Chat 页面输入（图片 + 文字）后，能调用后端生成真实菜谱
- ✅ Loading 页用 SSE 流式显示 AI 思考进度
- ✅ Result 页**不显示占位**，等所有内容（方案 + 配图 + 教程）就绪后才跳转
- ✅ 食材安全阀门可被真实测试（不再编造食材）
- ✅ MVP 阶段可本地端到端调试（不依赖生产部署）

### Non-Goals

- ❌ 不接 Redis（用内存 dict 缓存）
- ❌ 不接 OSS / 图片存储（图片 base64 直传）
- ❌ 不做登录 / 多用户 / 历史记录（PRD §3.6）
- ❌ 不做生产部署优化（FastAPI 本地跑通即可）
- ❌ 不做完整 ReAct 架构（用关键词 + LLM 兜底替代）
- ❌ 不做完整的菜品配图 Prompt 工程（image-01 用通用 prompt 模板）

---

## 3. 模型选型

用户已确认：

| 用途 | 模型 | 说明 |
|---|---|---|
| 多模态视觉 + 文本对话 | `MiniMax-M2.7-Highspeed` | 同一个模型承担视觉+对话，Fast 模型成本低 |
| 菜品配图 | `MiniMax-image-01` | PRD §6 Q1 已决策 |

**base URL**：`https://api.minimaxi.com/v1`（OpenAI 兼容）

**SDK**：使用 `openai` Python 包（兼容 OpenAI 协议），配置 `base_url` 指向 MiniMax。

> 字面拼写是用户口述。实施时若报 `model_not_found`，再回头确认。

---

## 4. 架构总览

```
┌─────────────────────────────────────────────────────────────────┐
│  Frontend (Vue 3 + Pinia + Vite)                                │
│                                                                  │
│   Chat.vue                                                       │
│      │                                                           │
│      │ POST /api/generate/stream                                 │
│      │ (JSON: { images: [base64], text: "" })                   │
│      ▼                                                           │
│   Loading.vue                                                    │
│      │ 接收 SSE 流（EventSource / ReadableStream）               │
│      │ 更新进度条 + 阶段提示                                       │
│      │ 完成 → router.push('result')                              │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ HTTP/SSE
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  Backend (FastAPI + Python)                                      │
│                                                                  │
│   routers/generate.py                                            │
│      │ POST /api/generate/stream                                 │
│      ▼                                                           │
│   services/orchestrator.py                                       │
│      │                                                           │
│      ├─ ① services/intent.py          (关键词 + LLM 兜底)         │
│      ├─ ② services/llm_client.py      (主 agent: 出方案)         │
│      ├─ ③ asyncio.gather ─┬─ image_gen.py  (image-01, 每张并行) │
│      │                    └─ llm_client.py (教程 agent, 每道并行)│
│      └─ ④ emit SSE events → 关闭流                                │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ HTTPS (OpenAI 兼容)
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  MiniMax API                                                      │
│     - MiniMax-M2.7-Highspeed (chat completions, vision)         │
│     - MiniMax-image-01 (image generations)                        │
└─────────────────────────────────────────────────────────────────┘
```

---

## 5. 端到端时序

```
用户                          Chat.vue                    Backend                          MiniMax
 │                                │                           │                                 │
 │ 选图 + 输入文字 + 点发送          │                           │                                 │
 ├──────────────────────────────►│                           │                                 │
 │                                │  POST /api/generate/stream  │                                 │
 │                                ├──────────────────────────►│                                 │
 │                                │                           │  ① 关键词命中？→ LLM 兜底        │
 │                                │                           ├─────────────── MiniMax chat ────►│
 │                                │                           │◄── ingredients[] ─────────────┤
 │                                │                           │                                 │
 │                                │  ← SSE: progress(10%)    │  ② 主 agent: 出方案              │
 │                                │                           ├─────────────── MiniMax chat ────►│
 │                                │                           │◄── scheme JSON ─────────────────┤
 │                                │  ← SSE: progress(30%)    │                                 │
 │                                │                           │  ③ 并行: 配图 + 教程             │
 │                                │                           │     ├─ image-01 × N (并行)       │
 │                                │                           │     ├──────── MiniMax image ──────►│
 │                                │  ← SSE: progress(image,  │     │                           │
 │                                │     dish_id=dish-1, url) │     ├─ chat × M (并行)            │
 │                                │  ← SSE: progress(image,  │     ├──────── MiniMax chat ────────►│
 │                                │     dish_id=dish-2, url) │                                 │
 │                                │  ← SSE: progress(tutorial,│                                 │
 │                                │     dish_id=dish-1, steps)│                                 │
 │                                │  ← SSE: progress(tutorial,│                                 │
 │                                │     dish_id=dish-2, steps)│                                 │
 │                                │                           │  ④ 全部完成 → emit done          │
 │                                │  ← SSE: done(scheme)     │                                 │
 │ 收到 done                      │                           │                                 │
 ├──────────────────────────────►│                           │                                 │
 │ 跳 Result（带配图 + 教程）         │                           │                                 │
```

---

## 6. SSE 事件协议

**Content-Type**: `text/event-stream`

### 6.1 事件类型

| event 字段 | 含义 | data payload |
|---|---|---|
| `progress` | 阶段进度推送 | `{stage, percent, message, dish_id?, url?, steps?}` |
| `done` | 全部完成 | `{scheme: DishScheme}` |
| `error` | 出错 | `{code, message}` |

### 6.2 ProgressEvent 字段

```typescript
interface ProgressEvent {
  stage: "intent" | "scheme" | "image" | "tutorial"
  percent: number         // 0-100
  message: string         // 用户可见的提示文案
  dish_id?: string        // image / tutorial 阶段标识是哪个 dish
  url?: string            // image 阶段：配图 URL
  steps?: DishStep[]      // tutorial 阶段：该 dish 的详细步骤
}
```

### 6.3 事件序列示例

```
event: progress
data: {"stage":"intent","percent":10,"message":"识别完成：番茄、鸡蛋、土豆"}

event: progress
data: {"stage":"scheme","percent":30,"message":"方案生成完成"}

event: progress
data: {"stage":"image","percent":50,"dish_id":"dish-1","message":"画配图中...","url":"https://..."}

event: progress
data: {"stage":"image","percent":65,"dish_id":"dish-2","message":"画配图中...","url":"https://..."}

event: progress
data: {"stage":"tutorial","percent":80,"dish_id":"dish-1","message":"写教程中...","steps":[...]}

event: progress
data: {"stage":"tutorial","percent":95,"dish_id":"dish-2","message":"写教程中...","steps":[...]}

event: done
data: {"scheme":{"id":"...","dishes":[...],"carbRecommendation":{...},"createdAt":...}}
```

---

## 7. 组件设计

### 7.1 后端文件结构

```
eat/backend/
├── requirements.txt
├── .env.example
├── .gitignore
└── app/
    ├── __init__.py
    ├── main.py             # FastAPI app + CORS + lifespan (启动时 init LLM client)
    ├── config.py           # 读 .env，提供单例 settings
    ├── schemas.py          # Pydantic models (GenerateRequest, ProgressEvent, DishScheme...)
    ├── routers/
    │   ├── __init__.py
    │   └── generate.py     # POST /api/generate/stream
    └── services/
        ├── __init__.py
        ├── llm_client.py   # MiniMax chat client 单例（含 vision 支持）
        ├── image_gen.py    # MiniMax image-01 client
        ├── intent.py       # 关键词 + LLM 兜底意图识别
        ├── prompts.py      # 三个 prompt 模板（主 agent / 教程 / 配图）
        ├── orchestrator.py # 编排 ① ② ③ ④，emit SSE 事件
        └── cache.py        # 内存 dict 缓存（dishId -> DishScheme）
```

### 7.2 各模块职责

#### `config.py`
```python
class Settings(BaseSettings):
    MiniMax_API_KEY: str
    MiniMax_BASE_URL: str = "https://api.minimaxi.com/v1"
    MiniMax_TEXT_MODEL: str = "MiniMax-M2.7-Highspeed"
    MiniMax_IMAGE_MODEL: str = "MiniMax-image-01"
    
    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()
```

#### `llm_client.py`
封装 OpenAI 兼容 SDK 单例，提供两个函数：
- `chat_with_vision(images_b64: list[str], system: str, user: str) -> str`（视觉+对话）
- `chat_text_only(system: str, user: str, json_mode: bool = True) -> str`（纯文本对话）

#### `image_gen.py`
封装 image-01 调用：
```python
async def generate_dish_image(dish_name: str) -> str:
    """返回图片 URL"""
```

#### `intent.py`
```python
INGREDIENT_KEYWORDS: set[str]  # 200-500 词

async def check_intent(images: list[str], text: str) -> tuple[bool, list[str]]:
    """
    返回 (是否食材相关, 识别出的食材列表)
    
    第一层：关键词命中即过
    第二层：LLM 短 prompt 兜底（YES/NO + 食材列表）
    """
```

**关键决策**：
- **不加否定词**（用户明确要求）：图片有噪音，关键词+LLM 综合判断更鲁棒
- 兜底 prompt 极短（"图中是否有食材/菜品/水果？回 YES 或 NO"），避免拖慢主流程

#### `prompts.py`
三个常量 prompt：

```python
MAIN_AGENT_SYSTEM = """
你是开饭的菜谱设计师。基于用户提供的食材列表和文字意图，输出 1-3 道家常菜方案。

【食材安全阀门】
- 主要食材必须来自用户提供的食材列表，**严禁编造**
- 基础调味默认有（油、盐、酱油、葱姜蒜等），无需询问

【输出要求】
- 1-3 道菜（食材丰富度决定数量）
- 每道菜含：name / description / taste / cookingMethod / difficulty / estimatedTime / mainIngredients / steps（步骤框架即可，详细步骤后续生成）
- 营养均衡：每方案至少 1 蛋白质 + 1 蔬菜
- 口味多变（避免全炒菜）

【输出格式】严格 JSON，无其他文字。
"""

TUTORIAL_AGENT_SYSTEM = """
你是烹饪教学专家。基于菜品方案，为这道菜生成详细烹饪步骤。

【要求】
- 每步骤 30 秒 - 5 分钟
- 用量人话化：一茶勺/一餐勺/小半碗/几滴
- 数字与中文之间必须有空格（"腌制 15 分钟"）
- 倒计时步骤标 hasTimer: true + timerSeconds
"""

DISH_IMAGE_PROMPT_TEMPLATE = """
{dish_name}, top-down 45-degree angle, served on a clean minimalist white plate,
pure white background, soft natural lighting with gentle shadows,
professional food photography, fine-dining presentation,
no patterns or decorations, fresh and appetizing
"""
```

#### `orchestrator.py`
核心编排：

```python
async def orchestrate(req: GenerateRequest, emit: Callable[[ProgressEvent], Awaitable]):
    """端到端编排：① 意图识别 → ② 主 agent → ③ 并行子 agent → ④ emit done"""
    
    # ① 意图识别
    ok, ingredients = await check_intent(req.images, req.text)
    if not ok:
        await emit_error("INGREDIENT_RATIO_LOW", "请上传正确菜品")
        return
    await emit_progress("intent", 10, f"识别完成：{', '.join(ingredients)}")
    
    # ② 主 agent 出方案
    scheme = await run_main_agent(ingredients, req.text)
    await emit_progress("scheme", 30, "方案生成完成")
    
    # ③ 并行：配图 + 教程
    image_tasks = [emit_image_for_dish(dish, emit) for dish in scheme.dishes]
    tutorial_tasks = [emit_tutorial_for_dish(dish, emit) for dish in scheme.dishes]
    await asyncio.gather(*image_tasks, *tutorial_tasks)
    
    # ④ 完成
    await emit_done(scheme)
```

#### `cache.py`
```python
class InMemoryCache:
    _store: dict[str, DishScheme] = {}
    
    def put(self, scheme_id: str, scheme: DishScheme): ...
    def get(self, scheme_id: str) -> DishScheme | None: ...
    def invalidate(self, scheme_id: str | None = None): ...
```

#### `routers/generate.py`
```python
@router.post("/api/generate/stream")
async def generate_stream(req: GenerateRequest):
    async def event_generator():
        async def emit(ev: ProgressEvent):
            yield f"event: {ev.stage}\ndata: {ev.model_dump_json()}\n\n"
        await orchestrate(req, emit)
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
    )
```

---

## 8. 数据契约（对齐前后端）

复用前端 `frontend/src/stores/dish.ts` 的 `DishScheme` / `Dish` / `DishStep` 类型：

```typescript
interface Dish {
  id: string
  name: string
  description: string
  estimatedTime: string
  previewImage: string        // 配图 URL（image-01 生成）
  mainIngredients: string[]
  taste: string
  cookingMethod: string
  difficulty: string
  steps: DishStep[]
}

interface DishStep {
  index: number
  title: string
  description: string
  hasTimer?: boolean
  timerSeconds?: number
}

interface DishScheme {
  id: string
  dishes: Dish[]
  carbRecommendation: { name: string; reason: string }
  createdAt: number
}
```

后端 Pydantic 模型必须与之**字段一一对应**（命名一致、类型兼容）。

---

## 9. 前端改动

### 9.1 Chat.vue 改动

**当前**：
```typescript
function onSend() {
  dishStore.addImages(...)  // 只写图片到 store
  router.push({ name: 'loading' })  // 直接跳 Loading
}
```

**改为**：
```typescript
async function onSend() {
  const text = textInput.value.trim()
  const imagesB64 = await Promise.all(
    pendingImages.value.map(img => fileToBase64(img.file))
  )
  // POST 到后端，后端在 orchestrator 完成后再返回
  // 前端在 Chat.vue 等待？还是 Loading.vue 等待？
  // → 让 Loading.vue 等待，Chat.vue 只触发跳 Loading + 传 query
  router.push({
    name: 'loading',
    query: { text, imageCount: imagesB64.length }
  })
  // 实际请求在 Loading.vue 触发
}
```

> 实际 SSE 请求放在 Loading.vue 里发起更清晰（Chat.vue 只负责把数据暂存到 store 或 query 传过去）。

### 9.2 Loading.vue 改动

**当前**：3.5s 后跳 Result（mock）。

**改为**：触发 `POST /api/generate/stream`，监听 SSE 事件：
- 监听 `progress` 事件 → 更新进度条 + 阶段文案
- 监听 `done` 事件 → `dishStore.setScheme(scheme)` → 跳 Result
- 监听 `error` 事件 → 显示错误 UI（INGREDIENT_RATIO_LOW 等）

```typescript
const progressPercent = ref(0)
const stageText = ref('开饭正在思考中')
let abortController: AbortController | null = null

onMounted(async () => {
  const response = await fetch('http://localhost:8000/api/generate/stream', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      images: imageB64List,  // 从 store 取
      text: dishStore.text,
    }),
    signal: abortController?.signal,
  })
  
  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  
  while (true) {
    const { value, done } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    
    // 解析 SSE
    const parsed = parseSSE(buffer)
    buffer = parsed.rest
    
    for (const ev of parsed.events) {
      handleProgressEvent(ev)
    }
  }
})

function handleProgressEvent(ev: ProgressEvent) {
  if (ev.stage === 'intent') {
    stageText.value = ev.message
    progressPercent.value = ev.percent
  } else if (ev.stage === 'scheme') {
    stageText.value = ev.message
    progressPercent.value = ev.percent
  } else if (ev.stage === 'image') {
    progressPercent.value = ev.percent
    stageText.value = `${ev.message}（${ev.dish_id}）`
  } else if (ev.stage === 'tutorial') {
    progressPercent.value = ev.percent
  } else if (ev.stage === 'done') {
    dishStore.setScheme(ev.scheme)
    router.push({ name: 'result' })
  } else if (ev.stage === 'error') {
    // 显示错误 UI
    errorState.value = ev
  }
}
```

### 9.3 store/dish.ts 改动

新增字段：
```typescript
const text = ref<string>('')  // Chat.vue 输入的文字
const progressPercent = ref<number>(0)
const stageText = ref<string>('')

function setText(value: string) { text.value = value }
function setProgress(percent: number) { progressPercent.value = percent }
function setStage(text: string) { stageText.value = text }
```

---

## 10. 错误处理

| 错误 | 触发条件 | 用户感知 |
|---|---|---|
| `INGREDIENT_RATIO_LOW` | 关键词未命中 + LLM 判断不是食材 | Loading 页提示"请上传正确菜品"，按钮"返回 Chat" |
| 网络错误 | 后端不可达 / 超时 | Loading 页"网络开小差了"，按钮"重试" |
| LLM 超时 | 后端 5 分钟未返回 | Loading 页"AI 想得有点久，重试一下" |
| JSON 解析失败 | LLM 输出格式异常 | 后端重试 1 次；仍失败返回 `PARSE_ERROR` |
| 单张配图失败 | image-01 某张图失败 | 不阻塞流程，该 dish 用占位图 |

---

## 11. 缓存策略

**MVP 内存 dict**：

```python
# cache.py
class InMemoryCache:
    _store: dict[str, DishScheme] = {}
    
    def put(scheme_id, scheme): _store[scheme_id] = scheme
    def get(scheme_id): return _store.get(scheme_id)
    def invalidate(scheme_id=None): 
        if scheme_id: _store.pop(scheme_id, None)
        else: _store.clear()
```

**触发清空**：
- 用户点 Result 页"换一批菜" → 后端清掉当前 scheme_id 缓存
- 用户刷新页面 / 退出登录（无） → 内存自动清空

**未来接 Redis 时**：
- 把 `InMemoryCache` 改成 `RedisCache`，接口不变
- Redis key: `kaifan:scheme:{scheme_id}`，TTL 30 分钟

---

## 12. CORS 配置

后端 FastAPI 配：
```python
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # 前端 dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**SSE 特殊要求**：`X-Accel-Buffering: no` 防止 nginx 等反向代理缓冲。

---

## 13. 验证清单

### 13.1 后端单独验证
- [ ] `cd eat/backend && uvicorn app.main:app --reload --port 8000` 启动成功
- [ ] `http://localhost:8000/docs` 显示 Swagger UI
- [ ] `curl -N -X POST http://localhost:8000/api/generate/stream -H "Content-Type: application/json" -d '{"images":[],"text":"我买了番茄鸡蛋"}'` 看到 SSE 流式事件

### 13.2 意图识别验证
- [ ] 关键词命中：`text="我买了番茄和鸡蛋"` → 走方案生成（不要 LLM 兜底）
- [ ] 关键词未命中 + 无图：`text="今天天气真好"` → 走 LLM 兜底 → 返回 INGREDIENT_RATIO_LOW
- [ ] 关键词未命中 + 有图：上传一张菜品截图 → 走 LLM 兜底 → YES → 走方案生成
- [ ] 兜底 LLM：上传非食材图 → LLM 兜底 → NO → 返回 INGREDIENT_RATIO_LOW

### 13.3 端到端验证
- [ ] Chat 发送 → Loading 显示"识别食材..."（10%）→ "出方案..."（30%）→ "画配图..."（50-65%）→ "写教程..."（80-95%）→ 完成跳 Result
- [ ] Result 页菜品卡片显示**真实生成的配图**（不是占位）
- [ ] 点击菜品 → DishDetail 大图区也是**真实配图**
- [ ] 点"开始做菜" → Tutorial 步骤是真实生成的详细步骤
- [ ] Tutorial 进入时不需要等待（教程已完成）

### 13.4 错误路径验证
- [ ] 上传菜品图 + 不输入文字 → 走通
- [ ] 只输入文字（无图） → 关键词命中 → 走通
- [ ] 故意传非食材图 → Loading 显示"请上传正确菜品"
- [ ] 断网测试 → Loading 显示"网络开小差了，重试一下"

---

## 14. 风险与权衡

| 风险 | 缓解 |
|---|---|
| `MiniMax-M2.7-Highspeed` 模型 ID 不匹配 | 实施时试一次，失败立刻查文档或问用户 |
| image-01 慢（5-15s/张）阻塞流程 | 并行生成 + 单张失败不影响其他 |
| SSE 长连接被代理切断 | 设置 30s 心跳事件（`:heartbeat\n\n`） |
| 缓存占内存 | MVP 数据小可忽略；后期接 Redis |
| 后端 5 分钟超时 | FastAPI 默认无超时，加 `uvicorn --timeout-keep-alive 300` |
| API key 泄露 | 仅放 `.env`，加 `.gitignore` 防止提交 |

---

## 15. 后续可扩展（不在本次范围）

- [ ] 接 Redis 替代内存缓存
- [ ] 接阿里云 OSS 存储用户上传的图片
- [ ] 配图 CDN 加速
- [ ] 流式进度改成 WebSocket（双向通信，更灵活）
- [ ] 教程生成缓存独立 key（`scheme_id:dish_id` → 步骤）
- [ ] 错误上报（Sentry / 阿里云日志）
- [ ] LLM 调用限流（按 IP / session）
- [ ] ReAct 完整架构（如果简单兜底不够用）

---

## 16. 验收标准（Definition of Done）

- [ ] 后端代码可在本地 `uvicorn app.main:app --reload` 启动
- [ ] 前后端打通：用户上传买菜截图 → 30 秒内看到带真实配图和教程的 Result 页
- [ ] 食材安全阀门验证：故意传非食材内容会被打回
- [ ] Loading 页能看到至少 3 个阶段进度更新（识别 / 方案 / 配图+教程）
- [ ] 错误路径有 UI 兜底（不是白屏）
- [ ] API key 不在前端代码中可见
- [ ] README 写明启动步骤 + 环境变量要求
