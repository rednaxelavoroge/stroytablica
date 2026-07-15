#!/usr/bin/env python3
"""Generate multi-language landings for stroytablica.ru"""
from __future__ import annotations
from pathlib import Path
import json
import re

ROOT = Path(__file__).resolve().parents[1]

LANGS = [
    ("ru", "/", "RU", "Русский"),
    ("uk", "/uk/", "UK", "Українська"),
    ("be", "/be/", "BE", "Беларуская"),
    ("kk", "/kk/", "KK", "Қазақша"),
    ("ka", "/ka/", "KA", "ქართული"),
    ("hy", "/hy/", "HY", "Հայերեն"),
    ("tr", "/tr/", "TR", "Türkçe"),
]

BRAND = {
    "ru": "СтройТаблица",
    "uk": "БудТаблиця",
    "be": "БудаўнТабліца",
    "kk": "ҚұрылысКесте",
    "ka": "მშენცხრილი",
    "hy": "ՇինԱղյուսակ",
    "tr": "İnşaatTablo",
}

CSS = r"""
:root{--ink:#101623;--mut:#5b6472;--amber:#f59e0b;--amber-d:#d97706;--bg:#f6f7f9;--card:#fff;--line:#e6e8ec;--tg:#2aabee;--wa:#25d366;--ok:#16a34a;--no:#dc2626}
*{margin:0;padding:0;box-sizing:border-box}
html{scroll-behavior:smooth}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,'Noto Sans',Arial,sans-serif;color:var(--ink);background:var(--bg);line-height:1.55}
.wrap{max-width:1060px;margin:0 auto;padding:0 16px}
nav{position:sticky;top:0;background:rgba(255,255,255,.95);backdrop-filter:blur(8px);border-bottom:1px solid var(--line);z-index:20}
nav .wrap{display:flex;align-items:center;justify-content:space-between;gap:10px;min-height:56px;height:auto;padding:10px 0}
.logo{font-weight:800;font-size:1.05rem;text-decoration:none;color:var(--ink);white-space:nowrap;flex-shrink:0;max-width:42vw;overflow:hidden;text-overflow:ellipsis}
.nav-right{display:flex;align-items:center;gap:8px;flex-shrink:0;margin-left:auto}
nav .links{display:flex;gap:12px;align-items:center;flex-wrap:nowrap}
nav .links a{color:var(--mut);text-decoration:none;font-size:.88rem;white-space:nowrap}
.lang-dd{position:relative}
.lang-dd>summary{list-style:none;cursor:pointer;font-size:.78rem;font-weight:700;padding:6px 10px;border-radius:8px;border:1px solid var(--line);color:var(--ink);background:#fff;user-select:none;white-space:nowrap}
.lang-dd>summary::-webkit-details-marker{display:none}
.lang-dd>summary::after{content:' ▾';opacity:.55;font-size:.7em}
.lang-dd[open]>summary{background:var(--ink);color:#fff;border-color:var(--ink)}
.lang-menu{position:absolute;right:0;top:calc(100% + 6px);min-width:168px;background:#fff;border:1px solid var(--line);border-radius:10px;box-shadow:0 12px 32px rgba(0,0,0,.12);padding:6px;z-index:30}
.lang-menu a{display:flex;justify-content:space-between;gap:12px;padding:8px 10px;border-radius:7px;color:var(--ink);text-decoration:none;font-size:.86rem}
.lang-menu a:hover{background:#f3f4f6}
.lang-menu a.active{background:#101623;color:#fff}
.lang-menu a span{color:var(--mut);font-size:.75rem;font-weight:700}
.lang-menu a.active span{color:#c6cede}
.btn{display:inline-block;background:var(--amber);color:#fff;font-weight:700;padding:13px 28px;border-radius:10px;text-decoration:none;transition:.15s;white-space:nowrap}
.btn:hover{background:var(--amber-d)}
.btn.sm{padding:8px 14px;font-size:.88rem}
.btn.ghost{background:transparent;color:var(--ink);border:1.5px solid var(--line)}
.hero{background:linear-gradient(160deg,#0e1726 0%,#1a2740 70%,#233252 100%);color:#fff;padding:68px 0 80px}
.hero .wrap{display:grid;grid-template-columns:1.1fr .9fr;gap:48px;align-items:center}
.hero h1{font-size:2.2rem;line-height:1.22;margin-bottom:18px;word-wrap:break-word}
.hero h1 em{color:var(--amber);font-style:normal}
.hero p.sub{color:#c6cede;font-size:1.05rem;margin-bottom:26px}
.hero .note{color:#8d97ab;font-size:.9rem;margin-top:12px}
.chat{background:#fff;border-radius:16px;padding:18px;box-shadow:0 18px 50px rgba(0,0,0,.35);max-width:430px;margin-left:auto}
.chat .head{display:flex;align-items:center;gap:10px;border-bottom:1px solid var(--line);padding-bottom:10px;margin-bottom:12px}
.chat .ava{width:34px;height:34px;border-radius:50%;background:var(--amber);display:flex;align-items:center;justify-content:center;font-size:1.05rem;flex-shrink:0}
.chat .head b{font-size:.95rem;color:var(--ink)}
.chat .head span{display:block;font-size:.75rem;color:var(--tg)}
.msg{max-width:88%;padding:9px 13px;border-radius:12px;font-size:.83rem;margin-bottom:9px;color:var(--ink);white-space:pre-line}
.msg.user{background:#e3f1fd;margin-left:auto;border-bottom-right-radius:4px}
.msg.bot{background:#f2f3f6;border-bottom-left-radius:4px}
.video-frame{position:relative;padding-bottom:56.25%;height:0;overflow:hidden;border-radius:16px;box-shadow:0 18px 50px rgba(0,0,0,.18);border:1px solid var(--line);background:#000}
.video-frame iframe{position:absolute;top:0;left:0;width:100%;height:100%;border:0}
section{padding:60px 0}
section h2{font-size:1.8rem;margin-bottom:8px}
section p.lead{color:var(--mut);margin-bottom:32px;max-width:720px;font-size:1.02rem}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:18px}
.card{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:24px}
.card .ico{font-size:1.6rem;margin-bottom:10px}
.card h3{font-size:1.05rem;margin-bottom:8px}
.card p{color:var(--mut);font-size:.93rem}
.steps{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:18px;counter-reset:st}
.step{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:26px 24px 22px;position:relative}
.step::before{counter-increment:st;content:counter(st);position:absolute;top:-14px;left:20px;background:var(--amber);color:#fff;font-weight:800;width:30px;height:30px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:.95rem}
.step h3{margin:6px 0;font-size:1rem}
.step p{color:var(--mut);font-size:.92rem}
.chips{display:flex;flex-wrap:wrap;gap:10px;margin-top:6px}
.chip{background:var(--card);border:1px solid var(--line);border-radius:22px;padding:9px 16px;font-size:.88rem;color:var(--ink)}
.chip::before{content:'«'}
.chip::after{content:'»'}
.tblwrap{overflow-x:auto;border:1px solid var(--line);border-radius:14px;background:#fff}
table{border-collapse:collapse;width:100%;min-width:640px;font-size:.92rem}
th,td{padding:13px 16px;text-align:left;border-bottom:1px solid var(--line)}
th{background:#fafbfc;font-size:.85rem;color:var(--mut)}
td:first-child{font-weight:600}
thead th:nth-child(2){color:var(--amber-d);font-weight:800}
.ok{color:var(--ok);font-weight:700}
.no{color:var(--no);font-weight:700}
.plans{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:18px;align-items:stretch}
.plan{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:26px;display:flex;flex-direction:column}
.plan.hot{border:2px solid var(--amber);position:relative}
.plan.hot::before{content:attr(data-badge);position:absolute;top:-12px;left:50%;transform:translateX(-50%);background:var(--amber);color:#fff;font-size:.72rem;font-weight:700;padding:3px 12px;border-radius:20px;white-space:nowrap}
.plan h3{font-size:1.05rem}
.plan .price{font-size:1.9rem;font-weight:800;margin:10px 0 2px}
.plan .price span{font-size:.85rem;font-weight:400;color:var(--mut)}
.plan ul{list-style:none;margin:16px 0 22px;flex:1}
.plan li{font-size:.9rem;color:var(--mut);padding:5px 0 5px 24px;position:relative}
.plan li::before{content:'✓';position:absolute;left:2px;color:var(--amber);font-weight:700}
.plan li.soon{font-style:italic}
.plan li.soon::before{content:'•';color:var(--mut);font-weight:700}
details:not(.lang-dd){background:var(--card);border:1px solid var(--line);border-radius:12px;padding:16px 20px;margin-bottom:10px}
details:not(.lang-dd) summary{font-weight:600;cursor:pointer}
details:not(.lang-dd) p{color:var(--mut);margin-top:10px;font-size:.95rem}
.implant{margin-top:26px;background:linear-gradient(160deg,#0e1726,#233252);border-radius:14px;padding:28px 30px;color:#fff;display:flex;justify-content:space-between;align-items:center;gap:20px;flex-wrap:wrap}
.implant h3{margin-bottom:6px}
.implant p{color:#c6cede;font-size:.95rem;max-width:640px}
.cta-end{background:linear-gradient(160deg,#0e1726,#233252);color:#fff;text-align:center;border-radius:18px;padding:52px 28px;margin:16px 0 56px}
.cta-end h2{margin-bottom:10px}
.cta-end p{color:#c6cede;margin-bottom:24px}
footer{border-top:1px solid var(--line);padding:26px 0;color:var(--mut);font-size:.9rem}
footer .wrap{display:flex;justify-content:space-between;flex-wrap:wrap;gap:10px}
footer a{color:var(--mut)}
@media(max-width:1100px){nav .links>.nav-hide{display:none}}
@media(max-width:820px){.hero .wrap{grid-template-columns:1fr}.hero h1{font-size:1.7rem}.chat{margin:0 auto}.logo{font-size:.95rem;max-width:48vw}}
""".strip()

OWNER = "https://t.me/StableCent"
WA = "https://wa.me/37281952565"
BOT = "https://t.me/stroytablica_bot"


def hreflangs() -> str:
    lines = [f'<link rel="alternate" hreflang="{c}" href="https://stroytablica.ru{p if p != "/" else "/"}">' for c, p, _, _ in LANGS]
    lines.append('<link rel="alternate" hreflang="x-default" href="https://stroytablica.ru/">')
    return "\n".join(lines)


def lang_dropdown(active: str) -> str:
    label = next(code for c, _, code, _ in LANGS if c == active)
    items = []
    for c, path, code, name in LANGS:
        cls = ' class="active"' if c == active else ""
        items.append(f'<a href="{path}" hreflang="{c}"{cls}>{name}<span>{code}</span></a>')
    return (
        f'<details class="lang-dd">'
        f'<summary aria-label="Language">{label}</summary>'
        f'<div class="lang-menu">{"".join(items)}</div>'
        f"</details>"
    )


def bot_url(lang: str) -> str:
    return f"{BOT}?start=lang_{lang}"


def page(L: dict) -> str:
    brand = L["brand"]
    lang = L["lang"]
    home = L["home"]
    bot = bot_url(lang)
    can = L["canonical"]
    chips = "".join(f'<span class="chip">{c}</span>' for c in L["chips"])
    faq_html = "".join(f"<details><summary>{q}</summary><p>{a}</p></details>" for q, a in L["faq"])
    schema_app = {
        "@context": "https://schema.org",
        "@type": "SoftwareApplication",
        "name": brand,
        "operatingSystem": "Telegram",
        "applicationCategory": "BusinessApplication",
        "description": L["schema_desc"],
        "url": can,
        "offers": [
            {"@type": "Offer", "name": L["plan_free_name"], "price": "0", "priceCurrency": "RUB"},
            {"@type": "Offer", "name": L["plan_start_name"], "price": "990", "priceCurrency": "RUB"},
            {"@type": "Offer", "name": L["plan_biz_name"], "price": "2990", "priceCurrency": "RUB"},
            {"@type": "Offer", "name": L["plan_team_name"], "price": "6900", "priceCurrency": "RUB"},
        ],
    }
    schema_faq = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}}
            for q, a in L["faq_schema"]
        ],
    }
    logo = f"🏗 {brand}"
    return f'''<!DOCTYPE html>
<html lang="{lang}">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{L["title"]}</title>
<meta name="description" content="{L["description"]}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="{brand}">
<meta property="og:url" content="{can}">
<meta property="og:title" content="{L["og_title"]}">
<meta property="og:description" content="{L["og_description"]}">
<meta property="og:image" content="https://stroytablica.ru/og.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:locale" content="{L["og_locale"]}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{L["og_title"]}">
<meta name="twitter:description" content="{L["og_description"]}">
<meta name="twitter:image" content="https://stroytablica.ru/og.png">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%3E%3Ctext y='.9em' font-size='90'%3E%F0%9F%8F%97%3C/text%3E%3C/svg%3E">
<link rel="canonical" href="{can}">
{hreflangs()}
<script type="application/ld+json">
{json.dumps(schema_app, ensure_ascii=False)}
</script>
<script type="application/ld+json">
{json.dumps(schema_faq, ensure_ascii=False)}
</script>
<style>
{CSS}
</style>
</head>
<body>

<nav><div class="wrap">
<a class="logo" href="{home}">{logo}</a>
<div class="nav-right">
<div class="links">
<span class="nav-hide"><a href="#what">{L["nav_what"]}</a></span>
<span class="nav-hide"><a href="#demo">{L["nav_demo"]}</a></span>
<span class="nav-hide"><a href="#feat">{L["nav_feat"]}</a></span>
<span class="nav-hide"><a href="#comp">{L["nav_comp"]}</a></span>
<span class="nav-hide"><a href="#plans">{L["nav_plans"]}</a></span>
<span class="nav-hide"><a href="#partners">{L["nav_partners"]}</a></span>
</div>
{lang_dropdown(lang)}
<a class="btn sm" href="{bot}">{L["nav_bot"]}</a>
</div>
</div></nav>

<header class="hero"><div class="wrap">
<div>
<h1>{L["hero_h1"]}</h1>
<p class="sub">{L["hero_sub"]}</p>
<a class="btn" href="{bot}">{L["hero_cta"]}</a>
<p class="note">{L["hero_note"]}</p>
</div>
<div class="chat">
<div class="head"><div class="ava">🏗</div><div><b>{brand}</b><span>{L["chat_bot_label"]}</span></div></div>
<div class="msg user">{L["chat_u1"]}</div>
<div class="msg bot">{L["chat_b1"]}</div>
<div class="msg user">{L["chat_u2"]}</div>
<div class="msg bot">{L["chat_b2"]}</div>
<div class="msg user">{L["chat_u3"]}</div>
<div class="msg bot">{L["chat_b3"]}</div>
</div>
</div></header>

<section id="demo"><div class="wrap">
<h2>{L["demo_h2"]}</h2>
<p class="lead">{L["demo_lead"]}</p>
<div class="video-frame"><iframe src="https://www.youtube.com/embed/kqz7XeqbkGw" title="{brand} — {L["demo_label"]}" allow="accelerometer; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe></div>
</div></section>

<section id="what" style="background:#fff"><div class="wrap">
<h2>{L["what_h2"]}</h2>
<p class="lead">{L["what_lead"]}</p>
<div class="steps">
<div class="step"><h3>{L["step1_h"]}</h3><p>{L["step1_p"]}</p></div>
<div class="step"><h3>{L["step2_h"]}</h3><p>{L["step2_p"]}</p></div>
<div class="step"><h3>{L["step3_h"]}</h3><p>{L["step3_p"]}</p></div>
</div>
</div></section>

<section id="feat"><div class="wrap">
<h2>{L["feat_h2"]}</h2>
<p class="lead">{L["feat_lead"]}</p>
<div class="grid">
<div class="card"><div class="ico">🔍</div><h3>{L["f1_h"]}</h3><p>{L["f1_p"]}</p></div>
<div class="card"><div class="ico">👥</div><h3>{L["f2_h"]}</h3><p>{L["f2_p"]}</p></div>
<div class="card"><div class="ico">📊</div><h3>{L["f3_h"]}</h3><p>{L["f3_p"]}</p></div>
<div class="card"><div class="ico">📉</div><h3>{L["f4_h"]}</h3><p>{L["f4_p"]}</p></div>
<div class="card"><div class="ico">⚖️</div><h3>{L["f5_h"]}</h3><p>{L["f5_p"]}</p></div>
<div class="card"><div class="ico">💰</div><h3>{L["f6_h"]}</h3><p>{L["f6_p"]}</p></div>
</div>
<p class="lead" style="margin:34px 0 12px;font-weight:600;color:var(--ink)">{L["chips_lead"]}</p>
<div class="chips">
{chips}
</div>
</div></section>

<section id="comp" style="background:#fff"><div class="wrap">
<h2>{L["comp_h2"]}</h2>
<p class="lead">{L["comp_lead"]}</p>
<div class="tblwrap"><table>
<thead><tr><th></th><th>🏗 {brand}</th><th>Microsoft Copilot</th><th>ChatGPT</th><th>{L["comp_col_1c"]}</th></tr></thead>
<tbody>
<tr><td>{L["comp_r1"]}</td><td class="ok">{L["yes"]}</td><td class="no">{L["comp_r1_copilot"]}</td><td class="no">{L["no"]}</td><td class="ok">{L["yes"]}</td></tr>
<tr><td>{L["comp_r2"]}</td><td class="ok">{L["yes"]}</td><td class="ok">{L["yes"]}</td><td class="ok">{L["yes"]}</td><td class="no">{L["comp_r2_1c"]}</td></tr>
<tr><td>{L["comp_r3"]}</td><td class="ok">{L["yes"]}</td><td>{L["partial"]}</td><td class="no">{L["comp_r3_gpt"]}</td><td class="ok">{L["yes"]}</td></tr>
<tr><td>{L["comp_r4"]}</td><td class="ok">{L["yes"]}</td><td class="no">{L["no"]}</td><td class="no">{L["no"]}</td><td class="ok">{L["yes"]}</td></tr>
<tr><td>{L["comp_r5"]}</td><td class="ok">{L["comp_r5_us"]}</td><td>{L["comp_r5_copilot"]}</td><td>{L["comp_r5_gpt"]}</td><td class="no">{L["comp_r5_1c"]}</td></tr>
<tr><td>{L["comp_r6"]}</td><td class="ok">{L["comp_r6_us"]}</td><td>{L["comp_r6_copilot"]}</td><td>{L["comp_r6_gpt"]}</td><td class="no">{L["comp_r6_1c"]}</td></tr>
</tbody>
</table></div>
</div></section>

<section><div class="wrap">
<h2>{L["who_h2"]}</h2>
<p class="lead">{L["who_lead"]}</p>
<div class="grid">
<div class="card"><div class="ico">📦</div><h3>{L["w1_h"]}</h3><p>{L["w1_p"]}</p></div>
<div class="card"><div class="ico">👷</div><h3>{L["w2_h"]}</h3><p>{L["w2_p"]}</p></div>
<div class="card"><div class="ico">💼</div><h3>{L["w3_h"]}</h3><p>{L["w3_p"]}</p></div>
<div class="card"><div class="ico">🧮</div><h3>{L["w4_h"]}</h3><p>{L["w4_p"]}</p></div>
</div>
</div></section>

<section id="plans" style="background:#fff"><div class="wrap">
<h2>{L["plans_h2"]}</h2>
<p class="lead">{L["plans_lead"]}</p>
<div class="plans">
<div class="plan"><h3>{L["plan_free_name"]}</h3><div class="price">0 ₽</div>
<ul><li>{L["pf1"]}</li><li>{L["pf2"]}</li><li>{L["pf3"]}</li><li>{L["pf4"]}</li></ul>
<a class="btn ghost" href="{bot}">{L["plan_start_tg"]}</a></div>
<div class="plan"><h3>{L["plan_start_name"]}</h3><div class="price">990 ₽<span>{L["per_mo"]}</span></div>
<ul><li>{L["ps1"]}</li><li>{L["ps2"]}</li><li>{L["ps3"]}</li><li>{L["ps4"]}</li></ul>
<a class="btn ghost" href="{OWNER}">{L["plan_connect"]}</a></div>
<div class="plan hot" data-badge="{L["popular"]}"><h3>{L["plan_biz_name"]}</h3><div class="price">2 990 ₽<span>{L["per_mo"]}</span></div>
<ul><li>{L["pb1"]}</li><li>{L["pb2"]}</li><li>{L["pb3"]}</li><li class="soon">{L["pb4"]}</li><li>{L["pb5"]}</li></ul>
<a class="btn" href="{OWNER}">{L["plan_connect"]}</a></div>
<div class="plan"><h3>{L["plan_team_name"]}</h3><div class="price">6 900 ₽<span>{L["per_mo"]}</span></div>
<ul><li>{L["pt1"]}</li><li>{L["pt2"]}</li><li>{L["pt3"]}</li><li class="soon">{L["pt4"]}</li><li>{L["pt5"]}</li></ul>
<a class="btn ghost" href="{OWNER}">{L["plan_connect"]}</a></div>
</div>
<div class="implant">
<div><h3>{L["implant_h"]}</h3>
<p>{L["implant_p"]}</p></div>
<a class="btn" href="{OWNER}">{L["implant_cta"]}</a>
</div>
</div></section>

<section id="partners"><div class="wrap">
<h2>{L["partners_h2"]}</h2>
<p class="lead">{L["partners_lead"]}</p>
<div class="grid">
<div class="card"><div class="ico">🧾</div><h3>{L["pa1_h"]}</h3><p>{L["pa1_p"]}</p></div>
<div class="card"><div class="ico">🖥️</div><h3>{L["pa2_h"]}</h3><p>{L["pa2_p"]}</p></div>
<div class="card"><div class="ico">🏗️</div><h3>{L["pa3_h"]}</h3><p>{L["pa3_p"]}</p></div>
</div>
<p style="margin-top:22px"><a class="btn" href="{OWNER}">{L["partners_cta"]}</a></p>
</div></section>

<section style="background:#fff"><div class="wrap">
<h2>{L["faq_h2"]}</h2>
{faq_html}
</div></section>

<div class="wrap"><div class="cta-end">
<h2>{L["cta_h2"]}</h2>
<p>{L["cta_p"]}</p>
<a class="btn" href="{bot}">{L["cta_btn"]}</a>
</div></div>

<footer><div class="wrap">
<div>© 2026 {brand} · {L["footer_articles"]}: <a href="/oshibki-v-smete-excel.html">{L["art1"]}</a> · <a href="/uchet-materialov-excel.html">{L["art2"]}</a> · <a href="/neyroset-dlya-excel.html">{L["art3"]}</a></div>
<div>{L["footer_docs"]}: <a href="/privacy.html">{L["privacy"]}</a> · <a href="/terms.html">{L["terms"]}</a></div>
<div>{L["footer_contact"]}: <a href="{OWNER}">Telegram</a> · <a href="mailto:info@stroytablica.ru">info@stroytablica.ru</a> · {L["footer_cis"]}: <a href="{WA}">WhatsApp</a></div>
</div></footer>

<script>
// Close language dropdown when clicking outside
document.addEventListener('click',function(e){{
  document.querySelectorAll('details.lang-dd[open]').forEach(function(d){{
    if(!d.contains(e.target)) d.removeAttribute('open');
  }});
}});
</script>
</body>
</html>
'''


def base_common(**kw):
    """Shared structure filled per language via kw."""
    return kw


# ---------- content builders ----------

def content_ru():
    b = BRAND["ru"]
    return {
        "lang": "ru", "home": "/", "brand": b, "og_locale": "ru_RU",
        "canonical": "https://stroytablica.ru/",
        "title": f"{b} — ИИ-аналитик Excel-таблиц для стройки. В Telegram",
        "description": "Пришлите боту таблицу — учёт материалов, план-факт, прайс — и задавайте вопросы обычным текстом. Ошибки, дубли, сводки — за секунды. Бесплатно до 3 файлов в месяц, без карты.",
        "og_title": f"{b} — Excel-таблицы отвечают на вопросы. В Telegram",
        "og_description": "Пришлите боту таблицу и спрашивайте обычным текстом: ошибки в суммах, дубли, сводки — за секунды. Бесплатно до 3 файлов в месяц, без карты.",
        "schema_desc": f"ИИ-аналитик Excel-таблиц для строительных компаний в Telegram: находит ошибки, дубли, строит сводки. Расчёты выполняет база данных.",
        "nav_what": "Что это", "nav_demo": "Демо", "nav_feat": "Возможности", "nav_comp": "Сравнение", "nav_plans": "Тарифы", "nav_partners": "Партнёрам", "nav_bot": "Открыть бота",
        "hero_h1": "Ваши Excel-таблицы <em>отвечают на вопросы</em>. В Telegram.",
        "hero_sub": "Пришлите боту учёт материалов, план-факт или прайс — и спрашивайте обычным текстом, как у коллеги. Ошибки в суммах, дубли, сводки по поставщикам — за секунды, а не за вечер с фильтрами и формулами.",
        "hero_cta": "Попробовать бесплатно", "hero_note": "3 файла в месяц бесплатно · без карты · без установки · без обучения",
        "chat_bot_label": "бот",
        "chat_u1": "📎 Материалы_ЖК_Луговая12.xlsx",
        "chat_b1": "✅ 603 строки, 11 колонок. Задавайте вопросы!",
        "chat_u2": "Найди строки, где сумма не сходится с кол-во × цена",
        "chat_b2": "⚠️ Нашёл 6 строк с расхождением:\n• Строка 376: Арматура А500С d16 — в файле 4 550 856 ₽, по расчёту 3 374 728 ₽, отклонение +1 176 128 ₽\n• Строка 385: Раствор М150 — +75 233 ₽…",
        "chat_u3": "Есть ли дубли?", "chat_b3": "Да, 3 пары полных дублей: строки 25 и 602, 11 и 601, 60 и 603.",
        "demo_h2": "Смотрите сами", "demo_lead": "Загрузка файла и вопросы обычным текстом — в реальном времени, без монтажа.", "demo_label": "демо",
        "what_h2": "Что это такое — простыми словами",
        "what_lead": f"{b} — это бот в Telegram, которому вы отправляете свой обычный Excel-файл — тот самый, в котором снабженец ведёт закупки, а ПТО — план-факт. Дальше вы пишете вопрос словами, как написали бы сотруднику: «сколько потратили на бетон в мае?» — и через несколько секунд получаете точный ответ с цифрами и номерами строк. Не нужно знать формулы, сводные таблицы и фильтры. Не нужно ничего устанавливать и никого обучать. Если вы умеете отправить файл в Telegram — вы уже умеете всё.",
        "step1_h": "Ваш файл", "step1_p": "Любая таблица: учёт материалов, ведомость, прайсы, план-факт. Как есть, без подготовки — даже с «кривой» шапкой.",
        "step2_h": "Ваш вопрос", "step2_p": "Обычными словами, как коллеге. Можно с телефона, прямо с объекта.",
        "step3_h": "Точный ответ", "step3_p": "Цифры считает база данных, а не нейросеть «на глазок». Каждая находка — с номером строки исходного файла.",
        "feat_h2": "Что умеет бот", "feat_lead": "Шесть задач, которые сейчас съедают часы работы в Excel — бот делает их за секунды.",
        "f1_h": "Находит ошибки в суммах", "f1_p": "Сумма не сходится с количеством × ценой? Бот найдёт каждую такую строку и покажет размер расхождения. Одна найденная ошибка в накладной окупает подписку на годы вперёд.",
        "f2_h": "Ловит дубли и пропуски", "f2_p": "Задвоенные накладные, повторные позиции, пустые цены и количества — всё, что теряется в сотнях строк, бот выводит списком с номерами строк.",
        "f3_h": "Строит сводки", "f3_p": "По поставщикам, объектам, месяцам, категориям — по любой колонке вашего файла. То, ради чего раньше строили сводные таблицы часами.",
        "f4_h": "План-факт и перерасход", "f4_p": "«Где перерасход больше 10%?» — и через секунды список статей и объектов, где бюджет ушёл в минус, с цифрами.",
        "f5_h": "Сравнивает прайсы", "f5_p": "Загрузите прайс с ценами нескольких поставщиков — и спрашивайте, у кого дешевле конкретная позиция или весь заказ целиком.",
        "f6_h": "Следит за оплатами", "f6_p": "«Сколько не оплачено и кому?» — мгновенная картина по дебиторке и незакрытым позициям из вашей же таблицы.",
        "chips_lead": "Примеры вопросов, которые можно задать прямо сейчас:",
        "chips": ["Сколько потрачено на арматуру в марте?", "Найди строки, где сумма не сходится", "Есть ли дубли?", "Сводка по поставщикам", "У кого дешевле кирпич М150?", "Где перерасход больше 10%?", "Топ-10 самых дорогих закупок", "Сколько не оплачено и кому?", "Что покупали у ТД Арсенал в мае?", "Средняя цена бетона B25 по месяцам", "Какие позиции без цены?", "Сравни план и факт по объекту"],
        "comp_h2": "Почему этого больше нигде нет",
        "comp_lead": "Прямого аналога — ИИ-аналитика таблиц в Telegram — на рынке нет. А то, что есть, для стройки часто не подходит: Microsoft Copilot юрлицам в ряде стран недоступен, ChatGPT требует зарубежную карту и отправляет ваш файл в нейросеть целиком, а внедрение 1С или BI — месяцы и сотни тысяч рублей.",
        "comp_col_1c": "Внедрение 1С / BI", "yes": "Да", "no": "Нет", "partial": "Частично",
        "comp_r1": "Доступен напрямую, зарубежная карта не нужна", "comp_r1_copilot": "Нет — ограничения",
        "comp_r2": "Понимает вопросы обычным текстом", "comp_r2_1c": "Нет — отчёты настраивают программисты",
        "comp_r3": "Точные расчёты (считает база данных)", "comp_r3_gpt": "Нет — может «придумать» цифру",
        "comp_r4": "Файл целиком НЕ уходит в нейросеть",
        "comp_r5": "Запуск без внедрения и обучения", "comp_r5_us": "1 минута", "comp_r5_copilot": "Дни", "comp_r5_gpt": "Часы", "comp_r5_1c": "Месяцы",
        "comp_r6": "Цена", "comp_r6_us": "от 0 ₽", "comp_r6_copilot": "~2 800 ₽/чел/мес", "comp_r6_gpt": "~2 000 ₽/мес", "comp_r6_1c": "от 300 000 ₽",
        "who_h2": "Кому это нужно", "who_lead": "Всем в строительной компании, кто живёт в таблицах.",
        "w1_h": "Снабженец", "w1_p": "Сравнение прайсов, поиск лучшей цены, контроль заявок и оплат — без ручного перебора сотен строк.",
        "w2_h": "Прораб / ПТО", "w2_p": "Учёт материалов по объектам, план-факт, перерасход — прямо с объекта, с телефона, без ожидания отчёта из офиса.",
        "w3_h": "Директор", "w3_p": "Сводка по любому файлу за минуту. Дебиторка, топ затрат, контроль снабженцев — без звонков и совещаний.",
        "w4_h": "Бухгалтерия", "w4_p": "Сверка ведомостей, поиск расхождений и дублей перед закрытием месяца — без ночных бдений над ВПР.",
        "plans_h2": "Тарифы",
        "plans_lead": "Начните бесплатно — без карты и регистрации. Подключение платного тарифа — напишите нам в Telegram, подключим в течение часа. Оплата по счёту или переводом, онлайн-оплата скоро. <b>При оплате за год — два месяца в подарок.</b>",
        "plan_free_name": "Бесплатный", "plan_start_name": "Старт", "plan_biz_name": "Бизнес", "plan_team_name": "Команда",
        "per_mo": "/мес", "popular": "Популярный",
        "pf1": "3 файла в месяц", "pf2": "15 вопросов на файл", "pf3": "Файлы до 2 000 строк", "pf4": "Все виды анализа",
        "ps1": "30 файлов в месяц", "ps2": "Вопросы без ограничений", "ps3": "Файлы до 20 000 строк", "ps4": "За год: 9 900 ₽ — 2 месяца в подарок",
        "pb1": "Файлы без лимита", "pb2": "До 200 000 строк", "pb3": "Сверка двух файлов", "pb4": "КС-2 / КС-3 — скоро", "pb5": "За год: 29 900 ₽ — 2 месяца в подарок",
        "pt1": "Всё из «Бизнес»", "pt2": "5 сотрудников", "pt3": "Приоритетная поддержка", "pt4": "КС-2 / КС-3 — скоро", "pt5": "За год: 69 000 ₽ — 2 месяца в подарок",
        "plan_start_tg": "Начать в Telegram", "plan_connect": "Подключить в Telegram",
        "implant_h": "Внедрение под ключ — для компаний от 20 сотрудников",
        "implant_p": "Настроим бота под ваши реальные файлы, обучим снабженцев и ПТО, сопроводим первый месяц. Разовая услуга от 15 000 ₽ — плюс любой тариф.",
        "implant_cta": "Обсудить внедрение",
        "partners_h2": "Партнёрам — 25% с каждого платежа",
        "partners_lead": f"Бухгалтерские компании, 1С-франчайзи, поставщики стройматериалов: у вас уже есть доступ к снабженцам и директорам строительных компаний. Рекомендуйте им {b} — и получайте 25% от всех платежей приведённого клиента в течение первого года. Клиент называет вас при подключении, выплаты — ежемесячно.",
        "pa1_h": "Бухгалтериям и аутсорсерам", "pa1_p": "Ваши клиенты-строители перестанут приносить таблицы с ошибками — а вы заработаете на рекомендации.",
        "pa2_h": "1С-франчайзи и интеграторам", "pa2_p": "Простое дополнение к вашим внедрениям: без техподдержки с вашей стороны, мы всё берём на себя.",
        "pa3_h": "Поставщикам стройматериалов", "pa3_p": "Ваши покупатели-снабженцы получают инструмент, вы — процент и лояльность клиентов.",
        "partners_cta": "Стать партнёром", "faq_h2": "Частые вопросы",
        "faq": [
            ("Куда попадают мои данные? Это безопасно?", "Файл загружается в изолированную базу данных на защищённом сервере. В нейросеть таблица целиком не передаётся — только названия колонок и несколько первых строк. Все расчёты выполняет база данных — поэтому цифры точные. Рекомендуем загружать таблицы без персональных данных."),
            ("Какие файлы поддерживаются?", ".xlsx, .xls, .csv и .ods — Excel любой версии, МойОфис, Р7-Офис, LibreOffice и выгрузки из 1С. Размер — до 20 МБ."),
            ("У меня «кривая» таблица. Справится?", "Да. Бот понимает форматы чисел с пробелами («1 234,56»), шапки в две строки, пустые строки и опечатки. Если чего-то не поймёт — честно скажет."),
            ("Нужен ли Microsoft Office?", "Нет. Бот читает сам файл и не встраивается в Excel."),
            ("Сколько это стоит? Есть скрытые платежи?", "Нет. Бесплатный тариф — навсегда: 3 файла в месяц, карта не нужна. Платные тарифы — фиксированная цена. За год — два месяца в подарок."),
            ("Работает ли в Казахстане, Беларуси, Украине, Грузии, Армении, Турции?", "Да, везде, где работает Telegram. Ответы — на языке, на котором вы пишете. Для СНГ — те же тарифы."),
            ("Нужно что-то особенное под мою компанию?", "Напишите нам — дорабатываем бота: свои отчёты, интеграции, обучение. Для компаний от 20 человек — внедрение под ключ."),
        ],
        "faq_schema": [
            ("Куда попадают данные?", "Файл в изолированной БД. В нейросеть целиком не уходит. Цифры считает база."),
            ("Какие файлы?", "xlsx, xls, csv, ods до 20 МБ."),
            ("Нужен Office?", "Нет."),
            ("Цена?", "Бесплатно 3 файла/мес. Платные от 990 ₽."),
            ("СНГ и другие страны?", "Да, везде где Telegram. Ответ на языке сообщения."),
        ],
        "cta_h2": "Попробуйте на своём файле прямо сейчас",
        "cta_p": "Загрузите таблицу — и через минуту получите первый ответ. Бесплатно, без карты.",
        "cta_btn": "Открыть бота в Telegram",
        "footer_articles": "Статьи", "art1": "ошибки в Excel", "art2": "учёт материалов", "art3": "нейросеть для Excel",
        "footer_docs": "Документы", "privacy": "Политика конфиденциальности", "terms": "Пользовательское соглашение",
        "footer_contact": "Подключение и вопросы", "footer_cis": "для СНГ",
    }


def content_uk():
    b = BRAND["uk"]
    return {
        "lang": "uk", "home": "/uk/", "brand": b, "og_locale": "uk_UA",
        "canonical": "https://stroytablica.ru/uk/",
        "title": f"{b} — ШІ-аналітик Excel-таблиць для будівництва. У Telegram",
        "description": "Надішліть боту таблицю — облік матеріалів, план-факт, прайс — і ставте запитання звичайним текстом. Помилки, дублі, зведення — за секунди. Безкоштовно до 3 файлів на місяць, без картки.",
        "og_title": f"{b} — Excel-таблиці відповідають на запитання. У Telegram",
        "og_description": "Надішліть боту таблицю і питайте звичайним текстом: помилки в сумах, дублі, зведення — за секунди. Безкоштовно до 3 файлів на місяць.",
        "schema_desc": f"ШІ-аналітик Excel для будівельних компаній у Telegram. Точні розрахунки через базу даних.",
        "nav_what": "Що це", "nav_demo": "Демо", "nav_feat": "Можливості", "nav_comp": "Порівняння", "nav_plans": "Тарифи", "nav_partners": "Партнерам", "nav_bot": "Відкрити бота",
        "hero_h1": "Ваші Excel-таблиці <em>відповідають на запитання</em>. У Telegram.",
        "hero_sub": "Надішліть боту облік матеріалів, план-факт або прайс — і питайте звичайним текстом, як у колеги. Помилки в сумах, дублі, зведення по постачальниках — за секунди, а не вечір із фільтрами й формулами.",
        "hero_cta": "Спробувати безкоштовно", "hero_note": "3 файли на місяць безкоштовно · без картки · без встановлення · без навчання",
        "chat_bot_label": "бот",
        "chat_u1": "📎 Materials_Lugovaya12.xlsx",
        "chat_b1": "✅ 603 рядки, 11 колонок. Ставте запитання!",
        "chat_u2": "Знайди рядки, де сума не збігається з к-сть × ціна",
        "chat_b2": "⚠️ Знайшов 6 рядків із розбіжністю:\n• Рядок 376: Арматура А500С d16 — у файлі 4 550 856 ₽, за розрахунком 3 374 728 ₽, відхилення +1 176 128 ₽\n• Рядок 385: Розчин М150 — +75 233 ₽…",
        "chat_u3": "Чи є дублі?", "chat_b3": "Так, 3 пари повних дублів: рядки 25 і 602, 11 і 601, 60 і 603.",
        "demo_h2": "Дивіться самі", "demo_lead": "Завантаження файлу й запитання звичайним текстом — у реальному часі, без монтажу.", "demo_label": "демо",
        "what_h2": "Що це — простими словами",
        "what_lead": f"{b} — це бот у Telegram, якому ви надсилаєте свій звичайний Excel-файл — той самий, у якому постачальник веде закупівлі, а ПТО — план-факт. Далі пишете запитання словами: «скільки витратили на бетон у травні?» — і за кілька секунд отримуєте точну відповідь із цифрами та номерами рядків. Не потрібно знати формули й зведені таблиці. Якщо вмієте надіслати файл у Telegram — ви вже все вмієте.",
        "step1_h": "Ваш файл", "step1_p": "Будь-яка таблиця: облік матеріалів, відомості, прайси, план-факт. Як є, без підготовки.",
        "step2_h": "Ваше запитання", "step2_p": "Звичайними словами, як колезі. З телефону, прямо з об'єкта.",
        "step3_h": "Точна відповідь", "step3_p": "Цифри рахує база даних, а не нейромережа «на око». Кожна знахідка — з номером рядка.",
        "feat_h2": "Що вміє бот", "feat_lead": "Шість задач, які зараз з'їдають години в Excel — бот робить за секунди.",
        "f1_h": "Знаходить помилки в сумах", "f1_p": "Сума не збігається з кількістю × ціною? Бот знайде кожен такий рядок і покаже розмір розбіжності.",
        "f2_h": "Ловить дублі та пропуски", "f2_p": "Подвійні накладні, повторні позиції, порожні ціни — усе списком із номерами рядків.",
        "f3_h": "Будує зведення", "f3_p": "По постачальниках, об'єктах, місяцях, категоріях — по будь-якій колонці вашого файлу.",
        "f4_h": "План-факт і перевитрата", "f4_p": "«Де перевитрата більше 10%?» — за секунди список статей і об'єктів із цифрами.",
        "f5_h": "Порівнює прайси", "f5_p": "Завантажте прайс кількох постачальників — і питайте, у кого дешевше.",
        "f6_h": "Слідкує за оплатами", "f6_p": "«Скільки не оплачено і кому?» — миттєва картина з вашої таблиці.",
        "chips_lead": "Приклади запитань:",
        "chips": ["Скільки витрачено на арматуру в березні?", "Знайди рядки, де сума не збігається", "Чи є дублі?", "Зведення по постачальниках", "У кого дешевше цегла М150?", "Де перевитрата більше 10%?", "Топ-10 найдорожчих закупівель", "Скільки не оплачено і кому?", "Що купували у ТД Арсенал у травні?", "Середня ціна бетону B25 по місяцях", "Які позиції без ціни?", "Порівняй план і факт по об'єкту"],
        "comp_h2": "Чому цього більше ніде немає",
        "comp_lead": "Прямого аналога — ШІ-аналітика таблиць у Telegram — на ринку немає. Microsoft Copilot часто недоступний, ChatGPT потребує іноземної картки і надсилає файл у нейромережу цілком, а впровадження 1С/BI — місяці та великі бюджети.",
        "comp_col_1c": "Впровадження 1С / BI", "yes": "Так", "no": "Ні", "partial": "Частково",
        "comp_r1": "Доступний напряму, іноземна картка не потрібна", "comp_r1_copilot": "Ні — обмеження",
        "comp_r2": "Розуміє запитання звичайним текстом", "comp_r2_1c": "Ні — звіти налаштовують програмісти",
        "comp_r3": "Точні розрахунки (рахує база даних)", "comp_r3_gpt": "Ні — може «вигадувати» цифру",
        "comp_r4": "Файл цілком НЕ йде в нейромережу",
        "comp_r5": "Запуск без впровадження й навчання", "comp_r5_us": "1 хвилина", "comp_r5_copilot": "Дні", "comp_r5_gpt": "Години", "comp_r5_1c": "Місяці",
        "comp_r6": "Ціна", "comp_r6_us": "від 0 ₽", "comp_r6_copilot": "~2 800 ₽/ос/міс", "comp_r6_gpt": "~2 000 ₽/міс", "comp_r6_1c": "від 300 000 ₽",
        "who_h2": "Кому це потрібно", "who_lead": "Усім у будівельній компанії, хто живе в таблицях.",
        "w1_h": "Постачальник", "w1_p": "Порівняння прайсів, найкраща ціна, контроль заявок і оплат.",
        "w2_h": "Виконроб / ПТО", "w2_p": "Облік матеріалів, план-факт, перевитрата — з об'єкта, з телефону.",
        "w3_h": "Директор", "w3_p": "Зведення по будь-якому файлу за хвилину. Без дзвінків і нарад.",
        "w4_h": "Бухгалтерія", "w4_p": "Звірка відомостей, пошук розбіжностей і дублів перед закриттям місяця.",
        "plans_h2": "Тарифи",
        "plans_lead": "Почніть безкоштовно — без картки й реєстрації. Платний тариф — напишіть у Telegram, підключимо протягом години. <b>За рік — два місяці в подарунок.</b>",
        "plan_free_name": "Безкоштовний", "plan_start_name": "Старт", "plan_biz_name": "Бізнес", "plan_team_name": "Команда",
        "per_mo": "/міс", "popular": "Популярний",
        "pf1": "3 файли на місяць", "pf2": "15 запитань на файл", "pf3": "Файли до 2 000 рядків", "pf4": "Усі види аналізу",
        "ps1": "30 файлів на місяць", "ps2": "Запитання без обмежень", "ps3": "Файли до 20 000 рядків", "ps4": "За рік: 9 900 ₽ — 2 місяці в подарунок",
        "pb1": "Файли без ліміту", "pb2": "До 200 000 рядків", "pb3": "Звірка двох файлів", "pb4": "КС-2 / КС-3 — скоро", "pb5": "За рік: 29 900 ₽ — 2 місяці в подарунок",
        "pt1": "Усе з «Бізнес»", "pt2": "5 співробітників", "pt3": "Пріоритетна підтримка", "pt4": "КС-2 / КС-3 — скоро", "pt5": "За рік: 69 000 ₽ — 2 місяці в подарунок",
        "plan_start_tg": "Почати в Telegram", "plan_connect": "Підключити в Telegram",
        "implant_h": "Впровадження під ключ — для компаній від 20 співробітників",
        "implant_p": "Налаштуємо бота під ваші файли, навчимо постачальників і ПТО, супроводимо перший місяць. Від 15 000 ₽ + будь-який тариф.",
        "implant_cta": "Обговорити впровадження",
        "partners_h2": "Партнерам — 25% з кожного платежу",
        "partners_lead": f"Бухгалтерські компанії, 1С-франчайзі, постачальники будматеріалів: рекомендуйте {b} і отримуйте 25% від платежів приведеного клієнта протягом першого року.",
        "pa1_h": "Бухгалтеріям", "pa1_p": "Клієнти-будівельники перестануть приносити таблиці з помилками — ви заробите на рекомендації.",
        "pa2_h": "1С-франчайзі", "pa2_p": "Просте доповнення до впроваджень: техпідтримку беремо на себе.",
        "pa3_h": "Постачальникам будматеріалів", "pa3_p": "Ваші покупці отримують інструмент, ви — відсоток і лояльність.",
        "partners_cta": "Стати партнером", "faq_h2": "Часті запитання",
        "faq": [
            ("Куди потрапляють мої дані? Це безпечно?", "Файл у ізольованій базі на захищеному сервері. У нейромережу таблиця цілком не йде — лише назви колонок і кілька перших рядків. Розрахунки виконує база даних."),
            ("Які файли підтримуються?", ".xlsx, .xls, .csv і .ods — Excel, LibreOffice, вивантаження з 1С. До 20 МБ."),
            ("«Крива» таблиця: шапка в два рядки, числа з пробілами. Впорається?", "Так. Бот розуміє формати чисел із пробілами, подвійні шапки, порожні рядки й друкарські помилки."),
            ("Чи потрібен Microsoft Office?", "Ні. Бот читає сам файл і не вбудовується в Excel."),
            ("Скільки це коштує?", "Безкоштовний тариф назавжди: 3 файли на місяць. Платні — фіксована ціна. За рік — два місяці в подарунок."),
            ("Працює в Україні, Казахстані, Білорусі, Грузії?", "Так, скрізь, де є Telegram. Відповіді мовою вашого повідомлення."),
            ("Потрібно щось особливе під компанію?", "Напишіть — допрацьовуємо: звіти, інтеграції, навчання. Від 20 людей — впровадження під ключ."),
        ],
        "faq_schema": [
            ("Безпека даних?", "Файл в ізольованій БД. У нейромережу цілком не йде."),
            ("Файли?", "xlsx, xls, csv, ods до 20 МБ."),
            ("Office?", "Не потрібен."),
            ("Ціна?", "3 файли/міс безкоштовно. Платні від 990 ₽."),
            ("Країни?", "Будь-де, де Telegram."),
        ],
        "cta_h2": "Спробуйте на своєму файлі просто зараз",
        "cta_p": "Завантажте таблицю — і за хвилину отримаєте першу відповідь. Безкоштовно, без картки.",
        "cta_btn": "Відкрити бота в Telegram",
        "footer_articles": "Статті", "art1": "помилки в Excel", "art2": "облік матеріалів", "art3": "нейромережа для Excel",
        "footer_docs": "Документи", "privacy": "Політика конфіденційності", "terms": "Угода користувача",
        "footer_contact": "Підключення та питання", "footer_cis": "для СНД",
    }


def content_be():
    b = BRAND["be"]
    return {
        "lang": "be", "home": "/be/", "brand": b, "og_locale": "be_BY",
        "canonical": "https://stroytablica.ru/be/",
        "title": f"{b} — ШІ-аналітык Excel-табліц для будаўніцтва. У Telegram",
        "description": "Дашліце боту табліцу — улік матэрыялаў, план-факт, прайс — і задавайце пытанні звычайным тэкстам. Памылкі, дублі, зводкі — за секунды. Бясплатна да 3 файлаў на месяц, без карткі.",
        "og_title": f"{b} — Excel-табліцы адказваюць на пытанні. У Telegram",
        "og_description": "Дашліце боту табліцу і пытайце звычайным тэкстам: памылкі ў сумах, дублі, зводкі — за секунды. Бясплатна да 3 файлаў на месяц.",
        "schema_desc": f"ШІ-аналітык Excel для будаўнічых кампаній у Telegram. Дакладныя разлікі праз базу дадзеных.",
        "nav_what": "Што гэта", "nav_demo": "Дэма", "nav_feat": "Магчымасці", "nav_comp": "Параўнанне", "nav_plans": "Тарыфы", "nav_partners": "Партнёрам", "nav_bot": "Адкрыць бота",
        "hero_h1": "Вашы Excel-табліцы <em>адказваюць на пытанні</em>. У Telegram.",
        "hero_sub": "Дашліце боту ўлік матэрыялаў, план-факт ці прайс — і пытайце звычайным тэкстам, як калегу. Памылкі ў сумах, дублі, зводкі па пастаўшчыках — за секунды.",
        "hero_cta": "Паспрабаваць бясплатна", "hero_note": "3 файлы на месяц бясплатна · без карткі · без усталёўкі · без навучання",
        "chat_bot_label": "бот",
        "chat_u1": "📎 Materials_Lugovaya12.xlsx",
        "chat_b1": "✅ 603 радкі, 11 калонак. Задавайце пытанні!",
        "chat_u2": "Знайдзі радкі, дзе сума не сыходзіцца з кольк × цана",
        "chat_b2": "⚠️ Знайшоў 6 радкоў з разыходжаннем:\n• Радок 376: Арматура А500С d16 — у файле 4 550 856 ₽, па разліку 3 374 728 ₽, адхіленне +1 176 128 ₽\n• Радок 385: Раствор М150 — +75 233 ₽…",
        "chat_u3": "Ці ёсць дублі?", "chat_b3": "Так, 3 пары поўных дубляў: радкі 25 і 602, 11 і 601, 60 і 603.",
        "demo_h2": "Глядзіце самі", "demo_lead": "Загрузка файла і пытанні звычайным тэкстам — у рэальным часе, без мантажу.", "demo_label": "дэма",
        "what_h2": "Што гэта — простымі словамі",
        "what_lead": f"{b} — гэта бот у Telegram, якому вы дасылаеце свой звычайны Excel-файл. Далей пішаце пытанне словамі: «колькі патрацілі на бетон у маі?» — і праз некалькі секунд атрымліваеце дакладны адказ з лічбамі і нумарамі радкоў. Не трэба ведаць формулы і зводныя табліцы.",
        "step1_h": "Ваш файл", "step1_p": "Любая табліца: улік матэрыялаў, ведамасці, прайсы, план-факт. Як ёсць, без падрыхтоўкі.",
        "step2_h": "Ваша пытанне", "step2_p": "Звычайнымі словамі, як калегу. З тэлефона, проста з аб'екта.",
        "step3_h": "Дакладны адказ", "step3_p": "Лічбы лічыць база дадзеных, а не нейрасетка «на вока». Кожная знаходка — з нумарам радка.",
        "feat_h2": "Што ўмее бот", "feat_lead": "Шэсць задач, якія зараз з'ядаюць гадзіны ў Excel — бот робіць за секунды.",
        "f1_h": "Знаходзіць памылкі ў сумах", "f1_p": "Сума не сыходзіцца з колькасцю × цаной? Бот знойдзе кожны такі радок і пакажа памер разыходжання.",
        "f2_h": "Лавіць дублі і пропускі", "f2_p": "Падвоеныя накладныя, паўторныя пазіцыі, пустыя цэны — усё спісам з нумарамі радкоў.",
        "f3_h": "Будзе зводкі", "f3_p": "Па пастаўшчыках, аб'ектах, месяцах, катэгорыях — па любой калонцы файла.",
        "f4_h": "План-факт і перавыдатак", "f4_p": "«Дзе перавыдатак больш за 10%?» — за секунды спіс артыкулаў і аб'ектаў з лічбамі.",
        "f5_h": "Параўноўвае прайсы", "f5_p": "Загрузіце прайс некалькіх пастаўшчыкоў — і пытайце, у каго танней.",
        "f6_h": "Сачыць за аплатамі", "f6_p": "«Колькі не аплачана і каму?» — імгненная карціна з вашай табліцы.",
        "chips_lead": "Прыклады пытанняў:",
        "chips": ["Колькі патрачана на арматуру ў сакавіку?", "Знайдзі радкі, дзе сума не сыходзіцца", "Ці ёсць дублі?", "Зводка па пастаўшчыках", "У каго танней цэгла М150?", "Дзе перавыдатак больш за 10%?", "Топ-10 самых дарагіх закупак", "Колькі не аплачана і каму?", "Што куплялі ў ТД Арсенал у маі?", "Сярэдняя цана бетону B25 па месяцах", "Якія пазіцыі без цаны?", "Параўнай план і факт па аб'екце"],
        "comp_h2": "Чаму гэтага больш нідзе няма",
        "comp_lead": "Прамога аналага — ШІ-аналітыка табліц у Telegram — на рынку няма. Copilot часта недаступны, ChatGPT патрабуе замежную картку і дасылае файл у нейрасетку цалкам, а ўкараненне 1С/BI — месяцы і вялікія бюджэты.",
        "comp_col_1c": "Укараненне 1С / BI", "yes": "Так", "no": "Не", "partial": "Часткова",
        "comp_r1": "Даступны напрамую, замежная картка не патрэбна", "comp_r1_copilot": "Не — абмежаванні",
        "comp_r2": "Разумее пытанні звычайным тэкстам", "comp_r2_1c": "Не — справаздачы наладжваюць праграмісты",
        "comp_r3": "Дакладныя разлікі (лічыць база дадзеных)", "comp_r3_gpt": "Не — можа «прыдумаць» лічбу",
        "comp_r4": "Файл цалкам НЕ ідзе ў нейрасетку",
        "comp_r5": "Запуск без укаранення і навучання", "comp_r5_us": "1 хвіліна", "comp_r5_copilot": "Дні", "comp_r5_gpt": "Гадзіны", "comp_r5_1c": "Месяцы",
        "comp_r6": "Цана", "comp_r6_us": "ад 0 ₽", "comp_r6_copilot": "~2 800 ₽/чал/мес", "comp_r6_gpt": "~2 000 ₽/мес", "comp_r6_1c": "ад 300 000 ₽",
        "who_h2": "Каму гэта трэба", "who_lead": "Усім у будаўнічай кампаніі, хто жыве ў табліцах.",
        "w1_h": "Снабжэнец", "w1_p": "Параўнанне прайсаў, лепшая цана, кантроль заявак і аплат.",
        "w2_h": "Прараб / ПТО", "w2_p": "Улік матэрыялаў, план-факт, перавыдатак — з аб'екта, з тэлефона.",
        "w3_h": "Дырэктар", "w3_p": "Зводка па любым файле за хвіліну. Без званкоў і паседжанняў.",
        "w4_h": "Бухгалтэрыя", "w4_p": "Зверка ведамасцей, пошук разыходжанняў і дубляў перад закрыццём месяца.",
        "plans_h2": "Тарыфы",
        "plans_lead": "Пачніце бясплатна — без карткі і рэгістрацыі. Платы тарыф — напішыце ў Telegram, падключым на працягу гадзіны. <b>За год — два месяцы ў падарунак.</b>",
        "plan_free_name": "Бясплатны", "plan_start_name": "Старт", "plan_biz_name": "Бізнес", "plan_team_name": "Каманда",
        "per_mo": "/мес", "popular": "Папулярны",
        "pf1": "3 файлы на месяц", "pf2": "15 пытанняў на файл", "pf3": "Файлы да 2 000 радкоў", "pf4": "Усе віды аналізу",
        "ps1": "30 файлаў на месяц", "ps2": "Пытанні без абмежаванняў", "ps3": "Файлы да 20 000 радкоў", "ps4": "За год: 9 900 ₽ — 2 месяцы ў падарунак",
        "pb1": "Файлы без ліміту", "pb2": "Да 200 000 радкоў", "pb3": "Зверка двух файлаў", "pb4": "КС-2 / КС-3 — хутка", "pb5": "За год: 29 900 ₽ — 2 месяцы ў падарунак",
        "pt1": "Усё з «Бізнес»", "pt2": "5 супрацоўнікаў", "pt3": "Прыярытэтная падтрымка", "pt4": "КС-2 / КС-3 — хутка", "pt5": "За год: 69 000 ₽ — 2 месяцы ў падарунак",
        "plan_start_tg": "Пачаць у Telegram", "plan_connect": "Падключыць у Telegram",
        "implant_h": "Укараненне пад ключ — для кампаній ад 20 супрацоўнікаў",
        "implant_p": "Наладзім бота пад вашы файлы, навучым снабжэнцаў і ПТО, суправадзім першы месяц. Ад 15 000 ₽ + любы тарыф.",
        "implant_cta": "Абмеркаваць укараненне",
        "partners_h2": "Партнёрам — 25% з кожнага платежу",
        "partners_lead": f"Бухгалтарскія кампаніі, 1С-франчайзі, пастаўшчыкі будматэрыялаў: раіце {b} і атрымлівайце 25% ад плацяжоў прыведзенага кліента на працягу першага года.",
        "pa1_h": "Бухгалтэрыям", "pa1_p": "Кліенты-будаўнікі перастануць прыносіць табліцы з памылкамі — вы зарабіце на рэкамендацыі.",
        "pa2_h": "1С-франчайзі", "pa2_p": "Простае дапаўненне да ўкараненняў: тэхпадтрымку бярэм на сябе.",
        "pa3_h": "Пастаўшчыкам будматэрыялаў", "pa3_p": "Вашы пакупнікі атрымліваюць інструмент, вы — працэнт і лаяльнасць.",
        "partners_cta": "Стаць партнёрам", "faq_h2": "Частыя пытанні",
        "faq": [
            ("Куды трапляюць мае дадзеныя? Гэта бяспечна?", "Файл у ізаляванай базе на абароненым серверы. У нейрасетку табліца цалкам не ідзе — толькі назвы калонак і некалькі першых радкоў. Разлікі выконвае база дадзеных."),
            ("Якія файлы падтрымліваюцца?", ".xlsx, .xls, .csv і .ods — Excel, LibreOffice, выгрузкі з 1С. Да 20 МБ."),
            ("«Крывавая» табліца. Справіцца?", "Так. Бот разумее фарматы лікаў з прабеламі, падвойныя шапкі, пустыя радкі і памылкі набору."),
            ("Ці патрэбны Microsoft Office?", "Не. Бот чытае сам файл і не ўбудоўваецца ў Excel."),
            ("Колькі гэта каштуе?", "Бясплатны тарыф назаўжды: 3 файлы на месяц. Платныя — фіксаваная цана. За год — два месяцы ў падарунак."),
            ("Працуе ў Беларусі, Казахстане, Украіне, Грузіі?", "Так, усюды, дзе ёсць Telegram. Адказы мовай вашага паведамлення."),
            ("Трэба нешта асаблівае пад кампанію?", "Напішыце — дапрацоўваем: справаздачы, інтэграцыі, навучанне. Ад 20 чалавек — укараненне пад ключ."),
        ],
        "faq_schema": [
            ("Бяспека?", "Файл у ізаляванай БД. У нейрасетку цалкам не ідзе."),
            ("Файлы?", "xlsx, xls, csv, ods да 20 МБ."),
            ("Office?", "Не патрэбны."),
            ("Цана?", "3 файлы/мес бясплатна. Платныя ад 990 ₽."),
            ("Краіны?", "Усюды, дзе Telegram."),
        ],
        "cta_h2": "Паспрабуйце на сваім файле зараз",
        "cta_p": "Загрузіце табліцу — і праз хвіліну атрымаеце першы адказ. Бясплатна, без карткі.",
        "cta_btn": "Адкрыць бота ў Telegram",
        "footer_articles": "Артыкулы", "art1": "памылкі ў Excel", "art2": "улік матэрыялаў", "art3": "нейрасетка для Excel",
        "footer_docs": "Дакументы", "privacy": "Палітыка канфідэнцыяльнасці", "terms": "Карыстальніцкае пагадненне",
        "footer_contact": "Падключэнне і пытанні", "footer_cis": "для СНД",
    }


def content_kk():
    b = BRAND["kk"]
    return {
        "lang": "kk", "home": "/kk/", "brand": b, "og_locale": "kk_KZ",
        "canonical": "https://stroytablica.ru/kk/",
        "title": f"{b} — Құрылыс үшін Excel кестелерінің AI-талдаушысы. Telegram-да",
        "description": "Ботқа кесте жіберіңіз — материалдар есебі, жоспар-факт, баға тізімі — және қарапайым мәтінмен сұраңыз. Қателер, дубльдер, жиынтықтар — секундтарда. Айына 3 файл тегін, картасыз.",
        "og_title": f"{b} — Excel кестелері сұрақтарға жауап береді. Telegram-да",
        "og_description": "Ботқа кесте жіберіп, қарапайым мәтінмен сұраңыз: сома қателері, дубльдер, жиынтықтар — секундтарда. Айына 3 файл тегін.",
        "schema_desc": f"Telegram-дағы құрылыс компаниялары үшін Excel AI-талдаушысы. Есептеулерді дерекқор жасайды.",
        "nav_what": "Бұл не", "nav_demo": "Демо", "nav_feat": "Мүмкіндіктер", "nav_comp": "Салыстыру", "nav_plans": "Тарифтер", "nav_partners": "Серіктестерге", "nav_bot": "Ботты ашу",
        "hero_h1": "Excel кестелеріңіз <em>сұрақтарға жауап береді</em>. Telegram-да.",
        "hero_sub": "Ботқа материалдар есебін, жоспар-факт немесе баға тізімін жіберіңіз — әріптеске сияқты қарапайым мәтінмен сұраңыз. Сомадағы қателер, дубльдер, жеткізушілер бойынша жиынтық — секундтарда.",
        "hero_cta": "Тегін байқап көру", "hero_note": "Айына 3 файл тегін · картасыз · орнатусыз · оқытусыз",
        "chat_bot_label": "бот",
        "chat_u1": "📎 Materials_Lugovaya12.xlsx",
        "chat_b1": "✅ 603 жол, 11 баған. Сұрақтарыңызды қойыңыз!",
        "chat_u2": "Сома саны × бағамен сәйкес келмейтін жолдарды тап",
        "chat_b2": "⚠️ 6 жолда айырмашылық таптым:\n• Жол 376: Арматура А500С d16 — файлда 4 550 856 ₽, есеп бойынша 3 374 728 ₽, ауытқу +1 176 128 ₽\n• Жол 385: Ерітінді М150 — +75 233 ₽…",
        "chat_u3": "Дубль бар ма?", "chat_b3": "Иә, 3 толық дубль жұбы: жолдар 25 және 602, 11 және 601, 60 және 603.",
        "demo_h2": "Өзіңіз көріңіз", "demo_lead": "Файл жүктеу және қарапайым мәтінмен сұрақтар — нақты уақытта, монтажсыз.", "demo_label": "демо",
        "what_h2": "Бұл не — қарапайым тілмен",
        "what_lead": f"{b} — Telegram-дағы бот: оған әдеттегі Excel файлыңызды жібересіз. Содан кейін қызметкерге жазғандай сұрақ жазасыз: «мамырда бетонға қанша жұмсадық?» — бірнеше секундтан кейін сандар мен жол нөмірлерімен нақты жауап аласыз. Формулалар мен pivot білудің қажеті жоқ.",
        "step1_h": "Файлыңыз", "step1_p": "Кез келген кесте: материалдар есебі, ведомость, баға тізімдері, жоспар-факт. Дайындықсыз, сол қалпында.",
        "step2_h": "Сұрағыңыз", "step2_p": "Қарапайым сөзбен, әріптеске сияқты. Телефоннан, нысаннан тікелей.",
        "step3_h": "Нақты жауап", "step3_p": "Сандарды дерекқор есептейді, нейрожелі «көзбен» емес. Әр табылған нәрсе — бастапқы файл жолының нөмірімен.",
        "feat_h2": "Бот не істей алады", "feat_lead": "Excel-де сағаттар алатын алты міндет — бот секундтарда орындайды.",
        "f1_h": "Сома қателерін табады", "f1_p": "Сома саны × бағамен сәйкес келмей ме? Бот әр жолды тауып, айырмашылықты көрсетеді.",
        "f2_h": "Дубль мен бос орындарды ұстайды", "f2_p": "Қосарлы накладной, қайталанған позициялар, бос бағалар — жол нөмірлерімен тізім.",
        "f3_h": "Жиынтық құрады", "f3_p": "Жеткізушілер, нысандар, айлар, санаттар бойынша — файлдағы кез келген баған бойынша.",
        "f4_h": "Жоспар-факт және артық шығын", "f4_p": "«Қайда 10%-дан артық шығын бар?» — секундтарда мақалалар мен нысандар тізімі.",
        "f5_h": "Баға тізімдерін салыстырады", "f5_p": "Бірнеше жеткізушінің бағасын жүктеңіз — нақты позиция немесе бүкіл тапсырыс кімде арзанырақ деп сұраңыз.",
        "f6_h": "Төлемдерді қадағалайды", "f6_p": "«Қанша төленбеген және кімге?» — өз кестеңізден лезде сурет.",
        "chips_lead": "Сұрақ үлгілері:",
        "chips": ["Наурызда арматураға қанша жұмсалды?", "Сома сәйкес келмейтін жолдарды тап", "Дубль бар ма?", "Жеткізушілер бойынша жиынтық", "М150 кірпіш кімде арзан?", "Қайда 10%-дан артық шығын?", "Ең қымбат 10 сатып алу", "Қанша төленбеген және кімге?", "Мамырда ТД Арсеналдан не сатып алдық?", "B25 бетонның айлар бойынша орташа бағасы", "Бағасыз позициялар қайсы?", "Нысан бойынша жоспар мен фактіні салыстыр"],
        "comp_h2": "Неге мұны басқа жерден таба алмайсыз",
        "comp_lead": "Telegram-дағы кесте AI-талдаушысының тікелей аналогы жоқ. Copilot көбіне қолжетімсіз, ChatGPT шетелдік карта талап етеді және файлды толық нейрожеліге жібереді, ал 1С/BI енгізу — айлар мен үлкен бюджет.",
        "comp_col_1c": "1С / BI енгізу", "yes": "Иә", "no": "Жоқ", "partial": "Ішінара",
        "comp_r1": "Тікелей қолжетімді, шетелдік карта керек емес", "comp_r1_copilot": "Жоқ — шектеулер",
        "comp_r2": "Қарапайым мәтінмен сұрақтарды түсінеді", "comp_r2_1c": "Жоқ — есептерді бағдарламашылар баптайды",
        "comp_r3": "Нақты есептеулер (дерекқор санайды)", "comp_r3_gpt": "Жоқ — санды «ойлап табуы» мүмкін",
        "comp_r4": "Файл толығымен нейрожеліге БАРМАЙДЫ",
        "comp_r5": "Енгізу мен оқытусыз іске қосу", "comp_r5_us": "1 минут", "comp_r5_copilot": "Күндер", "comp_r5_gpt": "Сағаттар", "comp_r5_1c": "Айлар",
        "comp_r6": "Баға", "comp_r6_us": "0 ₽-ден", "comp_r6_copilot": "~2 800 ₽/адам/ай", "comp_r6_gpt": "~2 000 ₽/ай", "comp_r6_1c": "300 000 ₽-ден",
        "who_h2": "Кімге керек", "who_lead": "Кестелерде өмір сүретін құрылыс компаниясындағы барлығына.",
        "w1_h": "Жабдықтаушы", "w1_p": "Баға тізімін салыстыру, ең жақсы баға, өтінім мен төлемдерді бақылау.",
        "w2_h": "Прораб / ПТО", "w2_p": "Нысандар бойынша материалдар, жоспар-факт, артық шығын — нысаннан, телефоннан.",
        "w3_h": "Директор", "w3_p": "Кез келген файл бойынша бір минутта жиынтық. Қоңырау мен жиналыссыз.",
        "w4_h": "Бухгалтерия", "w4_p": "Ведомость салыстыру, ай жабылар алдында айырмашылық пен дубль іздеу.",
        "plans_h2": "Тарифтер",
        "plans_lead": "Тегін бастаңыз — картасыз және тіркеусіз. Ақылы тариф — Telegram-да жазыңыз, бір сағат ішінде қосамыз. <b>Жылдық төлемде — екі ай сыйлық.</b>",
        "plan_free_name": "Тегін", "plan_start_name": "Старт", "plan_biz_name": "Бизнес", "plan_team_name": "Команда",
        "per_mo": "/ай", "popular": "Танымал",
        "pf1": "Айына 3 файл", "pf2": "Файлға 15 сұрақ", "pf3": "2 000 жолға дейін", "pf4": "Талдаудың барлық түрі",
        "ps1": "Айына 30 файл", "ps2": "Шексіз сұрақ", "ps3": "20 000 жолға дейін", "ps4": "Жылына: 9 900 ₽ — 2 ай сыйлық",
        "pb1": "Файл шектеуі жоқ", "pb2": "200 000 жолға дейін", "pb3": "Екі файлды салыстыру", "pb4": "КС-2 / КС-3 — жақында", "pb5": "Жылына: 29 900 ₽ — 2 ай сыйлық",
        "pt1": "«Бизнестегі» барлығы", "pt2": "5 қызметкер", "pt3": "Басым қолдау", "pt4": "КС-2 / КС-3 — жақында", "pt5": "Жылына: 69 000 ₽ — 2 ай сыйлық",
        "plan_start_tg": "Telegram-да бастау", "plan_connect": "Telegram-да қосу",
        "implant_h": "Кілтпен енгізу — 20+ қызметкері бар компанияларға",
        "implant_p": "Ботты нақты файлдарыңызға баптаймыз, жабдықтау мен ПТО-ны үйретеміз, бірінші айды сүйемелдейміз. 15 000 ₽-ден + кез келген тариф.",
        "implant_cta": "Енгізуді талқылау",
        "partners_h2": "Серіктестерге — әр төлемнен 25%",
        "partners_lead": f"Бухгалтерлік компаниялар, 1С-франчайзи, құрылыс материалдары жеткізушілері: {b} ұсынып, әкелген клиенттің бірінші жылғы төлемдерінен 25% алыңыз.",
        "pa1_h": "Бухгалтерияларға", "pa1_p": "Құрылыс клиенттері қате кесте әкелуді тоқтатады — сіз ұсыныстан табыс табасыз.",
        "pa2_h": "1С-франчайзиге", "pa2_p": "Енгізулеріңізге қарапайым қосымша: техподдержканы өзіміз аламыз.",
        "pa3_h": "Құрылыс материалдары жеткізушілеріне", "pa3_p": "Сатып алушыларыңыз құрал алады, сіз — пайыз және адалдық.",
        "partners_cta": "Серіктес болу", "faq_h2": "Жиі қойылатын сұрақтар",
        "faq": [
            ("Деректерім қайда кетеді? Қауіпсіз бе?", "Файл қорғалған сервердегі оқшауланған дерекқорға жүктеледі. Кесте толығымен нейрожеліге жіберілмейді — тек баған атаулары мен бірнеше алғашқы жол. Есептеулерді дерекқор жасайды."),
            ("Қандай файлдар қолдау табады?", ".xlsx, .xls, .csv және .ods — Excel, LibreOffice, 1С шығару. 20 МБ-қа дейін."),
            ("«Қисық» кесте: екі жолды тақырып, бос орынды сандар. Қолынан келе ме?", "Иә. Бот бос орынды сан пішімдерін, қос тақырыптарды, бос жолдар мен қателерді түсінеді."),
            ("Microsoft Office керек пе?", "Жоқ. Бот файлды өзі оқиды, Excel-ге енбейді."),
            ("Қанша тұрады?", "Тегін тариф мәңгі: айына 3 файл. Ақылы — тұрақты баға. Жылына — екі ай сыйлық."),
            ("Қазақстанда, Беларусте, Украинада, Грузияда жұмыс істей ме?", "Иә, Telegram бар жердің бәрінде. Жауаптар хабарламаңыздың тілінде."),
            ("Компанияма арнайы нәрсе керек пе?", "Жазыңыз — бейімдейміз: есептер, интеграциялар, оқыту. 20+ адамға — кілтпен енгізу."),
        ],
        "faq_schema": [
            ("Қауіпсіздік?", "Файл оқшауланған ДҚ-да. Нейрожеліге толық кетпейді."),
            ("Файлдар?", "xlsx, xls, csv, ods 20 МБ-қа дейін."),
            ("Office?", "Керек емес."),
            ("Баға?", "Айына 3 файл тегін. Ақылы 990 ₽-ден."),
            ("Елдер?", "Telegram бар жерде."),
        ],
        "cta_h2": "Өз файлыңызда қазір байқап көріңіз",
        "cta_p": "Кестені жүктеңіз — бір минутта алғашқы жауапты алыңыз. Тегін, картасыз.",
        "cta_btn": "Telegram-да ботты ашу",
        "footer_articles": "Мақалалар", "art1": "Excel қателері", "art2": "материалдар есебі", "art3": "Excel үшін нейрожелі",
        "footer_docs": "Құжаттар", "privacy": "Құпиялылық саясаты", "terms": "Пайдаланушы келісімі",
        "footer_contact": "Қосылу және сұрақтар", "footer_cis": "ТМД үшін",
    }


def content_ka():
    b = BRAND["ka"]
    return {
        "lang": "ka", "home": "/ka/", "brand": b, "og_locale": "ka_GE",
        "canonical": "https://stroytablica.ru/ka/",
        "title": f"{b} — Excel-ცხრილების AI-ანალიტიკოსი მშენებლობისთვის. Telegram-ში",
        "description": "გაუგზავნეთ ბოტს ცხრილი — მასალების აღრიცხვა, გეგმა-ფაქტი, ფასთა სია — და დაუსვით კითხვები ჩვეულებრივი ტექსტით. შეცდომები, დუბლიკატები, შეჯამებები — წამებში. უფასოდ 3 ფაილი თვეში, ბარათის გარეშე.",
        "og_title": f"{b} — Excel-ცხრილები პასუხობენ კითხვებს. Telegram-ში",
        "og_description": "გაუგზავნეთ ბოტს ცხრილი და იკითხეთ ჩვეულებრივი ტექსტით: შეცდომები ჯამებში, დუბლიკატები, შეჯამებები — წამებში. უფასოდ 3 ფაილი თვეში.",
        "schema_desc": f"Excel AI-ანალიტიკოსი სამშენებლო კომპანიებისთვის Telegram-ში. გამოთვლებს ასრულებს მონაცემთა ბაზა.",
        "nav_what": "რა არის", "nav_demo": "დემო", "nav_feat": "შესაძლებლობები", "nav_comp": "შედარება", "nav_plans": "ტარიფები", "nav_partners": "პარტნიორებს", "nav_bot": "ბოტი",
        "hero_h1": "თქვენი Excel-ცხრილები <em>პასუხობენ კითხვებს</em>. Telegram-ში.",
        "hero_sub": "გაუგზავნეთ ბოტს მასალების აღრიცხვა, გეგმა-ფაქტი ან ფასთა სია — და იკითხეთ ჩვეულებრივი ტექსტით, როგორც კოლეგას. შეცდომები ჯამებში, დუბლიკატები, შეჯამებები მომწოდებლების მიხედვით — წამებში.",
        "hero_cta": "უფასოდ ცდა", "hero_note": "3 ფაილი თვეში უფასოდ · ბარათის გარეშე · ინსტალაციის გარეშე · სწავლების გარეშე",
        "chat_bot_label": "ბოტი",
        "chat_u1": "📎 Materials_Lugovaya12.xlsx",
        "chat_b1": "✅ 603 სტრიქონი, 11 სვეტი. დასვით კითხვები!",
        "chat_u2": "იპოვე სტრიქონები, სადაც ჯამი არ ემთხვევა რაოდენობა × ფასი",
        "chat_b2": "⚠️ ვიპოვე 6 სტრიქონი განსხვავებით:\n• სტრიქონი 376: არმატურა А500С d16 — ფაილში 4 550 856 ₽, გამოთვლით 3 374 728 ₽, გადახრა +1 176 128 ₽\n• სტრიქონი 385: ხსნარი М150 — +75 233 ₽…",
        "chat_u3": "არის დუბლიკატები?", "chat_b3": "დიახ, 3 წყვილი სრული დუბლიკატი: სტრიქონები 25 და 602, 11 და 601, 60 და 603.",
        "demo_h2": "ნახეთ თავად", "demo_lead": "ფაილის ატვირთვა და კითხვები ჩვეულებრივი ტექსტით — რეალურ დროში, მონტაჟის გარეშე.", "demo_label": "დემო",
        "what_h2": "რა არის ეს — მარტივად",
        "what_lead": f"{b} არის ბოტი Telegram-ში, რომელსაც უგზავნით თქვენს ჩვეულებრივ Excel-ფაილს. შემდეგ წერთ კითხვას: «რამდენი დავხარჯეთ ბეტონზე მაისში?» — და რამდენიმე წამში იღებთ ზუსტ პასუხს ციფრებითა და სტრიქონების ნომრებით. ფორმულები და pivot არ გჭირდებათ.",
        "step1_h": "თქვენი ფაილი", "step1_p": "ნებისმიერი ცხრილი: მასალების აღრიცხვა, უწყისი, ფასთა სიები, გეგმა-ფაქტი. როგორც არის.",
        "step2_h": "თქვენი კითხვა", "step2_p": "ჩვეულებრივი სიტყვებით, როგორც კოლეგას. ტელეფონიდან, ობიექტიდან.",
        "step3_h": "ზუსტი პასუხი", "step3_p": "ციფრებს ითვლის მონაცემთა ბაზა, არა ნეიროქსელი «თვალით». ყოველი პოვნა — სტრიქონის ნომრით.",
        "feat_h2": "რას შეუძლია ბოტს", "feat_lead": "ექვსი ამოცანა, რომელიც Excel-ში საათებს ჭამს — ბოტი წამებში აკეთებს.",
        "f1_h": "პოულობს შეცდომებს ჯამებში", "f1_p": "ჯამი არ ემთხვევა რაოდენობა × ფასს? ბოტი იპოვის ყოველ სტრიქონს და აჩვენებს განსხვავებას.",
        "f2_h": "იჭერს დუბლიკატებს", "f2_p": "ორმაგი ზედნადები, განმეორებითი პოზიციები, ცარიელი ფასები — სიით სტრიქონების ნომრებით.",
        "f3_h": "აგებს შეჯამებებს", "f3_p": "მომწოდებლების, ობიექტების, თვეების, კატეგორიების მიხედვით — ნებისმიერი სვეტით.",
        "f4_h": "გეგმა-ფაქტი და გადაჭარბება", "f4_p": "«სად არის გადაჭარბება 10%-ზე მეტი?» — წამებში სია ციფრებით.",
        "f5_h": "ადარებს ფასთა სიებს", "f5_p": "ატვირთეთ რამდენიმე მომწოდებლის ფასები — იკითხეთ, ვისთან იაფია.",
        "f6_h": "აკონტროლებს გადახდებს", "f6_p": "«რამდენი არ არის გადახდილი და ვის?» — მყისიერი სურათი თქვენი ცხრილიდან.",
        "chips_lead": "კითხვების მაგალითები:",
        "chips": ["რამდენი დაიხარჯა არმატურაზე მარტში?", "იპოვე სტრიქონები, სადაც ჯამი არ ემთხვევა", "არის დუბლიკატები?", "შეჯამება მომწოდებლების მიხედვით", "ვისთან იაფია აგური М150?", "სად არის გადაჭარბება 10%-ზე მეტი?", "ტოპ-10 ყველაზე ძვირი შესყიდვა", "რამდენი არ არის გადახდილი და ვის?", "რა ვიყიდეთ ТД Арсенал-თან მაისში?", "ბეტონი B25-ის საშუალო ფასი თვეების მიხედვით", "რომელი პოზიციებია ფასის გარეშე?", "შეადარე გეგმა და ფაქტი ობიექტის მიხედვით"],
        "comp_h2": "რატომ არ არის ეს სხვაგან",
        "comp_lead": "ცხრილების AI-ანალიტიკოსის პირდაპირი ანალოგი Telegram-ში ბაზარზე არ არის. Copilot ხშირად მიუწვდომელია, ChatGPT მოითხოვს უცხოურ ბარათს და ფაილს მთლიანად უგზავნის ნეიროქსელს, 1С/BI დანერგვა — თვეები და დიდი ბიუჯეტი.",
        "comp_col_1c": "1С / BI დანერგვა", "yes": "დიახ", "no": "არა", "partial": "ნაწილობრივ",
        "comp_r1": "ხელმისაწვდომია პირდაპირ, უცხოური ბარათი არ სჭირდება", "comp_r1_copilot": "არა — შეზღუდვები",
        "comp_r2": "იგებს კითხვებს ჩვეულებრივი ტექსტით", "comp_r2_1c": "არა — ანგარიშებს პროგრამისტები აყენებენ",
        "comp_r3": "ზუსტი გამოთვლები (ითვლის მონაცემთა ბაზა)", "comp_r3_gpt": "არა — შეიძლება «მოიფიქროს» ციფრი",
        "comp_r4": "ფაილი მთლიანად არ მიდის ნეიროქსელში",
        "comp_r5": "გაშვება დანერგვისა და სწავლების გარეშე", "comp_r5_us": "1 წუთი", "comp_r5_copilot": "დღეები", "comp_r5_gpt": "საათები", "comp_r5_1c": "თვეები",
        "comp_r6": "ფასი", "comp_r6_us": "0 ₽-დან", "comp_r6_copilot": "~2 800 ₽/ად/თვ", "comp_r6_gpt": "~2 000 ₽/თვ", "comp_r6_1c": "300 000 ₽-დან",
        "who_h2": "ვის სჭირდება", "who_lead": "სამშენებლო კომპანიაში ყველას, ვინც ცხრილებში ცხოვრობს.",
        "w1_h": "მომარაგება", "w1_p": "ფასთა სიების შედარება, საუკეთესო ფასი, განაცხადებისა და გადახდების კონტროლი.",
        "w2_h": "ოსტატი / ПТО", "w2_p": "მასალების აღრიცხვა, გეგმა-ფაქტი, გადაჭარბება — ობიექტიდან, ტელეფონით.",
        "w3_h": "დირექტორი", "w3_p": "შეჯამება ნებისმიერ ფაილზე ერთ წუთში. ზარებისა და კრებების გარეშე.",
        "w4_h": "ბუღალტერია", "w4_p": "უწყისების შეჯერება, განსხვავებებისა და დუბლიკატების ძებნა თვის დახურვამდე.",
        "plans_h2": "ტარიფები",
        "plans_lead": "დაიწყეთ უფასოდ — ბარათისა და რეგისტრაციის გარეშე. ფასიანი ტარიფი — მოგვწერეთ Telegram-ში, ერთ საათში ჩავრთავთ. <b>წლიური გადახდისას — ორი თვე საჩუქრად.</b>",
        "plan_free_name": "უფასო", "plan_start_name": "სტარტი", "plan_biz_name": "ბიზნესი", "plan_team_name": "გუნდი",
        "per_mo": "/თვ", "popular": "პოპულარული",
        "pf1": "3 ფაილი თვეში", "pf2": "15 კითხვა ფაილზე", "pf3": "ფაილები 2 000 სტრიქონამდე", "pf4": "ანალიზის ყველა სახეობა",
        "ps1": "30 ფაილი თვეში", "ps2": "კითხვები შეუზღუდავად", "ps3": "ფაილები 20 000 სტრიქონამდე", "ps4": "წელიწადში: 9 900 ₽ — 2 თვე საჩუქრად",
        "pb1": "ფაილები ლიმიტის გარეშე", "pb2": "200 000 სტრიქონამდე", "pb3": "ორი ფაილის შეჯერება", "pb4": "КС-2 / КС-3 — მალე", "pb5": "წელიწადში: 29 900 ₽ — 2 თვე საჩუქრად",
        "pt1": "ყველაფერი «ბიზნესიდან»", "pt2": "5 თანამშრომელი", "pt3": "პრიორიტეტული მხარდაჭერა", "pt4": "КС-2 / КС-3 — მალე", "pt5": "წელიწადში: 69 000 ₽ — 2 თვე საჩუქრად",
        "plan_start_tg": "დაწყება Telegram-ში", "plan_connect": "ჩართვა Telegram-ში",
        "implant_h": "გასაღებზე დანერგვა — 20+ თანამშრომლის კომპანიებისთვის",
        "implant_p": "მოვარგებთ ბოტს თქვენს ფაილებს, ვასწავლით მომარაგებას და ПТО-ს, გაგიყვებით პირველ თვეს. 15 000 ₽-დან + ნებისმიერი ტარიფი.",
        "implant_cta": "განვიხილოთ დანერგვა",
        "partners_h2": "პარტნიორებს — 25% ყოველი გადახდიდან",
        "partners_lead": f"საბუღალტრო კომპანიები, 1С-ფრანჩაიზი, სამშენებლო მასალების მომწოდებლები: ურჩიეთ {b} — და მიიღეთ 25% მოყვანილი კლიენტის ყველა გადახდიდან პირველი წლის განმავლობაში.",
        "pa1_h": "ბუღალტერიებს", "pa1_p": "კლიენტები-მშენებლები აღარ მოიტანენ ცხრილებს შეცდომებით — თქვენ გამოიმუშავებთ რეკომენდაციაზე.",
        "pa2_h": "1С-ფრანჩაიზს", "pa2_p": "მარტივი დამატება დანერგვებზე: ტექმხარდაჭერას ჩვენ ვიღებთ.",
        "pa3_h": "სამშენებლო მასალების მომწოდებლებს", "pa3_p": "მყიდველები იღებენ ინსტრუმენტს, თქვენ — პროცენტს და ლოიალობას.",
        "partners_cta": "გახდით პარტნიორი", "faq_h2": "ხშირი კითხვები",
        "faq": [
            ("სად მიდის ჩემი მონაცემები? უსაფრთხოა?", "ფაილი იტვირთება იზოლირებულ მონაცემთა ბაზაში დაცულ სერვერზე. ნეიროქსელში ცხრილი მთლიანად არ გადაეცემა. გამოთვლებს ასრულებს მონაცემთა ბაზა."),
            ("რომელი ფაილებია მხარდაჭერილი?", ".xlsx, .xls, .csv და .ods — Excel, LibreOffice, 1С ექსპორტი. 20 მბ-მდე."),
            ("«დახრილი» ცხრილი. გაუმკლავდება?", "დიახ. ბოტი იგებს რიცხვების ფორმატებს სფეისებით, ორ სტრიქონიან სათაურებს და ბეჭდვით შეცდომებს."),
            ("სჭირდება Microsoft Office?", "არა. ბოტი კითხულობს თავად ფაილს."),
            ("რამდენი ღირს?", "უფასო ტარიფი სამუდამოდ: 3 ფაილი თვეში. ფასიანი — ფიქსირებული ფასი. წელიწადში — ორი თვე საჩუქრად."),
            ("მუშაობს საქართველოში, სომხეთში, ყაზახეთში?", "დიახ, ყველგან, სადაც Telegram მუშაობს. პასუხები თქვენი შეტყობინების ენაზე."),
            ("ჩემს კომპანიაზე რაღაც განსაკუთრებული მჭირდება?", "მოგვწერეთ — ვასრულებთ: ანგარიშები, ინტეგრაციები, სწავლება. 20+ ადამიანზე — გასაღებზე დანერგვა."),
        ],
        "faq_schema": [
            ("უსაფრთხოება?", "ფაილი იზოლირებულ ბაზაში. ნეიროქსელში მთლიანად არ მიდის."),
            ("ფაილები?", "xlsx, xls, csv, ods 20 მბ-მდე."),
            ("Office?", "არ სჭირდება."),
            ("ფასი?", "3 ფაილი/თვ უფასოდ. ფასიანი 990 ₽-დან."),
            ("ქვეყნები?", "სადაც Telegram მუშაობს."),
        ],
        "cta_h2": "სცადეთ საკუთარ ფაილზე ახლავე",
        "cta_p": "ატვირთეთ ცხრილი — და ერთ წუთში მიიღებთ პირველ პასუხს. უფასოდ, ბარათის გარეშე.",
        "cta_btn": "ბოტის გახსნა Telegram-ში",
        "footer_articles": "სტატიები", "art1": "შეცდომები Excel-ში", "art2": "მასალების აღრიცხვა", "art3": "ნეიროქსელი Excel-ისთვის",
        "footer_docs": "დოკუმენტები", "privacy": "კონფიდენციალურობის პოლიტიკა", "terms": "მომხმარებლის შეთანხმება",
        "footer_contact": "ჩართვა და კითხვები", "footer_cis": "სნგ-სთვის",
    }


def content_hy():
    b = BRAND["hy"]
    return {
        "lang": "hy", "home": "/hy/", "brand": b, "og_locale": "hy_AM",
        "canonical": "https://stroytablica.ru/hy/",
        "title": f"{b} — Excel-աղյուսակների AI-վերլուծաբան շինարարության համար. Telegram-ում",
        "description": "Ուղարկեք բոտին աղյուսակ՝ նյութերի հաշվառում, պլան-փաստ, գնացուցակ — և տվեք հարցեր սովորական տեքստով։ Սխալներ, կրկնօրինակներ, ամփոփումներ — վայրկյաններում։ Անվճար մինչև 3 ֆայլ ամսում։",
        "og_title": f"{b} — Excel-աղյուսակները պատասխանում են հարցերին. Telegram-ում",
        "og_description": "Ուղարկեք բոտին աղյուսակ և հարցրեք սովորական տեքստով՝ գումարների սխալներ, կրկնօրինակներ, ամփոփումներ — վայրկյաններում։ Անվճար մինչև 3 ֆայլ ամսում։",
        "schema_desc": f"Excel AI-վերլուծաբան շինարարական ընկերությունների համար Telegram-ում. Հաշվարկները կատարում է տվյալների բազան.",
        "nav_what": "Ի՞նչ է", "nav_demo": "Դեմո", "nav_feat": "Հնարավորություններ", "nav_comp": "Համեմատություն", "nav_plans": "Սակագներ", "nav_partners": "Գործընկերներին", "nav_bot": "Բոտ",
        "hero_h1": "Ձեր Excel-աղյուսակները <em>պատասխանում են հարցերին</em>. Telegram-ում.",
        "hero_sub": "Ուղարկեք բոտին նյութերի հաշվառում, պլան-փաստ կամ գնացուցակ — և հարցրեք սովորական տեքստով, ինչպես գործընկերոջը։ Սխալներ գումարներում, կրկնօրինակներ, ամփոփումներ — վայրկյաններում։",
        "hero_cta": "Փորձել անվճար", "hero_note": "3 ֆայլ ամսում անվճար · առանց քարտի · առանց տեղադրման · առանց ուսուցման",
        "chat_bot_label": "բոտ",
        "chat_u1": "📎 Materials_Lugovaya12.xlsx",
        "chat_b1": "✅ 603 տող, 11 սյունակ։ Տվեք հարցեր։",
        "chat_u2": "Գտիր տողերը, որտեղ գումարը չի համընկնում քանակ × գին",
        "chat_b2": "⚠️ Գտա 6 տող շեղումով.\n• Տող 376. Արմատուրա А500С d16 — ֆայլում 4 550 856 ₽, հաշվարկով 3 374 728 ₽, շեղում +1 176 128 ₽\n• Տող 385. Լուծույթ М150 — +75 233 ₽…",
        "chat_u3": "Կա՞ն կրկնօրինակներ։", "chat_b3": "Այո, 3 զույգ ամբողջական կրկնօրինակ. տողեր 25 և 602, 11 և 601, 60 և 603։",
        "demo_h2": "Տեսեք ինքներդ", "demo_lead": "Ֆայլի վերբեռնում և հարցեր սովորական տեքստով — իրական ժամանակում, առանց մոնտաժի։", "demo_label": "դեմո",
        "what_h2": "Ի՞նչ է սա — պարզ լեզվով",
        "what_lead": f"{b}-ն Telegram-ի բոտ է, որին ուղարկում եք ձեր սովորական Excel-ֆայլը։ Այնուհետև գրում եք հարցը բառերով. «որքա՞ն ծախսեցինք բետոնի վրա մայիսին» — և մի քանի վայրկյանից ստանում եք ճշգրիտ պատասխան թվերով և տողերի համարներով։",
        "step1_h": "Ձեր ֆայլը", "step1_p": "Ցանկացած աղյուսակ. նյութերի հաշվառում, տեղեկագիր, գնացուցակներ, պլան-փաստ։ Առանց պատրաստման։",
        "step2_h": "Ձեր հարցը", "step2_p": "Սովորական բառերով, ինչպես գործընկերոջը։ Հեռախոսից, ուղիղ օբյեկտից։",
        "step3_h": "Ճշգրիտ պատասխան", "step3_p": "Թվերը հաշվում է տվյալների բազան, ոչ թե նեյրոցանցը «աչքով»։ Յուրաքանչյուր գտածո — տողի համարով։",
        "feat_h2": "Ի՞նչ է կարողանում բոտը", "feat_lead": "Վեց խնդիր, որոնք Excel-ում ժամեր են խլում — բոտը անում է վայրկյաններում։",
        "f1_h": "Գտնում է սխալներ գումարներում", "f1_p": "Գումարը չի համընկնում քանակ × գնին՞։ Բոտը կգտնի ամեն տող և կցույց տա շեղումը։",
        "f2_h": "Բռնում է կրկնօրինակներ", "f2_p": "Կրկնակի բեռնագրեր, կրկնվող դիրքեր, դատարկ գներ — ցանկով՝ տողերի համարներով։",
        "f3_h": "Կառուցում է ամփոփումներ", "f3_p": "Մատակարարների, օբյեկտների, ամիսների, կատեգորիաների համաձայն — ցանկացած սյունակով։",
        "f4_h": "Պլան-փաստ և գերածախս", "f4_p": "«Որտե՞ղ է գերածախսը 10%-ից ավելի» — վայրկյաններում ցանկ թվերով։",
        "f5_h": "Համեմատում է գնացուցակներ", "f5_p": "Վերբեռնեք մի քանի մատակարարների գներ — հարցրեք, ում մոտ ավելի էժան է։",
        "f6_h": "Հսկում է վճարումները", "f6_p": "«Որքա՞ն չի վճարվել և ում» — ակնթարթային պատկեր ձեր աղյուսակից։",
        "chips_lead": "Հարցերի օրինակներ.",
        "chips": ["Որքա՞ն է ծախսվել արմատուրայի վրա մարտին։", "Գտիր տողերը, որտեղ գումարը չի համընկնում", "Կա՞ն կրկնօրինակներ։", "Ամփոփում մատակարարների համաձայն", "Ո՞ւմ մոտ է ավելի էժան աղյուսը М150։", "Որտե՞ղ է գերածախսը 10%-ից ավելի։", "Թոփ-10 ամենաթանկ գնումները", "Որքա՞ն չի վճարվել և ում։", "Ի՞նչ գնեցինք ТД Арсенал-ից մայիսին։", "Բետոն B25-ի միջին գինը ամիսների համաձայն", "Որո՞նք են գին չունեցող դիրքերը։", "Համեմատիր պլանը և փաստը օբյեկտի համաձայն"],
        "comp_h2": "Ինչու սա այլուր չկա",
        "comp_lead": "Աղյուսակների AI-վերլուծաբանի ուղղակի անալոգ Telegram-ում շուկայում չկա։ Copilot-ը հաճախ անհասանելի է, ChatGPT-ն պահանջում է արտասահմանյան քարտ և ֆայլն ամբողջությամբ ուղարկում է նեյրոցանց, 1С/BI ներդրումը — ամիսներ և մեծ բյուջե։",
        "comp_col_1c": "1С / BI ներդրում", "yes": "Այո", "no": "Ոչ", "partial": "Մասամբ",
        "comp_r1": "Հասանելի է ուղղակիորեն, արտասահմանյան քարտ պետք չէ", "comp_r1_copilot": "Ոչ — սահմանափակումներ",
        "comp_r2": "Հասկանում է հարցերը սովորական տեքստով", "comp_r2_1c": "Ոչ — հաշվետվությունները կարգավորում են ծրագրավորողները",
        "comp_r3": "Ճշգրիտ հաշվարկներ (հաշվում է տվյալների բազան)", "comp_r3_gpt": "Ոչ — կարող է «հորինել» թիվ",
        "comp_r4": "Ֆայլն ամբողջությամբ ՉԻ գնում նեյրոցանց",
        "comp_r5": "Մեկնարկ առանց ներդրման և ուսուցման", "comp_r5_us": "1 րոպե", "comp_r5_copilot": "Օրեր", "comp_r5_gpt": "Ժամեր", "comp_r5_1c": "Ամիսներ",
        "comp_r6": "Գին", "comp_r6_us": "0 ₽-ից", "comp_r6_copilot": "~2 800 ₽/մարդ/ամիս", "comp_r6_gpt": "~2 000 ₽/ամիս", "comp_r6_1c": "300 000 ₽-ից",
        "who_h2": "Ո՞ւմ է պետք", "who_lead": "Շինարարական ընկերությունում բոլորին, ով ապրում է աղյուսակներում։",
        "w1_h": "Մատակարարում", "w1_p": "Գնացուցակների համեմատություն, լավագույն գին, հայտերի և վճարումների վերահսկում։",
        "w2_h": "Վարպետ / ПТО", "w2_p": "Նյութերի հաշվառում, պլան-փաստ, գերածախս — օբյեկտից, հեռախոսով։",
        "w3_h": "Տնօրեն", "w3_p": "Ամփոփում ցանկացած ֆայլի վրա մեկ րոպեում։ Առանց զանգերի և ժողովների։",
        "w4_h": "Հաշվապահություն", "w4_p": "Տեղեկագրերի համադրում, շեղումների և կրկնօրինակների որոնում ամսվա փակումից առաջ։",
        "plans_h2": "Սակագներ",
        "plans_lead": "Սկսեք անվճար — առանց քարտի և գրանցման։ Վճարովի սակագին — գրեք Telegram-ում, միացնենք մեկ ժամում։ <b>Տարեկան վճարման դեպքում — երկու ամիս նվեր։</b>",
        "plan_free_name": "Անվճար", "plan_start_name": "Ստարտ", "plan_biz_name": "Բիզնես", "plan_team_name": "Թիմ",
        "per_mo": "/ամիս", "popular": "Հանրաճանաչ",
        "pf1": "3 ֆայլ ամսում", "pf2": "15 հարց ֆայլի վրա", "pf3": "Ֆայլեր մինչև 2 000 տող", "pf4": "Վերլուծության բոլոր տեսակները",
        "ps1": "30 ֆայլ ամսում", "ps2": "Հարցեր առանց սահմանափակման", "ps3": "Ֆայլեր մինչև 20 000 տող", "ps4": "Տարեկան. 9 900 ₽ — 2 ամիս նվեր",
        "pb1": "Ֆայլեր առանց սահմանի", "pb2": "Մինչև 200 000 տող", "pb3": "Երկու ֆայլի համադրում", "pb4": "КС-2 / КС-3 — շուտով", "pb5": "Տարեկան. 29 900 ₽ — 2 ամիս նվեր",
        "pt1": "Ամեն ինչ «Բիզնեսից»", "pt2": "5 աշխատակից", "pt3": "Առաջնահերթ աջակցություն", "pt4": "КС-2 / КС-3 — շուտով", "pt5": "Տարեկան. 69 000 ₽ — 2 ամիս նվեր",
        "plan_start_tg": "Սկսել Telegram-ում", "plan_connect": "Միացնել Telegram-ում",
        "implant_h": "Բանալիով ներդրում — 20+ աշխատակից ունեցող ընկերությունների համար",
        "implant_p": "Կարգավորենք բոտը ձեր ֆայլերի համար, սովորեցնենք մատակարարմանը և ПТО-ին, ուղեկցենք առաջին ամիսը։ 15 000 ₽-ից + ցանկացած սակագին։",
        "implant_cta": "Քննարկել ներդրումը",
        "partners_h2": "Գործընկերներին — 25% յուրաքանչյուր վճարումից",
        "partners_lead": f"Հաշվապահական ընկերություններ, 1С-ֆրանչայզներ, շինանյութերի մատակարարներ. խորհուրդ տվեք {b} — և ստացեք 25% բերված հաճախորդի վճարումներից առաջին տարում։",
        "pa1_h": "Հաշվապահություններին", "pa1_p": "Հաճախորդ-շինարարները այլևս չեն բերի սխալներով աղյուսակներ — դուք կվաստակեք առաջարկությունից։",
        "pa2_h": "1С-ֆրանչայզներին", "pa2_p": "Պարզ լրացում ներդրումներին. տեխաջակցությունը վերցնում ենք մենք։",
        "pa3_h": "Շինանյութերի մատակարարներին", "pa3_p": "Գնորդները ստանում են գործիք, դուք — տոկոս և հավատարմություն։",
        "partners_cta": "Դառնալ գործընկեր", "faq_h2": "Հաճախակի հարցեր",
        "faq": [
            ("Որտե՞ղ են գնում իմ տվյալները։ Անվտա՞նգ է։", "Ֆայլը վերբեռնվում է մեկուսացված տվյալների բազա պաշտպանված սերվերում։ Աղյուսակն ամբողջությամբ նեյրոցանց չի գնում։ Հաշվարկները կատարում է տվյալների բազան։"),
            ("Որո՞նք են աջակցվող ֆայլերը։", ".xlsx, .xls, .csv և .ods — Excel, LibreOffice, 1С արտահանում։ Մինչև 20 ՄԲ։"),
            ("«Ծուռ» աղյուսակ։ Կհաղթահարի՞։", "Այո։ Բոտը հասկանում է թվերի ձևաչափեր բացատներով, երկտող վերնագրեր և տպագրական սխալներ։"),
            ("Պե՞տք է Microsoft Office։", "Ոչ։ Բոտը կարդում է ինքը ֆայլը։"),
            ("Որքա՞ն արժե։", "Անվճար սակագինը ընդմիշտ. 3 ֆայլ ամսում։ Վճարովի — ֆիքսված գին։ Տարեկան — երկու ամիս նվեր։"),
            ("Աշխատո՞ւմ է Հայաստանում, Վրաստանում, Ղազախստանում։", "Այո, ամենուր, որտեղ աշխատում է Telegram-ը։ Պատասխանները ձեր հաղորդագրության լեզվով։"),
            ("Հատուկ բան է պետք ընկերության համար։", "Գրեք — հարմարեցնում ենք. հաշվետվություններ, ինտեգրացիաներ, ուսուցում։ 20+ մարդու համար — բանալիով ներդրում։"),
        ],
        "faq_schema": [
            ("Անվտանգություն?", "Ֆայլը մեկուսացված ԲԴ-ում։ Նեյրոցանց ամբողջությամբ չի գնում։"),
            ("Ֆայլեր?", "xlsx, xls, csv, ods մինչև 20 ՄԲ։"),
            ("Office?", "Պետք չէ։"),
            ("Գին?", "3 ֆայլ/ամիս անվճար։ Վճարովի 990 ₽-ից։"),
            ("Երկրներ?", "Որտեղ Telegram կա։"),
        ],
        "cta_h2": "Փորձեք ձեր ֆայլի վրա հենց հիմա",
        "cta_p": "Վերբեռնեք աղյուսակը — և մեկ րոպեից ստացեք առաջին պատասխանը։ Անվճար, առանց քարտի։",
        "cta_btn": "Բացել բոտը Telegram-ում",
        "footer_articles": "Հոդվածներ", "art1": "սխալներ Excel-ում", "art2": "նյութերի հաշվառում", "art3": "նեյրոցանց Excel-ի համար",
        "footer_docs": "Փաստաթղթեր", "privacy": "Գաղտնիության քաղաքականություն", "terms": "Օգտագործման պայմաններ",
        "footer_contact": "Միացում և հարցեր", "footer_cis": "ԱՊՀ-ի համար",
    }


def content_tr():
    b = BRAND["tr"]
    return {
        "lang": "tr", "home": "/tr/", "brand": b, "og_locale": "tr_TR",
        "canonical": "https://stroytablica.ru/tr/",
        "title": f"{b} — İnşaat için Excel tablolarının AI analisti. Telegram’da",
        "description": "Bota tablo gönderin — malzeme takibi, plan-gerçek, fiyat listesi — ve sorularınızı düz metinle sorun. Hatalar, kopyalar, özetler — saniyeler içinde. Ayda 3 dosya ücretsiz, kart gerekmez.",
        "og_title": f"{b} — Excel tablolarınız sorulara cevap veriyor. Telegram’da",
        "og_description": "Bota tablo gönderin ve düz metinle sorun: toplam hataları, kopyalar, özetler — saniyeler içinde. Ayda 3 dosya ücretsiz.",
        "schema_desc": f"Telegram’da inşaat şirketleri için Excel AI analisti. Hesapları veritabanı yapar.",
        "nav_what": "Nedir", "nav_demo": "Demo", "nav_feat": "Özellikler", "nav_comp": "Karşılaştırma", "nav_plans": "Tarifeler", "nav_partners": "Ortaklar", "nav_bot": "Botu aç",
        "hero_h1": "Excel tablolarınız <em>sorulara cevap veriyor</em>. Telegram’da.",
        "hero_sub": "Bota malzeme takibi, plan-gerçek veya fiyat listesi gönderin — bir iş arkadaşına sorar gibi düz metinle sorun. Toplamlardaki hatalar, kopyalar, tedarikçi özetleri — saniyeler içinde.",
        "hero_cta": "Ücretsiz dene", "hero_note": "Ayda 3 dosya ücretsiz · kart yok · kurulum yok · eğitim yok",
        "chat_bot_label": "bot",
        "chat_u1": "📎 Materials_Lugovaya12.xlsx",
        "chat_b1": "✅ 603 satır, 11 sütun. Sorularınızı sorun!",
        "chat_u2": "Toplamın miktar × fiyat ile tutmadığı satırları bul",
        "chat_b2": "⚠️ 6 satırda sapma buldum:\n• Satır 376: Donatı А500С d16 — dosyada 4 550 856 ₽, hesaba göre 3 374 728 ₽, sapma +1 176 128 ₽\n• Satır 385: Harç М150 — +75 233 ₽…",
        "chat_u3": "Kopya var mı?", "chat_b3": "Evet, 3 tam kopya çifti: satırlar 25 ve 602, 11 ve 601, 60 ve 603.",
        "demo_h2": "Kendiniz görün", "demo_lead": "Dosya yükleme ve düz metin sorular — gerçek zamanlı, montaj yok.", "demo_label": "demo",
        "what_h2": "Bu nedir — basitçe",
        "what_lead": f"{b}, Telegram’da bir bottur: ona her zamanki Excel dosyanızı gönderirsiniz. Sonra soru yazarsınız: «mayıs ayında betona ne kadar harcadık?» — ve birkaç saniye içinde satır numaraları ve rakamlarla net cevap alırsınız. Formül ve pivot bilmeniz gerekmez.",
        "step1_h": "Dosyanız", "step1_p": "Herhangi bir tablo: malzeme takibi, cetvel, fiyat listeleri, plan-gerçek. Olduğu gibi.",
        "step2_h": "Sorunuz", "step2_p": "Sıradan kelimelerle, bir iş arkadaşına sorar gibi. Telefondan, şantiyeden.",
        "step3_h": "Net cevap", "step3_p": "Rakamları veritabanı hesaplar, yapay zekâ «göz kararı» değil. Her bulgu — satır numarasıyla.",
        "feat_h2": "Bot ne yapabilir", "feat_lead": "Excel’de saatlerinizi yiyen altı iş — bot saniyeler içinde yapar.",
        "f1_h": "Toplam hatalarını bulur", "f1_p": "Toplam, miktar × fiyata uymuyor mu? Bot her satırı bulur ve sapmayı gösterir.",
        "f2_h": "Kopyaları yakalar", "f2_p": "Çift irsaliyeler, tekrarlayan kalemler, boş fiyatlar — satır numaralarıyla listelenir.",
        "f3_h": "Özet çıkarır", "f3_p": "Tedarikçilere, şantiyelere, aylara, kategorilere göre — herhangi bir sütuna.",
        "f4_h": "Plan-gerçek ve bütçe aşımı", "f4_p": "«Nerede %10’dan fazla aşım var?» — saniyeler içinde liste, rakamlarla.",
        "f5_h": "Fiyat listelerini karşılaştırır", "f5_p": "Birkaç tedarikçinin fiyatlarını yükleyin — kimin daha ucuz diye sorun.",
        "f6_h": "Ödemeleri izler", "f6_p": "«Ne kadar ödenmedi ve kime?» — kendi tablonuzdan anlık tablo.",
        "chips_lead": "Örnek sorular:",
        "chips": ["Martta donatıya ne kadar harcandı?", "Toplamın tutmadığı satırları bul", "Kopya var mı?", "Tedarikçilere göre özet", "М150 tuğla kimin daha ucuz?", "Nerede %10’dan fazla aşım var?", "En pahalı 10 alım", "Ne kadar ödenmedi ve kime?", "Mayısta ТД Арсенал’dan ne aldık?", "B25 betonun aylara göre ortalama fiyatı", "Fiyatsız kalemler hangileri?", "Şantiyeye göre plan ve gerçeği karşılaştır"],
        "comp_h2": "Neden başka yerde yok",
        "comp_lead": "Telegram’da tablo AI analistinin doğrudan bir muadili yok. Copilot sık kapalı, ChatGPT yabancı kart ister ve dosyayı bütünüyle modele yollar; 1C/BI kurulumu aylar ve büyük bütçe demek.",
        "comp_col_1c": "1C / BI kurulumu", "yes": "Evet", "no": "Hayır", "partial": "Kısmen",
        "comp_r1": "Doğrudan erişilir, yabancı kart gerekmez", "comp_r1_copilot": "Hayır — kısıtlamalar",
        "comp_r2": "Soruları düz metinle anlar", "comp_r2_1c": "Hayır — raporları programcılar kurar",
        "comp_r3": "Doğru hesap (veritabanı sayar)", "comp_r3_gpt": "Hayır — rakam «uydurabilir»",
        "comp_r4": "Dosya bütünüyle modele GİTMEZ",
        "comp_r5": "Kurulum ve eğitim olmadan başlar", "comp_r5_us": "1 dakika", "comp_r5_copilot": "Günler", "comp_r5_gpt": "Saatler", "comp_r5_1c": "Aylar",
        "comp_r6": "Fiyat", "comp_r6_us": "0 ₽’den", "comp_r6_copilot": "~2 800 ₽/kişi/ay", "comp_r6_gpt": "~2 000 ₽/ay", "comp_r6_1c": "300 000 ₽’den",
        "who_h2": "Kime lazım", "who_lead": "Tablolarda yaşayan inşaat şirketindeki herkese.",
        "w1_h": "Satın alma", "w1_p": "Fiyat listesi karşılaştırması, en iyi fiyat, talep ve ödeme kontrolü.",
        "w2_h": "Şantiye şefi / PTO", "w2_p": "Malzeme, plan-gerçek, aşım — şantiyeden, telefondan.",
        "w3_h": "Müdür", "w3_p": "Her dosyada bir dakikada özet. Toplantı ve arama olmadan.",
        "w4_h": "Muhasebe", "w4_p": "Cetvel mutabakatı, ay kapanmadan sapma ve kopya arama.",
        "plans_h2": "Tarifeler",
        "plans_lead": "Ücretsiz başlayın — kart ve kayıt yok. Ücretli tarife için Telegram’dan yazın, bir saat içinde açarız. <b>Yıllık ödemede — iki ay hediye.</b>",
        "plan_free_name": "Ücretsiz", "plan_start_name": "Start", "plan_biz_name": "Business", "plan_team_name": "Takım",
        "per_mo": "/ay", "popular": "Popüler",
        "pf1": "Ayda 3 dosya", "pf2": "Dosya başına 15 soru", "pf3": "2 000 satıra kadar", "pf4": "Tüm analiz türleri",
        "ps1": "Ayda 30 dosya", "ps2": "Sınırsız soru", "ps3": "20 000 satıra kadar", "ps4": "Yıllık: 9 900 ₽ — 2 ay hediye",
        "pb1": "Dosya limiti yok", "pb2": "200 000 satıra kadar", "pb3": "İki dosya mutabakatı", "pb4": "КС-2 / КС-3 — yakında", "pb5": "Yıllık: 29 900 ₽ — 2 ay hediye",
        "pt1": "«Business»in tamamı", "pt2": "5 çalışan", "pt3": "Öncelikli destek", "pt4": "КС-2 / КС-3 — yakında", "pt5": "Yıllık: 69 000 ₽ — 2 ay hediye",
        "plan_start_tg": "Telegram’da başla", "plan_connect": "Telegram’da bağla",
        "implant_h": "Anahtar teslim kurulum — 20+ çalışanlı şirketler için",
        "implant_p": "Botu dosyalarınıza göre ayarlarız, tedarik ve PTO’yu eğitiriz, ilk ayı eşlik ederiz. 15 000 ₽’den + herhangi bir tarife.",
        "implant_cta": "Kurulumu konuşalım",
        "partners_h2": "Ortaklara — her ödemeden %25",
        "partners_lead": f"Muhasebe firmaları, 1C franchise, yapı malzemesi tedarikçileri: {b} önerin — getirilen müşterinin ilk yıl ödemelerinden %25 alın.",
        "pa1_h": "Muhasebe", "pa1_p": "İnşaat müşterileriniz hatalı tablo getirmeyi bırakır — siz öneriden kazanırsınız.",
        "pa2_h": "1C franchise", "pa2_p": "Kurulumlara basit ek: teknik destek bizde.",
        "pa3_h": "Yapı malzemesi tedarikçileri", "pa3_p": "Alıcılarınız araç alır, siz yüzde ve sadakat.",
        "partners_cta": "Ortak ol", "faq_h2": "Sık sorulan sorular",
        "faq": [
            ("Verilerim nereye gidiyor? Güvenli mi?", "Dosya korumalı sunucuda izole veritabanına yüklenir. Tablo bütünüyle modele gitmez. Hesapları veritabanı yapar."),
            ("Hangi dosyalar desteklenir?", ".xlsx, .xls, .csv ve .ods — Excel, LibreOffice, 1C. 20 MB’a kadar."),
            ("«Eğri» tablo. Başarır mı?", "Evet. Bot boşluklu sayıları, iki satırlı başlıkları ve yazım hatalarını anlar."),
            ("Microsoft Office gerekir mi?", "Hayır. Bot dosyayı kendisi okur."),
            ("Ne kadar?", "Ücretsiz tarife sonsuza kadar: ayda 3 dosya. Ücretli — sabit fiyat. Yıllıkta iki ay hediye."),
            ("Türkiye, Gürcistan, Ermenistan, Kazakistan’da çalışır mı?", "Evet, Telegram’ın çalıştığı her yerde. Cevaplar mesajınızın dilinde."),
            ("Şirketime özel bir şey lazımsa?", "Yazın — uyarlarız: raporlar, entegrasyonlar, eğitim. 20+ kişi için anahtar teslim kurulum."),
        ],
        "faq_schema": [
            ("Güvenlik?", "Dosya izole DB’de. Modele bütün gitmez."),
            ("Dosyalar?", "xlsx, xls, csv, ods 20 MB’a kadar."),
            ("Office?", "Gerekmez."),
            ("Fiyat?", "Ayda 3 dosya ücretsiz. Ücretli 990 ₽’den."),
            ("Ülkeler?", "Telegram olan her yer."),
        ],
        "cta_h2": "Kendi dosyanızda hemen deneyin",
        "cta_p": "Tabloyu yükleyin — bir dakikada ilk cevabı alın. Ücretsiz, kart yok.",
        "cta_btn": "Telegram’da botu aç",
        "footer_articles": "Yazılar", "art1": "Excel hataları", "art2": "malzeme takibi", "art3": "Excel için yapay zekâ",
        "footer_docs": "Belgeler", "privacy": "Gizlilik politikası", "terms": "Kullanım koşulları",
        "footer_contact": "Bağlantı ve sorular", "footer_cis": "BDT için",
    }


def write_sitemap():
    alts = "\n".join(
        f'  <xhtml:link rel="alternate" hreflang="{c}" href="https://stroytablica.ru{p if p != "/" else "/"}"/>'
        for c, p, _, _ in LANGS
    )
    alts += '\n  <xhtml:link rel="alternate" hreflang="x-default" href="https://stroytablica.ru/"/>'
    urls = []
    for c, p, _, _ in LANGS:
        loc = f"https://stroytablica.ru{p if p != '/' else '/'}"
        pri = "1.0" if c == "ru" else "0.95"
        urls.append(f"<url>\n  <loc>{loc}</loc>\n{alts}\n  <changefreq>weekly</changefreq><priority>{pri}</priority>\n</url>")
    for slug in ("oshibki-v-smete-excel.html", "uchet-materialov-excel.html", "neyroset-dlya-excel.html"):
        urls.append(f'<url><loc>https://stroytablica.ru/{slug}</loc><changefreq>monthly</changefreq><priority>0.8</priority></url>')
    body = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">\n'
    body += "\n".join(urls) + "\n</urlset>\n"
    (ROOT / "sitemap.xml").write_text(body, encoding="utf-8")


def write_bot_i18n():
    langs = [c for c, *_ in LANGS]
    md = f"""# Бот: мультиязычность ({" / ".join(x.upper() for x in langs)})

## Стандартный подход (как у нормальных Telegram-ботов)

**Приоритет определения `ui_lang`:**

1. **Явный выбор** — `/lang` или deep-link `?start=lang_XX` (с лендинга) → сохранить в `app.users.ui_lang`, больше не трогать автоматически.
2. **Telegram `from.language_code`** при **первом** `/start` (создание пользователя):
   - `ru` → ru  
   - `uk` → uk  
   - `be` → be  
   - `kk` → kk  
   - `ka` → ka  
   - `hy` → hy  
   - `tr` → tr  
   - `en` / прочее → **ru** (дефолт продукта; ответы LLM всё равно на языке вопроса)
3. **Язык сообщения** — system prompt Claude: *всегда отвечать на языке текущего вопроса пользователя* (даже если UI на другом).
4. OS/телефон **напрямую не читаем** — у Telegram-бота единственный надёжный сигнал языка клиента это `language_code` профиля TG + текст сообщения. Это и есть «как обычно».

Лендинг deep-links:
"""
    for c, p, code, name in LANGS:
        md += f"- {code} ({name}): `https://t.me/stroytablica_bot?start=lang_{c}`\n"
    md += f"""
## Миграция

```sql
alter table app.users
  add column if not exists ui_lang text not null default 'ru';
-- при необходимости ослабить check:
-- alter table app.users drop constraint if exists users_ui_lang_check;
-- alter table app.users add constraint users_ui_lang_check check (ui_lang in ({", ".join(repr(x) for x in langs)}));
```

## UI-строки

Все hardcoded-сообщения (`/start`, лимиты, ошибки, /tariffs, /support) — словарь `I18N[ui_lang][key]` с fallback на `ru`.

**Бренд в UI** (как на лендинге):
"""
    for c, name in BRAND.items():
        md += f"- {c}: {name}\n"
    md += """
Убрать «по-русски» / «только на русском» из всех локалей.

## System prompt (вопросы по файлу)

```
Respond in the same language as the user's current question
(Russian, Ukrainian, Belarusian, Kazakh, Georgian, Armenian, Turkish, etc.).
Keep numbers, row IDs and column names exactly as in the data.
UI language preference: {ui_lang} — use it only for fixed UI templates, not for forcing answer language.
```

## Команды / regex

Русские триггеры сверки + синонимы (uk/be/kk/ka/hy/tr) или роутинг через LLM.

## Критерии

1. Новый user с TG language_code=uk → welcome на украинском (бренд БудТаблиця).
2. `/start lang_kk` с лендинга → казахский UI.
3. Вопрос на грузинском → ответ на грузинском, даже если ui_lang=ru.
4. `/lang` позволяет сменить вручную.
5. Реферальный `/start CODE` не ломается.
"""
    (ROOT / "BOT_I18N.md").write_text(md, encoding="utf-8")


def main():
    builders = {
        "ru": content_ru,
        "uk": content_uk,
        "be": content_be,
        "kk": content_kk,
        "ka": content_ka,
        "hy": content_hy,
        "tr": content_tr,
    }
    for code, path, _, _ in LANGS:
        L = builders[code]()
        html = page(L)
        if path == "/":
            out = ROOT / "index.html"
        else:
            d = ROOT / path.strip("/")
            d.mkdir(parents=True, exist_ok=True)
            out = d / "index.html"
        out.write_text(html, encoding="utf-8")
        # sanity
        assert BRAND[code] in html
        assert "lang-dd" in html
        assert "по-русски" not in html and "По-русски" not in html
        print(f"OK {code}: {out.relative_to(ROOT)} brand={BRAND[code]!r} bytes={len(html.encode())}")
    write_sitemap()
    write_bot_i18n()
    print("sitemap + BOT_I18N updated")


if __name__ == "__main__":
    main()
