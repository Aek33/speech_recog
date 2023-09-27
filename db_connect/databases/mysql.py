from pymysql import connect
from databases.config import RECOGNITION_DB, IMASV2_DB

"""
CREATE TABLE `recognition`.`attachments_video_speech`
    (`id` BIGINT(11) NOT NULL AUTO_INCREMENT,
    `attachment_id` BIGINT(11) NOT NULL,
    `post_id` BIGINT(11) NOT NULL,
    `link` VARCHAR(1000) NOT NULL,
    `content` TEXT NOT NULL, 
    `status` VARCHAR(50) NOT NULL,
    `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP on update CURRENT_TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (`id`)) ENGINE = InnoDB;
"""


class RecogDB:
    def __init__(self):
        self.conn = connect(host=RECOGNITION_DB['host'],
                            user=RECOGNITION_DB['user'],
                            password=RECOGNITION_DB['password'],
                            database=RECOGNITION_DB['db'])

    def _execute_select(self, query: str):
        try:
            with self.conn.cursor() as cur:
                cur.execute(query)
                self.conn.commit()
                return cur.fetchall()
        except Exception as e:
            print("Error: ", "\n", str(e))
            return e

    def _execute_update(self, query: str):
        try:
            with self.conn.cursor() as cur:
                cur.execute(query)
                return self.conn.commit()
        except Exception as e:
            print("Error: ", "\n", str(e))
            return e

    def get_await_links(self):
        # recognition database
        # SELECT id, post_id, link FROM attachments_video_speech WHERE status='await';
        q = """SELECT id, post_id, link FROM attachments_video_speech WHERE status='await';"""
        return self._execute_select(q)

    def update_status(self, video_id: int, status: str):
        # recognition database
        # UPDATE attachments_video_speech SET status = "processing" where id = video_id
        q = f"""UPDATE attachments_video_speech SET status = '{status}' where id = {video_id}"""
        return self._execute_update(q)

    def update_attachment(self, video_id: int, content: str, status: str):
        # recognition database
        # UPDATE attachments_video_speech SET text = text, status = status where id = video_id;
        q = """UPDATE attachments_video_speech SET content = %s, status = %s where id = %s;"""
        with self.conn.cursor() as cur:
            cur.execute(q, (content, status, video_id))
            return self.conn.commit()


class Imasv2DB:
    def __init__(self):
        self.conn = connect(host=IMASV2_DB['host'],
                            user=IMASV2_DB['user'],
                            password=IMASV2_DB['password'],
                            database=IMASV2_DB['db'])

    def _execute_select(self, query: str):
        try:
            with self.conn.cursor() as cur:
                cur.execute(query)
                self.conn.commit()
                return cur.fetchall()
        except Exception as e:
            print("Error: ", "\n", str(e))
            return e

    def get_language(self, post_id: int):
        # imasv2 database
        # SELECT lang FROM sentiment_lang WHERE smi_social = 2 AND news_id=%s;
        q = f"""SELECT lang FROM sentiment_lang WHERE smi_social = 2 AND news_id={post_id};"""
        return self._execute_select(q)
