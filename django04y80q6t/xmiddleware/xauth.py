#coding:utf-8

import logging

from django.utils.deprecation import MiddlewareMixin
from django.http import JsonResponse
from django.apps import apps

from util.auth import Auth
from util.codes import *
from util.security import json_response
from dj2.settings import dbName as schemaName

logger = logging.getLogger('django.middleware')


class Xauth(MiddlewareMixin):
    def process_request(self,request):
        fullPath = request.get_full_path()
        logger.debug("fullPath===============>%s", fullPath)
        if request.META.get('HTTP_UPGRADE')=='websocket':
            return
        if request.method == 'GET':
            # 已登录用户标记为 CSRF 豁免（API 使用自定义 Token 认证）
            request.csrf_processing_done = True

            filterList = [
                "/index",
                "/follow",
                "/favicon.ico",
                "/login",
                "/register",
                "/notify",
                "/file",
                "/admin",
                "/xadmin",
                "/yolo",
                "/baike",
                "/{}/remind/".format(schemaName),
                "/{}/option/".format(schemaName),
            ]

            # 静态文件后缀白名单（精确后缀匹配）
            static_exts = (
                '.js', '.css', '.jpg', '.jpeg', '.png', '.gif',
                '.mp4', '.mp3', '.ttf', '.wotf', '.woff', '.woff2',
                '.otf', '.eot', '.svg', '.csv', '.webp',
                '.xls', '.xlsx', '.doc', '.docx', '.ppt', '.pptx',
                '.html', '.htm',
            )

            allModels = apps.get_app_config('main').get_models()
            for m in allModels:
                foreEndList = getattr(m, '__foreEndList__', None)
                if foreEndList is None or foreEndList != "前要登":
                    filterList.append("/{}/sendemail".format(m.__tablename__))
                    filterList.append("/{}/sendsms".format(m.__tablename__))
                    filterList.append("/{}/list".format(m.__tablename__))
                    filterList.append("/{}/detail".format(m.__tablename__))

            auth = True
            if fullPath == '/':
                auth = False
            else:
                if fullPath.endswith(static_exts):
                    auth = False
                else:
                    for i in filterList:
                        if fullPath == i or fullPath.startswith(i + '?') or fullPath.startswith(i + '/'):
                            auth = False
                            break

            if auth:
                result = Auth.identify(Auth, request)
                if result.get('code') != normal_code:
                    return json_response(result)

        elif request.method == 'POST':
            # 已登录用户标记为 CSRF 豁免
            request.csrf_processing_done = True

            post_whitelist = [
                '/{}/defaultuser/register'.format(schemaName),
                '/{}/defaultuser/login'.format(schemaName),
                '/{}/users/register'.format(schemaName),
                '/{}/users/login'.format(schemaName),
                '/{}/examusers/login'.format(schemaName),
                '/{}/examusers/register'.format(schemaName),
                '/{}/file/upload'.format(schemaName),
                '/update',
            ]
            # 精确匹配白名单，不再使用子串匹配绕过
            if fullPath not in post_whitelist:
                result = Auth.identify(Auth, request)
                if result.get('code') != normal_code:
                    logger.debug("jwt auth fail")
                    return json_response(result)
