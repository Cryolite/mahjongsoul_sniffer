#!/usr/bin/env python3

import re
import datetime
import json
from typing import (List,)
import jsonschema
import botocore.exceptions
import boto3
import mahjongsoul_sniffer.config as config_
import mahjongsoul_sniffer.game_detail as game_detail_


class Bucket:
    def __init__(self, *, module_name: str):
        self.__config = config_.get(module_name)
        self.__config = self.__config['s3']

        self.__game_abstract_schema = None

        s3 = boto3.resource('s3')
        bucket_name = self.__config['bucket_name']
        self.__bucket = s3.Bucket(bucket_name)

    def __get_game_abstract_schema(self) -> dict:
        if self.__game_abstract_schema is None:
            with open('schema/game-abstract.json') as schema_file:
                self.__game_abstract_schema = json.load(schema_file)

        return self.__game_abstract_schema

    def put_game_abstract(self, game_abstract: dict) -> None:
        key_prefix = self.__config['game_abstract_key_prefix']
        key_prefix = re.sub('/*$', '', key_prefix)

        uuid = game_abstract['uuid']
        mode = game_abstract['mode']
        start_time = game_abstract['start_time']
        key_prefix = start_time.strftime(key_prefix)
        key = f'{key_prefix}/{uuid}'

        game_abstract = {
            'uuid': uuid,
            'mode': mode,
            'start_time': int(start_time.timestamp())
        }
        jsonschema.validate(instance=game_abstract,
                            schema=self.__get_game_abstract_schema())

        data = json.dumps(game_abstract, ensure_ascii=False,
                          allow_nan=False, separators=(',', ':'))
        data = data.encode('UTF-8')
        self.__bucket.put_object(Key=key, Body=data)

    def get_game_abstracts(self, max_keys: int=1000) -> List[dict]:
        key_prefix = self.__config['game_abstract_key_prefix']
        key_prefix = re.sub('/*$', '', key_prefix)

        # https://github.com/boto/boto3/issues/2186
        game_abstract_objects = self.__bucket.objects.filter(
            Prefix=key_prefix)
        game_abstract_objects = game_abstract_objects.limit(
            count=max_keys)

        game_abstracts = []

        for game_abstract_object in game_abstract_objects:
            game_abstract = game_abstract_object.get()
            game_abstract = game_abstract['Body']
            game_abstract = game_abstract.read()
            game_abstract = game_abstract.decode('UTF-8')
            game_abstract = json.loads(game_abstract)
            jsonschema.validate(
                instance=game_abstract,
                schema=self.__get_game_abstract_schema())
            game_abstract['start_time'] = datetime.datetime.fromtimestamp(
                game_abstract['start_time'], tz=datetime.timezone.utc)
            game_abstract['key'] = game_abstract_object.key
            game_abstracts.append(game_abstract)

        return game_abstracts

    def has_game_detail(self, game_abstract: dict) -> bool:
        uuid = game_abstract['uuid']
        start_time = game_abstract['start_time']

        key_prefix = self.__config['game_detail_key_prefix']
        key_prefix = re.sub('/*$', '', key_prefix)
        key_prefix = start_time.strftime(key_prefix)

        key = f'{key_prefix}/{uuid}'

        game_detail_object = self.__bucket.Object(key)
        try:
            game_detail_object.load()
        except botocore.exceptions.ClientError as e:
            return False

        return True

    def put_game_detail(self, message: bytes) -> None:
        game_abstract = game_detail_.get_game_abstract(message)
        uuid = game_abstract['uuid']
        start_time = game_abstract['start_time']

        key_prefix = self.__config['game_detail_key_prefix']
        key_prefix = re.sub('/*$', '', key_prefix)
        key_prefix = start_time.strftime(key_prefix)

        key = f'{key_prefix}/{uuid}'

        self.__bucket.put_object(Key=key, Body=message)

    def delete_object(self, key: str) -> None:
        obj = self.__bucket.Object(key)
        obj.delete()
