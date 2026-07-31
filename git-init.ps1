# eatv.0 本地 git 初始化脚本
# 用法：打开 PowerShell，cd 到 eat 目录，跑 .\git-init.ps1
# 要求：你已经在 GitHub 创建了空仓库 eatv.0

# 1. 配置 git 身份（改成你的）
git config --global user.name "你的名字"
git config --global user.email "你的邮箱"

# 2. 初始化仓库（默认分支 main）
cd $PSScriptRoot
git init -b main

# 3. 添加所有文件（.gitignore 会排除 .env / node_modules / venv / dist 等）
git add .

# 4. 检查是否有 .env 被错误加入（应该为空）
$envFiles = git status --porcelain | Select-String "\.env$"
if ($envFiles) {
    Write-Host "❌ 警告：检测到 .env 文件被加入！中止。请检查 .gitignore。" -ForegroundColor Red
    exit 1
} else {
    Write-Host "✅ .env 未被加入（安全）" -ForegroundColor Green
}

# 5. 首次提交
git commit -m "feat: eatv.0 初始提交

- 前端：Vue 3 + Pinia + Vite（7 个页面：Home/Chat/Loading/Result/DishDetail/Tutorial/Done）
- 后端：FastAPI + MiniMax LLM（方案 M2.5 + 教程 M2.7 + 配图 image-01）+ SSE
- 端到端：上传食材 → Loading 落停 → Result → 详情 → 教程（带 substeps）
- 性能：单菜 17s，3 菜 37s
- 换一批去重：3 次上限 + history 限最近 2 轮"

# 6. 设置远程（改成你的 GitHub 用户名）
# 先在 https://github.com/new 创建空仓库 eatv.0（不要勾 README）
# 然后改下面这行的用户名：
$githubUser = "你的github用户名"
git remote add origin "https://github.com/$githubUser/eatv.0.git"

# 7. 推送（需要 GitHub 用户名密码 / PAT token）
Write-Host "准备推送到 GitHub..." -ForegroundColor Cyan
Write-Host "如果弹出登录框，用 GitHub Personal Access Token（不是密码）" -ForegroundColor Yellow
git push -u origin main

Write-Host "`n🎉 完成！仓库地址：https://github.com/$githubUser/eatv.0" -ForegroundColor Green
