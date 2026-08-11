<script setup>
import { inject, ref } from 'vue'
import dayjs from 'dayjs'

/**
 * @description 新闻资讯
 * newsData 新闻数据
 * newsData.tilte 新闻资讯 别名
 * newsData.list 新闻列表
 * item.addtime 发布时间
 * item.title 标题
 * item.introduction 简介
 * item.content 内容
 */

let { newsData } = inject('home')

const dialogVisible = ref(false)
const actData = ref({})
function showContent(item) {
  actData.value = item
  dialogVisible.value = true
}
</script>
<template>
  <div class="home-news">
    <div class="title">{{ newsData.title }}</div>
    <div class="list">
      <div v-for="(item, index) in newsData.list" :key="item.id" class="item" @click="showContent(item)">
        <span class="index">0{{ index + 1 }}</span>
        <el-icon>
          <svg t="1764577059109" class="icon" viewBox="0 0 1024 1024" version="1.1" xmlns="http://www.w3.org/2000/svg" p-id="5941" width="256" height="256">
            <path d="M516.75946 514.747097L810.79074 5.495912 801.271821 0 213.20926 1018.502371l9.518919 5.495912 294.031281-509.251186z" fill="currentColor" p-id="5942"></path>
          </svg>
        </el-icon>
        <div class="lable"><span class="title">{{ item.title }}</span> <span class="addtime">{{ dayjs(item.addtime).format('YYYY-MM-DD') }}</span></div>
        <div class="info">{{ item.introduction }}</div>
      </div>
    </div>

    <el-dialog v-model="dialogVisible" :title="actData.title" width="80%">
      <div class="introduction">{{ actData.introduction }}</div>
      <div class="ql-snow ql-editor" v-html="actData.content"></div>
    </el-dialog>
  </div>
</template>

<style>
.home-news {
  width: calc(100% - 0px);
  background: #fff;
  border-radius: 10px;
  padding: 10px;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2), 0 2px 4px -1px rgba(0, 0, 0, 0.1);

  .lable {
    width: 100%;
  }
  .title {
    width: calc(100% - 160px);
    font-weight: 500;
    text-align: left;
    height: 32px;
    line-height: 32px;
    white-space:nowrap;
    overflow:hidden;
    text-overflow:ellipsis;
  }
  .info {
    width:100%;
    color:#999;
    font-size:12px;
    font-weight: 500;
    text-align: left;
    height: 32px;
    line-height: 32px;
    display:-webkit-box;
    text-overflow:ellipsis;
    overflow:hidden;
    -webkit-box-orient:vertical;
    -webkit-line-clamp:1;
  }
  .item {
    margin-top: 12px;
    border-bottom:1px solid #eee;

    .index {
      color: #bbb;
      font-size: 20px;
      font-weight: 600;
      display:none;
    }
    .label {
      color: #000;
      transition: all 0.3s linear;
      cursor: pointer;
    }
    .addtime{
      float:right;
      color: #999;
      font-size: 12px;
    }
    .el-icon {
      margin: 0 6px;
      display:none;
    }
    &:hover {
      .label {
        color: #1890ff;
      }
    }

    &:nth-of-type(1) {
      .index {
        color: #ef7900;
      }
    }
    &:nth-of-type(2) {
      .index {
        color: #2775a7;
      }
    }
    &:nth-of-type(3) {
      .index {
        color: #1bb4bb;
      }
    }
    &:nth-of-type(4) {
      .index {
        color: #b997b3;
      }
    }
  }
}
</style>

