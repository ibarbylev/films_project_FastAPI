import json
from pathlib import Path

from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from urllib.parse import urlencode

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"

FILMS_FILE = DATA_DIR / "films.json"
STATS_FILE = DATA_DIR / "statistics.json"

PER_PAGE = 10

filtered_films: list[dict] = []

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


def load_json(path: Path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def paginate(items, page: int, per_page: int = PER_PAGE):
    total = len(items)

    start = (page - 1) * per_page
    end = start + per_page

    sliced = items[start:end]

    print('total:', total, 'start:', start, 'end:', end)
    return {
        "items": sliced,
        "has_prev": page > 1,
        "has_next": end < total,
        "page": page,
        "offset": start,
    }


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(
        "home.html",
        {
            "request": request,
            "title": "Home",
        },
    )


@app.get("/genres", response_class=HTMLResponse)
def genres(request: Request):
    films = load_json(FILMS_FILE)

    genres = sorted({film["genre"] for film in films})

    return templates.TemplateResponse(
        "genres.html",
        {
            "request": request,
            "title": "Genres",
            "genres": genres,
        },
    )


@app.get("/genres/{genre}", response_class=HTMLResponse)
def films_by_genre(request: Request, genre: str, page: int = 1):
    films = load_json(FILMS_FILE)

    filtered = [f for f in films if f["genre"] == genre]

    pagination = paginate(filtered, page)

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


@app.get("/search/keyword", response_class=HTMLResponse)
def keyword_form(request: Request):
    return templates.TemplateResponse(
        "keyword.html",
        {
            "request": request,
            "title": "Search by keyword",
            "items": [],
        },
    )



@app.post("/search/keyword", response_class=HTMLResponse)
def keyword_search(
    request: Request,
    keyword: str = Form(...),
    page: int = 1,
):
    films = load_json(FILMS_FILE)

    keyword_lower = keyword.lower()

    filtered = [
        f for f in films
        if keyword_lower in f["title"].lower()
    ]

    pagination = paginate(filtered, page)

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


# POST: фильтруем и сохраняем
@app.post("/search/year")
def year_form_submit(
    year_from: int = Form(...),
    year_to: int = Form(...),
):
    global filtered_films
    films = load_json("data/films.json")  # ваша функция чтения файлов
    filtered_films = [
        f for f in films
        if year_from <= f["year"] <= year_to
    ]
    return RedirectResponse(url="/search/year", status_code=303)

# GET: просто отображаем с пагинацией
@app.get("/search/year", response_class=HTMLResponse)
def year_search(request: Request, page: int = 1):
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
    stats = load_json(STATS_FILE)

    return templates.TemplateResponse(
        "statistics.html",
        {
            "request": request,
            "title": "Statistics",
            "stats": stats,
        },
    )
