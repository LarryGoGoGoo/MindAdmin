
<script setup>
/**
 * @description 角色菜单
 */
import { inject } from 'vue'
const { roleMenus, userName, userAvatar, roleMenuEvent, notreadnum } = inject('header')
</script>

<template>
  <el-dropdown class="rolemenus" trigger="click" @command="roleMenuEvent">
    <div class="avatar">
      <span v-if="notreadnum" class="notreadnum">{{ notreadnum }}</span>
      <img class="img" :src="userAvatar" />
      <span class="name">{{ userName }}</span>
    </div>

    <template #dropdown>
      <el-dropdown-menu>
        <el-dropdown-item v-for="item in roleMenus" :key="item.key" :command="item.key">
          <div class="menu-item" :list-key="item.key">
            <el-icon>
              <component :is="item.icon" />
            </el-icon>
            <span>{{ item.label }}</span>
          </div>
        </el-dropdown-item>
      </el-dropdown-menu>
    </template>
  </el-dropdown>
</template>

<style>
.rolemenus {
  color: inherit;
  cursor: pointer;
  display: flex;
  justify-content: center;
  align-items: center;

  .avatar {
    display: flex;
    justify-content: center;
    align-items: center;
  }
  .notreadnum {
    position: absolute;
    z-index: 9;
    left: 0;
    top: 0;
    background-color: #f56c6c;
    color: #fff;
    padding: 3px 6px;
    border-radius: 10px;
    font-size: 12px;
  }

  .img {
    width: 50px;
    height: 50px;
    border: 1px solid transparent;
    margin-right: 10px;
  }

  .name {
    font-size: 14px;
    color: inherit;
  }
}
</style>
  