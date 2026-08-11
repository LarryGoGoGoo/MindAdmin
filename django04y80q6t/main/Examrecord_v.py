#coding:utf-8
import base64, copy, hashlib, time, json, datetime
from django.http import JsonResponse
from django.apps import apps
import numbers
from django.db.models.aggregates import Count,Sum
from django.db.models import Case, When, IntegerField, F
from django.forms import model_to_dict
import requests
from util.CustomJSONEncoder import CustomJsonEncoder
from .models import examrecord
from util.codes import *
from urllib.parse import unquote
from util.auth import Auth
from util.common import Common
import util.message as mes
from django.db import connection
import random
from django.core.mail import send_mail
from django.conf import settings
from django.shortcuts import redirect
from django.db.models import Q
from util.baidubce_api import BaiDuBce
from .config_model import config
from .models import exampaper, examquestion, jiankangyujing, popupremind, users, xinliyisheng, yonghu
from .scl90 import calculate_scl90, is_scl90_paper, normalize_score


PROGRESS_TYPE = -1
PROGRESS_QUESTION_NAME = "__PROGRESS__"
SCL90_WARNING_TITLE = "SCL-90测评预警"
JIANKANGYUJING_ACCOUNT_MAX_LENGTH = 16
JIANKANGYUJING_NAME_MAX_LENGTH = 16
JIANKANGYUJING_TEXT_MAX_LENGTH = 200


def _active_records_q():
    return ~Q(questionname=PROGRESS_QUESTION_NAME)


def _current_user(request):
    token_info = Auth().getTokenInfo(request)
    params = token_info.get('params') or {}
    return params.get("id"), params.get("username") or params.get("yonghuzhanghao") or params.get("yishenggonghao") or ""


def uni_username_fallback(request):
    token_info = Auth().getTokenInfo(request)
    params = token_info.get('params') or {}
    for key in ("username", "yonghuxingming", "yonghuzhanghao", "xingming", "name", "yishengxingming", "yishenggonghao"):
        if params.get(key):
            return params.get(key)
    return ""


def _parse_json(value, default):
    if value in (None, ""):
        return default
    if isinstance(value, (dict, list)):
        return value
    try:
        return json.loads(value)
    except Exception:
        return default


def _safe_int(value, default=0):
    try:
        return int(float(value))
    except Exception:
        return default


def _answer_to_text(value):
    if value in (None, ""):
        return ""
    if isinstance(value, list):
        return ",".join(str(item) for item in value)
    return str(value)


def _score_answer(question_type, answer_value, options):
    if int(question_type or 0) == 4:
        return 0
    if isinstance(answer_value, list):
        selected = set(str(item) for item in answer_value)
        return sum(_safe_int(option.get("score")) for option in options if str(option.get("code")) in selected)
    for option in options:
        if str(answer_value) == str(option.get("code")):
            return _safe_int(option.get("score"))
    return 0


def _serialize_answer_payload(answers):
    if isinstance(answers, str):
        return answers
    return json.dumps(answers or {}, ensure_ascii=False)


def _serialize_progress_payload(answers, updated_at=None):
    return json.dumps({
        "answers": answers or {},
        "updatedAt": _safe_int(updated_at, int(time.time() * 1000)),
    }, ensure_ascii=False)


def _parse_progress_payload(value):
    payload = _parse_json(value, {})
    if not isinstance(payload, dict):
        return {}, 0
    if isinstance(payload.get("answers"), dict):
        return payload.get("answers") or {}, _safe_int(payload.get("updatedAt"), 0)
    return payload, 0


def _get_progress_record(user_id, paper_id):
    return examrecord.objects.filter(
        userid=user_id,
        paperid=paper_id,
        questionname=PROGRESS_QUESTION_NAME,
        type=PROGRESS_TYPE,
        ismark=0,
    ).order_by("-addtime", "-id").first()


def _progress_question(paper_id):
    return examquestion.objects.filter(paperid=paper_id).order_by("-sequence", "id").first()


def _question_position_map(questions):
    ordered = sorted(list(questions), key=lambda item: item.sequence or 0, reverse=True)
    return {item.id: index + 1 for index, item in enumerate(ordered)}, ordered


def _build_scl90_result(paper, records):
    questions = examquestion.objects.filter(paperid=paper.id).all()
    position_map, ordered_questions = _question_position_map(questions)
    if not is_scl90_paper(paper.name, len(ordered_questions)):
        return {}
    scores_by_position = {}
    for record in records:
        position = position_map.get(record.questionid)
        if position:
            scores_by_position[position] = normalize_score(record.myanswer)
    return calculate_scl90(scores_by_position)


def _truncate_text(value, max_length=255):
    text = str(value or "")
    return text[:max_length]


def _format_scl90_score(value):
    try:
        return "{:.2f}".format(float(value))
    except Exception:
        return str(value or 0)


def _scl90_warning_marker(examno):
    digest = hashlib.sha1(str(examno or "").encode("utf-8")).hexdigest()[:12]
    return "SCL90WARN:{}".format(digest)


def _scl90_warning_factors(result):
    factors = result.get("factors") if isinstance(result, dict) else []
    if not isinstance(factors, list):
        return []
    return [factor for factor in factors if isinstance(factor, dict) and factor.get("warning")]


def _build_scl90_warning_payload(user_id, username, paper, examno, result):
    warning_factors = _scl90_warning_factors(result)
    factor_text = "、".join(
        "{}({})".format(item.get("name") or item.get("key"), _format_scl90_score(item.get("score")))
        for item in warning_factors
    ) or "总分或阳性项目达到预警标准"
    guidance_items = []
    for factor in warning_factors:
        guidance = factor.get("guidance")
        if guidance:
            guidance_items.append("{}：{}".format(factor.get("name") or factor.get("key"), guidance))
    if not guidance_items:
        guidance_items.append("建议管理员或心理医生尽快查看该用户测评报告，并结合访谈进行进一步评估。")

    user = yonghu.objects.filter(id=user_id).first()
    user_account = (user.yonghuzhanghao if user else "") or username or str(user_id)
    user_name = (user.yonghuxingming if user else "") or username or user_account
    total_score = _format_scl90_score(result.get("totalScore"))
    average_score = _format_scl90_score(result.get("averageScore"))
    positive_count = result.get("positiveItemCount", 0)
    marker = _scl90_warning_marker(examno)
    brief = "用户{}的{}结果触发预警：总分{}，总均分{}，阳性项目{}项，异常因子：{}。".format(
        user_name,
        paper.name,
        total_score,
        average_score,
        positive_count,
        factor_text,
    )
    content = "\n".join([
        "{} {}".format(SCL90_WARNING_TITLE, marker),
        "用户账号：{}".format(user_account),
        "用户姓名：{}".format(user_name),
        "测评试卷：{}".format(paper.name),
        "考试编号：{}".format(examno),
        "总分：{}".format(total_score),
        "总均分：{}".format(average_score),
        "阳性项目数：{}".format(positive_count),
        "异常因子：{}".format(factor_text),
        "建议：{}".format("；".join(guidance_items)),
    ])
    return {
        "marker": marker,
        "userAccount": user_account,
        "userName": user_name,
        "brief": brief,
        "content": content,
        "factorText": factor_text,
        "guidance": "；".join(guidance_items),
    }


def _scl90_warning_recipients():
    recipients = []
    for admin in users.objects.all():
        recipients.append({
            "userid": admin.id,
            "role": admin.username,
        })
    for doctor in xinliyisheng.objects.all():
        recipients.append({
            "userid": doctor.id,
            "role": doctor.yishenggonghao,
        })
    return recipients


def _create_scl90_warning(user_id, username, paper, examno, result):
    if not isinstance(result, dict) or not result.get("isPositive"):
        return {"created": False, "recipientCount": 0}

    payload = _build_scl90_warning_payload(user_id, username, paper, examno, result)
    marker = payload["marker"]
    if jiankangyujing.objects.filter(yujingtixing__contains=marker).exists() or popupremind.objects.filter(
        title=SCL90_WARNING_TITLE,
        content__contains=marker,
    ).exists():
        return {"created": False, "recipientCount": 0}

    now = datetime.datetime.now()
    jiankangyujing.objects.create(
        yonghuzhanghao=_truncate_text(payload["userAccount"], JIANKANGYUJING_ACCOUNT_MAX_LENGTH),
        yonghuxingming=_truncate_text(payload["userName"], JIANKANGYUJING_NAME_MAX_LENGTH),
        yujingtixing=_truncate_text(
            "{}：{} {}".format(SCL90_WARNING_TITLE, payload["factorText"], marker),
            JIANKANGYUJING_TEXT_MAX_LENGTH,
        ),
        xinlijianyi=_truncate_text(payload["guidance"], JIANKANGYUJING_TEXT_MAX_LENGTH),
        yujingshijian=now,
    )

    recipients = _scl90_warning_recipients()
    for recipient in recipients:
        popupremind.objects.create(
            userid=recipient["userid"],
            role=_truncate_text(recipient["role"]),
            title=SCL90_WARNING_TITLE,
            type="个人",
            brief=payload["brief"],
            content=payload["content"],
            remindtime=now,
        )
    return {"created": True, "recipientCount": len(recipients)}


def _is_admin_request(request):
    tablename = Auth().getTokenInfo(request).get('tablename')
    if tablename == 'users':
        return True
    allModels = apps.get_app_config('main').get_models()
    for model in allModels:
        if model.__tablename__ == tablename:
            return getattr(model, "__isAdmin__", None) == "是"
    return False


def _forbidden_response(msg='无权查看该测评报告'):
    return JsonResponse({"code": 403, "msg": msg, "data": {}})


def examrecord_default(request):

    if request.method in ["POST", "GET"]:
        msg = {"code": normal_code,"msg": mes.normal_code, "data": {}}
        req_dict = request.session.get("req_dict")
        req_dict.update({"isdefault":"是"})
        data=examrecord.getbyparams(examrecord, examrecord, req_dict)
        if len(data)>0:
            msg['data']  = data[0]
        else:
            msg['data']  = {}
        return JsonResponse(msg, encoder=CustomJsonEncoder)

def examrecord_page(request):
    '''
    '''
    if request.method in ["POST", "GET"]:
        msg = {"code": normal_code, "msg": mes.normal_code,  "data":{"currPage":1,"totalPage":1,"total":1,"pageSize":10,"list":[]}}
        req_dict = request.session.get("req_dict")
        global examrecord
        #当前登录用户信息
        tablename = Auth().getTokenInfo(request).get('tablename')
        # 判断当前表的表属性isAdmin,为真则是管理员
        __isAdmin__ = None
        allModels = apps.get_app_config('main').get_models()
        for m in allModels:
            if m.__tablename__==tablename:
                __isAdmin__ = getattr(m, "__isAdmin__", None)
                break
        if __isAdmin__!="是":
            req_dict["userid"]=Auth().getTokenInfo(request).get('params').get("id")

        msg['data']['list'], msg['data']['currPage'], msg['data']['totalPage'], msg['data']['total'], \
        msg['data']['pageSize']  =examrecord.page(examrecord, examrecord, req_dict, request, _active_records_q())
        return JsonResponse(msg, encoder=CustomJsonEncoder)

def examrecord_autoSort(request):
    '''
    ．智能推荐功能(表属性：[intelRecom（是/否）],新增clicktime[前端不显示该字段]字段（调用info/detail接口的时候更新），按clicktime排序查询)
主要信息列表（如商品列表，新闻列表）中使用，显示最近点击的或最新添加的5条记录就行
    '''
    if request.method in ["POST", "GET"]:
        msg = {"code": normal_code, "msg": mes.normal_code,  "data":{"currPage":1,"totalPage":1,"total":1,"pageSize":10,"list":[]}}
        req_dict = request.session.get("req_dict")
        if "clicknum"  in examrecord.getallcolumn(examrecord,examrecord):
            req_dict['sort']='clicknum'
        elif "browseduration"  in examrecord.getallcolumn(examrecord,examrecord):
            req_dict['sort']='browseduration'
        else:
            req_dict['sort']='clicktime'
        req_dict['order']='desc'
        msg['data']['list'], msg['data']['currPage'], msg['data']['totalPage'], msg['data']['total'], \
        msg['data']['pageSize']  = examrecord.page(examrecord, examrecord, req_dict, {}, _active_records_q())

        return JsonResponse(msg, encoder=CustomJsonEncoder)

#分类列表
def examrecord_lists(request):
    if request.method in ["POST", "GET"]:
        msg = {"code": normal_code, "msg": mes.normal_code,  "data":[]}
        msg['data'],_,_,_,_  = examrecord.page(examrecord, examrecord, {}, {}, _active_records_q())
        return JsonResponse(msg, encoder=CustomJsonEncoder)

def examrecord_query(request):
    '''
    '''
    if request.method in ["POST", "GET"]:
        msg = {"code": normal_code, "msg": mes.normal_code, "data": {}}
        try:
            query_result = examrecord.objects.filter(**request.session.get("req_dict")).exclude(questionname=PROGRESS_QUESTION_NAME).values()
            msg['data'] = query_result[0]
        except Exception as e:

            msg['code'] = crud_error_code
            msg['msg'] = f"发生错误：{e}"
        return JsonResponse(msg, encoder=CustomJsonEncoder)

def examrecord_list(request):
    '''
    前台分页
    '''
    if request.method in ["POST", "GET"]:
        msg = {"code": normal_code, "msg": mes.normal_code,  "data":{"currPage":1,"totalPage":1,"total":1,"pageSize":10,"list":[]}}
        req_dict = request.session.get("req_dict")
        #获取全部列名
        columns=  examrecord.getallcolumn( examrecord, examrecord)
        if "vipread" in req_dict and "vipread" not in columns:
          del req_dict["vipread"]
        #表属性[foreEndList]前台list:和后台默认的list列表页相似,只是摆在前台,否:指没有此页,是:表示有此页(不需要登陆即可查看),前要登:表示有此页且需要登陆后才能查看
        __foreEndList__ = getattr(examrecord, "__foreEndList__", None)
        __foreEndListAuth__ = getattr(examrecord, "__foreEndListAuth__", None)

        #authSeparate
        __authSeparate__ = getattr(examrecord, "__authSeparate__", None)

        if __foreEndListAuth__ =="是" and __authSeparate__=="是":
            tablename=Auth().getTokenInfo(request).get('tablename')
            if tablename!="users" and Auth().getTokenInfo(request).get('params') is not None:
                req_dict['userid']=Auth().getTokenInfo(request).get('params').get("id")

        tablename = Auth().getTokenInfo(request).get('tablename')
        if tablename == "users" and req_dict.get("userid") != None:#判断是否存在userid列名
            del req_dict["userid"]
        else:
            __isAdmin__ = None

            allModels = apps.get_app_config('main').get_models()
            for m in allModels:
                if m.__tablename__==tablename:

                    __isAdmin__ = getattr(m, "__isAdmin__", None)
                    break

            if __isAdmin__ == "是":
                if req_dict.get("userid"):
        # del req_dict["userid"]
                    pass
            else:
    #非管理员权限的表,判断当前表字段名是否有userid
                if "userid" in columns:
                    try:
                        pass
                    except Exception:
                        pass
        #当列属性authTable有值(某个用户表)[该列的列名必须和该用户表的登陆字段名一致]，则对应的表有个隐藏属性authTable为”是”，那么该用户查看该表信息时，只能查看自己的
        __authTables__ = getattr(examrecord, "__authTables__", None)

        if __authTables__!=None and  __authTables__!={} and __foreEndListAuth__=="是":
            for authColumn,authTable in __authTables__.items():
                if authTable==tablename:
                    try:
                        del req_dict['userid']
                    except Exception:
                        pass
                    params = Auth().getTokenInfo(request).get('params')
                    req_dict[authColumn]=params.get(authColumn)
                    username=params.get(authColumn)
                    break
        
        if examrecord.__tablename__[:7]=="discuss":
            try:
                del req_dict['userid']
            except Exception:
                pass

        q = _active_records_q()
        msg['data']['list'], msg['data']['currPage'], msg['data']['totalPage'], msg['data']['total'], \
        msg['data']['pageSize']  = examrecord.page(examrecord, examrecord, req_dict, request, q)
        return JsonResponse(msg, encoder=CustomJsonEncoder)

def examrecord_save(request):
    '''
    后台新增
    '''
    if request.method in ["POST", "GET"]:
        msg = {"code": normal_code, "msg": mes.normal_code, "data": {}}
        req_dict = request.session.get("req_dict")
        if 'clicktime' in req_dict.keys():
            del req_dict['clicktime']
        tablename=Auth().getTokenInfo(request).get('tablename')
        __isAdmin__ = None
        allModels = apps.get_app_config('main').get_models()
        for m in allModels:
            if m.__tablename__==tablename:

                __isAdmin__ = getattr(m, "__isAdmin__", None)
                break

        #获取全部列名
        columns=  examrecord.getallcolumn( examrecord, examrecord)
        if tablename!='users' and req_dict.get("userid")==None and 'userid' in columns  and __isAdmin__!='是':
            params=Auth().getTokenInfo(request).get('params')
            req_dict['userid']=params.get('id')


        if 'addtime' in req_dict.keys():
            del req_dict['addtime']

        idOrErr= examrecord.createbyreq(examrecord,examrecord, req_dict)
        if isinstance(idOrErr, str):
            msg['code'] = crud_error_code
            msg['msg'] = idOrErr
        else:
            msg['data'] = idOrErr

        return JsonResponse(msg, encoder=CustomJsonEncoder)

def examrecord_add(request):
    '''
    前台新增
    '''
    if request.method in ["POST", "GET"]:
        msg = {"code": normal_code, "msg": mes.normal_code, "data": {}}
        req_dict = request.session.get("req_dict")
        tablename=Auth().getTokenInfo(request).get('tablename')

        #获取全部列名
        columns=  examrecord.getallcolumn( examrecord, examrecord)
        __authSeparate__ = getattr(examrecord, "__authSeparate__", None)

        if __authSeparate__=="是":
            tablename=Auth().getTokenInfo(request).get('tablename')
            if tablename!="users" and 'userid' in columns:
                try:
                    req_dict['userid']=Auth().getTokenInfo(request).get('params').get("id")
                except Exception:
                    pass

        __foreEndListAuth__ = getattr(examrecord, "__foreEndListAuth__", None)

        if __foreEndListAuth__ and __foreEndListAuth__!="否":
            tablename=Auth().getTokenInfo(request).get('tablename')
            if tablename!="users":
                req_dict['userid']=Auth().getTokenInfo(request).get('params').get("id")


        if 'addtime' in req_dict.keys():
            del req_dict['addtime']
        error= examrecord.createbyreq(examrecord,examrecord, req_dict)
        if isinstance(error, str):
            msg['code'] = crud_error_code
            msg['msg'] = error
        else:
            msg['data'] = error
        return JsonResponse(msg, encoder=CustomJsonEncoder)


def examrecord_progress(request):
    '''
    保存或读取测评中断进度。
    '''
    if request.method in ["POST", "GET"]:
        msg = {"code": normal_code, "msg": mes.normal_code, "data": {}}
        req_dict = request.session.get("req_dict")
        user_id, username = _current_user(request)
        paper_id = req_dict.get("paperid")
        if not user_id or not paper_id:
            msg["code"] = validate_param_code
            msg["msg"] = "缺少用户或测评ID"
            return JsonResponse(msg, encoder=CustomJsonEncoder)

        try:
            paper_id = int(paper_id)
        except Exception:
            msg["code"] = validate_param_code
            msg["msg"] = "测评ID格式错误"
            return JsonResponse(msg, encoder=CustomJsonEncoder)

        if request.method == "GET":
            record = _get_progress_record(user_id, paper_id)
            if record:
                answers, updated_at = _parse_progress_payload(record.options)
                msg["data"] = {
                    "examno": record.examno,
                    "paperid": record.paperid,
                    "papername": record.papername,
                    "currentIndex": _safe_int(record.score, 0),
                    "answers": answers,
                    "updatedAt": updated_at,
                    "savedAt": record.addtime,
                }
            return JsonResponse(msg, encoder=CustomJsonEncoder)

        current_index = _safe_int(req_dict.get("currentIndex"), 0)
        answers = req_dict.get("answers") or {}
        updated_at = req_dict.get("updatedAt") or int(time.time() * 1000)
        updated_at = _safe_int(updated_at, int(time.time() * 1000))
        paper_name = req_dict.get("papername") or ""
        examno = req_dict.get("examno") or "{}-{}".format(user_id, int(time.time() * 1000))
        payload = _serialize_progress_payload(answers, updated_at)

        record = _get_progress_record(user_id, paper_id)
        progress_question = _progress_question(paper_id)
        if not progress_question:
            msg["code"] = validate_param_code
            msg["msg"] = "当前测评没有题目，无法保存进度"
            return JsonResponse(msg, encoder=CustomJsonEncoder)
        params = {
            "userid": user_id,
            "username": username,
            "paperid": paper_id,
            "papername": paper_name,
            "questionid": progress_question.id,
            "questionname": PROGRESS_QUESTION_NAME,
            "type": PROGRESS_TYPE,
            "ismark": 0,
            "options": payload,
            "score": current_index,
            "answer": "",
            "analysis": "未完成测评进度",
            "myscore": 0,
            "myanswer": PROGRESS_QUESTION_NAME,
            "examno": examno,
        }
        if record:
            params["id"] = record.id
            error = examrecord.updatebyparams(examrecord, examrecord, params)
            if error:
                msg["code"] = crud_error_code
                msg["msg"] = error
        else:
            record_id = examrecord.createbyreq(examrecord, examrecord, params)
            if isinstance(record_id, str):
                msg["code"] = crud_error_code
                msg["msg"] = record_id
        msg["data"] = {
            "examno": examno,
            "paperid": paper_id,
            "currentIndex": current_index,
            "answers": answers,
            "updatedAt": updated_at,
        }
        return JsonResponse(msg, encoder=CustomJsonEncoder)


def examrecord_submit(request):
    '''
    一次性提交整份测评，后端统一保存逐题记录并生成SCL-90结果。
    '''
    if request.method in ["POST", "GET"]:
        msg = {"code": normal_code, "msg": mes.normal_code, "data": {}}
        req_dict = request.session.get("req_dict")
        user_id, username = _current_user(request)
        paper_id = req_dict.get("paperid")
        if not user_id or not paper_id:
            msg["code"] = validate_param_code
            msg["msg"] = "缺少用户或测评ID"
            return JsonResponse(msg, encoder=CustomJsonEncoder)

        paper = exampaper.objects.filter(id=paper_id).first()
        if not paper:
            msg["code"] = validate_param_code
            msg["msg"] = "测评不存在"
            return JsonResponse(msg, encoder=CustomJsonEncoder)

        answers = _parse_json(req_dict.get("answers"), req_dict.get("answers") or {})
        if not isinstance(answers, dict):
            msg["code"] = validate_param_code
            msg["msg"] = "答案格式错误"
            return JsonResponse(msg, encoder=CustomJsonEncoder)

        examno = req_dict.get("examno") or "{}-{}".format(user_id, int(time.time() * 1000))
        question_list = list(examquestion.objects.filter(paperid=paper.id).all())
        question_list.sort(key=lambda item: item.sequence or 0, reverse=True)
        has_subject = any(int(item.type or 0) == 4 for item in question_list)

        # Replace only the same unfinished/submitted attempt; other history remains intact.
        examrecord.objects.filter(userid=user_id, paperid=paper.id, examno=examno).delete()

        total_score = 0
        saved_records = []
        for question in question_list:
            answer_value = answers.get(str(question.id), answers.get(question.id, ""))
            options = _parse_json(question.options, [])
            myscore = _score_answer(question.type, answer_value, options)
            total_score += myscore
            params = {
                "userid": user_id,
                "username": username or uni_username_fallback(request),
                "paperid": paper.id,
                "papername": paper.name,
                "questionid": question.id,
                "questionname": question.questionname,
                "type": question.type,
                "ismark": 0 if has_subject else 1,
                "options": json.dumps(options, ensure_ascii=False),
                "score": question.score,
                "answer": question.answer,
                "analysis": question.analysis,
                "myscore": myscore,
                "myanswer": _answer_to_text(answer_value),
                "examno": examno,
            }
            record = examrecord.objects.create(**params)
            params["id"] = record.id
            saved_records.append(params)

        progress = _get_progress_record(user_id, paper.id)
        if progress:
            progress.delete()

        result = {}
        if is_scl90_paper(paper.name, len(question_list)):
            scores_by_position = {}
            for index, question in enumerate(question_list, start=1):
                answer_value = answers.get(str(question.id), answers.get(question.id, ""))
                scores_by_position[index] = normalize_score(answer_value)
            result = calculate_scl90(scores_by_position)
            warning_info = _create_scl90_warning(user_id, username or uni_username_fallback(request), paper, examno, result)
        else:
            warning_info = {"created": False, "recipientCount": 0}

        msg["data"] = {
            "examno": examno,
            "paperid": paper.id,
            "papername": paper.name,
            "score": total_score,
            "recordCount": len(saved_records),
            "result": result,
            "warning": warning_info,
        }
        return JsonResponse(msg, encoder=CustomJsonEncoder)


def examrecord_result(request):
    '''
    获取某次测评聚合结果；SCL-90返回因子分析。
    '''
    if request.method in ["POST", "GET"]:
        msg = {"code": normal_code, "msg": mes.normal_code, "data": {}}
        req_dict = request.session.get("req_dict")
        user_id, _ = _current_user(request)
        paper_id = req_dict.get("paperid")
        examno = req_dict.get("examno")
        if not paper_id:
            msg["code"] = validate_param_code
            msg["msg"] = "缺少用户或测评ID"
            return JsonResponse(msg, encoder=CustomJsonEncoder)
        paper = exampaper.objects.filter(id=paper_id).first()
        if not paper:
            msg["code"] = validate_param_code
            msg["msg"] = "测评不存在"
            return JsonResponse(msg, encoder=CustomJsonEncoder)

        queryset = examrecord.objects.filter(paperid=paper.id).exclude(questionname=PROGRESS_QUESTION_NAME)
        if _is_admin_request(request):
            requested_user_id = req_dict.get("userid")
            if requested_user_id:
                queryset = queryset.filter(userid=requested_user_id)
        else:
            if not user_id:
                return _forbidden_response("请先登录后查看测评报告")
            requested_user_id = req_dict.get("userid")
            if requested_user_id and str(requested_user_id) != str(user_id):
                return _forbidden_response("无权查看他人的测评报告")
            queryset = queryset.filter(userid=user_id)
        if examno:
            queryset = queryset.filter(examno=examno)
        else:
            latest = queryset.order_by("-addtime", "-id").first()
            if latest:
                queryset = queryset.filter(examno=latest.examno)
                examno = latest.examno
        records = list(queryset.all())
        total_score = sum(int(item.myscore or 0) for item in records)
        result = _build_scl90_result(paper, records)
        answered_count = len([item for item in records if item.myanswer not in (None, "", PROGRESS_QUESTION_NAME)])
        question_count = examquestion.objects.filter(paperid=paper.id).count()
        completed_at = max([item.addtime for item in records], default=None)
        msg["data"] = {
            "examno": examno,
            "userid": records[0].userid if records else (req_dict.get("userid") or user_id),
            "username": records[0].username if records else "",
            "paperid": paper.id,
            "papername": paper.name,
            "score": total_score,
            "recordCount": len(records),
            "answeredCount": answered_count,
            "questionCount": question_count or len(records),
            "completedAt": completed_at,
            "result": result,
        }
        return JsonResponse(msg, encoder=CustomJsonEncoder)

def examrecord_thumbsup(request,id_):
    '''
     点赞：表属性thumbsUp[是/否]，刷表新增thumbsupnum赞和crazilynum踩字段，
    '''
    if request.method in ["POST", "GET"]:
        msg = {"code": normal_code, "msg": mes.normal_code, "data": {}}
        req_dict = request.session.get("req_dict")
        id_=int(id_)
        type_=int(req_dict.get("type",0))
        rets=examrecord.getbyid(examrecord,examrecord,id_)

        update_dict={
        "id":id_,
        }
        if type_==1:#赞
            update_dict["thumbsupnum"]=int(rets[0].get('thumbsupnum'))+1
        elif type_==2:#踩
            update_dict["crazilynum"]=int(rets[0].get('crazilynum'))+1
        error = examrecord.updatebyparams(examrecord,examrecord, update_dict)
        if error!=None:
            msg['code'] = crud_error_code
            msg['msg'] = error
        return JsonResponse(msg, encoder=CustomJsonEncoder)


def examrecord_info(request,id_):
    '''
    '''
    if request.method in ["POST", "GET"]:
        msg = {"code": normal_code, "msg": mes.normal_code, "data": {}}

        data = examrecord.getbyid(examrecord,examrecord, int(id_))
        if len(data)>0:
            msg['data']=data[0]
            if msg['data'].__contains__("reversetime"):
                if isinstance(msg['data']['reversetime'], datetime.datetime):
                    msg['data']['reversetime'] = msg['data']['reversetime'].strftime("%Y-%m-%d %H:%M:%S")
                else:
                    if msg['data']['reversetime'] != None:
                        reversetime = datetime.datetime.strptime(msg['data']['reversetime'], '%Y-%m-%d %H:%M:%S')
                        msg['data']['reversetime'] = reversetime.strftime("%Y-%m-%d %H:%M:%S")

        #浏览点击次数
        __browseClick__ = getattr(examrecord, "__browseClick__", None)

        if __browseClick__=="是"  and  "clicknum"  in examrecord.getallcolumn(examrecord,examrecord):
            try:
                clicknum=int(data[0].get("clicknum",0))+1
            except Exception:
                clicknum=0+1
            click_dict={"id":int(id_),"clicknum":clicknum,"clicktime":datetime.datetime.now()}
            ret=examrecord.updatebyparams(examrecord,examrecord,click_dict)
            if ret!=None:
                msg['code'] = crud_error_code
                msg['msg'] = ret
        return JsonResponse(msg, encoder=CustomJsonEncoder)

def examrecord_detail(request,id_):
    '''
    '''
    if request.method in ["POST", "GET"]:
        msg = {"code": normal_code, "msg": mes.normal_code, "data": {}}

        data =examrecord.getbyid(examrecord,examrecord, int(id_))
        if len(data)>0:
            msg['data']=data[0]
            if msg['data'].__contains__("reversetime"):
                if isinstance(msg['data']['reversetime'], datetime.datetime):
                    msg['data']['reversetime'] = msg['data']['reversetime'].strftime("%Y-%m-%d %H:%M:%S")
                else:
                    if msg['data']['reversetime'] != None:
                        reversetime = datetime.datetime.strptime(msg['data']['reversetime'], '%Y-%m-%d %H:%M:%S')
                        msg['data']['reversetime'] = reversetime.strftime("%Y-%m-%d %H:%M:%S")

        #浏览点击次数
        __browseClick__ = getattr(examrecord, "__browseClick__", None)

        if __browseClick__=="是"   and  "clicknum"  in examrecord.getallcolumn(examrecord,examrecord):
            try:
                clicknum=int(data[0].get("clicknum",0))+1
            except Exception:
                clicknum=0+1
            click_dict={"id":int(id_),"clicknum":clicknum,"clicktime":datetime.datetime.now()}

            ret=examrecord.updatebyparams(examrecord,examrecord,click_dict)
            if ret!=None:
                msg['code'] = crud_error_code
                msg['msg'] = ret
        return JsonResponse(msg, encoder=CustomJsonEncoder)

def examrecord_update(request):
    '''
    '''
    if request.method in ["POST", "GET"]:
        msg = {"code": normal_code, "msg": mes.normal_code, "data": {}}
        req_dict = request.session.get("req_dict")
        if 'clicktime' in req_dict.keys() and req_dict['clicktime']=="None":
            del req_dict['clicktime']
        if req_dict.get("mima") and "mima" not in examrecord.getallcolumn(examrecord,examrecord) :
            del req_dict["mima"]
        if req_dict.get("password") and "password" not in examrecord.getallcolumn(examrecord,examrecord) :
            del req_dict["password"]
        try:
            del req_dict["clicknum"]
        except Exception:
            pass


        error = examrecord.updatebyparams(examrecord, examrecord, req_dict)
        if error!=None:
            msg['code'] = crud_error_code
            msg['msg'] = error

        return JsonResponse(msg)


def examrecord_delete(request):
    '''
    批量删除
    '''
    if request.method in ["POST", "GET"]:
        msg = {"code": normal_code, "msg": mes.normal_code, "data": {}}
        req_dict = request.session.get("req_dict")

        error=examrecord.deletes(examrecord,
            examrecord,
             req_dict.get("ids")
        )
        if error!=None:
            msg['code'] = crud_error_code
            msg['msg'] = error
        return JsonResponse(msg)


def examrecord_vote(request,id_):
    '''
    浏览点击次数（表属性[browseClick:是/否]，点击字段（clicknum），调用info/detail接口的时候后端自动+1）、投票功能（表属性[vote:是/否]，投票字段（votenum）,调用vote接口后端votenum+1）
统计商品或新闻的点击次数；提供新闻的投票功能
    '''
    if request.method in ["POST", "GET"]:
        msg = {"code": normal_code, "msg": mes.normal_code}


        data= examrecord.getbyid(examrecord, examrecord, int(id_))
        for i in data:
            votenum=i.get('votenum')
            if votenum!=None:
                params={"id":int(id_),"votenum":votenum+1}
                error=examrecord.updatebyparams(examrecord,examrecord,params)
                if error!=None:
                    msg['code'] = crud_error_code
                    msg['msg'] = error
        return JsonResponse(msg)

def examrecord_importExcel(request):
    if request.method in ["POST", "GET"]:
        msg = {"code": normal_code, "msg": "成功", "data": {}}

        excel_file = request.FILES.get("file", "")
        if excel_file.size > 100 * 1024 * 1024:  # 限制为 100MB
            msg['code'] = 400
            msg["msg"] = '文件大小不能超过100MB'
            return JsonResponse(msg)

        file_type = excel_file.name.split('.')[1]
        
        if file_type in ['xlsx', 'xls']:
            data = xlrd.open_workbook(filename=None, file_contents=excel_file.read())
            table = data.sheets()[0]
            rows = table.nrows
            
            try:
                for row in range(1, rows):
                    row_values = table.row_values(row)
                    req_dict = {}
                    examrecord.createbyreq(examrecord, examrecord, req_dict)
                    
            except Exception:
                pass
                
        else:
            msg = {
                "msg": "文件类型错误",
                "code": 500
            }
                
        return JsonResponse(msg)

def examrecord_autoSort2(request):
    return JsonResponse({"code": 0, "msg": '',  "data":{}})


#选项统计接口
def examrecord_options_num(request):
    if request.method in ["POST", "GET"]:
        msg = {"code": normal_code, "msg": mes.normal_code, "data": {}}
        req_dict = request.session.get("req_dict")
        # 处理参数
        try:
            page1 = int(req_dict.get("page"))
        except Exception:
            page1 = 1
        try:
            limit1 = int(req_dict.get("limit"))
        except Exception:
            limit1 = 10
        start = limit1 * (page1 - 1)
        end = limit1 * (page1 - 1) + limit1 + 1
        try:
            del req_dict["page"]
            del req_dict["limit"]
        except Exception:
            pass
        datas = examrecord.objects.filter(**req_dict).exclude(questionname=PROGRESS_QUESTION_NAME).annotate(paperids=Count('paperid')).all()
        try:
            data = [model_to_dict(i) for i in datas]
            for item in data:
                anum = datas.filter(questionid=item['questionid']).aggregate(
                    anum=Sum(Case(When(myanswer__contains='A', then=1), default=0, output_field=IntegerField())))[
                    'anum']
                bnum = datas.filter(questionid=item['questionid']).aggregate(
                    bnum=Sum(Case(When(myanswer__contains='B', then=1), default=0, output_field=IntegerField())))[
                    'bnum']
                cnum = datas.filter(questionid=item['questionid']).aggregate(
                    cnum=Sum(Case(When(myanswer__contains='C', then=1), default=0, output_field=IntegerField())))[
                    'cnum']
                dnum = datas.filter(questionid=item['questionid']).aggregate(
                    dnum=Sum(Case(When(myanswer__contains='D', then=1), default=0, output_field=IntegerField())))[
                    'dnum']
                item['anum']=anum
                item['bnum']=bnum
                item['cnum']=cnum
                item['dnum']=dnum
        except Exception:
            data = datas
        result_list = []
        for item in data:
            has_questionname_one = any(i['questionname'] == item['questionname'] for i in result_list)
            if not has_questionname_one:
                result_list.append(item)
        data = result_list
        # 赋值分页查询所得数据
        try:
            div = divmod(len(data), limit1)
            if div[1] > 0:
                totalPage = div[0] + 1
            else:
                totalPage = div[0]
        except Exception:
            totalPage = 1
        # 赋值分页参数
        msg["data"] = {"pageSize": limit1,
                       "total": len(data),
                       "totalPage": totalPage,
                       "currPage": page1,
                       "list": data[start:end]
                       }
        return JsonResponse(msg, encoder=CustomJsonEncoder)

def examrecord_groupby(request):
    '''
    按每次测评提交聚合报告入口，前台用于查看柱状图和心理分析。
    '''
    if request.method in ["POST", "GET"]:
        msg = {"code": normal_code, "msg": mes.normal_code, "data": {}}
        req_dict = request.session.get("req_dict")
        try:
            try:
                page1 = int(req_dict.get("page"))
            except Exception:
                page1 = 1
            try:
                limit1 = int(req_dict.get("limit"))
            except Exception:
                limit1 = 10

            papername = str(req_dict.get("papername") or "").replace("%", "")
            paperid = req_dict.get("paperid")
            requested_userid = req_dict.get("userid")
            queryset = examrecord.objects.exclude(questionname=PROGRESS_QUESTION_NAME)
            if paperid:
                queryset = queryset.filter(paperid=paperid)
            if papername:
                queryset = queryset.filter(papername__icontains=papername)
            if _is_admin_request(request):
                if requested_userid:
                    queryset = queryset.filter(userid=requested_userid)
            else:
                current_userid, _ = _current_user(request)
                if not current_userid:
                    return _forbidden_response("请先登录后查看测评报告")
                if requested_userid and str(requested_userid) != str(current_userid):
                    return _forbidden_response("无权查看他人的测评报告")
                queryset = queryset.filter(userid=current_userid)

            question_counts = {}
            paper_ids = set(queryset.values_list("paperid", flat=True))
            if paper_ids:
                question_counts = dict(
                    examquestion.objects.filter(paperid__in=paper_ids)
                    .values("paperid")
                    .annotate(count=Count("id"))
                    .values_list("paperid", "count")
                )

            attempts = {}
            for item in queryset.order_by("-addtime", "-id").all():
                key = "{}#{}#{}".format(item.userid, item.paperid, item.examno or "")
                if key not in attempts:
                    attempts[key] = {
                        "userid": item.userid,
                        "username": item.username,
                        "paperid": item.paperid,
                        "papername": item.papername,
                        "myscore": 0,
                        "examno": item.examno,
                        "ismark": 0,
                        "recordCount": 0,
                        "answeredCount": 0,
                        "questionCount": question_counts.get(item.paperid, 0),
                        "createdAt": item.addtime,
                    }
                attempt = attempts[key]
                attempt["myscore"] += int(item.myscore or 0)
                attempt["recordCount"] += 1
                if item.myanswer not in (None, "", PROGRESS_QUESTION_NAME):
                    attempt["answeredCount"] += 1
                if int(item.type or 0) == 4 and int(item.ismark or 0) == 0:
                    attempt["ismark"] = 1
                if item.addtime and item.addtime > attempt["createdAt"]:
                    attempt["createdAt"] = item.addtime
            dataList = sorted(attempts.values(), key=lambda item: item.get("createdAt") or datetime.datetime.min, reverse=True)

            total = len(dataList)
            try:
                div = divmod(total, limit1)
                if div[1] > 0:
                    totalPage = div[0] + 1
                else:
                    totalPage = div[0]
            except Exception:
                totalPage = 1
            start = limit1 * (page1 - 1)
            end = limit1 * (page1 - 1) + limit1

            msg["data"] = {"pageSize": limit1,
                           "total": total,
                           "totalPage": totalPage,
                           "currPage": page1,
                           "list":dataList[start:end]
                           }
        except Exception as e:
            msg['code'] = crud_error_code
            msg['msg'] = f"发生错误：{e}"
        return JsonResponse(msg, encoder=CustomJsonEncoder)

def examrecord_deleterecords(request):
    '''
    按键值对参数添加删除记录
    '''
    if request.method in ["POST", "GET"]:
        msg = {"code": normal_code, "msg": mes.normal_code}
        req_dict = request.session.get("req_dict")
        error=examrecord.deletebyparams(examrecord,examrecord,req_dict)
        if error!=None:
            msg['code'] = crud_error_code
            msg['msg'] = error
        return JsonResponse(msg)










