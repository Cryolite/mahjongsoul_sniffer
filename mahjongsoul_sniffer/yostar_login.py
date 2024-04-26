import datetime
import logging
import re
import time
from typing import Optional

import mahjongsoul_sniffer.config as config_
import mahjongsoul_sniffer.s3 as s3_


class YostarLogin:
    def __init__(self, *, module_name: str):
        config = config_.get(module_name)

        yostar_login_config = config["yostar_login"]
        self.__email_address = yostar_login_config["email_address"]

        self.__s3_bucket = s3_.Bucket(module_name=module_name)

    def get_email_address(self) -> str:
        return self.__email_address

    def __get_auth_code(
        self,
        *,
        start_time: datetime.datetime,
    ) -> Optional[str]:
        emails = self.__s3_bucket.get_authentication_emails()

        target_date = None
        target_content = None

        for key, email in emails.items():
            if "Date" not in email:
                self.__s3_bucket.delete_object(key)
                logging.info(f"Deleted the object `{key}`.")
                continue
            date = datetime.datetime.strptime(
                email["Date"],
                "%a, %d %b %Y %H:%M:%S %z",
            )

            now = datetime.datetime.now(tz=datetime.timezone.utc)
            if date < now - datetime.timedelta(minutes=30):
                # 認証コードの有効期限が30分なので，30分以上前に送られた
                # メールは無条件で削除する．
                self.__s3_bucket.delete_object(key)
                logging.info(f"Deleted the object `{key}`.")
                continue

            if "To" not in email:
                self.__s3_bucket.delete_object(key)
                logging.info(f"Deleted the object `{key}`.")
                continue
            if email["To"] != self.__email_address:
                # 宛先が異なるメールは他のクローラに対して送られた
                # メールの可能性があるので無視する．
                continue

            if date < start_time:
                self.__s3_bucket.delete_object(key)
                logging.info(f"Deleted the object `{key}`.")
                continue
            if target_date is not None and date < target_date:
                self.__s3_bucket.delete_object(key)
                logging.info(f"Deleted the object `{key}`.")
                continue

            if "From" not in email:
                self.__s3_bucket.delete_object(key)
                logging.info(f"Deleted the object `{key}`.")
                continue
            if email["From"] != "info@passport.yostar.co.jp":
                self.__s3_bucket.delete_object(key)
                logging.info(f"Deleted the object `{key}`.")
                continue

            if "Subject" not in email:
                self.__s3_bucket.delete_object(key)
                logging.info(f"Deleted the object `{key}`.")
                continue
            if email["Subject"] != "Eメールアドレスの確認":
                self.__s3_bucket.delete_object(key)
                logging.info(f"Deleted the object `{key}`.")
                continue

            target_date = date
            body = email.get_body()
            target_content = body.get_content()

            self.__s3_bucket.delete_object(key)
            logging.info(f"Deleted the object `{key}`.")

        if target_content is None:
            return None

        m = re.search(">(\\d{6})<", target_content)
        if m is None:
            return None

        return m.group(1)

    def get_auth_code(
        self,
        *,
        start_time: datetime.datetime,
        timeout: datetime.timedelta,
    ) -> str:
        while True:
            auth_code = self.__get_auth_code(start_time=start_time)
            if auth_code is not None:
                break

            now = datetime.datetime.now(tz=datetime.timezone.utc)
            if now > start_time + timeout:
                msg = "Extraction of the authentication has timed out."
                raise RuntimeError(msg)
            time.sleep(1)
            now = datetime.datetime.now(tz=datetime.timezone.utc)
            if now > start_time + timeout:
                msg = "Extraction of the authentication has timed out."
                raise RuntimeError(msg)

        return auth_code
