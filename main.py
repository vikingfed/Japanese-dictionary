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
        return templates.TemplateResponse("error.html", {
            'request': request,
            'error_message': f'Иероглиф "{hieroglyph}" не найден в словаре',
            'back_url': '/'
        }, status_code=404)

    return templates.TemplateResponse("search_result.html", {
        'request': request,
        'data': searched_data
    })


@app.get('/add-hieroglyph')
def add_hieroglyph_form(request: Request):
    return templates.TemplateResponse('add_hieroglyph.html', {'request': request})


@app.post('/add-hieroglyph')
def add_full_hieroglyph(
        request: Request,
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
        return templates.TemplateResponse("error.html", {
            'request': request,
            'error_message': 'Добавьте хотя бы один вариант использования',
            'back_url': '/add-hieroglyph'
        }, status_code=400)

    try:
        hieroglyph_data = CreateHieroglyph(
            hieroglyph=hieroglyph,
            usages=[Usage(**u) for u in usages]
        )
    except Exception as ex:
        return templates.TemplateResponse("error.html", {
            'request': request,
            'error_message': f'Некорректные данные: {ex}',
            'back_url': '/add-hieroglyph'
        }, status_code=400)

    try:
        database.add_card(hieroglyph_data.hieroglyph, usages)
        return RedirectResponse(url='/', status_code=303)
    except Exception as ex:
        return templates.TemplateResponse("error.html", {
            'request': request,
            'error_message': f'Ошибка при добавлении в базу: {ex}',
            'back_url': '/add-hieroglyph'
        }, status_code=500)


@app.get('/add-usage')
def add_usage_form(request: Request):
    return templates.TemplateResponse('add_usage.html', {'request': request})


@app.post('/add-usage')
def add_single_usage(
        request: Request,
        hieroglyph: str = Form(...),
        usage: str = Form(...),
        reading: str = Form(...),
        translation: str = Form(...)
):
    try:
        usage_data = Usage(usage=usage, reading=reading, translation=translation)
    except Exception as ex:
        return templates.TemplateResponse("error.html", {
            'request': request,
            'error_message': f'Некорректные данные: {ex}',
            'back_url': '/add-usage'
        }, status_code=400)


    success = database.add_one_usage(hieroglyph, usage_data.usage, usage_data.reading, usage_data.translation)
    if not success:
        return templates.TemplateResponse("error.html", {
            'request': request,
            'error_message': f'Иероглиф "{hieroglyph}" не найден в словаре',
            'back_url': '/add-usage'
        }, status_code=404)

    return RedirectResponse(url='/', status_code=303)


@app.get('/edit-usage')
def edit_usage_form(request: Request):
    return templates.TemplateResponse('edit_usage.html', {'request': request})


@app.post('/edit-usage')
def edit_usage(
    request: Request,
    usage_id: int = Form(...),
    new_reading: Optional[str] = Form(None),
    new_translation: Optional[str] = Form(None)
):
    if not new_reading and not new_translation:
        return templates.TemplateResponse("error.html", {
            'request': request,
            'error_message': 'Укажите хотя бы одно поле для изменения',
            'back_url': '/edit-usage'
        }, status_code=400)

    try:
        update_data = UpdateUsage(new_reading=new_reading, new_translation=new_translation)
    except Exception as ex:
        return templates.TemplateResponse("error.html", {
            'request': request,
            'error_message': f'Некорректные данные: {ex}',
            'back_url': '/edit-usage'
        }, status_code=400)

    success = database.edit_card_by_usage_id(usage_id, update_data.new_reading, update_data.new_translation)

    if not success:
        return templates.TemplateResponse("error.html", {
            'request': request,
            'error_message': f'Вариант использования с ID {usage_id} не найден',
            'back_url': '/edit-usage'
        }, status_code=404)

    return RedirectResponse(url='/', status_code=303)


@app.post('/delete-hieroglyph')
def delete_hieroglyph_info(
        request: Request,
        hieroglyph: str = Form(...)
):
    success = database.delete_hieroglyph(hieroglyph)

    if not success:
        return templates.TemplateResponse("error.html", {
            'request': request,
            'error_message': f'Иероглиф "{hieroglyph}" не найден',
            'back_url': '/'
        }, status_code=404)

    return RedirectResponse(url='/', status_code=303)






