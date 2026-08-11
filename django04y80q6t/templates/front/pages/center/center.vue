<template>
	<view class="content">
		<view :style='{"minHeight":"100%","width":"100%","padding":"0","position":"relative","background":"#fff","height":"auto"}'>
			<view v-if="user&&user.id" :style='{"padding":"24rpx 24rpx 60rpx","margin":"0 0 20rpx 0","borderRadius":"0 0 0 100rpx","background":"url(http://codegen.caihongy.cn/20250813/1bc10d619a144bbe950427f2be4dd6c3.jpg) no-repeat center top / cover","display":"flex","width":"100%","position":"relative","height":"auto"}' @tap="onPageTap('../user-info/user-info')" class="header" v-bind:class="{'status':isH5Plus}">
				<view :style='{"alignContent":"center","alignItems":"center","flexWrap":"wrap","flex":"1","flexDirection":"column","display":"flex","height":"100%"}' v-if="tableName=='yonghu'" class="userinfo">
					<image :style='{"width":"120rpx","padding":"0","margin":"0 20rpx 0 0","borderRadius":"100%","height":"120rpx"}' :src="user.touxiang?baseUrl+user.touxiang:require('../../static/gen/upload.png')"></image>
					<view :style='{"width":"auto","flex":"1","flexDirection":"column","justifyContent":"center","display":"flex"}' class="info">
						<view :style='{"width":"auto","lineHeight":"48rpx","fontSize":"24rpx","color":"#fff","textAlign":"center"}'>{{user.yonghuzhanghao}}<text v-if="user.vip&& user.vip=='是'">(VIP)</text></view>
					</view>
					
					<view :style='{"margin":"20rpx 0 0","flexDirection":"row","display":"flex","gap":"20rpx","width":"100%","flexFlow":"wrap","justifyContent":"center"}' class="info">
						<view :style='{"padding":"8rpx","borderRadius":"12rpx","textAlign":"center","background":"none","flexDirection":"column","display":"flex","width":"30%","lineHeight":"36rpx","fontSize":"24rpx"}'>
							<span :style='{"color":"#fff"}'>手机：</span>
							<span :style='{"color":"#fff"}'>{{user.shouji}}</span>
						</view>
						<view :style='{"padding":"8rpx","borderRadius":"12rpx","textAlign":"center","background":"none","flexDirection":"column","display":"flex","width":"30%","lineHeight":"36rpx","fontSize":"24rpx"}' v-if="user.jf||user.jf==0">
							<span :style='{"color":"#fff"}'>积分：</span>
							<span :style='{"color":"#fff"}'>{{user.jf}}</span>
						</view>
					</view>
					<view :style='{"width":"100%","margin":"20rpx 0","display":"flex"}'>
					  <view :style='{"margin":"0","alignItems":"center","borderRadius":"10rpx 0 0 10rpx","background":"#64558020","display":"flex","width":"50%","justifyContent":"center","height":"60rpx"}'>
					    <text class="icon iconfont icon-zan10" :style='{"margin":"0 4rpx 0 0","lineHeight":"1.5","fontSize":"28rpx","color":"#fff"}'></text>
					    <text :style='{"color":"#fff","lineHeight":"1.5","fontSize":"28rpx"}'>点赞 {{user.thumbsnum}}</text>
					  </view>
					  <view :style='{"margin":"0","alignItems":"center","borderRadius":"0 10rpx 10rpx 0","background":"#4D357B30","display":"flex","width":"50%","justifyContent":"center","height":"60rpx"}'>
					    <text class="icon iconfont icon-shoucang10" :style='{"margin":"0 4rpx 0 0","lineHeight":"1.5","fontSize":"28rpx","color":"#fff"}'></text>
					    <text :style='{"color":"#fff","lineHeight":"1.5","fontSize":"28rpx"}'>收藏 {{user.storenum}}</text>
					  </view>
					</view>
				</view>
				<view :style='{"alignContent":"center","alignItems":"center","flexWrap":"wrap","flex":"1","flexDirection":"column","display":"flex","height":"100%"}' v-if="tableName=='xinliyisheng'" class="userinfo">
					<image :style='{"width":"120rpx","padding":"0","margin":"0 20rpx 0 0","borderRadius":"100%","height":"120rpx"}' :src="user.touxiang?baseUrl+user.touxiang:require('../../static/gen/upload.png')"></image>
					<view :style='{"width":"auto","flex":"1","flexDirection":"column","justifyContent":"center","display":"flex"}' class="info">
						<view :style='{"width":"auto","lineHeight":"48rpx","fontSize":"24rpx","color":"#fff","textAlign":"center"}'>{{user.yishenggonghao}}<text v-if="user.vip&& user.vip=='是'">(VIP)</text></view>
						<view :style='{"overflow":"hidden","whiteSpace":"nowrap","color":"#fff","width":"100%","lineHeight":"48rpx","fontSize":"24rpx","textOverflow":"ellipsis"}'>{{user.yishengjianjie}}</view>
					</view>
					
					<view :style='{"margin":"20rpx 0 0","flexDirection":"row","display":"flex","gap":"20rpx","width":"100%","flexFlow":"wrap","justifyContent":"center"}' class="info">
						<view :style='{"padding":"8rpx","borderRadius":"12rpx","textAlign":"center","background":"none","flexDirection":"column","display":"flex","width":"30%","lineHeight":"36rpx","fontSize":"24rpx"}'>
							<span :style='{"color":"#fff"}'>电话号码：</span>
							<span :style='{"color":"#fff"}'>{{user.dianhuahaoma}}</span>
						</view>
						<view :style='{"padding":"8rpx","borderRadius":"12rpx","textAlign":"center","background":"none","flexDirection":"column","display":"flex","width":"30%","lineHeight":"36rpx","fontSize":"24rpx"}' v-if="user.jf||user.jf==0">
							<span :style='{"color":"#fff"}'>积分：</span>
							<span :style='{"color":"#fff"}'>{{user.jf}}</span>
						</view>
					</view>
					<view :style='{"width":"100%","margin":"20rpx 0","display":"flex"}'>
					  <view :style='{"margin":"0","alignItems":"center","borderRadius":"10rpx 0 0 10rpx","background":"#64558020","display":"flex","width":"50%","justifyContent":"center","height":"60rpx"}'>
					    <text class="icon iconfont icon-zan10" :style='{"margin":"0 4rpx 0 0","lineHeight":"1.5","fontSize":"28rpx","color":"#fff"}'></text>
					    <text :style='{"color":"#fff","lineHeight":"1.5","fontSize":"28rpx"}'>点赞 {{user.thumbsnum}}</text>
					  </view>
					  <view :style='{"margin":"0","alignItems":"center","borderRadius":"0 10rpx 10rpx 0","background":"#4D357B30","display":"flex","width":"50%","justifyContent":"center","height":"60rpx"}'>
					    <text class="icon iconfont icon-shoucang10" :style='{"margin":"0 4rpx 0 0","lineHeight":"1.5","fontSize":"28rpx","color":"#fff"}'></text>
					    <text :style='{"color":"#fff","lineHeight":"1.5","fontSize":"28rpx"}'>收藏 {{user.storenum}}</text>
					  </view>
					</view>
				</view>
				<view :style='{"padding":"0","alignItems":"center","top":"30rpx","flexDirection":"row","display":"flex","width":"84rpx","position":"absolute","right":"40rpx","justifyContent":"center","height":"auto"}' class="setting">
					<text class="icon iconfont icon-qita6" :style='{"border":"0","margin":"0 10rpx 0 0","color":"#fff","borderRadius":"0","width":"64rpx","lineHeight":"64rpx","fontSize":"64rpx"}'></text>
					<text :style='{"lineHeight":"2","fontSize":"24rpx","color":"#fff","flex":"none"}'>设置</text>
				</view>
			</view>
			
			<view v-else :style='{"padding":"24rpx 24rpx 60rpx","margin":"0 0 20rpx 0","borderRadius":"0 0 0 100rpx","background":"url(http://codegen.caihongy.cn/20250813/1bc10d619a144bbe950427f2be4dd6c3.jpg) no-repeat center top / cover","display":"flex","width":"100%","position":"relative","height":"auto"}' @tap="loginClick" class="header" v-bind:class="{'status':isH5Plus}">
				<view :style='{"minHeight":"300rpx","alignItems":"center","color":"#333","display":"flex","width":"100%","fontSize":"36rpx","justifyContent":"center","height":"auto"}'>登录/注册</view>
			</view>
			
			<view :style='{"width":"100%","background":"none","height":"auto"}' class="list">
				
				<view :style='{"width":"100%","padding":"0 24rpx 0 24rpx","height":"auto"}'>
					<view :style='{"width":"100%","padding":"0 20rpx 0 60rpx","background":"url(http://codegen.caihongy.cn/20250813/599b0f53d88f438a9cae979efe780834.png) no-repeat center center / 100% auto","justifyContent":"space-between","display":"flex","height":"auto"}'>
						<view :style='{"color":"#fff","fontSize":"28rpx","lineHeight":"72rpx"}'>我的服务</view>
					</view>
					<view class="me-menu-view">
						<block v-for="item in menuList" v-bind:key="item.roleName">
							<block v-if="role==item.roleName" v-bind:key="menu.menu" v-for="(menu,index) in item.backMenu">
								<block v-bind:key="child.tableName" v-for=" (child,sort) in menu.child">
									<view class="me-menu-item" v-if="hasBack(child.tableName)" @tap="onPageTap(getBackMenuUrl(child))" hover-class="hover">
										<view class="me-menu-icon" :class="child.appFrontIcon" :style="{'color': meMenuColor[index]}"></view>
										<view class="text">{{child.menu}}</view>
										<view class="icon iconfont icon-jinru"></view>
									</view>
								</block>
							</block>
						</block>


						<view v-if="user&&user.id" @tap="passwordShow()" class="me-menu-item" hover-class="hover">
							<view class="cuIcon-lock me-menu-icon" :style="{'color': meMenuColor[6]}"></view>
							<view class="text">修改密码</view>
							<view class="icon iconfont icon-jinru"></view>
						</view>
					</view>
				</view>
			</view>
			
			<!-- 推荐 -->
			<view class="recommend" :style='{"width":"100%","padding":"0 24rpx 0 24rpx","margin":"40rpx 0 0","background":"none","height":"auto"}' v-if="recommendList.length">
				<view :style='{"padding":"0 0 0 60rpx","margin":"0","color":"#fff","alignItems":"center","background":"url(http://codegen.caihongy.cn/20250813/599b0f53d88f438a9cae979efe780834.png) no-repeat center center / 100% auto","display":"flex","width":"100%","fontSize":"32rpx","position":"relative","justifyContent":"left","height":"76rpx"}'>为你推荐</view>
				<view :style='{"padding":"0","margin":"40rpx 0 0","flexWrap":"wrap","background":"none","display":"flex","gap":"20rpx","width":"100%","justifyContent":"space-between","height":"auto"}'>
					<view v-for="(item,index) in recommendList" :key="index" :style='{"border":"none","padding":"0","margin":"0 0 30rpx 0","borderRadius":"10rpx","background":"none","width":"100%","position":"relative","height":"auto"}' @click="recommendDetail(item.id)">
						<image v-if="preHttp(item[recommendPicture])" :style='{"width":"30%","objectFit":"cover","borderRadius":"20rpx","float":"left","display":"block","height":"200rpx"}' :src="item[recommendPicture]"></image>
						<image v-else :style='{"width":"30%","objectFit":"cover","borderRadius":"20rpx","float":"left","display":"block","height":"200rpx"}' :src="item[recommendPicture]?(baseUrl + item[recommendPicture].split(',')[0]):''"></image>
						<view :style='{"padding":"0","overflow":"hidden","color":"#333","maxHeight":"80rpx","width":"65%","lineHeight":"40rpx","fontSize":"28rpx","float":"right"}'>{{item[recommendTitle]}}</view>
						<view :style='{"padding":"8rpx","color":"#666","textAlign":"center","background":"#D6B4D320","width":"65%","lineHeight":"24rpx","fontSize":"24rpx","float":"right"}'>{{item.addtime}}</view>
					</view>
				</view>
			</view>
			<view style="width: 100%;height: 80px"></view>
		</view>
		<uni-popup class="popup-content" ref="passwordPopup" type="bottom">
			<view class="passwordForm">
				<view class="passwordInput">
					<input type="password" v-model="passwordForm.mima" placeholder="原密码" />
				</view>
				<view class="passwordInput">
					<input type="password" v-model="passwordForm.newmima" placeholder="新密码" />
				</view>
				<view class="passwordInput">
					<input type="password" v-model="passwordForm.newmima1" placeholder="确认密码" />
				</view>
				<view class="passwordBtnView">
					<button class="passwordBtn" @click="updatePassword">更新</button>
				</view>
			</view>
		</uni-popup>
	</view>
</template>
<script>
	import menu from '@/utils/menu'
	export default {
		data() {
			return {
				isH5Plus: true,
				user: {},
				tableName:'',
				role: '',
				menuList: [],
				iconArr: [
					'cuIcon-same',
					'cuIcon-deliver',
					'cuIcon-evaluate',
					'cuIcon-shop',
					'cuIcon-ticket',
					'cuIcon-cascades',
					'cuIcon-discover',
					'cuIcon-question',
					'cuIcon-pic',
					'cuIcon-filter',
					'cuIcon-footprint',
					'cuIcon-pulldown',
					'cuIcon-pullup',
					'cuIcon-moreandroid',
					'cuIcon-refund',
					'cuIcon-qrcode',
					'cuIcon-remind',
					'cuIcon-profile',
					'cuIcon-home',
					'cuIcon-message',
					'cuIcon-link',
					'cuIcon-lock',
					'cuIcon-unlock',
					'cuIcon-vip',
					'cuIcon-weibo',
					'cuIcon-activity',
					'cuIcon-friendadd',
					'cuIcon-friendfamous',
					'cuIcon-friend',
					'cuIcon-goods',
					'cuIcon-selection'
				],
				recommendList: [],
				recommendTable: '',
				recommendTitle: '',
				recommendPicture: '',
				passwordForm: {
					mima: '',
					newmima: '',
					newmima1: '',
				},
				meMenuColor: '#409eff,#67c23a,#909399,#e6a23c,#f56c6c,#356c6c,#351c6c,#f093a9,#a7c23a,#104eff,#10441f,#a21233,#503319'.split(','),
			};
		},
		computed: {
			baseUrl() {
				return this.$base.url;
			},
		},
		async onLoad(){
			let menus = menu.list();
			this.menuList = menus;
			this.meMenuColor = this.meMenuColor.sort(()=> {
				return (0.5-Math.random());
			});
		},
		async onShow(){
            uni.removeStorageSync("useridTag");
			this.role = uni.getStorageSync("appRole");
			await this.getSession()
			this.getThumbsup()
			this.getStoreup()
			this.tableName = uni.getStorageSync("nowTable");
			let menus = menu.list();
			this.menuList = menus;
			this.getRecommendList()
			this.$forceUpdate()
		},
		methods: {
			hasBack(tableName) {
				if(tableName == 'exampaper'||tableName == 'examquestion') {
					return false
				}
				if(tableName.indexOf('chapter')!=-1) {
					return false
				}
				return true
			},
			async getSession(){
				let table = uni.getStorageSync("nowTable");
				let res = await this.$api.session(table);
				this.user = res.data;
				this.$forceUpdate()
			},
			async getThumbsup(){
				if(!this.user||!this.user.id){
					return false
				}
				let res = await this.$api.page('storeup',{userid: this.user.id,type: 21})
				this.user.thumbsnum = Number(res.data.total)
				this.$forceUpdate()
			},
			async getStoreup(){
				if(!this.user||!this.user.id){
					return false
				}
				let res = await this.$api.page('storeup',{userid: this.user.id,type: 1})
				this.user.storenum = Number(res.data.total)
				this.$forceUpdate()
			},
			loginClick(){
				uni.navigateTo({
					url: '../login/login'
				});
			},
			onPageTap(url) {
                uni.setStorageSync("useridTag",1);
				uni.navigateTo({
					url: url,
					fail: function() {
						uni.switchTab({
							url: url
						});
					}
				});
			},
			getBackMenuUrl(child) {
				const menuJump = child.menuJump ? `&menuJump=${child.menuJump}` : ''
				if (child.tableName == 'examrecord') {
					return `../${child.tableName}/list?menuJump=${child.menuJump || ''}`
				}
				return `../${child.tableName}/list?userid=${this.user.id}${menuJump}`
			},
			hasTranslate(){
				for(let x in this.menuList){
					if(this.menuList[x].roleName == this.role){
						for(let i in this.menuList[x].backMenu){
							if(this.menuList[x].backMenu[i].child.length) {
								for(let j in this.menuList[x].backMenu[i].child) {
									if(this.menuList[x].backMenu[i].child[j].tableName=='hasTranslate'){
										return true
									}
								}
							}
						}
					}
				}
				return false
			},
			
			preHttp(str) {
			    return str && str.substr(0,4)=='http';
			},
			async getRecommendList(){
				let params = {
					page: 1,
					limit: 2,
				}
				let res;
				if(uni.getStorageSync("appUserid")) {
					res = await this.$api.recommend2('xinlizhishi', params);
				} else {
					res = await this.$api.recommend('xinlizhishi', params);
				}
				this.recommendList = res.data.list
				this.recommendTable = 'xinlizhishi'
				this.recommendTitle = 'wenzhangbiaoti'
				this.recommendPicture = 'fengmiantupian'
				this.$forceUpdate()
			},
			recommendDetail(id) {
				uni.navigateTo({
					url: `../${this.recommendTable}/detail?id=${id}`,
					fail: function() {
						uni.switchTab({
							url: `../${this.recommendTable}/detail?id=${id}`
						});
					}
				});
			},
			passwordShow() {
				this.passwordForm = {
					mima: '',
					newmima: '',
					newmima1: '',
				}
				this.$forceUpdate()
				this.$refs.passwordPopup.open()
			},
			async updatePassword() {
				if (this.passwordForm.mima == ''){
					this.$utils.msg('原密码不能为空')
					return false
				}
				if (this.passwordForm.newmima == ''){
					this.$utils.msg('新密码不能为空')
					return false
				}
				if (this.passwordForm.newmima1 == ''){
					this.$utils.msg('确认密码不能为空')
					return false
				}
				if (this.passwordForm.newmima != this.passwordForm.newmima1){
					this.$utils.msg('两次密码不一致')
					return false
				}
				if (this.passwordForm.mima == this.passwordForm.newmima){
					this.$utils.msg('新密码与原密码相同！')
					return false
				}
				await this.$api.updatePassword(this.tableName,{
					oldPassword: this.passwordForm.mima,
					newPassword: this.passwordForm.newmima
				})
				this.$utils.msg('修改密码成功,下次登录系统生效')
				this.$refs.passwordPopup.close()
				this.getSession()
			},
		}
	}
</script>

<style lang="scss" scoped>
	.content {
		height: calc(100vh - 94px);
		box-sizing: border-box;
		background: #f6f8fb;
	}
	.header {
		border-radius: 0 0 28rpx 28rpx !important;
		box-shadow: 0 12rpx 36rpx rgba(42, 55, 78, .14);
	}
	.passwordForm {
		width: 100%;
		padding: 24px 20px 60px;
		background: #fff;
		border-radius: 24rpx 24rpx 0 0;
	
		.passwordInput {
			background: transparent;
			margin: 0 0 12px;
			padding: 0;
	
			input {
				height: 44px;
				line-height: 44px;
				font-size: 14px;
				padding: 0 14px;
			}
		}
	
		.passwordBtnView {
			width: 100%;
			display: flex;
			align-items: center;
			justify-content: center;
			padding: 10px 0;
	
			.passwordBtn {
				padding: 0 24px;
				width: 100%;
				height: 40px;
				line-height: 40px;
				font-size: 14px;
				color: #fff;
				background: #4f7cff;
				border: none;
				border-radius: 8px;
	
			}
		}
	}
	.me-menu-view {
		padding: 8rpx 24rpx;
		display: flex;
		width: 100%;
		flex-wrap: wrap;
		height: auto;
		border-radius: 20rpx;
		.me-menu-item {
			display: flex;
			width: 100%;
			border-color: #eeeeee;
			border-width: 0 0 2rpx 0;
			align-items: center;
			border-style: solid;
			height: auto;
			.me-menu-icon {
				color: rgba(0, 186, 189, 1);
				font-size: 60rpx;
				line-height: 1;
			}
			.text {
				padding: 0 20rpx;
				color: #263238;
				flex: 1;
				width: 100%;
				font-size: 28rpx;
				line-height: 100rpx;
			}
			.icon {
				color: #999;
				width: 28rpx;
				font-size: 28rpx;
				line-height: 28rpx;
			}
		}
	}
</style>
