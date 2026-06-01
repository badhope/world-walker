import axios from 'axios'
import type { AxiosInstance, AxiosRequestConfig, AxiosResponse, InternalAxiosRequestConfig } from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001'

const axiosInstance: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json',
  },
})

axiosInstance.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    return config
  },
  (error: unknown) => {
    return Promise.reject(error)
  }
)

axiosInstance.interceptors.response.use(
  (response: AxiosResponse) => {
    return response.data
  },
  (error: unknown) => {
    if (axios.isAxiosError(error)) {
      if (error.code === 'ECONNABORTED') {
        console.error('请求超时，请检查后端服务是否运行')
      } else if (error.code === 'ERR_NETWORK') {
        console.error('网络连接失败，请确认后端服务已启动 (端口 8001)')
      } else if (error.response) {
        const status = error.response.status
        const detail = (error.response.data as { detail?: string })?.detail || '未知错误'
        if (status >= 500) {
          console.error(`服务器错误 [${status}]: ${detail}`)
        } else if (status === 404) {
          console.error(`接口不存在 [404]: ${error.config?.url}`)
        } else if (status === 422) {
          console.error(`请求参数错误 [422]: ${detail}`)
        }
      } else {
        console.error('请求失败:', error.message)
      }
    }
    return Promise.reject(error)
  }
)

export const request = {
  get<T = unknown>(url: string, config?: AxiosRequestConfig): Promise<T> {
    return axiosInstance.get(url, config)
  },
  post<T = unknown>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<T> {
    return axiosInstance.post(url, data, config)
  },
  put<T = unknown>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<T> {
    return axiosInstance.put(url, data, config)
  },
  delete<T = unknown>(url: string, config?: AxiosRequestConfig): Promise<T> {
    return axiosInstance.delete(url, config)
  },
}

export default axiosInstance