"""Собирает index.html из tools/menu.json. Запуск: python tools/build.py"""
import json
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MENU = json.loads((ROOT / "tools" / "menu.json").read_text(encoding="utf-8"))
SCHEMA = "https://schema.org/"
# Сайт опубликован на GitHub Pages в подпапке, поэтому все локальные пути начинаются с неё
BASE = "/MyFamilyMenu/"

HERO_MAIN = "1504674900247-0877df9cc836"
HERO_ROUND = "1648726445011-9fbf3a5ddb90"
HERO_SMALL = "1571877227200-a0d98ea607e9"

SITE_URL = "https://rotaxxx123soft-stack.github.io/MyFamilyMenu/"
IMAGES = ROOT / "images"
needed_images = set()


def photo_url(photo, width):
    """Фото хранятся в репозитории: сторонний сервер картинок доступен не во всех сетях."""
    needed_images.add((photo, width))
    return f"{BASE}images/{photo}-{width}.jpg"


def download_missing_images():
    """Скачивает с Unsplash фото нужных размеров, которых ещё нет в папке images."""
    IMAGES.mkdir(exist_ok=True)
    missing = [(p, w) for p, w in sorted(needed_images) if not (IMAGES / f"{p}-{w}.jpg").exists()]

    def fetch(item):
        photo, width = item
        url = f"https://images.unsplash.com/photo-{photo}?fm=jpg&fit=crop&w={width}&q=72"
        req = urllib.request.Request(url, headers={"User-Agent": "MyFamilyMenu build script"})
        with urllib.request.urlopen(req, timeout=60) as resp:
            if not resp.headers.get("Content-Type", "").startswith("image/jpeg"):
                raise RuntimeError(f"{url}: не JPEG")
            (IMAGES / f"{photo}-{width}.jpg").write_bytes(resp.read())

    with ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(fetch, missing))
    return len(missing)


def srcset(photo, widths):
    return ", ".join(f"{photo_url(photo, w)} {w}w" for w in widths)


def price_html(price):
    return (
        f'<span class="price" itemprop="offers" itemscope itemtype="{SCHEMA}Offer">'
        f'<meta itemprop="price" content="{price}"><meta itemprop="priceCurrency" content="RUB">'
        f"{price:,}".replace(",", "&nbsp;") + "&nbsp;₽</span>"
    )


def dish_html(dish, index, feature, sizes):
    widths = (480, 800, 1200) if feature else (320, 480, 720)
    classes = "dish dish--feature reveal" if feature else "dish reveal"
    name = escape(dish["name"])
    focus = f' style="object-position:{dish["focus"]}"' if dish.get("focus") else ""
    return f"""
        <article class="{classes}" style="--i:{index % 3}" itemprop="hasMenuItem" itemscope itemtype="{SCHEMA}MenuItem">
          <div class="dish__photo">
            <img src="{photo_url(dish["photo"], widths[1])}" srcset="{srcset(dish["photo"], widths)}" sizes="{sizes}"
                 width="800" height="600" alt="{name}" loading="lazy" decoding="async" itemprop="image"{focus}>
          </div>
          <div class="dish__body">
            <h3 class="dish__name" itemprop="name">{name}</h3>
            <p class="dish__desc" itemprop="description">{escape(dish["desc"])}</p>
            <p class="dish__meta"><span class="dish__size">{escape(dish["size"])}</span>{price_html(dish["price"])}</p>
          </div>
        </article>"""


def sides_html(sides):
    rows = "".join(
        f"""
            <li class="side" itemprop="hasMenuItem" itemscope itemtype="{SCHEMA}MenuItem">
              <div>
                <h4 class="side__name" itemprop="name">{escape(item["name"])}</h4>
                <p class="side__desc" itemprop="description">{escape(item["desc"])}</p>
              </div>
              <div class="side__price">
                {price_html(item["price"])}
                <span class="dish__size">{escape(item["size"])}</span>
              </div>
            </li>"""
        for item in sides["items"]
    )
    return f"""
      <div class="sides reveal" itemprop="hasMenuSection" itemscope itemtype="{SCHEMA}MenuSection">
        <div class="sides__photo">
          <img src="{photo_url(sides["photo"], 800)}" srcset="{srcset(sides["photo"], (480, 800))}"
               sizes="(min-width: 900px) 38vw, 100vw" width="800" height="600"
               alt="{escape(sides["photo_alt"])}" loading="lazy" decoding="async">
        </div>
        <div class="sides__body">
          <h3 class="sides__title" itemprop="name">{escape(sides["title"])}</h3>
          <ul class="sides__list">{rows}
          </ul>
        </div>
      </div>"""


def section_html(section, number):
    compact = section.get("layout") == "compact"
    tone = f" section--{section['tone']}" if section.get("tone") else ""
    sizes = "(min-width: 1024px) 25vw, (min-width: 640px) 33vw, 50vw" if compact else "(min-width: 1024px) 33vw, (min-width: 640px) 50vw, 40vw"
    feature_sizes = "(min-width: 1024px) 40vw, (min-width: 640px) 55vw, 100vw"
    cards = "".join(
        dish_html(d, i, not compact and i == 0, feature_sizes if not compact and i == 0 else sizes)
        for i, d in enumerate(section["dishes"])
    )
    sides = sides_html(section["sides"]) if section.get("sides") else ""
    grid = "grid grid--compact" if compact else "grid"
    return f"""
    <section class="section{tone}" id="{section["id"]}" aria-labelledby="{section["id"]}-title"
             itemprop="hasMenuSection" itemscope itemtype="{SCHEMA}MenuSection">
      <div class="wrap">
        <header class="section__head reveal">
          <span class="section__num" aria-hidden="true">{number:02d}</span>
          <h2 class="section__title" id="{section["id"]}-title" itemprop="name">{escape(section["title"])}</h2>
          <p class="section__note">{escape(section["note"])}</p>
        </header>
        <div class="{grid}">{cards}
        </div>{sides}
      </div>
    </section>"""


def count_items(sections):
    total = 0
    for section in sections:
        total += len(section["dishes"]) + len(section.get("sides", {}).get("items", []))
    return total


def plural(n, one, few, many):
    if n % 10 == 1 and n % 100 != 11:
        return one
    if 2 <= n % 10 <= 4 and not 12 <= n % 100 <= 14:
        return few
    return many


sections = MENU["sections"]
nav_links = "\n".join(f'          <li><a href="#{s["id"]}">{escape(s["nav"])}</a></li>' for s in sections)
foot_links = "\n".join(f'          <li><a href="#{s["id"]}">{escape(s["title"])}</a></li>' for s in sections)
body = "".join(section_html(s, i + 1) for i, s in enumerate(sections))
total = count_items(sections)
positions = f"{total} {plural(total, 'позиция', 'позиции', 'позиций')}"
description = (
    "Онлайн-меню кафе My family: супы, основные блюда, фастфуд, салаты, десерты и напитки. "
    "Состав, вес порции и цена каждого блюда."
)

page = f"""<!doctype html>
<html lang="ru">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
  <title>Меню кафе My family — супы, горячее, фастфуд, десерты и напитки</title>
  <meta name="description" content="{description}">
  <meta name="theme-color" content="#F6EFE3">
  <meta property="og:type" content="website">
  <meta property="og:locale" content="ru_RU">
  <meta property="og:site_name" content="My family">
  <meta property="og:title" content="Меню кафе My family">
  <meta property="og:description" content="{description}">
  <meta property="og:image" content="{SITE_URL}images/{HERO_MAIN}-1200.jpg">
  <meta name="twitter:card" content="summary_large_image">
  <link rel="icon" href="{BASE}favicon.svg" type="image/svg+xml">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,500;0,600;1,500&family=Manrope:wght@400;500;700&display=swap">
  <link rel="stylesheet" href="{BASE}css/style.css">
  <script src="{BASE}js/main.js" defer></script>
  <script type="application/ld+json">
  {{"@context":"{SCHEMA}","@type":"CafeOrCoffeeShop","name":"My family","description":"{description}","hasMenu":"#menu"}}
  </script>
</head>
<body>
  <a class="skip" href="#menu">К меню</a>

  <header class="site-header" id="top">
    <div class="wrap site-header__inner">
      <a class="logo" href="#top" aria-label="My family — в начало страницы">My family</a>
      <nav class="cats" aria-label="Разделы меню">
        <ul class="cats__list">
{nav_links}
        </ul>
      </nav>
    </div>
  </header>

  <section class="hero" aria-labelledby="hero-title">
    <div class="wrap hero__grid">
      <div class="hero__text">
        <p class="hero__eyebrow">Кафе My family</p>
        <h1 class="hero__title" id="hero-title">Меню</h1>
        <p class="hero__lead">Супы, горячие блюда, фастфуд, салаты, десерты и&nbsp;напитки. Для каждого блюда указаны состав, вес порции и&nbsp;цена.</p>
        <ul class="hero__facts">
          <li>{len(sections)} разделов</li>
          <li>{positions}</li>
          <li>Цены в рублях</li>
        </ul>
      </div>
      <div class="hero__media">
        <figure class="hero__img hero__img--main">
          <img src="{photo_url(HERO_MAIN, 1000)}" srcset="{srcset(HERO_MAIN, (640, 1000, 1400))}"
               sizes="(min-width: 900px) 40vw, 100vw" width="1000" height="1250"
               alt="Мясо, зелень и специи на тёмном столе" fetchpriority="high" decoding="async">
        </figure>
        <figure class="hero__img hero__img--round">
          <img src="{photo_url(HERO_ROUND, 480)}" width="480" height="480" alt="Тарелка борща со сметаной и зеленью" decoding="async">
        </figure>
        <figure class="hero__img hero__img--small">
          <img src="{photo_url(HERO_SMALL, 560)}" width="560" height="420" alt="Порция тирамису" decoding="async">
        </figure>
      </div>
    </div>
  </section>

  <main id="menu" itemscope itemtype="{SCHEMA}Menu">
    <meta itemprop="name" content="Меню кафе My family">{body}
  </main>

  <footer class="site-footer">
    <div class="wrap site-footer__grid">
      <p class="site-footer__logo">My family</p>
      <nav aria-label="Разделы меню в подвале">
        <ul class="site-footer__nav">
{foot_links}
        </ul>
      </nav>
      <div class="site-footer__notes">
        <p>Цены указаны в рублях. Вес порции — в готовом виде.</p>
        <p>Об аллергенах и составе блюд можно спросить у официанта.</p>
        <p>Подача может отличаться от фотографий. Фото: Unsplash.</p>
      </div>
    </div>
  </footer>
</body>
</html>
"""

needed_images.add((HERO_MAIN, 1200))  # превью ссылки в мессенджерах
downloaded = download_missing_images()

(ROOT / "index.html").write_text(page, encoding="utf-8")
print(f"index.html: {total} позиций, {len(page) // 1024} КБ; скачано фото: {downloaded}")
