import boto3
from config import access_key, access_key_id, region_name


def yandex_cloud_auth():
    session = boto3.session.Session()
    s3 = session.client(
        service_name="s3",
        endpoint_url="https://storage.yandexcloud.net/",
        aws_access_key_id=access_key_id,
        aws_secret_access_key=access_key,
        region_name=region_name
    )
    return s3
