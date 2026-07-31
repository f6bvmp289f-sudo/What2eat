# 开饭后端

开饭 App 的 FastAPI 后端，集成 MiniMax LLM 用于菜谱生成。

## 启动

```bash
cd eat/backend

# 1. 创建虚拟环境
python -m venv venv

# 2. 激活虚拟环境
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 配置环境变量
cp .env.example .env
# 编辑 .env，填入你的 MiniMax_API_KEY

# 5. 启动
uvicorn app.main:app --reload --port 8000
```

## 端点

| 端点 | 方法 | 用途 |
|------|------|------|
| `/` | GET | 服务信息 |
| `/health` | GET | liveness 探活 |
| `/ready` | GET | readiness（检查 LLM 可用） |
| `/api/generate/stream` | POST | **核心**：SSE 流式菜谱生成 |
| `/api/regenerate` | POST | 换一批（占位） |
| `/docs` | GET | Swagger UI |

## SSE 事件协议

`POST /api/generate/stream` 请求体：
```json
{
  "images": ["data:image/jpeg;base64,..."],
  "text": "用户文字描述（可选）"
}
```

响应（`text/event-stream`）：
```
event: progress
data: {"stage":"intent","percent":15,"message":"识别完成"}

event: progress
data: {"stage":"scheme","percent":45,"message":"方案已生成（2 道菜）"}

event: done
data: {"stage":"done","percent":100,"scheme":{完整方案}}
```

错误时：
```
event: error
data: {"stage":"error","code":"INGREDIENT_RATIO_LOW","message":"..."}
```

## 设计文档

- `docs/superpowers/specs/2026-07-30-kaifan-llm-integration-design.md`
- `docs/superpowers/specs/2026-07-30-kaifan-llm-integration-design.md`
