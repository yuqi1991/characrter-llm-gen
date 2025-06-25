#!/bin/bash

# Character LLM Dataset Generator 部署脚本
# 支持 Docker 和 Docker Compose 部署方式

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_message() {
    echo -e "${2}${1}${NC}"
}

print_success() {
    print_message "$1" "$GREEN"
}

print_warning() {
    print_message "$1" "$YELLOW"
}

print_error() {
    print_message "$1" "$RED"
}

print_info() {
    print_message "$1" "$BLUE"
}

# 检查命令是否存在
check_command() {
    if ! command -v "$1" &> /dev/null; then
        print_error "❌ $1 未安装或不在 PATH 中"
        print_info "请安装 $1 后重试"
        exit 1
    fi
}

# 检查 Docker 是否运行
check_docker_running() {
    if ! docker info &> /dev/null; then
        print_error "❌ Docker daemon 未运行"
        print_info "请启动 Docker 后重试"
        exit 1
    fi
}

# 创建必要的目录
create_directories() {
    print_info "📁 创建必要的目录..."
    mkdir -p data logs export config
    print_success "✅ 目录创建完成"
}

# 设置权限
set_permissions() {
    print_info "🔐 设置目录权限..."
    chmod 755 data logs export config
    print_success "✅ 权限设置完成"
}

# Docker 部署
deploy_docker() {
    print_info "🐳 使用 Docker 部署..."
    
    local image_name="ghcr.io/YOUR_USERNAME/character-llm-gen:latest"
    local container_name="character-llm-gen"
    local port="7860"
    
    # 停止并删除现有容器
    if docker ps -a --format '{{.Names}}' | grep -q "^${container_name}$"; then
        print_warning "⚠️  停止现有容器..."
        docker stop "$container_name" || true
        docker rm "$container_name" || true
    fi
    
    # 拉取最新镜像
    print_info "📥 拉取最新镜像..."
    docker pull "$image_name"
    
    # 启动新容器
    print_info "🚀 启动容器..."
    docker run -d \
        --name "$container_name" \
        -p "${port}:7860" \
        -v "$(pwd)/data:/app/data" \
        -v "$(pwd)/logs:/app/logs" \
        -v "$(pwd)/export:/app/export" \
        -v "$(pwd)/config:/app/config" \
        --restart unless-stopped \
        "$image_name"
    
    print_success "✅ Docker 部署完成！"
    print_info "🌐 访问地址: http://localhost:${port}"
}

# Docker Compose 部署
deploy_compose() {
    print_info "🐙 使用 Docker Compose 部署..."
    
    if [ ! -f "docker-compose.yml" ]; then
        print_error "❌ docker-compose.yml 文件不存在"
        exit 1
    fi
    
    # 停止现有服务
    print_info "⏹️  停止现有服务..."
    docker-compose down || true
    
    # 拉取最新镜像
    print_info "📥 拉取最新镜像..."
    docker-compose pull
    
    # 启动服务
    print_info "🚀 启动服务..."
    docker-compose up -d
    
    print_success "✅ Docker Compose 部署完成！"
    print_info "🌐 访问地址: http://localhost:7860"
}

# 构建本地镜像
build_local() {
    print_info "🔨 构建本地镜像..."
    
    if [ ! -f "Dockerfile" ]; then
        print_error "❌ Dockerfile 不存在"
        exit 1
    fi
    
    docker build -t character-llm-gen:local .
    print_success "✅ 本地镜像构建完成！"
    
    # 使用本地镜像部署
    print_info "🚀 使用本地镜像部署..."
    local container_name="character-llm-gen"
    local port="7860"
    
    # 停止现有容器
    if docker ps -a --format '{{.Names}}' | grep -q "^${container_name}$"; then
        docker stop "$container_name" || true
        docker rm "$container_name" || true
    fi
    
    # 启动容器
    docker run -d \
        --name "$container_name" \
        -p "${port}:7860" \
        -v "$(pwd)/data:/app/data" \
        -v "$(pwd)/logs:/app/logs" \
        -v "$(pwd)/export:/app/export" \
        -v "$(pwd)/config:/app/config" \
        --restart unless-stopped \
        character-llm-gen:local
    
    print_success "✅ 本地镜像部署完成！"
    print_info "🌐 访问地址: http://localhost:${port}"
}

# 显示帮助信息
show_help() {
    echo "Character LLM Dataset Generator 部署脚本"
    echo ""
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  docker      使用 Docker 部署（推荐）"
    echo "  compose     使用 Docker Compose 部署"
    echo "  build       构建本地镜像并部署"
    echo "  status      查看部署状态"
    echo "  logs        查看应用日志"
    echo "  stop        停止应用"
    echo "  restart     重启应用"
    echo "  clean       清理容器和镜像"
    echo "  help        显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0 docker    # 使用 Docker 部署"
    echo "  $0 compose   # 使用 Docker Compose 部署"
    echo "  $0 build     # 构建并部署本地镜像"
}

# 查看状态
show_status() {
    print_info "📊 查看部署状态..."
    
    if docker ps --format '{{.Names}}' | grep -q "character-llm-gen"; then
        print_success "✅ 应用正在运行"
        docker ps --filter "name=character-llm-gen" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    else
        print_warning "⚠️  应用未运行"
    fi
    
    # 检查端口
    if curl -s -f http://localhost:7860/ > /dev/null 2>&1; then
        print_success "✅ 应用健康检查通过"
        print_info "🌐 访问地址: http://localhost:7860"
    else
        print_warning "⚠️  应用健康检查失败"
    fi
}

# 查看日志
show_logs() {
    print_info "📝 查看应用日志..."
    
    if docker ps --format '{{.Names}}' | grep -q "character-llm-gen"; then
        docker logs -f character-llm-gen
    else
        print_error "❌ 容器未运行"
    fi
}

# 停止应用
stop_app() {
    print_info "⏹️  停止应用..."
    
    if [ -f "docker-compose.yml" ]; then
        docker-compose down
    else
        docker stop character-llm-gen || true
        docker rm character-llm-gen || true
    fi
    
    print_success "✅ 应用已停止"
}

# 重启应用
restart_app() {
    print_info "🔄 重启应用..."
    stop_app
    sleep 2
    
    if [ -f "docker-compose.yml" ]; then
        docker-compose up -d
    else
        deploy_docker
    fi
    
    print_success "✅ 应用已重启"
}

# 清理
clean_up() {
    print_warning "⚠️  这将删除所有相关的容器和镜像"
    read -p "确定要继续吗？(y/N): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_info "🧹 清理容器和镜像..."
        
        # 停止容器
        docker stop character-llm-gen || true
        docker rm character-llm-gen || true
        
        # 删除镜像
        docker rmi character-llm-gen:local || true
        docker rmi ghcr.io/YOUR_USERNAME/character-llm-gen:latest || true
        
        # 清理 Docker Compose
        if [ -f "docker-compose.yml" ]; then
            docker-compose down --rmi all || true
        fi
        
        print_success "✅ 清理完成"
    else
        print_info "取消清理"
    fi
}

# 主函数
main() {
    print_success "🚀 Character LLM Dataset Generator 部署脚本"
    print_info "======================================"
    
    # 检查参数
    if [ $# -eq 0 ]; then
        show_help
        exit 0
    fi
    
    case "$1" in
        "docker")
            check_command docker
            check_docker_running
            create_directories
            set_permissions
            deploy_docker
            ;;
        "compose")
            check_command docker
            check_command docker-compose
            check_docker_running
            create_directories
            set_permissions
            deploy_compose
            ;;
        "build")
            check_command docker
            check_docker_running
            create_directories
            set_permissions
            build_local
            ;;
        "status")
            show_status
            ;;
        "logs")
            show_logs
            ;;
        "stop")
            stop_app
            ;;
        "restart")
            restart_app
            ;;
        "clean")
            clean_up
            ;;
        "help"|"-h"|"--help")
            show_help
            ;;
        *)
            print_error "❌ 未知选项: $1"
            show_help
            exit 1
            ;;
    esac
}

# 运行主函数
main "$@" 