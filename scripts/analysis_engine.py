#!/usr/bin/env python3
from __future__ import annotations

ANALYSIS_DIMENSIONS = {
    "institutional": ["HIA机制约束力", "跨部门协作模式", "中央-地方权力博弈", "国际-国内规范对接"],
    "geopolitical": ["遗产外交策略", "资助国身份转变", "被占领土文化主权", "东道国合规性压力"],
    "conservation_logic": ["活态遗产的人为投入悖论", "过度旅游的可逆性边界", "技术跨界应用潜力", "预防性保护vs.修复性保护"],
    "competition": ["申遗唯一性稀释", "预备名录排队机制", "系列遗产vs.单体遗产", "考古发现对既有论证的冲击"],
}


def classify(title: str) -> tuple[str, list[str]]:
    text = title.lower()
    if any(x in text for x in ["hia", "buffer", "jongmyo", "reactive", "缓冲区", "宗庙"]):
        return "institutional", ANALYSIS_DIMENSIONS["institutional"]
    if any(x in text for x in ["ukraine", "palest", "sebastia", "oman", "diplomacy", "乌克兰", "巴勒斯坦", "阿曼"]):
        return "geopolitical", ANALYSIS_DIMENSIONS["geopolitical"]
    if any(x in text for x in ["banaue", "angkor", "tourism", "climate", "restoration", "living", "巴纳韦", "吴哥", "旅游", "活态"]):
        return "conservation_logic", ANALYSIS_DIMENSIONS["conservation_logic"]
    if any(x in text for x in ["nomination", "tentative", "inscription", "申遗", "列入"]):
        return "competition", ANALYSIS_DIMENSIONS["competition"]
    return "institutional", ["跨部门协作模式", "国际-国内规范对接"]


def fallback_analysis(item: dict) -> str:
    title = item["title_original"]
    text = title.lower()
    if any(x in text for x in ["creative products", "apec", "文创"]):
        return "这条新闻的本质是博物馆从收藏展示机构变成文化交流和旅游消费的接口。机制上，文创产品能扩大遗产传播，但也会带来符号简化和商业目标压过研究阐释的风险。对其他城市和遗产地而言，关键不是多做商品，而是把文创放回知识生产、公共教育和地方品牌治理中，形成可解释而非只可销售的遗产表达。"
    if any(x in text for x in ["angkor", "visitor", "hotel", "tourism", "吴哥", "游客", "旅游"]):
        return "这条新闻的核心不是游客数量本身，而是吴哥作为成熟世界遗产地如何重新划定旅游承载与保护底线。机制上，航线、酒店投资和游客管理会同时改变遗产地压力分布；如果管理标准只跟着客流补救，就容易落后于市场扩张。它对其他热门遗产地的意义在于：过度旅游治理必须前置到交通、住宿、票务和分区管理，而不是只在遗产核心区做末端控制。"
    if any(x in text for x in ["digital", "preservation", "数字"]):
        return "这条新闻的本质是遗产保护能力从实体修复扩展到数据、展示和机构协作。数字化不是简单建档，而是把脆弱遗产、馆藏知识和公众传播纳入同一套可持续基础设施。它对其他遗产机构的启示是：技术项目真正有价值时，必须服务于长期保存、跨机构共享和灾害/冲突情境下的备份能力，而不只是一次性展示工程。"
    if any(x in text for x in ["museum", "bell", "artifact", "artefact", "博物馆", "文物"]):
        return "这条新闻的价值在于把单件馆藏放回历史阐释和公共教育体系中。机制上，博物馆不是遗产价值的终点，而是把考古、工艺、宗教记忆和国家叙事重新组织给公众的场所。对其他馆藏型遗产而言，关键问题是：单件文物如何从“珍品展示”转向可比较、可研究、可传播的知识线索。"
    if any(x in text for x in ["geopark", "nature and culture", "地质公园"]):
        return "这条新闻值得关注，因为地质公园把自然遗产、地方文化和社区旅游放进同一个治理框架。它不同于单纯景区宣传，关键在于能否把地质价值转化为教育、社区收益和保护约束。对世界遗产工作而言，这类案例提供了文化与自然双重叙事的参照：遗产价值越复合，越需要跨部门管理和清晰的利益分配机制。"
    if any(x in text for x in ["toltec", "burials", "archaeologist", "archaeology", "考古", "墓葬"]):
        return "这条新闻的价值不只是“又有新发现”，而是新材料可能改变区域文明叙事和遗址价值排序。托尔特克浮雕与墓葬如果能提供更清晰的年代、祭祀或社会结构证据，就会影响相关遗址的比较研究、展示解释和潜在申遗论证。对考古类新闻，关键要追踪后续发表、发掘报告和管理机构如何把发现转化为保护边界。"
    if any(x in text for x in ["ukraine", "war", "conflict", "乌克兰"]):
        return "这条新闻的重点是战时遗产保护从临时救援转向制度化工具。UNESCO移交战略工具，意味着保护工作不只处理受损建筑，还要建立风险识别、优先级排序和跨机构协调机制。它对其他冲突或灾害高风险地区的意义在于：遗产保护能力必须在危机前形成方法和数据底座，危机后才可能快速转入修复、申报和国际援助。"
    kind, dims = classify(title)
    if kind == "institutional":
        return f"这条新闻的本质是遗产保护规则与现实治理压力之间的检验。它值得关注，不只因为事件本身，而是因为它会暴露 HIA、缓冲区、OUV 或跨部门协调机制是否真正有约束力。对其他遗产地而言，意义在于：申遗成功后的核心风险常常不是缺少保护口号，而是当开发、旅游、地方财政或公共展示目标进入同一空间时，谁有权定义保护底线。"
    if kind == "geopolitical":
        return f"这条新闻的本质是遗产被放入国际政治和文化主权叙事中。机制上，UNESCO、国家机构、资助方或被占领土主体都会借遗产保护表达合法性、责任和外交位置。它对其他遗产地的普遍意义在于：遗产不只是保护对象，也可能成为国际承认、援助网络和国家形象竞争的制度入口。"
    if kind == "conservation_logic":
        return f"这条新闻的本质是保护、使用和持续投入之间的张力。活态遗产、游客管理、气候适应或修复工程都不是一次性技术问题，而是长期维护机制。它提示其他遗产地：真正的保护能力不只看修复资金，还要看社区、旅游、技术和日常管理能否形成可持续闭环。"
    return f"这条新闻的本质是申遗竞争中的价值叙事塑造。机制上，候选项目需要把地方资源转译成可比较、可论证、可被咨询机构接受的 OUV 语言。对其他遗产地而言，它提醒我们：申遗不是把好故事提交上去，而是在同类遗产越来越多的情况下证明唯一性、完整性和管理可信度。"


def generate_deep_analysis(item: dict) -> str:
    return fallback_analysis(item)
