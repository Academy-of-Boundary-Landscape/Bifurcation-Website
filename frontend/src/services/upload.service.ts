import api from './api'

// 上传图片
export const uploadImage = (file: File) => {
  const formData = new FormData()
  formData.append('file', file)

  return api.post<{ url: string }>('/uploads/', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  })
}