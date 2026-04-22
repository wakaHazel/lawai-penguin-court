# 企鹅法庭公网部署说明

这套项目要想把前后端都放到公网，实际可行的方式只有两种：

1. 最稳方案：前后端都部署到 Render，同一域名直接访问完整服务。
2. 分离方案：前端部署到 GitHub Pages，后端部署到 Render，前端通过 `VITE_API_BASE_URL` 指向 Render API。

如果你的目标是“别人直接打开就能看完整功能”，优先用第一种。  
如果你的目标是“代码挂 GitHub，同时也能公开演示”，就用第二种。

---

## 一、推荐方案：Render 直接跑完整服务

仓库里已经有这些文件：

- `Dockerfile`
- `render.yaml`

后端 FastAPI 会直接把构建后的前端静态文件一起服务出去，所以这一种不需要 GitHub Pages，不需要跨域，也不需要额外配置前端 API 地址。

### Render 部署步骤

1. 打开 Render 后台。
2. 选择 `New +`。
3. 选择 `Blueprint`。
4. 连接 GitHub 仓库：`wakaHazel/lawai-penguin-court`。
5. Render 会自动识别根目录的 `render.yaml`。
6. 创建服务后，在环境变量里补齐：
   - `YUANQI_APP_ID`
   - `YUANQI_APP_KEY`
   - `PENGUIN_SIMULATION_MODE=live`
   - `PENGUIN_LIVE_PROVIDER=yuanqi`
7. 如果前端和后端同域名部署在 Render，不需要额外设置 `PENGUIN_CORS_ORIGINS`。
8. 部署完成后，直接打开 Render 分配的公网地址即可。

### 这条路线的优点

- 前后端同域名，不会有跨域问题。
- 不需要再维护 `github.io -> 后端` 的跳转关系。
- 最接近正式演示环境。
- 后端接口、静态图片、数据库都在一套服务里。

---

## 二、分离方案：GitHub Pages 前端 + Render 后端

这一套已经在仓库里补好了 GitHub Pages 工作流：

- `.github/workflows/deploy-pages.yml`

### 这条路线的前提

- GitHub Pages 只能托管静态前端。
- FastAPI 后端必须单独部署到 Render。
- 前端构建时必须知道后端公网地址。

### 第一步：先部署 Render 后端

仍然按上一节的 Render 流程部署，但这次额外补一个跨域变量：

- `PENGUIN_CORS_ORIGINS=https://wakahazel.github.io`

如果以后仓库名变了，或者你换账号了，就把这里改成真实的 Pages 域名。

部署完成后，拿到 Render 后端地址，例如：

`https://lawai-penguin-court.onrender.com`

### 第二步：配置 GitHub Pages 构建变量

进入 GitHub 仓库后台：

1. `Settings`
2. `Secrets and variables`
3. `Actions`
4. `Variables`
5. 新建变量：
   - 名称：`VITE_API_BASE_URL`
   - 值：你的 Render 后端地址，例如 `https://lawai-penguin-court.onrender.com`

### 第三步：开启 GitHub Pages

1. 打开仓库 `Settings`
2. 进入 `Pages`
3. `Source` 选择 `GitHub Actions`
4. 提交代码到 `main` 后，Actions 会自动构建并发布

发布成功后，地址通常是：

`https://wakahazel.github.io/lawai-penguin-court/`

### 这条路线的优点

- 仓库更新后，前端展示页会自动发布。
- 分享源码和分享演示页都方便。

### 这条路线的缺点

- 前后端分离，链路更长。
- Render 休眠时，首次请求可能会慢一点。
- 后端域名改了，必须同步更新 `VITE_API_BASE_URL`。

---

## 三、当前仓库里已经做好的适配

为了让分离部署可用，仓库已经补了这些逻辑：

1. `apps/web/vite.config.ts`
   - 支持 `VITE_BASE_PATH`
   - 适配 GitHub Pages 子路径部署

2. `apps/web/src/services/api/client.ts`
   - GitHub Pages 环境下，如果没配置 `VITE_API_BASE_URL`，不会再错误请求 `github.io/api/...`

3. `apps/web/src/features/trial-simulation/components/TrialScenePanel.tsx`
   - 静态托管环境下，如果没配置后端地址，不再错误加载后端图片路径

4. `.github/workflows/deploy-pages.yml`
   - 自动构建并发布前端到 GitHub Pages

---

## 四、我给你的实际建议

如果你现在是为了“朋友直接看完整可用 demo”，不要再纠结 `github.io`。

直接用：

1. Render 部署完整服务
2. 配好 `YUANQI_APP_ID` 和 `YUANQI_APP_KEY`
3. 直接把 Render 公网链接发给别人

如果你同时还想保留一个 GitHub 展示页，再额外开 GitHub Pages。

也就是说：

- `Render` 负责“真能跑的完整系统”
- `GitHub Pages` 负责“项目展示入口 / 静态前端镜像”

这是这套项目目前最稳的公网方案。
