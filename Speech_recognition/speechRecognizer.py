import os
import requests
import subprocess
import time
import glob

import webvtt
import youtube_dl
from re import match

from languages import youtubeLangs, yandexLangs
from cloud_auth import yandex_cloud_auth
from config import API_key, bucket_path, bucket_name

session = yandex_cloud_auth()


def determ_resource(res_link: str):
    """
    Определение типа ресурса на основе регулярных выражений
    :param res_link: Ссылка полученная в запросе
    :return: имя ресурса для дальнейшей обработки или "Undefined resource!"
    """
    if len(res_link) == 0:
        return "link is requaired"
    if match("^(https?\:\/\/)?(www\.)?(youtube\.com|youtu\.be)\/.+$", res_link):
        return "youtube"
    else:
        return "Undefined resource!"


def recognize_youtube_subs(video_link: str, language: str):
    """
    Загрузка субтитров из Youtube сылки с помощью библиотеки youtube_dl
    Если есть собственные субтитры, записывает их, если нет, пытается собрать
    :param video_link: Ссылка на видео, полученная в запросе
    :param language: Язык видео
    :return: статус обработки или ошибку
    """
    try:
        with youtube_dl.YoutubeDL() as ydl:
            video_info = ydl.extract_info(video_link, download=False)
        if language in video_info["subtitles"]:
            options = {
                "skip_download": True,
                "writesubtitles": True,
                "subtitleslangs": [language]}
            with youtube_dl.YoutubeDL(options) as ydl:
                ydl.download([video_link])
                sub_path = glob.glob(f"{os.path.abspath(os.getcwd())}/*{video_info['id']}.{language}.vtt")[0]
                vtt = webvtt.read(sub_path)
                lines = []
                clean_str = ""
                for line in vtt:
                    lines.extend(line.text.strip().replace("&nbsp;", "").splitlines())
                previous = None
                for line in lines:
                    if line == previous:
                        continue
                    clean_str += " " + line
                    previous = line
                os.remove(sub_path)
                return "recognized", clean_str
        else:
            options = {
                "skip_download": True,
                "writeautomaticsub": True,
                "subtitleslangs": [language]}
            with youtube_dl.YoutubeDL(options) as ydl:
                ydl.download([video_link])
                try:
                    sub_path = glob.glob(f"{os.path.abspath(os.getcwd())}/*{video_info['id']}.{language}.vtt")[0]
                except IndexError:
                    return "speech_not_found", "Speech not found"
                vtt = webvtt.read(sub_path)
                lines = []
                clean_str = ""
                for line in vtt:
                    lines.extend(line.text.strip().splitlines())
                previous = None
                for line in lines:
                    if line == previous:
                        continue
                    clean_str += " " + line
                    previous = line
                os.remove(sub_path)
                return "recognized", clean_str
    except Exception as e:
        return "error", str(e)


def yandex_recognizer(file_name: str, language: str, model: str = "deferred-general"):
    """
    Распознавание аудифайла с помощью сервиса яндекса. Файл должен находиться в облаке
    :param file_name: Имя файла
    :param language: Язык, который необходимо распознать (ru-RU, kk-KK)
    :param model: Модель асинхронного распознавания https://cloud.yandex.ru/docs/speechkit/stt/models
    :return: в случае успешного распознования возвращает 'recognized' и распознанный текст,
     в случае ошибки возвращает 'error' и контент реквеста с описанием ошибки
    """
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
        return "error", req.content
    else:
        data = req.json()
        while True:
            time.sleep(5)
            get_req = f"https://operation.api.cloud.yandex.net/operations/{data['id']}"
            req = requests.get(get_req, headers=header)
            req = req.json()
            if req['done']:
                break
            print("В обработке")
        # Показать полный ответ сервера в формате JSON.
        # print("Response:\n" + json.dumps(req, ensure_ascii=False, indent=2))
        # Блок обработки результатов запроса
        if "chunks" in req["response"]:
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
            return "recognized", text_by_channels
        else:
            return "speech_not_found", "Speech not found"

def recognize_youtube_video(video_link: str, language: str):
    """
    :param video_link: Имя файла
    :param language: Язык, который необходимо распознать (ru-RU, kk-KK)
    Распознавание видео ютуба с помощью сервиса яндекса
    1 этап: загрузка аудио, загружает файл, получает айди видео для дальнейшей работы
    2 этап: конвертирование в необходимый формат, перевод в формат .ogg
    3 этап: распознование, отправка аудио в бакет яндекса, отправка запроса на распознавание, получение ответа,
    удаление файла из бакета, удаление аудио
    """
    # Загрузка аудио
    try:
        options = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192'}],
        }
        with youtube_dl.YoutubeDL(options) as ydl:
            video_info = ydl.extract_info(video_link, download=False)
            ydl.download([video_link])
        video_id = video_info['id']
    except Exception as e:
        return "error", e
    # Конвертирование в формат .ogg
    try:
        video_path = glob.glob(f"{os.path.abspath(os.getcwd())}/*{video_id}*")[0]
        current_dir = os.path.abspath(".")
        command_list = ["/usr/bin/ffmpeg",
                        "-i", f"{video_path}",
                        "-map", "0:a", "-acodec", "libopus",
                        f"{current_dir}/{video_id}.ogg"]
        subprocess.run(command_list)
    except Exception as e:
        return "error", str(e)
    # Распознавание с помощью сервиса Яндекса
    try:
        session.upload_file(f"{video_id}.ogg", bucket_name, f"{video_id}.ogg")
        status_code, rec_text = yandex_recognizer(f"{video_id}.ogg", language)
        os.remove(video_path)
        os.remove(f"{video_id}.ogg")
        session.delete_object(Bucket=bucket_name, Key=f"{video_id}.ogg")
        return status_code, str(rec_text)
    except Exception as e:
        os.remove(video_path)
        os.remove(f"{video_id}.ogg")
        return "error", str(e)


def recognize_speech(link: str, language: int):
    """
    Обработка и распознавание видео
    :param link: ссылка для скачаивания видео
    :param language: язык, который необходимо распознать, коды языков находятся в файле languages.py
    :return: в случае успешного распознования возвращает "recognized" и распознанный текст,
     в случае ошибки возвращает "error" и ошибку
    """
    res_type = determ_resource(link)
    if res_type == "youtube":
        youtube_lang = youtubeLangs[language]
        if youtube_lang == "undefined":
            return "error_undefined_language", "undefined language"
        elif language == 10:
            yandex_lang = yandexLangs[language]
            status, text = recognize_youtube_video(link, yandex_lang)
            return status, text
        else:
            return recognize_youtube_subs(link, youtube_lang)

    else:
        return "undefined_resource", "incorrect or empty link"

