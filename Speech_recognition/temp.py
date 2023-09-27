import json
import time
import requests
from languages import youtubeLangs, yandexLangs
from cloud_auth import yandex_cloud_auth
from config import API_key, bucket_path, bucket_name
file_name = "vnuDlupIc-Y.ogg"
model = "deferred-general"
language = "kk-KK"
bucket = f"{bucket_path}/{file_name}"
post_req = "https://transcribe.api.cloud.yandex.net/speech/stt/v2/longRunningRecognize"
body = {
    "config": {
        "specification": {
            "languageCode": language,
            "model": model
        }
    },
    "audio": {
        "uri": bucket
    }
}
# Если использовать IAM-токен для аутентификации, заменить Api-Key на Bearer.
header = {'Authorization': f'Api-Key {API_key}'}
# Отправить запрос на распознавание.
# Реализация проверки
req = requests.post(post_req, headers=header, json=body)
if req.status_code != 200:
    print(req.content)
else:
    data = req.json()
    print(data)
    while True:
        time.sleep(5)
        get_req = f"https://operation.api.cloud.yandex.net/operations/{data['id']}"
        req = requests.get(get_req, headers=header)
        req = req.json()
        print(req)
        if req['done']:
            break
        print("В обработке")
    # Показать полный ответ сервера в формате JSON.
    print("Response:\n" + json.dumps(req, ensure_ascii=False, indent=2))
    if "chunks" in req["response"]:
    # Блок обработки результатов запроса
        text_list = []
        channel_list = []
        for chunk in req['response']['chunks']:
            text_list.append(chunk['alternatives'][0]['text'])
            channel_list.append(chunk["channelTag"][0])
        text_by_channels = {}
        for channel in list(set(channel_list)):
            text_by_channels[channel] = []
            for i in range(len(channel_list)):
                if channel_list[i] == channel:
                    text_by_channels[channel].append(text_list[i])
        print(text_by_channels)
    else:
        "speech_not_found"
