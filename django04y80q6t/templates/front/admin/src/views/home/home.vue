<script setup>
/**
 * @description 首页
 */
import '@/style/home.scss';
import { onMounted, ref, provide } from 'vue'

import HomeChart from './HomeChart.vue'
import HomeCount from './HomeCount.vue'
import HomeTitle from './HomeTitle.vue'
import HomeNews from './HomeNews.vue'
import Custom from './Custom.vue'

import { getCountAPI, getPageAPI } from '@/api/list'



// ----------------------------------
// ----------- 新闻资讯 --------------
// ----------------------------------
const newsData = ref({
  title: '发布信息',
  list: [],
})
getNews()
async function getNews() {
  let res = await getPageAPI('news', {
    page: 1,
    limit: 6,
  })
  newsData.value.list = res.data.list
}

onMounted(() => {
  setTimeout(() => {
    requestIdleCallback(() => {
      // 提前加载 列表页
      import("@/views/list/list.vue");
    });
  }, 1000);
});

provide('home', {
  newsData,
})
</script>

<template>
  <div
    class="home-wrapper"
    :style="
      $projectImages.bIndexBackgroundImg
        ? `background-image: url(${$projectImages.bIndexBackgroundImg})`
        : ''
    "
  >
    <HomeCount />  
<HomeChart />  
<HomeNews />
<Custom />  

  
  </div>
</template>
