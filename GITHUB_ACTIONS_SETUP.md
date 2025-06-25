# GitHub Actions Docker 镜像构建配置指南

本指南将帮助您配置 GitHub Actions 手动构建和推送 Docker 镜像到 GitHub Container Registry。

## 📋 前置要求

- GitHub 仓库
- GitHub Packages 权限

## 🔐 配置说明

### GitHub Container Registry (GHCR)

本项目使用 GitHub Container Registry 存储 Docker 镜像，使用内置的 `GITHUB_TOKEN`，无需额外配置 Secrets。

GHCR 的优势：
- 与 GitHub 仓库深度集成
- 无需额外的第三方账户
- 支持包级别的权限控制
- 免费使用

## 🚀 Workflow 功能说明

### 触发方式

本项目采用**手动触发**模式：

1. 进入 GitHub 仓库 → Actions 页面
2. 选择 "Build and Push Docker Image to GHCR" workflow
3. 点击 "Run workflow" 按钮
4. 可选择输入自定义镜像标签（留空则使用分支名）
5. 点击绿色的 "Run workflow" 按钮开始构建

### 标签策略

| 输入情况     | 生成的标签 | 示例                     |
| ------------ | ---------- | ------------------------ |
| 自定义标签   | 用户输入   | `v1.0.0`, `prod`, `test` |
| 空标签(默认) | 分支名     | `main`, `develop`        |
| 主分支       | `latest`   | `latest`                 |
| 提交 SHA     | SHA前缀    | `sha-abc1234`            |

### 多平台支持

自动构建以下平台的镜像：
- `linux/amd64` (Intel/AMD 64位)
- `linux/arm64` (ARM 64位，如 Apple Silicon)

## 📦 镜像发布位置

构建成功后，镜像将发布到：

**GitHub Container Registry**: `ghcr.io/YOUR_USERNAME/YOUR_REPO`

### 使用镜像

```bash
# 拉取最新镜像
docker pull ghcr.io/YOUR_USERNAME/YOUR_REPO:latest

# 运行容器
docker run -d -p 7860:7860 ghcr.io/YOUR_USERNAME/YOUR_REPO:latest

# 使用特定标签
docker pull ghcr.io/YOUR_USERNAME/YOUR_REPO:v1.0.0
```

## 🔧 自定义配置

### 修改镜像名称

编辑 `.github/workflows/docker-image.yml` 文件：

```yaml
env:
  IMAGE_NAME: your-custom-name  # 修改这里
```

### 添加构建参数

在 workflow 文件中的 `build-args` 部分添加：

```yaml
build-args: |
  BUILDTIME=${{ fromJSON(steps.meta.outputs.json).labels['org.opencontainers.image.created'] }}
  VERSION=${{ fromJSON(steps.meta.outputs.json).labels['org.opencontainers.image.version'] }}
  YOUR_CUSTOM_ARG=value
```

### 修改目标平台

如果只需要构建特定平台：

```yaml
platforms: linux/amd64  # 仅构建 AMD64
```

## 🧪 测试 Workflow

### 本地测试

使用 [act](https://github.com/nektos/act) 在本地测试 GitHub Actions：

```bash
# 安装 act
curl https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash

# 测试 workflow（手动触发事件）
act workflow_dispatch
```

### 手动触发测试

1. **进入 Actions 页面**
2. **选择 workflow** → "Build and Push Docker Image to GHCR"
3. **点击 "Run workflow"**
4. **输入测试标签**（如 `test-v1.0`）
5. **点击 "Run workflow" 开始构建**

## 📊 监控构建状态

### GitHub Actions 页面

1. 进入仓库 → Actions 页面
2. 查看 "Build and Push Docker Image to GHCR" workflow
3. 点击具体的运行查看详细日志

### 添加状态徽章

在 README.md 中添加构建状态徽章：

```markdown
[![Docker Image CI](https://github.com/USERNAME/REPO/actions/workflows/docker-image.yml/badge.svg)](https://github.com/USERNAME/REPO/actions/workflows/docker-image.yml)
```

## 🔍 故障排除

### 常见问题

**1. GHCR 认证失败**
```
Error: denied: permission_denied
```
解决方案：确保仓库的 Actions 有 `packages: write` 权限，通常这是默认启用的。

**2. 镜像推送权限不足**
```
Error: failed to push: denied: permission_denied
```
解决方案：检查 GitHub Token 权限，确保 Actions 可以写入 Packages。

**3. 多平台构建失败**
```
Error: failed to solve: linux/arm64
```
解决方案：某些依赖包可能不支持 ARM64，可以临时移除该平台或修复依赖。

**4. 镜像测试失败**
```
Health check failed
```
解决方案：检查应用是否在容器中正确启动，查看容器日志排查问题。

### 调试技巧

1. **启用调试模式**：
   在 workflow 文件中添加：
   ```yaml
   env:
     ACTIONS_STEP_DEBUG: true
   ```

2. **查看构建缓存**：
   ```bash
   docker buildx du
   ```

3. **本地构建测试**：
   ```bash
   docker buildx build --platform linux/amd64,linux/arm64 -t test-image .
   ```

## 🎯 使用场景

### 开发阶段
```bash
# 手动触发，使用 develop 标签
# 在 Actions 页面输入: develop
docker pull ghcr.io/username/repo:develop
```

### 发布版本
```bash
# 手动触发，使用版本标签
# 在 Actions 页面输入: v1.0.0
docker pull ghcr.io/username/repo:v1.0.0
```

### 测试构建
```bash
# 手动触发，使用测试标签
# 在 Actions 页面输入: test-feature-x
docker pull ghcr.io/username/repo:test-feature-x
```

## 🚀 部署使用

构建完成后，可以使用以下命令部署：

```bash
# 使用 GHCR 镜像
docker run -d -p 7860:7860 ghcr.io/your-username/character-llm-gen:latest

# 使用 docker-compose（需要修改镜像地址）
# 编辑 docker-compose.yml，将 image 改为 GHCR 地址
docker-compose up -d
```

## 📝 权限说明

### GHCR 权限

- 镜像默认为私有，仅仓库成员可访问
- 可在 GitHub Package 页面设置为公开
- 支持细粒度的权限控制

### 公开镜像设置

1. 进入 GitHub 仓库 → Packages
2. 找到对应的容器镜像
3. 点击 Package Settings
4. 选择 "Change visibility" → "Public"
5. 确认更改 