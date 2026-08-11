# coding:utf-8

import logging
import threading

from django.db import connection
from django.utils.deprecation import MiddlewareMixin

from util.hive_func import hive_func
from dj2.settings import dbName

logger = logging.getLogger('django.hive')

rename = {}


class HiveMiddleware(MiddlewareMixin):
    def process_response(self, request, response):
        sql_list = []
        for query in connection.queries:
            if query.get("sql") is None:
                continue

            raw_sql = query.get("sql")
            raw_sql = raw_sql.lower()

            if 'insert' in raw_sql and len(raw_sql) > 8:
                logger.debug("Hive sync SQL: %s", raw_sql)
                sql_list.append(raw_sql)

        if sql_list:
            # 异步同步，不阻塞主请求
            t = threading.Thread(target=hive_func, args=(sql_list,), daemon=True)
            t.start()
        return response
