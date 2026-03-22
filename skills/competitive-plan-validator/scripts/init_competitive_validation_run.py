#!/usr/bin/env python3
"""Create a three-file scaffold for competitor plus simulation product validation."""

from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path


SCAN_TEMPLATE = """# {title}竞品扫描记录
## 基于当前公开资料的竞品扫描

**记录日期**：{today}
**分析主题**：{title}
**依据方案**：{source}

---

## 一、分析目的

- 明确外部竞品与相邻产品格局
- 验证当前方案的市场位置
- 为后续产品增强提供依据

## 二、产品范围与假设

## 三、竞品分桶

## 四、选定竞品与原因

## 五、逐个来源记录

## 六、即时观察

## 七、阶段性判断
"""


REPORT_TEMPLATE = """# {title}竞品分析报告
## 基于竞品扫描的综合判断

**报告日期**：{today}
**分析主题**：{title}
**配套记录**：[{title}竞品扫描记录.md]({scan_link})
**依据方案**：{source}

---

## 一、结论先行

## 二、市场判断

## 三、对本产品优势的扩充

## 四、竞品不足与可吸收能力

## 五、改进优先级

## 六、对产品形态的启发

## 七、来源列表
"""


IMPROVEMENT_TEMPLATE = """# {title}产品增强建议
## 将竞品分析转化为可执行改进

**建议日期**：{today}
**分析主题**：{title}
**关联报告**：[{title}竞品分析报告.md]({report_link})
**依据方案**：{source}

---

## 一、设计原则

## 二、P0 改进

## 三、P1 改进

## 四、P2 改进

## 五、预期效果
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create markdown files for competitor-aware product validation."
    )
    parser.add_argument("title", help="Base title, for example: ADS竞品对标")
    parser.add_argument(
        "--output-dir",
        default=".",
        help="Directory where the markdown files will be created.",
    )
    parser.add_argument(
        "--source",
        default="[请替换为产品方案路径](PATH)",
        help="Markdown text used in the source document field.",
    )
    parser.add_argument(
        "--date",
        help="Optional absolute date (YYYY-MM-DD) written into the scaffold files.",
    )
    return parser.parse_args()


def resolve_date(raw: str | None) -> str:
    if not raw:
        return date.today().isoformat()
    return date.fromisoformat(raw).isoformat()


def write_if_missing(path: Path, content: str) -> None:
    if path.exists():
        raise FileExistsError(f"{path} already exists")
    path.write_text(content, encoding="utf-8")


def main() -> int:
    args = parse_args()
    output_dir = Path(args.output_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    today = resolve_date(args.date)
    base = args.title.strip()
    scan_name = f"{base}竞品扫描记录.md"
    report_name = f"{base}竞品分析报告.md"
    improvement_name = f"{base}产品增强建议.md"

    scan_path = output_dir / scan_name
    report_path = output_dir / report_name
    improvement_path = output_dir / improvement_name

    write_if_missing(
        scan_path,
        SCAN_TEMPLATE.format(title=base, today=today, source=args.source),
    )
    write_if_missing(
        report_path,
        REPORT_TEMPLATE.format(
            title=base,
            today=today,
            source=args.source,
            scan_link=scan_name,
        ),
    )
    write_if_missing(
        improvement_path,
        IMPROVEMENT_TEMPLATE.format(
            title=base,
            today=today,
            source=args.source,
            report_link=report_name,
        ),
    )

    print(scan_path)
    print(report_path)
    print(improvement_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
