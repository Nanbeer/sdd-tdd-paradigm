#!/bin/bash
# SDD-TDD Paradigm 安装脚本
#
# 用法：
#   ./install.sh                          # 交互式安装
#   ./install.sh --user                   # 安装到用户目录
#   ./install.sh --project /path/to/proj  # 安装到项目目录
#   ./install.sh --uninstall              # 卸载

set -euo pipefail

SKILL_NAME="sdd-tdd-paradigm"
USER_SKILL_DIR="$HOME/.claude/skills"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 颜色
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[OK]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

detect_shell() {
    if [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
        echo "windows"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        echo "macos"
    else
        echo "linux"
    fi
}

install_to_user() {
    local target_dir="$USER_SKILL_DIR/$SKILL_NAME"

    if [[ -d "$target_dir" ]]; then
        log_warn "用户技能目录已存在：$target_dir"
        read -p "是否覆盖？(y/N) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_info "取消安装"
            exit 0
        fi
        rm -rf "$target_dir"
    fi

    mkdir -p "$USER_SKILL_DIR"
    cp -r "$SCRIPT_DIR/skills/$SKILL_NAME" "$target_dir"
    chmod +x "$target_dir/scripts/"*.sh 2>/dev/null || true

    log_success "已安装到用户目录：$target_dir"
    log_info "该技能将在所有项目中可用"
}

install_to_project() {
    local project_dir="$1"
    local target_dir="$project_dir/.claude/skills/$SKILL_NAME"

    if [[ ! -d "$project_dir" ]]; then
        log_error "项目目录不存在：$project_dir"
        exit 1
    fi

    if [[ -d "$target_dir" ]]; then
        log_warn "项目技能目录已存在：$target_dir"
        read -p "是否覆盖？(y/N) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_info "取消安装"
            exit 0
        fi
        rm -rf "$target_dir"
    fi

    mkdir -p "$project_dir/.claude/skills"
    cp -r "$SCRIPT_DIR/skills/$SKILL_NAME" "$target_dir"
    chmod +x "$target_dir/scripts/"*.sh 2>/dev/null || true

    log_success "已安装到项目目录：$target_dir"
    log_info "该技能仅在该项目中可用"
}

uninstall() {
    local target_dir="$1"

    if [[ ! -d "$target_dir" ]]; then
        log_warn "安装目录不存在：$target_dir"
        exit 0
    fi

    read -p "确认卸载 $SKILL_NAME？(y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "取消卸载"
        exit 0
    fi

    rm -rf "$target_dir"
    log_success "已卸载：$target_dir"
}

interactive_install() {
    echo ""
    echo "╔════════════════════════════════════════════╗"
    echo "║    SDD-TDD Paradigm 安装程序              ║"
    echo "║    规格驱动 × 测试驱动开发流程            ║"
    echo "╚════════════════════════════════════════════╝"
    echo ""
    echo "请选择安装位置："
    echo ""
    echo "  1) 用户目录 (~/.claude/skills/)"
    echo "     所有项目可用（推荐）"
    echo ""
    echo "  2) 当前项目 (.claude/skills/)"
    echo "     仅当前项目可用"
    echo ""
    echo "  3) 自定义项目目录"
    echo ""
    echo "  0) 卸载"
    echo ""
    read -p "请选择 [0-3] (默认 1): " -r choice
    choice=${choice:-1}

    case "$choice" in
        1)
            install_to_user
            ;;
        2)
            install_to_project "$(pwd)"
            ;;
        3)
            read -p "请输入项目目录： " -r project_dir
            install_to_project "$project_dir"
            ;;
        0)
            echo ""
            echo "卸载位置："
            echo "  1) 用户目录"
            echo "  2) 当前项目"
            read -p "请选择 [1-2]: " -r uninstall_choice
            case "$uninstall_choice" in
                1) uninstall "$USER_SKILL_DIR/$SKILL_NAME" ;;
                2) uninstall "$(pwd)/.claude/skills/$SKILL_NAME" ;;
                *) log_error "无效选择"; exit 1 ;;
            esac
            ;;
        *)
            log_error "无效选择：$choice"
            exit 1
            ;;
    esac

    echo ""
    log_info "安装完成！"
    echo ""
    log_info "下一步："
    echo "  1. 在 Claude Code 中输入：/sdd-tdd"
    echo "  2. 描述你要开发的功能"
    echo "  3. 跟随流程完成开发"
    echo ""
    log_info "文档："
    echo "  - 快速开始：docs/QUICKSTART.md"
    echo "  - 架构说明：docs/ARCHITECTURE.md"
    echo "  - 方法论：docs/METHODOLOGY.md"
    echo ""
}

# 命令行参数处理
case "${1:-}" in
    --user)
        install_to_user
        ;;
    --project)
        if [[ -z "${2:-}" ]]; then
            log_error "请指定项目目录：install.sh --project /path/to/project"
            exit 1
        fi
        install_to_project "$2"
        ;;
    --uninstall)
        uninstall "$USER_SKILL_DIR/$SKILL_NAME"
        ;;
    --help|-h)
        echo "SDD-TDD Paradigm 安装脚本"
        echo ""
        echo "用法："
        echo "  install.sh                         交互式安装"
        echo "  install.sh --user                  安装到用户目录"
        echo "  install.sh --project <path>        安装到项目目录"
        echo "  install.sh --uninstall             卸载"
        echo "  install.sh --help                  显示帮助"
        ;;
    *)
        interactive_install
        ;;
esac
