from fastapi import FastAPI, Request, Form, HTTPException # Request для формальности у меня в проекте
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from contextlib import asynccontextmanager
import database
from typing import List, Optional
from pydantic import BaseModel

class Usage(BaseModel):
    usage: str
    reading: str
    translation: str

class CreateHieroglyph(BaseModel):
    hieroglyph: str
    usages: List[Usage]

class UpdateUsage(BaseModel):
    new_reading: Optional[str] = None
    new_translation: Optional[str] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    database.init_database()
    print('Инициализировали БД')
    yield

app = FastAPI(lifespan=lifespan)
templates = Jinja2Templates(directory='templates')


@app.get('/')
def read_root(request: Request):
    all_words = database.get_all_hieroglyphs()
    return templates.TemplateResponse('index.html', {
        'request': request,
        'words': all_words
    })


@app.post('/search')
def search_hieroglyph(
    request: Request,
    hieroglyph: str = Form(...)
):
    searched_data = database.get_by_hieroglyph(hieroglyph)
    if not searched_data:
        raise HTTPException(status_code=404, detail='Что ты там ищешь-то?')

    return templates.TemplateResponse("search_result.html", {
        'request': request,
        'data': searched_data
    })


@app.get('/add-hieroglyph')
def add_hieroglyph_form(request: Request):
    return templates.TemplateResponse('add_hieroglyph.html', {'request': request})


@app.post('/add-hieroglyph')
def add_full_hieroglyph(
        hieroglyph: str = Form(...),
        usage: List[str] = Form(...),
        reading: List[str] = Form(...),
        translation: List[str] = Form(...)
):
    usages = []
    for i in range(len(usage)):
        if usage[i] and reading[i] and translation[i]:
            usages.append({
                'usage': usage[i],
                "reading": reading[i],
                "translation": translation[i]
            })

    if not usages:
        raise HTTPException(status_code=400, detail='А где?')

    try:
        hieroglyph_data = CreateHieroglyph(
            hieroglyph=hieroglyph,
            usages=[Usage(**u) for u in usages]
        )
    except Exception as ex:
        raise HTTPException(status_code=400, detail=f'Некорректно введены данные: {ex}')


    database.add_card(hieroglyph_data.hieroglyph, usages)
    return RedirectResponse(url='/', status_code=303)


@app.get('/add-usage')
def add_usage_form(request: Request):
    return templates.TemplateResponse('add_usage.html', {'request': request})


@app.post('/add-usage')
def add_single_usage(
        hieroglyph: str = Form(...),
        usage: str = Form(...),
        reading: str = Form(...),
        translation: str = Form(...)
):
    try:
        usage_data = Usage(usage=usage, reading=reading, translation=translation)
    except Exception as ex:
        raise HTTPException(status_code=400, detail=f'Некорректно введены данные: {ex}')

    database.add_one_usage(hieroglyph, usage_data.usage, usage_data.reading, usage_data.translation)
    return RedirectResponse(url='/', status_code=303)


@app.get('/edit-usage')
def edit_usage_form(request: Request):
    return templates.TemplateResponse('edit_usage.html', {'request': request})


@app.post('/edit-usage')
def edit_usage(
    usage_id: int,
    new_reading: Optional[str] = None,
    new_translation: Optional[str] = None
):
    try:
        update_data = UpdateUsage(new_reading=new_reading, new_translation=new_translation)
    except Exception as ex:
        raise HTTPException(status_code=400, detail=f'Некорректно введены данные: {ex}')

    database.edit_card_by_usage_id(usage_id, update_data.new_reading, update_data.new_translation)
    return RedirectResponse(url='/', status_code=303)





