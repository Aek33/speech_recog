import requests

from fastapi import FastAPI, Request
from databases.mysql import RecogDB, Imasv2DB

app = FastAPI()
recog_db = RecogDB()
imasv2_db = Imasv2DB()


@app.post('/Send')
async def send_to_s2t_new_links():
    links = recog_db.get_await_links()
    if len(links) == 0:
        return {"status": "All attachments are processed"}
    else:
        for link in links:
            try:
                language = imasv2_db.get_language(link[1])
                if len(language) == 0:
                    language = ((0,),)
            except TypeError:
                recog_db.update_status(link[0], "lost_connection_lang_db")
                continue
            recog_db.update_status(link[0], "processing")
            json_post = {'id': link[0], 'link': link[2], 'language': language[0][0]}
            requests.post(f"http://127.0.0.1:5001/postRequest", json=json_post)
        return {"status": "All all requests sent"}

# @app.post('/Fix')
# def send_to_s2t_links_for_fix():
#     links = mysql.get_raw_links(2)
#     for link in links:
#         json_post = {'link': link[0], 'language': link[1]}
#         print(link[0])
#         requests.post(f"http://127.0.0.1:5001/postRequest", json=json_post)
#     return "Response sent"


@app.post('/postResponse')
async def get_from_s2t(resp_from_s2t: Request):
    speechrecog_resp = await resp_from_s2t.json()
    video_id = speechrecog_resp["id"]
    text = speechrecog_resp["text"]
    status = speechrecog_resp["status"]
    return recog_db.update_attachment(video_id, text, status)

# uvicorn main:app --host 127.0.0.1 --port 5000 --reload
