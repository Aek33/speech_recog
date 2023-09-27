import requests
from fastapi import FastAPI, Request, BackgroundTasks
from speechRecognizer import recognize_speech

app = FastAPI()


@app.post('/postRequest')
async def get_link(data_to_recognize: Request):
    data = await data_to_recognize.json()
    print(data)
    if "link" in data:
        video_id = data["id"]
        link = data["link"]
        language = data["language"]
        try:
            status_code, text = recognize_speech(link, language)
            if status_code == "recognized":
                resp = {'id': video_id, 'text': text, 'status': 'recognized'}
            else:
                resp = {'id': video_id, 'text': text, 'status': status_code}
        except Exception as e:
            resp = {'id': video_id, 'text': str(e), 'status': "error"}
        return requests.post("http://127.0.0.1:5000/postResponse", json=resp)

# uvicorn main:app --host 127.0.0.1 --port 5001 --reload
