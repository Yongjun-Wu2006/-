# -*- coding: utf-8 -*-
"""
期刊参考文献格式自动格式化工具
================================
功能：
1. 输入期刊名称，自动检索该期刊的参考文献引用格式
2. 输入待格式化的参考文献，自动按该期刊格式重新排版
3. 支持 APA / IEEE / Chicago / GB/T 7714-2015 / MLA / Vancouver / Nature / Science 等主流格式
4. 集成 Crossref API，可通过 DOI 精准获取格式化引文

依赖：requests（可选，用于网络检索与 Crossref 查询）
安装：pip install requests
"""

import re
import json
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from urllib.parse import quote
from typing import Optional, Dict, List, Tuple

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

# ============================================================
# 一、期刊 -> 引用格式 数据库
# ============================================================

# 常见期刊与其对应的引用格式
JOURNAL_STYLE_DB = {
    # 英文期刊
    "nature": "nature",
    "science": "science",
    "cell": "cell",
    "the lancet": "vancouver",
    "new england journal of medicine": "vancouver",
    "journal of the american medical association": "vancouver",
    "pnas": "pnas",
    "proceedings of the national academy of sciences": "pnas",
    "the journal of biological chemistry": "jbc",
    "plos one": "plos",
    "scientific reports": "nature",
    "nucleic acids research": "oxford",
    "bioinformatics": "oxford",
    "ieee transactions on pattern analysis and machine intelligence": "ieee",
    "ieee transactions on image processing": "ieee",
    "ieee transactions on multimedia": "ieee",
    "ieee transactions on circuits and systems for video technology": "ieee",
    "ieee transactions on communications": "ieee",
    "ieee transactions on wireless communications": "ieee",
    "acm computing surveys": "acm",
    "communications of the acm": "acm",
    "acm transactions on graphics": "acm",
    "journal of machine learning research": "jmlr",
    "the journal of finance": "apa",
    "american economic review": "chicago",
    "journal of political economy": "chicago",
    "american sociological review": "asa",
    "american psychological review": "apa",
    "psychological review": "apa",
    "journal of consulting and clinical psychology": "apa",
    "annals of the rheumatic diseases": "vancouver",
    "british medical journal": "vancouver",
    "the bmj": "vancouver",
    "journal of the american chemical society": "jacs",
    "angewandte chemie international edition": "wiley-vch",
    "chemical reviews": "acs",
    "accounts of chemical research": "acs",
    "journal of physical chemistry letters": "acs",
    "acs nano": "acs",
    "nano letters": "acs",
    "advanced materials": "wiley-vch",
    "advanced functional materials": "wiley-vch",
    "small": "wiley-vch",
    "applied physics letters": "aip",
    "physical review letters": "aps",
    "physical review b": "aps",
    "physical review d": "aps",
    "optics letters": "osa",
    "optics express": "osa",
    "journal of the optical society of america": "osa",
    "environmental science & technology": "acs",
    "water research": "elsvier",
    "journal of hazardous materials": "elsvier",
    "chemical engineering journal": "elsvier",
    "journal of cleaner production": "elsvier",
    "renewable and sustainable energy reviews": "elsvier",
    "applied energy": "elsvier",
    "energy": "elsvier",
    "international journal of heat and mass transfer": "elsvier",
    "construction and building materials": "elsvier",
    "cement and concrete research": "elsvier",
    "automation in construction": "elsvier",
    "journal of cleaner production": "elsvier",
    # 中文期刊
    "中国科学": "gbt7714",
    "科学通报": "gbt7714",
    "自然科学进展": "gbt7714",
    "计算机学报": "gbt7714",
    "软件学报": "gbt7714",
    "计算机研究与发展": "gbt7714",
    "自动化学报": "gbt7714",
    "电子学报": "gbt7714",
    "通信学报": "gbt7714",
    "控制与决策": "gbt7714",
    "系统工程理论与实践": "gbt7714",
    "管理世界": "gbt7714",
    "经济研究": "gbt7714",
    "管理科学学报": "gbt7714",
    "会计研究": "gbt7714",
    "金融研究": "gbt7714",
    "中国工业经济": "gbt7714",
    "世界经济": "gbt7714",
    "中国社会科学": "gbt7714",
    "社会学研究": "gbt7714",
    "心理学报": "gbt7714",
    "外语教学与研究": "gbt7714",
    "中国图书馆学报": "gbt7714",
    "情报学报": "gbt7714",
    "图书情报工作": "gbt7714",
    "中华医学杂志": "gbt7714",
    "中华内科杂志": "gbt7714",
    "中华外科杂志": "gbt7714",
    "中华心血管病杂志": "gbt7714",
    "中华肿瘤杂志": "gbt7714",
    "药学学报": "gbt7714",
    "中国中药杂志": "gbt7714",
    "中草药": "gbt7714",
    "高等学校化学学报": "gbt7714",
    "化学学报": "gbt7714",
    "无机化学学报": "gbt7714",
    "物理学报": "gbt7714",
    "光学学报": "gbt7714",
    "中国激光": "gbt7714",
    "力学学报": "gbt7714",
    "土木工程学报": "gbt7714",
    "建筑结构学报": "gbt7714",
    "水利学报": "gbt7714",
    "岩土工程学报": "gbt7714",
    "中国电机工程学报": "gbt7714",
    "电工技术学报": "gbt7714",
    "电力系统自动化": "gbt7714",
    "农业工程学报": "gbt7714",
    "作物学报": "gbt7714",
    "中国农业科学": "gbt7714",
    "园艺学报": "gbt7714",
    "植物保护学报": "gbt7714",
    "林业科学": "gbt7714",
    "环境科学": "gbt7714",
    "环境科学学报": "gbt7714",
    "中国环境科学": "gbt7714",
    "环境工程学报": "gbt7714",
}

# 引用格式的中文描述
STYLE_DESCRIPTIONS = {
    "apa": "APA (American Psychological Association) 第7版",
    "ieee": "IEEE (电气电子工程师学会)",
    "chicago": "Chicago (芝加哥) 注释与书目格式",
    "gbt7714": "GB/T 7714-2015 (中国国家标准)",
    "mla": "MLA (现代语言协会) 第9版",
    "vancouver": "Vancouver (温哥华/国际医学期刊编辑委员会)",
    "nature": "Nature 系列期刊",
    "science": "Science 期刊",
    "cell": "Cell 系列期刊",
    "pnas": "PNAS (美国国家科学院院刊)",
    "jbc": "Journal of Biological Chemistry",
    "plos": "PLOS 系列期刊",
    "oxford": "Oxford University Press",
    "acm": "ACM (计算机协会)",
    "jmlr": "Journal of Machine Learning Research",
    "asa": "ASA (美国社会学协会)",
    "jacs": "JACS (美国化学会志)",
    "acs": "ACS (美国化学会) 期刊",
    "wiley-vch": "Wiley-VCH 期刊",
    "aip": "AIP (美国物理联合会)",
    "aps": "APS (美国物理学会)",
    "osa": "OSA (美国光学学会)",
    "elsvier": "Elsevier 期刊",
}


def lookup_journal_style(journal_name: str) -> Optional[str]:
    """在本地数据库中查找期刊对应的引用格式"""
    name = journal_name.strip().lower()
    # 精确匹配
    if name in JOURNAL_STYLE_DB:
        return JOURNAL_STYLE_DB[name]
    # 模糊匹配（包含关键词）
    for key, style in JOURNAL_STYLE_DB.items():
        if key in name or name in key:
            return style
    return None


# ============================================================
# 二、网络检索期刊引用格式
# ============================================================

def search_journal_style_online(journal_name: str) -> Tuple[Optional[str], str]:
    """
    通过网络搜索查找期刊的引用格式。
    返回 (style, info)  其中 style 可能为 None，info 为搜索到的说明信息。
    """
    if not HAS_REQUESTS:
        return None, "未安装 requests 库，无法进行网络检索。请运行: pip install requests"

    try:
        # 使用 DuckDuckGo 的 HTML 搜索（无需 API key）
        query = quote(f'"{journal_name}" "author guidelines" reference format citation style')
        url = f"https://html.duckduckgo.com/html/?q={query}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        resp = requests.get(url, headers=headers, timeout=10)
        html = resp.text

        # 提取搜索结果片段
        snippets = re.findall(r'class="result__snippet">(.*?)</a>', html, re.S)
        # 清理 HTML 标签
        clean_snippets = []
        for s in snippets[:8]:
            text = re.sub(r'<[^>]+>', '', s).strip()
            text = re.sub(r'\s+', ' ', text)
            clean_snippets.append(text)

        combined = " ".join(clean_snippets).lower()

        # 根据关键词判断格式
        style_keywords = {
            "apa": ["apa", "american psychological association", "7th edition"],
            "ieee": ["ieee", "institute of electrical"],
            "chicago": ["chicago", "notes and bibliography"],
            "gbt7714": ["gb/t 7714", "gb/t7714", "中国国家标准", "7714"],
            "mla": ["mla", "modern language association"],
            "vancouver": ["vancouver", "icmje", "uniform requirements"],
            "nature": ["nature", "author guidelines"],
            "science": ["science magazine", "aaas"],
            "cell": ["cell press", "cell journal"],
            "acs": ["acs", "american chemical society"],
            "elsevier": ["elsevier"],
            "wiley": ["wiley"],
            "oxford": ["oxford university press"],
        }

        for style, keywords in style_keywords.items():
            for kw in keywords:
                if kw in combined:
                    info = f"根据网络搜索结果推断该期刊使用 {STYLE_DESCRIPTIONS.get(style, style)} 格式"
                    if clean_snippets:
                        info += "\n\n搜索结果摘要:\n" + "\n".join(f"- {s}" for s in clean_snippets[:4])
                    return style, info

        if clean_snippets:
            info = "未能自动识别引用格式，请在下方手动选择。搜索结果摘要:\n" + "\n".join(
                f"- {s}" for s in clean_snippets[:4])
        else:
            info = "网络搜索未返回有效结果，请手动选择引用格式。"
        return None, info

    except Exception as e:
        return None, f"网络检索失败: {str(e)}\n请手动选择引用格式。"


# ============================================================
# 三、参考文献解析器
# ============================================================

class Reference:
    """解析后的参考文献结构化数据"""
    def __init__(self):
        self.authors: List[Dict] = []   # [{"given":"...", "family":"..."}]
        self.title: str = ""
        self.container: str = ""         # 期刊名 / 书名 / 会议名
        self.year: str = ""
        self.volume: str = ""
        self.issue: str = ""
        self.pages: str = ""
        self.doi: str = ""
        self.url: str = ""
        self.publisher: str = ""
        self.place: str = ""
        self.type: str = "journal"       # journal / book / conference / thesis / report
        self.raw: str = ""


def _parse_single_author(name: str) -> Dict:
    """解析单个作者名，自动识别命名规范"""
    name = name.strip().strip('.。')
    if not name:
        return {"given": "", "family": ""}

    # 中文名
    if re.search(r'[\u4e00-\u9fff]', name):
        parts = name.split()
        if len(parts) >= 2:
            return {"given": ' '.join(parts[1:]), "family": parts[0]}
        else:
            return {"given": "", "family": parts[0]}

    # 含逗号: "Family, Given" (APA/Chicago 风格)
    if ',' in name:
        fam, giv = name.split(',', 1)
        return {"given": giv.strip().strip('.'), "family": fam.strip()}

    parts = name.split()
    if len(parts) == 1:
        return {"given": "", "family": parts[0]}

    # IEEE 风格: 以缩写开头 (A. B. Smith)
    initials = []
    i = 0
    while i < len(parts) and re.match(r'^[A-Za-z]\.?$', parts[i]):
        initials.append(parts[i].strip('.'))
        i += 1
    if initials and i < len(parts):
        return {"given": ' '.join(initials), "family": ' '.join(parts[i:])}

    # Vancouver 风格: "Smith J A" — 首词为姓，其余为单字母缩写
    rest_are_initials = all(
        re.match(r'^[A-Za-z]\.?$', p) for p in parts[1:]
    )
    if rest_are_initials:
        return {
            "given": ' '.join(p.strip('.') for p in parts[1:]),
            "family": parts[0],
        }

    # 兜底: "Given Family" — 末词为姓
    return {"given": ' '.join(parts[:-1]), "family": parts[-1]}


def _split_authors(author_str: str) -> List[Dict]:
    """将作者字符串拆分为 [{given, family}] 列表"""
    # 处理 "等" / "et al." 等多作者省略标记
    author_str = re.sub(r'\s*,\s*等\s*\.?$', '', author_str)
    author_str = re.sub(r'\s+et\s+al\.?\s*$', '', author_str, flags=re.I)
    author_str = re.sub(r'\s+等\s*$', '', author_str)

    # 将 & / and / 和 / 及 统一替换为逗号（作者间分隔）
    author_str = re.sub(r'\s*,\s*&\s+', ', ', author_str)   # APA: ", & "
    author_str = re.sub(r'\s*&\s+', ', ', author_str)        # "& "
    author_str = re.sub(r'\s+and\s+', ', ', author_str, flags=re.I)
    author_str = re.sub(r'\s+(和|及)\s+', ', ', author_str)
    author_str = re.sub(r'[；;]', ',', author_str)

    authors = []
    # 按逗号拆分，但需要区分 APA 的 "姓, 名" 与作者间逗号
    sub_parts = [p.strip().strip('.。') for p in author_str.split(',')]
    sub_parts = [p for p in sub_parts if p]

    if not sub_parts:
        return authors

    # 检测是否为 APA 模式: 偶数位是姓(单词), 奇数位是缩写(如 A. L.)
    is_apa = False
    if len(sub_parts) >= 2:
        # 缩写正则: 单个字母(可带点) + 空格 重复，如 "A.", "A. L.", "J A"
        initials_re = re.compile(r'^[A-Za-z]\.?(?:\s+[A-Za-z]\.?)*$')
        odd_are_initials = all(
            initials_re.match(sub_parts[i])
            for i in range(1, len(sub_parts), 2)
        )
        if odd_are_initials:
            is_apa = True

    if is_apa:
        # APA: [姓, 名, 姓, 名, ...]
        for i in range(0, len(sub_parts), 2):
            fam = sub_parts[i]
            giv = sub_parts[i + 1] if i + 1 < len(sub_parts) else ""
            authors.append({"family": fam, "given": giv.strip('.')})
    else:
        # 非 APA: 每个逗号分隔段都是一个完整作者名
        for part in sub_parts:
            if part:
                authors.append(_parse_single_author(part))

    return authors


def parse_reference(text: str) -> Reference:
    """
    解析单条参考文献文本，提取结构化字段。
    支持中英文多种格式。
    """
    ref = Reference()
    ref.raw = text.strip()
    s = text.strip()

    # 去除序号前缀 (如 [1] 1. ①)
    s = re.sub(r'^\s*[\[\(]?\s*\d+\s*[\]\)]?\s*[.、．]?\s*', '', s)

    # 提取 DOI
    doi_match = re.search(r'(?:doi[:\s]*)?(10\.\d{4,9}/[^\s,;]+)', s, re.I)
    if doi_match:
        ref.doi = doi_match.group(1).rstrip('.')
        s = s[:doi_match.start()] + s[doi_match.end():]

    # 提取 URL
    url_match = re.search(r'https?://[^\s,;]+', s)
    if url_match:
        ref.url = url_match.group(0).rstrip('.')
        s = s[:url_match.start()] + s[url_match.end():]

    # 提取年份 (四位数 19xx/20xx)
    year_match = re.search(r'(19|20)\d{2}', s)
    if year_match:
        ref.year = year_match.group(0)
        year_end = year_match.end()
    else:
        year_end = 0

    # 尝试提取卷期页码: vol(issue):pages 或 vol, no.issue, pp.pages 或 年,卷(期):页码
    # 匹配模式1: 卷(期):页码  如 30(2):145-156
    vip_match = re.search(r'(\d+)\s*\(\s*(\d+)\s*\)\s*[:：]\s*([\d\-–—]+)', s)
    if vip_match:
        ref.volume = vip_match.group(1)
        ref.issue = vip_match.group(2)
        ref.pages = vip_match.group(3).replace('–', '-').replace('—', '-')
    else:
        # 匹配模式2: vol, no. issue, pp. pages
        vip_match2 = re.search(r'vol\.?\s*(\d+)[,\s]+no\.?\s*(\d+)[,\s]+pp\.?\s*([\d\-–—]+)', s, re.I)
        if vip_match2:
            ref.volume = vip_match2.group(1)
            ref.issue = vip_match2.group(2)
            ref.pages = vip_match2.group(3).replace('–', '-').replace('—', '-')
        else:
            # 匹配模式3: 卷:页码  如 123:456-789
            vp_match = re.search(r'(\d+)\s*[:：]\s*([\d\-–—]+)', s)
            if vp_match and not ref.volume:
                ref.volume = vp_match.group(1)
                ref.pages = vp_match.group(2).replace('–', '-').replace('—', '-')
            else:
                # 匹配模式4: pp. pages
                pp_match = re.search(r'pp\.?\s*([\d\-–—]+)', s, re.I)
                if pp_match:
                    ref.pages = pp_match.group(1).replace('–', '-').replace('—', '-')

    # 判断文献类型
    type_match = re.search(r'\[([A-Z]{1,3})(?:/[A-Z]{1,3})?\]', s)
    type_map = {"J": "journal", "M": "book", "C": "conference",
                "D": "thesis", "R": "report", "N": "newspaper",
                "S": "standard", "P": "patent", "EB": "online",
                "DB": "database", "CP": "computer_program"}
    if type_match:
        t = type_match.group(1)
        ref.type = type_map.get(t, "journal")

    # ===== 解析作者、标题、期刊 =====
    has_chinese = bool(re.search(r'[\u4e00-\u9fff]', s))
    has_type_tag = bool(re.search(r'\[[A-Z]{1,3}(?:/[A-Z]{1,3})?\]', s))

    # ---- 优先处理 GB/T 7714 格式（含 [J]/[M] 等类型标签，或中文文献） ----
    if has_type_tag or (has_chinese and not re.search(r'\((19|20)\d{2}\)', s)):
        # 按句号分割（注意：缩略词如 "et al." 中的点会被误切，但通常不影响前几段）
        segments = re.split(r'[.。]\s*', s)
        segments = [seg for seg in segments if seg.strip()]
        if len(segments) >= 3:
            ref.authors = _split_authors(segments[0])
            title_seg = re.sub(r'\s*\[[A-Z/]+\]\s*$', '', segments[1]).strip()
            ref.title = title_seg
            rest = '. '.join(segments[2:]).strip()
            journal_match = re.match(r'^([^,，]+)', rest)
            if journal_match:
                ref.container = journal_match.group(1).strip()
        elif len(segments) == 2:
            ref.authors = _split_authors(segments[0])
            title_seg = re.sub(r'\s*\[[A-Z/]+\]\s*$', '', segments[1]).strip()
            ref.title = title_seg
        else:
            ref.title = s
    else:
        # ---- 英文格式解析 ----
        # 1) APA: Authors (Year). Title. Journal, vol(issue), pages.
        paren_year = re.search(r'\((19|20)\d{2}\)', s)
        if paren_year:
            before = s[:paren_year.start()].strip().rstrip(',').strip()
            after = s[paren_year.end():].strip().lstrip('.').strip()
            ref.authors = _split_authors(before)
            # 标题：第一个 ". " 之前的内容
            title_end = -1
            for m in re.finditer(r'\.\s', after):
                # 排除 "et al." "vol." "no." "pp." 等缩略词
                seg = after[m.start():]
                if not re.match(r'\.\s+(et|vol|no|pp|al|Inc|Ltd|Jr|Sr)\b', seg, re.I):
                    title_end = m.start()
                    break
            if title_end == -1:
                title_end = after.rfind('.')
            if title_end > 0:
                ref.title = after[:title_end].strip()
                rest = after[title_end+1:].strip()
                journal_match = re.match(r'^([^,]+)', rest)
                if journal_match:
                    ref.container = journal_match.group(1).strip()
            else:
                ref.title = after
        else:
            # 2) IEEE: Authors, "Title," Journal, vol. X, no. Y, pp. ZZ, Year.
            quote_match = re.search(r'"([^"]+)"', s)
            if quote_match:
                before = s[:quote_match.start()].strip().rstrip(',').strip()
                ref.authors = _split_authors(before)
                ref.title = quote_match.group(1).strip().rstrip(',')
                rest = s[quote_match.end():].strip().lstrip(',').strip()
                journal_match = re.match(r'^([^,]+)', rest)
                if journal_match:
                    ref.container = journal_match.group(1).strip()
            else:
                # 3) 兜底：按句号+空格分割
                segments = re.split(r'(?<=[A-Za-z\u4e00-\u9fff])\.\s+', s)
                segments = [seg for seg in segments if seg.strip()]
                if len(segments) >= 2:
                    ref.authors = _split_authors(segments[0])
                    # 标题取第二段（通常是题名）
                    ref.title = segments[1].strip()
                    if len(segments) >= 3:
                        rest = '. '.join(segments[2:]).strip()
                        journal_match = re.match(r'^([^,，]+)', rest)
                        if journal_match:
                            ref.container = journal_match.group(1).strip()
                else:
                    ref.title = s

    # 清理标题中的类型标签和尾部标点
    ref.title = re.sub(r'\s*\[[A-Z/]+\]\s*$', '', ref.title).strip().rstrip('.。')

    return ref


# ============================================================
# 四、引用格式格式化器
# ============================================================

def _format_authors_apa(authors: List[Dict]) -> str:
    """APA 格式作者: Last, F. M., & Last, F. M."""
    if not authors:
        return ""
    formatted = []
    for a in authors:
        fam = a.get("family", "").strip()
        giv = a.get("given", "").strip()
        if fam and giv:
            # 中文名不缩写
            if re.search(r'[\u4e00-\u9fff]', fam + giv):
                formatted.append(f"{fam} {giv}".strip())
            else:
                # 缩写名
                initials = []
                for part in giv.split():
                    if part:
                        initials.append(part[0].upper() + '.')
                formatted.append(f"{fam}, {''.join(initials)}")
        elif fam:
            formatted.append(fam)
    if len(formatted) == 1:
        return formatted[0]
    elif len(formatted) == 2:
        return f"{formatted[0]}, & {formatted[1]}"
    elif len(formatted) <= 20:
        return f"{', '.join(formatted[:-1])}, & {formatted[-1]}"
    else:
        return f"{', '.join(formatted[:19])}, ... {formatted[-1]}"


def _format_authors_ieee(authors: List[Dict]) -> str:
    """IEEE 格式作者: F. M. Last and F. M. Last"""
    if not authors:
        return ""
    formatted = []
    for a in authors:
        fam = a.get("family", "").strip()
        giv = a.get("given", "").strip()
        if fam and giv:
            if re.search(r'[\u4e00-\u9fff]', fam + giv):
                formatted.append(f"{fam} {giv}".strip())
            else:
                initials = []
                for part in giv.split():
                    if part:
                        initials.append(part[0].upper() + '.')
                formatted.append(f"{''.join(initials)} {fam}")
        elif fam:
            formatted.append(fam)
    if len(formatted) == 1:
        return formatted[0]
    elif len(formatted) == 2:
        return f"{formatted[0]} and {formatted[1]}"
    else:
        return f"{', '.join(formatted[:-1])}, and {formatted[-1]}"


def _format_authors_nature(authors: List[Dict]) -> str:
    """Nature 格式作者: Last, F. M. et al. (多于1个时用 et al.)"""
    if not authors:
        return ""
    a = authors[0]
    fam = a.get("family", "").strip()
    giv = a.get("given", "").strip()
    if fam and giv:
        if re.search(r'[\u4e00-\u9fff]', fam + giv):
            first = f"{fam} {giv}".strip()
        else:
            initials = []
            for part in giv.split():
                if part:
                    initials.append(part[0].upper() + '.')
            first = f"{fam}, {''.join(initials)}"
    else:
        first = fam
    if len(authors) == 1:
        return first
    return f"{first} et al"


def _format_authors_vancouver(authors: List[Dict]) -> str:
    """Vancouver 格式作者: Last FM, Last FM (名缩写无点)"""
    if not authors:
        return ""
    formatted = []
    for a in authors:
        fam = a.get("family", "").strip()
        giv = a.get("given", "").strip()
        if fam and giv:
            if re.search(r'[\u4e00-\u9fff]', fam + giv):
                formatted.append(f"{fam} {giv}".strip())
            else:
                initials = ''.join(p[0].upper() for p in giv.split() if p)
                formatted.append(f"{fam} {initials}")
        elif fam:
            formatted.append(fam)
    if len(formatted) <= 6:
        return ', '.join(formatted)
    return ', '.join(formatted[:6]) + ', et al'


def _format_authors_gbt(authors: List[Dict]) -> str:
    """GB/T 7714 格式作者: 姓 名, 姓 名, 等."""
    if not authors:
        return ""
    formatted = []
    for a in authors:
        fam = a.get("family", "").strip()
        giv = a.get("given", "").strip()
        if re.search(r'[\u4e00-\u9fff]', fam + giv):
            formatted.append(f"{fam} {giv}".strip())
        else:
            # 英文作者：姓全拼，名缩写
            if fam and giv:
                initials = ''.join(p[0].upper() for p in giv.split() if p)
                formatted.append(f"{fam} {initials}")
            else:
                formatted.append(fam)
    if len(formatted) <= 3:
        return ', '.join(formatted)
    return ', '.join(formatted[:3]) + ', 等'


def format_reference(ref: Reference, style: str) -> str:
    """根据指定格式格式化参考文献"""
    if not ref.title:
        return ref.raw

    style = style.lower()

    # 作者格式化
    if style == "apa":
        authors_str = _format_authors_apa(ref.authors)
    elif style == "ieee":
        authors_str = _format_authors_ieee(ref.authors)
    elif style in ("nature", "science", "cell", "pnas", "jbc", "plos", "oxford", "aip", "aps", "osa"):
        authors_str = _format_authors_nature(ref.authors)
    elif style in ("vancouver",):
        authors_str = _format_authors_vancouver(ref.authors)
    elif style in ("gbt7714",):
        authors_str = _format_authors_gbt(ref.authors)
    elif style == "acs":
        authors_str = _format_authors_vancouver(ref.authors)
    elif style == "mla":
        # MLA: Last, First. et al.
        if ref.authors:
            a = ref.authors[0]
            giv = a.get('given', '').strip()
            if giv and not re.search(r'[\u4e00-\u9fff]', giv) and not giv.endswith('.'):
                giv += '.'
            authors_str = f"{a.get('family','')}, {giv}".strip()
            if len(ref.authors) > 1:
                authors_str += ", et al"
        else:
            authors_str = ""
    elif style == "chicago":
        if ref.authors:
            a = ref.authors[0]
            giv = a.get('given', '').strip()
            if giv and not re.search(r'[\u4e00-\u9fff]', giv) and not giv.endswith('.'):
                giv += '.'
            authors_str = f"{a.get('family','')}, {giv}".strip()
            if len(ref.authors) == 2:
                giv2 = ref.authors[1].get('given', '').strip()
                if giv2 and not re.search(r'[\u4e00-\u9fff]', giv2) and not giv2.endswith('.'):
                    giv2 += '.'
                authors_str += f", and {ref.authors[1].get('family','')} {giv2}".strip()
            elif len(ref.authors) > 2:
                authors_str += ", et al"
        else:
            authors_str = ""
    elif style == "acm":
        authors_str = _format_authors_ieee(ref.authors)
    elif style == "jmlr":
        authors_str = _format_authors_ieee(ref.authors)
    elif style == "jacs":
        authors_str = _format_authors_vancouver(ref.authors)
    elif style == "wiley-vch":
        authors_str = _format_authors_vancouver(ref.authors)
    elif style == "elsevier":
        authors_str = _format_authors_vancouver(ref.authors)
    else:
        authors_str = _format_authors_apa(ref.authors)

    # 统一去除作者串尾部句号，由各格式自行添加
    authors_str = authors_str.rstrip('. ')

    year_str = f"({ref.year})" if ref.year else ""
    vol_issue = ""
    if ref.volume and ref.issue:
        vol_issue = f"{ref.volume}({ref.issue})"
    elif ref.volume:
        vol_issue = ref.volume
    pages_str = ref.pages if ref.pages else ""

    # ============ 按格式输出 ============
    if style == "apa":
        # Author, A. A. (Year). Title. Journal, volume(issue), pages. DOI
        parts = []
        if authors_str:
            parts.append(f"{authors_str}. {year_str}.".strip())
        else:
            parts.append(f"{year_str}.")
        parts.append(f"{ref.title}.")
        if ref.container:
            j = f"{ref.container}"
            if vol_issue:
                j += f", {vol_issue}"
            if pages_str:
                j += f", {pages_str}"
            parts.append(f"{j}.")
        else:
            if vol_issue:
                parts.append(f"{vol_issue}.")
        if ref.doi:
            parts.append(f"https://doi.org/{ref.doi}")
        return ' '.join(parts).strip()

    elif style == "ieee":
        # A. A. Author, "Title," Journal, vol. X, no. Y, pp. ZZ, Month Year.
        parts = []
        if authors_str:
            parts.append(f"{authors_str},")
        parts.append(f'"{ref.title},"')
        if ref.container:
            parts.append(f"{ref.container},")
        if ref.volume:
            parts.append(f"vol. {ref.volume},")
        if ref.issue:
            parts.append(f"no. {ref.issue},")
        if pages_str:
            parts.append(f"pp. {pages_str},")
        if ref.year:
            parts.append(f"{ref.year}.")
        return ' '.join(parts).strip()

    elif style == "gbt7714":
        # 作者. 题名[J]. 刊名, 年, 卷(期): 页码.
        type_tag = {"journal": "[J]", "book": "[M]", "conference": "[C]",
                    "thesis": "[D]", "report": "[R]", "newspaper": "[N]"}.get(ref.type, "[J]")
        parts = []
        if authors_str:
            parts.append(f"{authors_str}.")
        parts.append(f"{ref.title}{type_tag}.")
        if ref.container:
            j = f"{ref.container}"
            if ref.year:
                j += f", {ref.year}"
            if ref.volume:
                j += f", {ref.volume}"
                if ref.issue:
                    j += f"({ref.issue})"
            if pages_str:
                j += f": {pages_str}"
            parts.append(f"{j}.")
        return ' '.join(parts).strip()

    elif style in ("nature", "science", "cell", "pnas", "jbc", "plos", "oxford"):
        # Author, F. M. et al. Title. Journal volume, pages (Year).
        parts = []
        if authors_str:
            parts.append(f"{authors_str}.")
        parts.append(f"{ref.title}.")
        j = ""
        if ref.container:
            j = f"{ref.container}"
        if ref.volume:
            j += f" {ref.volume}"
        if pages_str:
            j += f", {pages_str}"
        if ref.year:
            j += f" ({ref.year})"
        parts.append(f"{j}.")
        if ref.doi:
            parts.append(f"https://doi.org/{ref.doi}")
        return ' '.join(parts).strip()

    elif style == "vancouver":
        # Author FM. Title. Journal. Year;volume(issue):pages.
        parts = []
        if authors_str:
            parts.append(f"{authors_str}.")
        parts.append(f"{ref.title}.")
        if ref.container:
            j = f"{ref.container}."
            if ref.year:
                j += f" {ref.year}"
            if vol_issue:
                j += f";{vol_issue}"
            if pages_str:
                j += f":{pages_str}"
            parts.append(f"{j}.")
        if ref.doi:
            parts.append(f"doi:{ref.doi}.")
        return ' '.join(parts).strip()

    elif style == "mla":
        # Author. "Title of Article." Title of Journal, vol. X, no. Y, Year, pp. ZZ.
        parts = []
        if authors_str:
            parts.append(f"{authors_str}.")
        parts.append(f'"{ref.title}."')
        if ref.container:
            parts.append(f"{ref.container},")
        if ref.volume:
            parts.append(f"vol. {ref.volume},")
        if ref.issue:
            parts.append(f"no. {ref.issue},")
        if ref.year:
            parts.append(f"{ref.year},")
        if pages_str:
            parts.append(f"pp. {pages_str}.")
        return ' '.join(parts).strip()

    elif style == "chicago":
        # Author. "Title." Journal volume, no. issue (Year): pages.
        parts = []
        if authors_str:
            parts.append(f"{authors_str}.")
        parts.append(f'"{ref.title}."')
        if ref.container:
            j = f"{ref.container}"
            if ref.volume:
                j += f" {ref.volume}"
            if ref.issue:
                j += f", no. {ref.issue}"
            if ref.year:
                j += f" ({ref.year})"
            if pages_str:
                j += f": {pages_str}"
            parts.append(f"{j}.")
        return ' '.join(parts).strip()

    elif style in ("acs", "jacs"):
        # Author FM. Title. Journal Abbrev. Year, volume, pages.
        parts = []
        if authors_str:
            parts.append(f"{authors_str}.")
        parts.append(f"{ref.title}.")
        if ref.container:
            j = f"{ref.container}."
            if ref.year:
                j += f" {ref.year}"
            if ref.volume:
                j += f", {ref.volume}"
            if pages_str:
                j += f", {pages_str}"
            parts.append(f"{j}.")
        return ' '.join(parts).strip()

    elif style in ("wiley-vch", "elsevier", "aip", "aps", "osa"):
        # Author FM, Title. Journal Year, volume, pages.
        parts = []
        if authors_str:
            parts.append(f"{authors_str}.")
        parts.append(f"{ref.title}.")
        if ref.container:
            j = f"{ref.container}"
            if ref.year:
                j += f" {ref.year}"
            if ref.volume:
                j += f", {ref.volume}"
            if pages_str:
                j += f", {pages_str}"
            parts.append(f"{j}.")
        return ' '.join(parts).strip()

    elif style in ("acm", "jmlr"):
        # ACM: Author. Year. Title. Journal, volume(issue).
        parts = []
        if authors_str:
            parts.append(f"{authors_str}.")
        if ref.year:
            parts.append(f"{ref.year}.")
        parts.append(f"{ref.title}.")
        if ref.container:
            j = f"{ref.container}"
            if ref.volume:
                j += f", {ref.volume}"
                if ref.issue:
                    j += f"({ref.issue})"
            parts.append(f"{j}.")
        return ' '.join(parts).strip()

    else:
        # 默认 APA
        parts = []
        if authors_str:
            parts.append(f"{authors_str} {year_str}.".strip())
        parts.append(f"{ref.title}.")
        if ref.container:
            j = f"{ref.container}"
            if vol_issue:
                j += f", {vol_issue}"
            if pages_str:
                j += f", {pages_str}"
            parts.append(f"{j}.")
        return ' '.join(parts).strip()


# ============================================================
# 五、Crossref API 集成（精准格式化）
# ============================================================

def crossref_search(title: str, authors: str = "") -> Optional[str]:
    """
    通过 Crossref API 搜索文献，返回 DOI（若找到）。
    """
    if not HAS_REQUESTS:
        return None
    try:
        params = {"query.title": title, "rows": 3}
        if authors:
            params["query.author"] = authors
        resp = requests.get("https://api.crossref.org/works", params=params, timeout=10)
        data = resp.json()
        items = data.get("message", {}).get("items", [])
        if items:
            # 取第一个结果的 DOI
            return items[0].get("DOI")
    except Exception:
        pass
    return None


def crossref_get_citation(doi: str, style: str = "apa") -> Optional[str]:
    """
    通过 Crossref 内容协商接口，获取指定格式的引文。
    Crossref 支持上千种 CSL 样式。
    """
    if not HAS_REQUESTS:
        return None
    try:
        # 常见样式到 CSL style ID 的映射
        style_map = {
            "apa": "apa",
            "ieee": "ieee",
            "chicago": "chicago-author-date",
            "mla": "modern-language-association",
            "vancouver": "vancouver",
            "nature": "nature",
            "science": "science",
            "cell": "cell",
            "pnas": "pnas",
            "acs": "american-chemical-society",
            "elsevier": "elsevier-without-titles",
            "oxford": "oxford-university-press",
            "acm": "association-for-computing-machinery",
        }
        csl_style = style_map.get(style, "apa")
        url = f"https://api.crossref.org/works/{doi}/transform"
        headers = {"Accept": "text/x-bibliography", "style": csl_style}
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200 and resp.text.strip():
            return resp.text.strip()
    except Exception:
        pass
    return None


def crossref_format_reference(ref: Reference, style: str) -> Tuple[Optional[str], bool]:
    """
    尝试使用 Crossref 精准格式化。
    返回 (formatted_text, success)。
    """
    # 优先使用已有的 DOI
    doi = ref.doi
    if not doi:
        # 通过标题和作者搜索
        first_author = ""
        if ref.authors:
            first_author = ref.authors[0].get("family", "")
        doi = crossref_search(ref.title, first_author)
    if doi:
        ref.doi = doi  # 回写 DOI
        citation = crossref_get_citation(doi, style)
        if citation:
            return citation, True
    return None, False


# ============================================================
# 六、主处理逻辑
# ============================================================

def process_references(journal_name: str, references_text: str,
                       style: str = "", use_crossref: bool = True,
                       progress_callback=None) -> Tuple[str, str]:
    """
    主处理函数。
    返回 (formatted_references, log_info)
    """
    logs = []

    # 1. 确定引用格式
    if not style:
        style = lookup_journal_style(journal_name)
        if style:
            logs.append(f"✓ 本地数据库匹配: {journal_name} -> {STYLE_DESCRIPTIONS.get(style, style)}")
        else:
            style, info = search_journal_style_online(journal_name)
            logs.append(info)
            if not style:
                style = "apa"  # 默认 APA
                logs.append(f"⚠ 未识别到格式，默认使用 {STYLE_DESCRIPTIONS[style]}")
            else:
                logs.append(f"✓ 推断格式: {STYLE_DESCRIPTIONS.get(style, style)}")
    else:
        logs.append(f"使用指定格式: {STYLE_DESCRIPTIONS.get(style, style)}")

    # 2. 拆分参考文献
    raw_refs = [r.strip() for r in references_text.strip().split('\n') if r.strip()]
    if not raw_refs:
        return "", "未输入参考文献。"

    logs.append(f"\n共检测到 {len(raw_refs)} 条参考文献。")

    # 3. 逐条格式化
    formatted = []
    for i, raw in enumerate(raw_refs, 1):
        if progress_callback:
            progress_callback(i, len(raw_refs))
        try:
            ref = parse_reference(raw)
            result_text = None

            if use_crossref and HAS_REQUESTS:
                result_text, ok = crossref_format_reference(ref, style)
                if ok and result_text:
                    formatted.append(f"[{i}] {result_text}")
                    logs.append(f"  [{i}] ✓ Crossref 精准格式化成功 (DOI: {ref.doi})")
                    continue
                elif ref.doi:
                    logs.append(f"  [{i}] 找到 DOI: {ref.doi}，但格式化失败，使用本地格式化")
                else:
                    logs.append(f"  [{i}] Crossref 未找到匹配文献，使用本地格式化")

            # 本地格式化
            result_text = format_reference(ref, style)
            formatted.append(f"[{i}] {result_text}")
        except Exception as e:
            formatted.append(f"[{i}] {raw}")
            logs.append(f"  [{i}] ✗ 解析失败: {str(e)}")

    return '\n'.join(formatted), '\n'.join(logs)


# ============================================================
# 七、GUI 界面
# ============================================================

class ReferenceFormatterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("期刊参考文献格式自动格式化工具")
        self.root.geometry("1100x780")
        self.root.minsize(900, 650)

        self._build_ui()

    def _build_ui(self):
        # ===== 顶部：期刊名称输入 =====
        top_frame = ttk.LabelFrame(self.root, text="期刊信息", padding=10)
        top_frame.pack(fill=tk.X, padx=10, pady=8)

        ttk.Label(top_frame, text="期刊名称:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.journal_var = tk.StringVar()
        self.journal_entry = ttk.Entry(top_frame, textvariable=self.journal_var, width=50)
        self.journal_entry.grid(row=0, column=1, sticky=tk.W, padx=5)

        self.search_btn = ttk.Button(top_frame, text="检索引用格式", command=self.on_search_style)
        self.search_btn.grid(row=0, column=2, padx=5)

        ttk.Label(top_frame, text="引用格式:").grid(row=0, column=3, sticky=tk.W, padx=(15, 5))
        self.style_var = tk.StringVar(value="apa")
        style_options = sorted(STYLE_DESCRIPTIONS.keys())
        self.style_combo = ttk.Combobox(top_frame, textvariable=self.style_var,
                                        values=style_options, width=20, state="readonly")
        self.style_combo.grid(row=0, column=4, sticky=tk.W, padx=5)

        self.style_desc_label = ttk.Label(top_frame, text="", foreground="gray")
        self.style_desc_label.grid(row=0, column=5, sticky=tk.W, padx=10)

        # 格式变化时更新描述
        self.style_combo.bind("<<ComboboxSelected>>", self._on_style_change)
        self._update_style_desc()

        # ===== 中间：输入与输出 =====
        mid_frame = ttk.Frame(self.root)
        mid_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # 输入区
        input_frame = ttk.LabelFrame(mid_frame, text="待格式化参考文献（每行一条）", padding=5)
        input_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

        self.input_text = scrolledtext.ScrolledText(input_frame, wrap=tk.WORD, font=("Consolas", 10))
        self.input_text.pack(fill=tk.BOTH, expand=True)

        # 输出区
        output_frame = ttk.LabelFrame(mid_frame, text="格式化结果", padding=5)
        output_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 0))

        self.output_text = scrolledtext.ScrolledText(output_frame, wrap=tk.WORD, font=("Consolas", 10))
        self.output_text.pack(fill=tk.BOTH, expand=True)

        # ===== 选项区 =====
        opt_frame = ttk.Frame(self.root)
        opt_frame.pack(fill=tk.X, padx=10, pady=5)

        self.use_crossref_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(opt_frame, text="启用 Crossref 精准格式化（联网查询 DOI）",
                        variable=self.use_crossref_var).pack(side=tk.LEFT)

        if not HAS_REQUESTS:
            ttk.Label(opt_frame, text="(未安装 requests，网络功能不可用)",
                      foreground="red").pack(side=tk.LEFT, padx=10)

        # ===== 操作按钮 =====
        btn_frame = ttk.Frame(self.root)
        btn_frame.pack(fill=tk.X, padx=10, pady=8)

        self.format_btn = ttk.Button(btn_frame, text="开始格式化", command=self.on_format)
        self.format_btn.pack(side=tk.LEFT, padx=5)

        ttk.Button(btn_frame, text="复制结果", command=self.on_copy).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="清空全部", command=self.on_clear).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="加载示例", command=self.on_load_example).pack(side=tk.LEFT, padx=5)

        # ===== 底部：日志区 =====
        log_frame = ttk.LabelFrame(self.root, text="处理日志", padding=5)
        log_frame.pack(fill=tk.BOTH, padx=10, pady=(0, 8))

        self.log_text = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, height=8,
                                                  font=("Consolas", 9), foreground="darkgreen")
        self.log_text.pack(fill=tk.BOTH, expand=True)

        # 进度条
        self.progress = ttk.Progressbar(self.root, mode="determinate")
        self.progress.pack(fill=tk.X, padx=10, pady=(0, 5))

    def _update_style_desc(self):
        style = self.style_var.get()
        desc = STYLE_DESCRIPTIONS.get(style, "")
        self.style_desc_label.config(text=desc)

    def _on_style_change(self, event=None):
        self._update_style_desc()

    def _log(self, msg: str):
        self.log_text.insert(tk.END, msg + '\n')
        self.log_text.see(tk.END)
        self.root.update_idletasks()

    def on_search_style(self):
        """检索期刊引用格式"""
        journal = self.journal_var.get().strip()
        if not journal:
            messagebox.showwarning("提示", "请输入期刊名称")
            return

        self._log(f"正在检索期刊「{journal}」的引用格式...")
        self.root.config(cursor="watch")
        self.root.update_idletasks()

        # 先查本地库
        style = lookup_journal_style(journal)
        if style:
            self.style_var.set(style)
            self._update_style_desc()
            self._log(f"✓ 本地数据库匹配: {journal} -> {STYLE_DESCRIPTIONS.get(style, style)}")
        else:
            # 网络搜索
            style, info = search_journal_style_online(journal)
            self._log(info)
            if style:
                self.style_var.set(style)
                self._update_style_desc()

        self.root.config(cursor="")

    def on_format(self):
        """执行格式化"""
        journal = self.journal_var.get().strip()
        refs = self.input_text.get("1.0", tk.END).strip()
        if not refs:
            messagebox.showwarning("提示", "请输入待格式化的参考文献")
            return

        style = self.style_var.get()
        use_crossref = self.use_crossref_var.get()

        self.log_text.delete("1.0", tk.END)
        self._log(f"开始处理... 期刊: {journal or '(未指定)'}, 格式: {STYLE_DESCRIPTIONS.get(style, style)}")

        self.format_btn.config(state=tk.DISABLED)
        self.root.config(cursor="watch")
        self.root.update_idletasks()

        def progress_cb(current, total):
            self.progress["value"] = (current / total) * 100
            self.root.update_idletasks()

        try:
            result, log = process_references(journal, refs, style, use_crossref, progress_cb)
            self.output_text.delete("1.0", tk.END)
            self.output_text.insert("1.0", result)
            self._log(log)
            self._log("\n✓ 格式化完成！")
        except Exception as e:
            self._log(f"✗ 处理出错: {str(e)}")
            messagebox.showerror("错误", f"处理过程中出错:\n{str(e)}")
        finally:
            self.progress["value"] = 0
            self.format_btn.config(state=tk.NORMAL)
            self.root.config(cursor="")

    def on_copy(self):
        text = self.output_text.get("1.0", tk.END).strip()
        if text:
            self.root.clipboard_clear()
            self.root.clipboard_append(text)
            messagebox.showinfo("提示", "已复制到剪贴板")
        else:
            messagebox.showwarning("提示", "结果为空")

    def on_clear(self):
        if messagebox.askyesno("确认", "确定要清空所有内容吗？"):
            self.journal_var.set("")
            self.input_text.delete("1.0", tk.END)
            self.output_text.delete("1.0", tk.END)
            self.log_text.delete("1.0", tk.END)

    def on_load_example(self):
        """加载示例数据"""
        self.journal_var.set("Nature")
        examples = """Smith J A, Johnson L M, Williams R K. Deep learning for image recognition: a comprehensive review[J]. Nature Machine Intelligence, 2023, 5(3): 234-245.
Zhang Wei, Li Ming, Wang Fang. 基于Transformer的自然语言处理研究进展[J]. 计算机学报, 2024, 47(2): 215-230.
Brown, A. L., & Davis, K. M. (2022). Climate change impacts on biodiversity. Science, 376(6596), 1012-1017. https://doi.org/10.1126/science.abn9876
"""
        self.input_text.delete("1.0", tk.END)
        self.input_text.insert("1.0", examples)
        self._log("已加载示例数据，可点击「开始格式化」测试。")


# ============================================================
# 八、程序入口
# ============================================================

def main():
    root = tk.Tk()
    app = ReferenceFormatterApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
