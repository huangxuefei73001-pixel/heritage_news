#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from common import connect, init_db


TIER_LABELS = {
    "core_official": "官方/机构",
    "wire_media": "通讯社",
    "regional_media": "地区媒体",
    "specialist_media": "专业来源",
}


def insight_for(row) -> dict:
    text = f"{row['title_original']} {row['source_name']}".lower()
    role = {
        "core_official": "事实来源",
        "wire_media": "事实来源/现场补充",
        "regional_media": "现场补充",
        "specialist_media": "机制分析线索",
    }.get(row["source_tier"], "待判断")
    if any(k in text for k in ["nomination", "tentative", "inscription", "申遗", "预备名录", "列入世界遗产"]):
        return {
            "role": role,
            "issue": "申遗策略与比较叙事",
            "mechanism": "地方价值表述进入 UNESCO 提名、预评估或跨国系列遗产机制",
            "framework": "申遗策略 / 比较分析 / 属性识别",
            "comparison": "可与同类型既有遗产、同一主题系列遗产和咨询机构评估意见比较。",
            "question": "这个候选项目的 OUV 叙事是补足空白，还是复用已有类型？",
            "judgment": "这类新闻值得关注，因为它暴露了国家和地方如何把资源转译成世界遗产语言。",
            "lead": "适合进入申遗案例库，追踪预备名录、比较研究和 ICOMOS/IUCN 评估。",
            "comment": True,
        }
    if any(k in text for k in ["danger", "endangered", "reactive monitoring", "buffer zone", "delist", "withdraw", "濒危", "缓冲区", "退出", "除名"]):
        return {
            "role": role,
            "issue": "世界遗产风险治理与名录机制压力",
            "mechanism": "濒危名录、Reactive Monitoring、缓冲区管控或社区退出诉求触发制度回应",
            "framework": "SOC / Reactive Monitoring / 除名机制 / 社区参与 / 入遗后管理",
            "comparison": "可与德累斯顿易北河谷、利物浦、Ngorongoro、Tyre 等争议或风险案例比较。",
            "question": "现行世界遗产机制能处理的是 OUV 受损，还是也能处理社区不愿继续承受遗产地治理成本？",
            "judgment": "这类新闻比普通动态更重要，因为它显示名录荣誉背后的治理代价和制度边界。",
            "lead": "适合追踪 WHC 决议、SOC 报告、地方社区诉求和保护/发展冲突。",
            "comment": True,
        }
    if any(k in text for k in ["anniversary", "周年", "mature", "maturity", "volunteer", "public participation", "公众参与", "联动"]):
        return {
            "role": role,
            "issue": "遗产地成熟治理与公众参与",
            "mechanism": "入遗后的品牌、教育、志愿者、跨遗产协同和长期管理能力建设",
            "framework": "遗产地生命周期 / 入遗后管理 / 社区参与 / 能力建设",
            "comparison": "可与鼓浪屿、景迈山、乔治市、北京中轴线和杭州多遗产联动实践比较。",
            "question": "遗产地进入成熟期后，管理重点如何从申遗成功转向日常治理和公共价值生产？",
            "judgment": "这类新闻的价值在于观察遗产地从项目化申遗走向常态化治理。",
            "lead": "适合沉淀成熟遗产地治理案例和公众参与机制。",
            "comment": True,
        }
    if any(k in text for k in ["iucn", "climate", "nature", "conservation", "restoration", "biodiversity", "自然"]):
        return {
            "role": role,
            "issue": "自然遗产与文化遗产的交叉治理",
            "mechanism": "从自然保护、气候行动或生态修复机制外溢到遗产保护",
            "framework": "PNC 框架 / 融资机制 / 能力建设 / 属性识别",
            "comparison": "可与自然-文化复合型遗产、IUCN 评估意见、国家公园和世界遗产地管理比较。",
            "question": "自然保护框架如何改变文化遗产保护的价值表述和管理工具？",
            "judgment": "这类新闻的价值不在事件本身，而在外部机制可能重塑遗产工作方法。",
            "lead": "适合跟踪 IUCN、UNESCO WHC、国家林草局与自然保护地体系。",
            "comment": True,
        }
    if any(k in text for k in ["intangible", "living heritage", "patrimonio vivo", "非物质", "活态"]):
        return {
            "role": role,
            "issue": "活态遗产进入教育与社区发展",
            "mechanism": "从名录保护转向学习、传承和社区能力建设",
            "framework": "社区参与 / 能力建设 / 活态遗产教育",
            "comparison": "可与 UNESCO ICH、地方教育项目和社区传承案例比较。",
            "question": "活态遗产如何被转译成教育资源和地方发展能力？",
            "judgment": "这类新闻适合作为活态遗产从保护对象转向社会实践的观察样本。",
            "lead": "适合沉淀活态遗产教育案例库。",
            "comment": True,
        }
    if any(k in text for k in ["provenance", "restitution", "illicit", "traffic", "code of ethics", "返还", "非法"]):
        return {
            "role": role,
            "issue": "博物馆治理与文物流通",
            "mechanism": "伦理准则、来源研究、非法贩运治理和公共机构协作",
            "framework": "博物馆治理 / 文物流通 / 除名与返还机制 / 合规伦理",
            "comparison": "可与 ICOM 准则、ILAM 区域案例和国家文物局监管动态比较。",
            "question": "博物馆治理如何从藏品管理扩展到跨境法律和伦理机制？",
            "judgment": "这类新闻常常提供制度变化和现场冲突，比单纯官方通报更能形成判断。",
            "lead": "适合跟踪 ICOM、国家文物局、ILAM 与区域执法案例。",
            "comment": True,
        }
    if any(k in text for k in ["stonehenge", "world heritage", "世界遗产", "heritage site", "遗产地", "mature", "maturity"]):
        return {
            "role": role,
            "issue": "世界遗产地生命周期与成熟治理",
            "mechanism": "申遗后管理、展示、社区关系和长期规划进入成熟阶段",
            "framework": "入遗后管理 / 遗产地生命周期 / SOC 与 Reactive Monitoring",
            "comparison": "可与 Jodrell Bank、Pic du Midi、鼓浪屿、景迈山等遗产地成熟阶段比较。",
            "question": "遗产地 10 年、20 年、30 年后的管理问题如何变化？",
            "judgment": "这类新闻适合从单点动态进入横向比较和历史回溯。",
            "lead": "适合比较鼓浪屿、景迈山、滨城/英国遗产地等成熟案例。",
            "comment": True,
        }
    if any(k in text for k in ["archaeolog", "考古", "excavat", "unearthed", "遗址"]):
        return {
            "role": role,
            "issue": "考古发现到遗产叙事",
            "mechanism": "新发现通过研究、展示和媒体传播进入公共文化叙事",
            "framework": "属性识别 / 申遗策略 / 比较分析 / 展示阐释",
            "comparison": "可与同类遗址、区域文明叙事和既有申遗文本比较。",
            "question": "考古发现什么时候会变成地方身份、旅游或申遗资源？",
            "judgment": "这类新闻要重点判断其是否只是发现，还是已经进入遗产化过程。",
            "lead": "适合建立考古发现-展示转化案例清单。",
            "comment": False,
        }
    return {
        "role": role,
        "issue": "需人工复核的遗产动态",
        "mechanism": "信息价值明确，但机制含义需要结合上下文判断",
        "framework": "待归类",
        "comparison": "先查是否能联系过往事件、同类遗产地或现行机制。",
        "question": "这条新闻是否能连接到既有制度、历史案例或项目机会？",
        "judgment": "暂不做强判断，避免把普通新闻包装成研究线索。",
        "lead": "先保留为周报候选，不进入重点线索。",
        "comment": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Heritage News Chinese digest")
    parser.add_argument("--days", type=int, default=1)
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--language", default="zh")
    parser.add_argument("--include-opportunities", action="store_true")
    parser.add_argument("--insight", action="store_true", help="Add event-issue-mechanism research/work leads")
    parser.add_argument("--refresh", action="store_true", help="Fetch verified sources before generating digest")
    args = parser.parse_args()

    if args.refresh:
        subprocess.run(
            [sys.executable, str(Path(__file__).with_name("fetch.py")), "--all", "--update-db", "--force"],
            check=False,
        )

    conn = connect()
    init_db(conn)
    where = ["pub_date >= datetime('now', ?)"]
    params = [f"-{args.days} days"]
    if not args.include_opportunities:
        where.append("url NOT LIKE '%/opportunity/%'")
        where.append("lower(title_original) NOT LIKE '%coordinator%'")
        where.append("lower(title_original) NOT LIKE '%officer%'")
        where.append("lower(title_original) NOT LIKE '%trainer%'")
        where.append("lower(title_original) NOT LIKE '%vacancy%'")
        where.append("lower(title_original) NOT LIKE '%job%'")
    rows = conn.execute(
        f"""SELECT pub_date,source_name,source_tier,language,title_original,title_zh,summary_zh,url
            FROM heritage_news
            WHERE {' AND '.join(where)}
            ORDER BY pub_date DESC, source_tier ASC
            LIMIT ?""",
        [*params, args.limit],
    ).fetchall()
    conn.close()

    print(f"# 文化遗产新闻简报（近 {args.days} 天）\n")
    if not rows:
        print("当前数据库没有符合条件的真实来源新闻。")
        return
    for row in rows:
        title = row["title_zh"] or f"{row['title_original']} [{row['language']}]"
        print(f"- **{title}**")
        print(f"  来源：{row['source_name']}｜{TIER_LABELS.get(row['source_tier'], row['source_tier'])}｜{row['pub_date']}")
        if row["summary_zh"]:
            print(f"  摘要：{row['summary_zh'][:100]}")
        if args.insight:
            insight = insight_for(row)
            if insight["comment"]:
                print(f"  来源角色：{insight['role']}")
                print(f"  议题：{insight['issue']}")
                print(f"  机制：{insight['mechanism']}")
                print(f"  专业框架：{insight['framework']}")
                print(f"  比较/回溯：{insight['comparison']}")
                print(f"  研究问题：{insight['question']}")
                print(f"  观察判断：{insight['judgment']}")
                print(f"  工作线索：{insight['lead']}")
        print(f"  链接：{row['url']}")


if __name__ == "__main__":
    main()
