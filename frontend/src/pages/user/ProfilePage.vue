<script setup lang="ts">
import { NCard, NButton, NTag, NSpin, NAvatar, NUpload, NProgress } from 'naive-ui'
import { useRouter } from 'vue-router'
import { computed, ref, watch } from 'vue'
import type { UploadOnChange } from 'naive-ui/es/upload/src/public-types'
import { useAuthStore } from '@/stores/auth'
import { useMessage } from 'naive-ui'
import { useMyProfileQuery, useUpdateMyProfileMutation, useUploadUserAvatarMutation, useUserNodesQuery } from '@/features/user/queries'
import { storyStatusLabel } from '@/utils/storyStatus'

const message = useMessage()
const authStore = useAuthStore()
const router = useRouter()

// 获取当前用户信息
const { data: user, isLoading } = useMyProfileQuery()

const userNodesParams = computed(() => ({
  authorId: authStore.currentUser?.id,
  limit: 5,
}))
const { data: submittedNodes, isLoading: nodesLoading } = useUserNodesQuery(userNodesParams)

const { mutate: updateUser, isPending: updatingUser } = useUpdateMyProfileMutation()

const { mutate: uploadAvatar, isPending: uploadingAvatar } = useUploadUserAvatarMutation()

// 用户资料表单
const form = ref({
  username: '',
  bio: '',
  avatar: '',
})

// 头像文件选择
const avatarFile = ref<File | null>(null)
const avatarPreview = ref<string | null>(null)

function formatDateTime(value: string | null | undefined) {
  if (!value) return '-'

  const parsed = new Date(value)
  if (Number.isNaN(parsed.getTime())) return '-'

  return new Intl.DateTimeFormat('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  }).format(parsed)
}

const registeredAtLabel = computed(() => formatDateTime(user.value?.created_at))

watch(
  user,
  (nextUser) => {
    if (!nextUser) return
    form.value.username = nextUser.username || ''
    form.value.bio = nextUser.bio || ''
    form.value.avatar = nextUser.avatar || ''
    avatarPreview.value = nextUser.avatar || null
  },
  { immediate: true },
)

// 文件选择处理
const handleFileChange: UploadOnChange = ({ file }) => {
  if (file.file) {
    avatarFile.value = file.file
    
    // 预览图片
    const reader = new FileReader()
    reader.onload = (e) => {
      if (e.target?.result) {
        avatarPreview.value = e.target.result as string
      }
    }
    reader.readAsDataURL(file.file)
  }
}

// 提交用户资料更新
function handleSubmit() {
  if (!form.value.username.trim()) {
    message.error('用户名不能为空')
    return
  }
  
  // 如果有新头像，先上传
  if (avatarFile.value) {
    uploadAvatar(
      {
        file: avatarFile.value,
        onProgress: (progress) => {
          uploadProgress.value = progress
        },
      },
      {
        onSuccess: (data) => {
          message.success('头像上传成功')
          updateUser(
            { username: form.value.username, bio: form.value.bio, avatar: data.url },
            {
              onSuccess: (updatedUser) => {
                authStore.currentUser = updatedUser
                avatarFile.value = null
                form.value.avatar = updatedUser.avatar || ''
              },
              onError: (error) => {
                console.error('更新失败:', error)
                message.error('更新失败，请重试')
              },
            }
          )
        },
        onError: (error) => {
          console.error('上传失败:', error)
          message.error('头像上传失败，请重试')
        },
      }
    )
  } else {
    updateUser(
      { username: form.value.username, bio: form.value.bio, avatar: form.value.avatar || undefined },
      {
        onSuccess: (updatedUser) => {
          message.success('资料更新成功')
          authStore.currentUser = updatedUser
        },
        onError: (error) => {
          console.error('更新失败:', error)
          message.error('更新失败，请重试')
        },
      }
    )
  }
}

// 上传进度
const uploadProgress = ref<number>(0)

function handleOpenNode(nodeId: number) {
  void router.push({ name: 'story-node', params: { nodeId } })
}

function handleStartWriting() {
  void router.push({ name: 'books' })
}
</script>

<template>
  <div class="ui-page-stack profile-page">
    <n-spin :show="isLoading">
      <section class="ui-page-hero ui-shell-panel ui-shell-grid">
        <div class="ui-page-hero__grid profile-hero">
          <div>
            <p class="ui-shell-kicker">Account Console</p>
            <h1 class="ui-shell-title">个人中心</h1>
            <p class="ui-page-hero__lead">
              管理你的身份资料、头像和最近投稿。这里应该像一个稳定的作者控制台，而不是零散的表单集合。
            </p>
          </div>
          <div class="profile-hero__metrics">
            <div class="ui-metric-card">
              <p class="ui-metric-card__label">Role</p>
              <p class="ui-metric-card__value">{{ user?.role || 'observer' }}</p>
            </div>
            <div class="ui-metric-card">
              <p class="ui-metric-card__label">Nodes</p>
              <p class="ui-metric-card__value">{{ user?.nodes_count ?? 0 }}</p>
            </div>
          </div>
        </div>
      </section>

      <n-card class="ui-shell-panel profile-card">
        <template #header>
          <h2 class="ui-shell-title">资料设置</h2>
          <p class="profile-card__lead">更新你在站内显示的名称、简介和头像。</p>
        </template>
        
        <div class="profile-card__layout">
          <div class="profile-avatar-panel">
            <div class="profile-avatar-panel__inner">
              <div class="profile-avatar-frame">
                <n-avatar 
                  :size="120" 
                  :src="avatarPreview || user?.avatar || undefined"
                >
                  {{ user?.username?.charAt(0).toUpperCase() ?? '' }}
                </n-avatar>
                <div class="profile-avatar-frame__badge">
                  EDIT
                </div>
              </div>
              
              <n-upload
                :show-file-list="false"
                :multiple="false"
                :custom-request="() => {}"
                @change="handleFileChange"
                accept="image/*"
                :max="1"
              >
                <n-button size="small" ghost>
                  更换头像
                </n-button>
              </n-upload>
              
              <div v-if="uploadingAvatar" class="profile-avatar-panel__progress">
                <n-progress 
                  :percentage="uploadProgress" 
                  :show-text="true" 
                  :height="8" 
                  color="#f2f2f2"
                />
              </div>
            </div>
          </div>
          
          <div class="profile-form-panel">
            <h2 class="profile-form-panel__title">{{ user?.username ?? '未登录' }}</h2>
            
            <div class="profile-form-grid">
              <div class="profile-field">
                <span class="profile-field__label">用户名</span>
                <input 
                  v-model="form.username" 
                  class="profile-input"
                  placeholder="请输入用户名"
                />
              </div>
              
              <div class="profile-field">
                <span class="profile-field__label">个人简介</span>
                <textarea 
                  v-model="form.bio" 
                  class="profile-input profile-input--textarea"
                  placeholder="请简单介绍自己..."
                ></textarea>
              </div>
              
              <div class="profile-meta-grid">
                <div class="profile-meta-card ui-panel-section">
                  <span class="profile-meta-card__label">邮箱</span>
                  <span class="profile-meta-card__value">{{ user?.email || '-' }}</span>
                </div>
                <div class="profile-meta-card ui-panel-section">
                  <span class="profile-meta-card__label">注册时间</span>
                  <span class="profile-meta-card__value">{{ registeredAtLabel }}</span>
                </div>
              </div>
              
              <div class="profile-field">
                <span class="profile-field__label">角色</span>
                <div class="profile-role-tags">
                <n-tag 
                  v-if="user?.role === 'admin'" 
                  type="error"
                  size="small"
                >
                  管理员
                </n-tag>
                <n-tag 
                  v-else-if="user?.role === 'writer'" 
                  type="success"
                  size="small"
                >
                  作者
                </n-tag>
                <n-tag 
                  v-else 
                  type="default"
                  size="small"
                >
                  {{ user?.role }}
                </n-tag>
                </div>
              </div>
            </div>
            
            <div class="profile-actions">
              <n-button 
                type="primary" 
                :loading="updatingUser || uploadingAvatar" 
                @click="handleSubmit"
              >
                保存资料
              </n-button>
            </div>
          </div>
        </div>
      </n-card>
      
      <n-card class="ui-shell-panel profile-card">
        <template #header>
          <h2 class="ui-shell-title">我的投稿</h2>
          <p class="profile-card__lead">最近提交的 {{ submittedNodes?.length || 0 }} 个节点会显示在这里。</p>
        </template>
        
        <n-spin :show="nodesLoading">
          <div v-if="!submittedNodes || submittedNodes.length === 0" class="profile-empty-state ui-panel-section">
            <p class="ui-shell-kicker">Archive / Empty</p>
            <h3 class="ui-shell-title">暂无投稿节点</h3>
            <p class="ui-page-section__lead">你还没有在这个账户下留下任何世界线分支。</p>
              <n-button 
                type="primary" 
                @click="handleStartWriting"
              >
              开始创作
            </n-button>
          </div>
          
          <div v-else class="profile-node-list">
            <article
              v-for="node in submittedNodes" 
              :key="node.id" 
              class="profile-node-card ui-panel-section"
              @click="handleOpenNode(node.id)"
            >
              <div class="profile-node-card__inner">
                <div class="profile-node-card__content">
                  <h3 class="profile-node-card__title">
                    {{ node.title || node.branch_name || '无标题' }}
                  </h3>
                  <p class="profile-node-card__summary">
                    {{ node.summary || '暂无摘要。' }}
                  </p>
                  <div class="profile-node-card__meta">
                    <span>{{ node.created_at ? formatDateTime(node.created_at) : '-' }}</span>
                    <span>{{ storyStatusLabel(node.status) }}</span>
                    <span>{{ node.likes_count || 0 }} 赞</span>
                    <span>{{ node.comments_count || 0 }} 评论</span>
                    <span>{{ node.children_count || 0 }} 分支</span>
                  </div>
                </div>
                <n-avatar 
                  :size="32" 
                  :src="node.author?.avatar ?? undefined"
                  class="profile-node-card__avatar"
                >
                  {{ node.author?.username?.charAt(0).toUpperCase() }}
                </n-avatar>
              </div>
            </article>
          </div>
        </n-spin>
      </n-card>
    </n-spin>
  </div>
</template>

<style scoped>
.profile-page {
  max-width: 1080px;
  margin: 0 auto;
  padding: 32px 16px 48px;
}

.profile-hero {
  grid-template-columns: minmax(0, 1.8fr) minmax(260px, 0.9fr);
  align-items: start;
}

.profile-hero__metrics {
  display: grid;
  gap: 12px;
}

.profile-card__lead {
  margin: 8px 0 0;
  color: var(--text-secondary);
  line-height: 1.7;
}

.profile-card__layout {
  display: grid;
  grid-template-columns: 220px minmax(0, 1fr);
  gap: 28px;
}

.profile-avatar-panel__inner {
  display: grid;
  gap: 16px;
  justify-items: center;
}

.profile-avatar-frame {
  position: relative;
}

.profile-avatar-frame__badge {
  position: absolute;
  right: -8px;
  bottom: -8px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 42px;
  height: 24px;
  padding: 0 8px;
  border: 1px solid var(--line-strong);
  background: rgba(255, 255, 255, 0.06);
  color: var(--text-primary);
  font-size: 10px;
  letter-spacing: 0.14em;
}

.profile-avatar-panel__progress {
  width: 100%;
}

.profile-form-panel {
  min-width: 0;
}

.profile-form-panel__title {
  margin: 0 0 18px;
  font-family: var(--font-display);
  font-size: 1.25rem;
  letter-spacing: 0.03em;
}

.profile-form-grid {
  display: grid;
  gap: 18px;
}

.profile-field {
  display: grid;
  gap: 8px;
}

.profile-field__label {
  color: var(--text-faint);
  font-size: 11px;
  letter-spacing: 0.18em;
  text-transform: uppercase;
}

.profile-input {
  width: 100%;
  min-height: 44px;
  padding: 0 14px;
  border: 1px solid var(--line-soft);
  background: rgba(255, 255, 255, 0.03);
  color: var(--text-primary);
  transition: border-color var(--transition-fast), box-shadow var(--transition-fast);
}

.profile-input:focus {
  outline: none;
  border-color: var(--line-strong);
  box-shadow: var(--glow-focus);
}

.profile-input::placeholder {
  color: var(--text-faint);
}

.profile-input--textarea {
  min-height: 120px;
  padding-top: 12px;
  resize: vertical;
}

.profile-meta-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.profile-meta-card {
  display: grid;
  gap: 8px;
  padding: 14px;
}

.profile-meta-card__label {
  color: var(--text-faint);
  font-size: 11px;
  letter-spacing: 0.18em;
  text-transform: uppercase;
}

.profile-meta-card__value {
  color: var(--text-secondary);
  line-height: 1.7;
  word-break: break-word;
}

.profile-role-tags {
  display: flex;
  align-items: center;
  gap: 8px;
}

.profile-actions {
  margin-top: 6px;
}

.profile-empty-state {
  display: grid;
  gap: 10px;
  padding: 28px;
  text-align: center;
  justify-items: center;
}

.profile-node-list {
  display: grid;
  gap: 12px;
}

.profile-node-card {
  cursor: pointer;
  transition: border-color var(--transition-fast), transform var(--transition-fast), box-shadow var(--transition-fast);
}

.profile-node-card:hover {
  border-color: var(--line-strong);
  box-shadow: var(--glow-focus);
  transform: translateY(-1px);
}

.profile-node-card__inner {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  padding: 16px;
}

.profile-node-card__content {
  min-width: 0;
  flex: 1;
}

.profile-node-card__title {
  margin: 0 0 8px;
  font-size: 1rem;
  letter-spacing: 0.02em;
}

.profile-node-card__summary {
  margin: 0;
  color: var(--text-secondary);
  line-height: 1.7;
}

.profile-node-card__meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 14px;
  margin-top: 12px;
  color: var(--text-faint);
  font-size: 12px;
}

.profile-node-card__avatar {
  flex-shrink: 0;
}

@media (max-width: 900px) {
  .profile-hero,
  .profile-card__layout {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 640px) {
  .profile-page {
    padding-inline: 12px;
  }

  .profile-meta-grid {
    grid-template-columns: 1fr;
  }

  .profile-node-card__inner {
    flex-direction: column;
  }
}
</style>
