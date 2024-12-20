from openai import OpenAI
from fastapi import FastAPI, Form, Request, WebSocket
from typing import Annotated
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import os
from dotenv import load_dotenv
from openai import OpenAIError

load_dotenv()

openai = OpenAI(
    api_key = os.getenv('OPENAI_API_SECRET_KEY')
)

app = FastAPI()

templates = Jinja2Templates(directory="templates")

chat_responses = []

@app.get("/", response_class=HTMLResponse)
async def chat_page(request: Request):
    return templates.TemplateResponse("home.html", {"request": request, "chat_responses": chat_responses})


chat_log = [{'role': 'system',
             'content': 'You Are a professional trader that has a lot 50+ years experience in indonesia stock exchange market that always has good analysis to which market to invest every year to get maximum profit.'
             }]


@app.websocket("/ws")
async def chat(websocket: WebSocket):

    await websocket.accept()

    while True:
        user_input = await websocket.receive_text()
        chat_log.append({'role': 'user', 'content': user_input})
        chat_responses.append(user_input)

        try:
            response = openai.chat.completions.create(
                model='gpt-4o-mini',
                messages=chat_log,
                temperature=0.6,
                max_tokens=100,
                stream=True
            )

            ai_response = ''

            for chunk in response:
                if chunk.choices[0].delta.content is not None:
                    ai_response += chunk.choices[0].delta.content
                    await websocket.send_text(chunk.choices[0].delta.content)
            chat_responses.append(ai_response)

        except Exception as e:
            await websocket.send_text(f'Error: {str(e)}')
            break


@app.post("/", response_class=HTMLResponse)
async def chat(request: Request, user_input: Annotated[str, Form()]):

    chat_log.append({'role': 'user', 'content': user_input})
    chat_responses.append(user_input)

    response = openai.chat.completions.create(
        model='gpt-4o-mini',
        messages=chat_log,
        max_tokens=100,
        temperature=0.6
    )

    bot_response = response.choices[0].message.content
    chat_log.append({'role': 'assistant', 'content': bot_response})
    chat_responses.append(bot_response)

    return templates.TemplateResponse("home.html", {"request": request, "chat_responses": chat_responses})


@app.get("/image", response_class=HTMLResponse)
async def image_page(request: Request):
    return templates.TemplateResponse("image.html", {"request": request})


@app.post("/image", response_class=HTMLResponse)
async def create_image(request: Request, user_input: Annotated[str, Form()]):
    try:
        response = openai.images.generate(
            prompt=user_input,
            n=1,
            size="256x256"
        )
        image_url = response.data[0].url
        return templates.TemplateResponse("image.html", {"request": request, "image_url": image_url})
    except OpenAIError as e:
        # Handle OpenAI-specific errors
        error_message = f"An error occurred: {e}"
        return templates.TemplateResponse("image.html", {"request": request, "error_message": error_message})
    except Exception as e:
        # Handle other unforeseen errors
        error_message = f"An unexpected error occurred: {e}"
        return templates.TemplateResponse("image.html", {"request": request, "error_message": error_message})