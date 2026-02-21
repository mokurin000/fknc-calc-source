# fknc-calc

疯狂农场计算器。

## 准备uv

```bash
# Windows
winget install --id=astral-sh.uv  -e
# Linux/MacOS
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## 启动本机web ui

### uv 使用中国镜像

- Powershell

```pwsh
$env:UV_INDEX = "https://mirrors.bfsu.edu.cn/pypi/web/simple"
```

- Bash

```bash
export UV_INDEX = "https://mirrors.bfsu.edu.cn/pypi/web/simple"
```

- NuShell

```nushell
$env.UV_INDEX = "https://mirrors.bfsu.edu.cn/pypi/web/simple"
```

### 部署

```bash
uv run streamlit run ui.py
```
