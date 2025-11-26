const LOCAL_API_BASE_URL = 'http://localhost:5000/api'
const PROD_API_BASE_URL = 'https://student-analytics-backend-470050740360.asia-east1.run.app/api'

const detectEnvironment = () => {
  try {
    if (typeof window === 'undefined' || !window.location) {
      return 'production'
    }
    const hostname = window.location.hostname
    if (hostname === 'localhost' || hostname === '127.0.0.1') {
      return 'development'
    }
    return 'production'
  } catch (error) {
    return 'production'
  }
}

const ENVIRONMENT = detectEnvironment()
const API_BASE_URL = ENVIRONMENT === 'development' ? LOCAL_API_BASE_URL : PROD_API_BASE_URL

export const isDevelopmentEnvironment = () => ENVIRONMENT === 'development'

export const getEnvironmentInfo = () => ({
  environment: ENVIRONMENT,
  hostname:
    typeof window !== 'undefined' && window.location
      ? window.location.hostname
      : 'server',
  apiBaseUrl: API_BASE_URL
})

export { API_BASE_URL }
