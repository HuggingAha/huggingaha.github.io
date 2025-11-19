# 博客 - 基于 Blowfish 主题

> 使用 Hugo 和 Blowfish 主题构建的个人博客网站，部署在 GitHub Pages 上。

[![Hugo](https://img.shields.io/badge/Hugo-0.143.1-blue?logo=hugo)](https://gohugo.io/)
[![Blowfish](https://img.shields.io/badge/Theme-Blowfish-blue)](https://blowfish.page/)
[![Deploy Status](https://github.com/用户名/用户名.github.io/actions/workflows/hugo.yml/badge.svg)](https://github.com/用户名/用户名.github.io/actions/workflows/hugo.yml)
[![GitHub License](https://img.shields.io/github/license/用户名/用户名.github.io)](LICENSE)

---

## 项目简介

这是我的个人博客网站，采用 [Hugo](https://gohugo.io/) 静态网站生成器构建，并基于功能强大的 [Blowfish](https://blowfish.page/) 主题进行定制。

主题特性可查阅 [Blowfish 官方文档](https://blowfish.page/zh-cn/docs/)。

---

## 快速开始

### 前置要求

- [Git](https://git-scm.com/)
- [Hugo Extended](https://gohugo.io/installation/) 

### 本地运行

1. **克隆仓库**
   ```bash
   git clone https://github.com/HuggingAha/huggingaha.github.io.git
   cd huggingaha.github.io.git
   ```

2. **更新主题子模块**（如使用 submodule 方式）
   ```bash
   git submodule update --init --recursive
   ```

3. **启动本地服务器**
   ```bash
   hugo server -D
   ```

   打开浏览器访问 `http://localhost:1313` 即可预览。

### 构建站点

```bash
hugo --minify --gc
```

生成的静态文件位于 `public/` 目录。

---

## 部署说明

本博客使用 GitHub Actions 自动部署到 GitHub Pages。

**部署触发条件**：向 `main` 分支推送代码

**部署流程**：
1. GitHub Actions 自动检出代码
2. 安装 Hugo Extended 并构建站点
3. 将生成的静态文件部署至 GitHub Pages

**查看部署状态**：访问仓库的 **Actions** 标签页。

---

## 技术栈

- **框架**: [Hugo](https://gohugo.io/) 
- **主题**: [Blowfish](https://blowfish.page/)
- **样式**: [Tailwind CSS](https://tailwindcss.com/)
- **部署**: [GitHub Pages](https://pages.github.com/) + [GitHub Actions](https://github.com/features/actions)
- **版本控制**: Git

---

## 致谢

本博客基于 **Blowfish** 主题构建，感谢 [Nuno Coração](https://github.com/nunocoracao) 与社区贡献者的出色工作。

- 🌏 [Blowfish 示例站点](https://blowfish.page/)
- 📑 [Blowfish 主题文档](https://blowfish.page/zh-cn/docs/)
- 🐛 [主题 Bug 报告](https://github.com/nunocoracao/blowfish/issues)
- 💡 [功能建议与讨论](https://github.com/nunocoracao/blowfish/discussions)

---

## 许可证

本项目采用 [MIT 许可证](LICENSE)。Blowfish 主题本身的许可证请查看 [themes/blowfish/LICENSE](https://github.com/nunocoracao/blowfish/blob/main/LICENSE)。

