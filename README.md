# geo-ncbi-fetch

[![version](https://img.shields.io/badge/version-1.2.0-blue)](https://github.com/LovelyMonkey123/GEO_fetch_my)

Claude Code skill：输入 GSE 编号，自动从 NCBI GEO 提取数据集元数据并翻译为学术中文，输出 Excel。

## 安装

### 1. 克隆仓库

```bash
git clone https://github.com/LovelyMonkey123/GEO_fetch_my.git
```

### 2. 注册为 Claude Code Skill

将 `geo-ncbi-fetch/` 目录复制到 Claude Code 的 skills 目录：

**Windows**
```bash
xcopy geo-ncbi-fetch %USERPROFILE%\.claude\skills\geo-ncbi-fetch\ /E /I
```

**macOS / Linux**
```bash
cp -r geo-ncbi-fetch ~/.claude/skills/geo-ncbi-fetch/
```

### 3. 安装依赖

需要 conda 环境 + Biopython。首次调用时 Skill 会自动检测环境并引导安装（清华镜像）。

或手动安装：

```bash
pip install biopython openpyxl -i https://pypi.tuna.tsinghua.edu.cn/simple
```

## 使用

安装后在 Claude Code 中直接对话：

```
用 geo-ncbi-fetch 查一下这几个 GSE：GSE000000, GSE000001
```

```
把 数据集.xlsx 里的 GSE 元数据都拉下来
```

Skill 自动完成：环境检测 → NCBI 提取 → 中文学术翻译 → Excel 输出。

> 给 GSE 编号新建 Excel；给已有表格则追加列，输出 `<原名>_annotated.xlsx`。

## 输出示例

| Accession | GEO标题(中) | 实验类型(中) | 样本类型 | 样本数 | PubMed | 发布日期 | 数据下载 |
|-----------|-------------|-------------|---------|-------|--------|---------|---------|
| GSEXXXXXX | [中文学术标题] | 高通量测序表达谱分析 | 样本类型A、样本类型B | XX | XXXXXXXX | YYYY/MM/DD | GEO页面 🔗 |

## 依赖

- Python ≥ 3.8
- Biopython
- openpyxl

## 版本

| 版本 | 更新 |
|------|------|
| v1.2.0 | 双输出策略（新建/追加）、样本类型提取 |
| v1.1.0 | conda 环境自检、批次断点续跑 |
| v1.0.0 | 基础提取 |

## 作者

[@LovelyMonkey123](https://github.com/LovelyMonkey123)
