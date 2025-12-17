import json
from pathlib import Path
from urllib.parse import urlencode

from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# ==============================
# Папки и файлы проекта
# ==============================
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"

FILMS_FILE = DATA_DIR / "films.json"
STATS_FILE = DATA_DIR / "statistics.json"

# ==============================
# Константы
# ==============================
PER_PAGE = 10  # количество фильмов на странице

# ==============================
# Учебная переменная для хранения отфильтрованных фильмов
# Используется для однопользовательского режима
# ==============================
filtered_films: list[dict] = []

# ==============================
# FastAPI app
# ==============================
app = FastAPI()

# Подключаем static файлы
app.mount("/static", StaticFiles(directory="static"), name="static")

# Jinja2 шаблоны
templates = Jinja2Templates(directory="templates")


# ==============================
# Вспомогательные функции
# ==============================
def load_json(path: Path) -> list[dict]:
    """
    Загружает JSON-файл и возвращает данные как список словарей.

    :param path: Путь к файлу JSON
    :return: Список словарей
    """
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def paginate(items: list[dict], page: int, per_page: int = PER_PAGE) -> dict:
    """
    Пагинация списка элементов.

    :param items: Список элементов
    :param page: Текущая страница
    :param per_page: Количество элементов на странице
    :return: Словарь с информацией для пагинации
    """
    total = len(items)
    start = (page - 1) * per_page
    end = start + per_page
    sliced = items[start:end]

    # Для отладки можно раскомментировать
    # print('total:', total, 'start:', start, 'end:', end)

    return {
        "items": sliced,
        "has_prev": page > 1,
        "has_next": end < total,
        "page": page,
        "offset": start,
    }


# ==============================
# Эндпойнты
# ==============================

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    """
    Главная страница проекта.
    """
    return templates.TemplateResponse(
        "home.html",
        {"request": request, "title": "Home"},
    )


@app.get("/genres", response_class=HTMLResponse)
def genres(request: Request):
    """
    Страница со списком жанров всех фильмов.
    """
    films = load_json(FILMS_FILE)
    genres_list = sorted({film["genre"] for film in films})

    return templates.TemplateResponse(
        "genres.html",
        {
            "request": request,
            "title": "Genres",
            "genres": genres_list,
        },
    )


@app.get("/genres/{genre}", response_class=HTMLResponse)
def films_by_genre(request: Request, genre: str, page: int = 1):
    """
    Страница со списком фильмов конкретного жанра с пагинацией.

    :param genre: Название жанра
    :param page: Текущая страница пагинации
    """
    films = load_json(FILMS_FILE)

    # Обновляем глобальный список для однопользовательского варианта
    global filtered_films
    filtered_films = [f for f in films if f["genre"] == genre]

    pagination = paginate(filtered_films, page)

    return templates.TemplateResponse(
        "keyword.html",
        {
            "request": request,
            "title": f"Genre: {genre}",
            "items": pagination["items"],
            "columns": ["title", "description", "genre", "year"],
            "page": pagination["page"],
            "has_prev": pagination["has_prev"],
            "has_next": pagination["has_next"],
            "offset": pagination["offset"],
        },
    )


@app.post("/search/keyword", response_class=HTMLResponse)
def keyword_search(keyword: str = Form(...)):
    """
    POST-эндпойнт поиска фильмов по ключевому слову в названии.
    Сохраняет результат в глобальную переменную filtered_films.
    Делает редирект на GET-эндпойнт для отображения с пагинацией (PRG-паттерн).
    """
    kw_lower = keyword.lower()
    films = load_json(FILMS_FILE)

    global filtered_films
    filtered_films = [f for f in films if kw_lower in f["title"].lower()]

    return RedirectResponse(url="/search/keyword", status_code=303)


@app.get("/search/keyword", response_class=HTMLResponse)
def keyword_form(request: Request, page: int = 1):
    """
    GET-эндпойнт отображения результатов поиска по ключевому слову с пагинацией.
    """
    pagination = paginate(filtered_films, page)

    return templates.TemplateResponse(
        "keyword.html",
        {
            "request": request,
            "title": "Search by keyword",
            "items": pagination["items"],
            "columns": ["title", "description", "genre", "year"],
            "page": pagination["page"],
            "has_prev": pagination["has_prev"],
            "has_next": pagination["has_next"],
            "offset": pagination["offset"],
        },
    )


@app.post("/search/year")
def year_form_submit(year_from: int = Form(...), year_to: int = Form(...)):
    """
    POST-эндпойнт поиска фильмов по году выпуска.
    Сохраняет результат в глобальную переменную filtered_films.
    Делает редирект на GET-эндпойнт для отображения с пагинацией.
    """
    global filtered_films
    films = load_json(FILMS_FILE)
    filtered_films = [f for f in films if year_from <= f["year"] <= year_to]

    return RedirectResponse(url="/search/year", status_code=303)


@app.get("/search/year", response_class=HTMLResponse)
def year_search(request: Request, page: int = 1):
    """
    GET-эндпойнт отображения результатов поиска по годам с пагинацией.
    """
    pagination = paginate(filtered_films, page)

    return templates.TemplateResponse(
        "year.html",
        {
            "request": request,
            "items": pagination["items"],
            "columns": ["title", "description", "genre", "year"],
            "page": pagination["page"],
            "has_prev": pagination["has_prev"],
            "has_next": pagination["has_next"],
            "offset": pagination["offset"],
        },
    )


@app.get("/statistics", response_class=HTMLResponse)
def statistics(request: Request):
    """
    Страница статистики (прочитанные из файла statistics.json).
    """
    stats = load_json(STATS_FILE)

    return templates.TemplateResponse(
        "statistics.html",
        {
            "request": request,
            "title": "Statistics",
            "stats": stats,
        },
    )
