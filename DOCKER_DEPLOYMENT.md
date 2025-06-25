# Docker 部署指南

本指南将帮助您使用 Docker 和 Docker Compose 部署角色LLM数据生成器。

## 📋 前置要求

- Docker (版本 20.0+)
- Docker Compose (版本 2.0+)
- 至少 4GB 可用磁盘空间
- 至少 2GB 可用内存

## 🚀 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/your-username/character-llm-gen.git
cd character-llm-gen
```

### 2. 配置环境变量（可选）

如果您想预配置API密钥，可以创建 `.env` 文件：

```bash
# 复制示例文件
cp .env.example .env

# 编辑 .env 文件，填入您的API密钥
nano .env
```

### 3. 使用 Docker Compose 启动

```bash
# 构建并启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f
```

### 4. 访问应用

应用启动后，在浏览器中访问：
- **主应用**: http://localhost:7860

## 🔧 高级配置

### 自定义端口

如果需要修改端口，编辑 `docker-compose.yml` 文件：

```yaml
ports:
  - "8080:7860"  # 将应用映射到8080端口
```

### 环境变量配置

在 `docker-compose.yml` 中可以配置以下环境变量：

```yaml
environment:
  - GRADIO_SERVER_NAME=0.0.0.0
  - GRADIO_SERVER_PORT=7860
  - LOG_LEVEL=INFO
  - MAX_CONCURRENT_REQUESTS=5
  - REQUEST_TIMEOUT=30
```

### 数据持久化

默认配置已设置数据持久化，以下目录会被挂载：

- `./data` - 数据库文件
- `./logs` - 日志文件
- `./export` - 导出文件
- `./config` - 配置文件
- `./templates` - 模板文件

## 📊 监控和管理

### 查看容器状态

```bash
# 查看运行状态
docker-compose ps

# 查看资源使用情况
docker stats character-llm-gen
```

### 查看日志

```bash
# 实时查看日志
docker-compose logs -f

# 查看最近100行日志
docker-compose logs --tail=100
```

### 进入容器调试

```bash
# 进入运行中的容器
docker-compose exec character-llm-gen bash

# 或者使用sh（如果bash不可用）
docker-compose exec character-llm-gen sh
```

## 🛠️ 常用命令

### 启动和停止

```bash
# 启动服务
docker-compose up -d

# 停止服务
docker-compose down

# 重启服务
docker-compose restart

# 强制重新构建并启动
docker-compose up -d --build
```

### 更新应用

```bash
# 停止服务
docker-compose down

# 拉取最新代码
git pull

# 重新构建并启动
docker-compose up -d --build
```

### 数据备份

```bash
# 备份数据目录
tar -czf backup-$(date +%Y%m%d).tar.gz data/ logs/ export/ config/

# 恢复数据
tar -xzf backup-20240101.tar.gz
```

## 🔍 故障排除

### 常见问题

**1. 端口被占用**
```bash
# 检查端口占用
netstat -tlnp | grep 7860

# 或使用不同端口
```

**2. 权限问题**
```bash
# 确保目录权限正确
sudo chown -R $USER:$USER data/ logs/ export/ config/
```

**3. 内存不足**
```bash
# 检查系统资源
free -h
df -h
```

**4. 查看详细错误日志**
```bash
# 查看容器内部日志
docker-compose logs character-llm-gen

# 查看系统日志
journalctl -u docker
```

### 性能优化

**1. 限制容器资源使用**

在 `docker-compose.yml` 中添加：

```yaml
deploy:
  resources:
    limits:
      memory: 4G
      cpus: '2.0'
    reservations:
      memory: 2G
      cpus: '1.0'
```

**2. 使用生产级配置**

创建 `docker-compose.prod.yml`：

```yaml
version: '3.8'
services:
  character-llm-gen:
    extends:
      file: docker-compose.yml
      service: character-llm-gen
    environment:
      - LOG_LEVEL=WARNING
      - MAX_CONCURRENT_REQUESTS=10
    deploy:
      resources:
        limits:
          memory: 8G
          cpus: '4.0'
```

使用生产配置启动：
```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

## 🔒 安全注意事项

1. **不要在镜像中包含API密钥**，使用环境变量或挂载配置文件
2. **定期备份数据**，特别是 `data/` 目录
3. **限制容器权限**，避免使用 `privileged` 模式
4. **使用防火墙**限制访问端口
5. **定期更新基础镜像**以获取安全补丁

## 📚 更多资源

- [Docker 官方文档](https://docs.docker.com/)
- [Docker Compose 文档](https://docs.docker.com/compose/)
- [Gradio 部署指南](https://gradio.app/sharing-your-app/)

如有问题，请查看项目的 [Issues](https://github.com/your-username/character-llm-gen/issues) 页面。 