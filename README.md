# fknc-calc

疯狂农场计算器。

## Fine-tune co-efficient

Mean of different co-efficients will give the most great result for both multiplier factor.

```python
>>> 24000 / 11.5369
2080.281531433921
>>> 10300 / 0.7155 / 7
2056.503943296396
>>> 9482 / 3 / 1.29**1.5
2157.2184738448486
>>> 2080.281531433921 + 2056.503943296396 + 2157.2184738448486
6294.003948575166
>>> (2080.281531433921 + 2056.503943296396 + 2157.2184738448486) / 3
2098.001316191722
>>> 2098 * 11.5369
24204.4162
>>> 0.7155 * 7 * 2098
10507.832999999999
>>> 3 * 1.29**1.5 * 2098
9221.706675144465
```

## Prepare UV

```bash
# Windows
winget install --id=astral-sh.uv  -e
# Linux/MacOS
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## Start local WebUI

```bash
uv run streamlit run ui.py
```
