/**
 * LLM Settings - LLM配置管理界面
 * 支持多个LLM平台配置
 */
import { useState, useEffect } from 'react'
import { Settings, Check, AlertCircle, Loader2 } from 'lucide-react'
import axios from 'axios'

interface LLMProvider {
  id: string
  name: string
  description: string
  models: string[]
  required_fields: string[]
  optional_fields: string[]
}

interface LLMConfig {
  provider: string
  model_name: string
  temperature: number
  max_tokens: number
  [key: string]: any
}

export default function LLMSettings() {
  const [providers, setProviders] = useState<LLMProvider[]>([])
  const [selectedProvider, setSelectedProvider] = useState<string>('ollama')
  const [currentConfig, setCurrentConfig] = useState<LLMConfig | null>(null)
  const [formData, setFormData] = useState<any>({
    temperature: 0.7,
    max_tokens: 2048
  })
  const [isLoading, setIsLoading] = useState(false)
  const [isTesting, setIsTesting] = useState(false)
  const [testResult, setTestResult] = useState<{success: boolean; message: string} | null>(null)

  // 加载提供商列表
  useEffect(() => {
    loadProviders()
    loadCurrentConfig()
  }, [])

  const loadProviders = async () => {
    try {
      const response = await axios.get('/api/v1/llm/providers')
      setProviders(response.data.providers)
    } catch (error) {
      console.error('Failed to load providers:', error)
    }
  }

  const loadCurrentConfig = async () => {
    try {
      const response = await axios.get('/api/v1/llm/config')
      setCurrentConfig(response.data)
      setSelectedProvider(response.data.provider)
      setFormData({
        ...formData,
        model_name: response.data.model_name,
        temperature: response.data.temperature,
        max_tokens: response.data.max_tokens
      })
    } catch (error) {
      console.log('No current config found')
    }
  }

  const handleSaveConfig = async () => {
    setIsLoading(true)
    try {
      const config = {
        provider: selectedProvider,
        ...formData
      }

      await axios.post('/api/v1/llm/config', config)

      alert('配置已保存成功！')
      loadCurrentConfig()
    } catch (error: any) {
      alert(`保存失败: ${error.response?.data?.detail || error.message}`)
    } finally {
      setIsLoading(false)
    }
  }

  const handleTestLLM = async () => {
    setIsTesting(true)
    setTestResult(null)
    try {
      const response = await axios.post('/api/v1/llm/test')
      setTestResult(response.data)
    } catch (error: any) {
      setTestResult({
        success: false,
        message: error.response?.data?.detail || error.message
      })
    } finally {
      setIsTesting(false)
    }
  }

  const currentProvider = providers.find(p => p.id === selectedProvider)

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <Settings className="w-8 h-8 text-primary" />
        <div>
          <h1 className="text-2xl font-bold text-foreground">LLM 配置</h1>
          <p className="text-sm text-muted">配置大模型提供商和参数</p>
        </div>
      </div>

      {/* Current Config Status */}
      {currentConfig && (
        <div className="bg-success/10 border border-success/30 rounded-lg p-4">
          <div className="flex items-center gap-2">
            <Check className="w-5 h-5 text-success" />
            <div>
              <p className="text-sm font-medium text-success">当前配置</p>
              <p className="text-xs text-muted">
                {currentProvider?.name} - {currentConfig.model_name}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Provider Selection */}
      <div className="bg-white border border-border rounded-lg p-6 space-y-4">
        <h2 className="text-lg font-semibold text-foreground">选择 LLM 提供商</h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {providers.map((provider) => (
            <button
              key={provider.id}
              onClick={() => setSelectedProvider(provider.id)}
              className={`p-4 border-2 rounded-lg text-left transition-smooth ${
                selectedProvider === provider.id
                  ? 'border-primary bg-primary/5'
                  : 'border-border hover:border-primary/50'
              }`}
            >
              <h3 className="font-semibold text-foreground">{provider.name}</h3>
              <p className="text-xs text-muted mt-1">{provider.description}</p>
            </button>
          ))}
        </div>
      </div>

      {/* Configuration Form */}
      {currentProvider && (
        <div className="bg-white border border-border rounded-lg p-6 space-y-4">
          <h2 className="text-lg font-semibold text-foreground">配置参数</h2>

          <div className="space-y-4">
            {/* Model Selection */}
            {currentProvider.models.length > 0 && (
              <div>
                <label className="block text-sm font-medium text-foreground mb-2">
                  模型选择 *
                </label>
                <select
                  value={formData.model_name || ''}
                  onChange={(e) => setFormData({...formData, model_name: e.target.value})}
                  className="w-full px-4 py-2 border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
                >
                  <option value="">请选择模型</option>
                  {currentProvider.models.map((model) => (
                    <option key={model} value={model}>{model}</option>
                  ))}
                </select>
              </div>
            )}

            {/* Dynamic Fields */}
            {selectedProvider === 'dashscope' && (
              <div>
                <label className="block text-sm font-medium text-foreground mb-2">
                  API Key *
                </label>
                <input
                  type="password"
                  value={formData.api_key || ''}
                  onChange={(e) => setFormData({...formData, api_key: e.target.value})}
                  placeholder="输入阿里百炼 API Key"
                  className="w-full px-4 py-2 border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
                />
              </div>
            )}

            {selectedProvider === 'openai' && (
              <>
                <div>
                  <label className="block text-sm font-medium text-foreground mb-2">
                    API Key *
                  </label>
                  <input
                    type="password"
                    value={formData.api_key || ''}
                    onChange={(e) => setFormData({...formData, api_key: e.target.value})}
                    placeholder="输入 OpenAI API Key"
                    className="w-full px-4 py-2 border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-foreground mb-2">
                    Base URL (可选)
                  </label>
                  <input
                    type="text"
                    value={formData.base_url || ''}
                    onChange={(e) => setFormData({...formData, base_url: e.target.value})}
                    placeholder="https://api.openai.com/v1"
                    className="w-full px-4 py-2 border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
                  />
                </div>
              </>
            )}

            {selectedProvider === 'zhipuai' && (
              <div>
                <label className="block text-sm font-medium text-foreground mb-2">
                  API Key *
                </label>
                <input
                  type="password"
                  value={formData.api_key || ''}
                  onChange={(e) => setFormData({...formData, api_key: e.target.value})}
                  placeholder="输入智谱AI API Key"
                  className="w-full px-4 py-2 border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
                />
              </div>
            )}

            {selectedProvider === 'ollama' && (
              <div>
                <label className="block text-sm font-medium text-foreground mb-2">
                  Base URL *
                </label>
                <input
                  type="text"
                  value={formData.base_url || 'http://localhost:11434'}
                  onChange={(e) => setFormData({...formData, base_url: e.target.value})}
                  placeholder="http://localhost:11434"
                  className="w-full px-4 py-2 border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
                />
              </div>
            )}

            {/* Temperature */}
            <div>
              <label className="block text-sm font-medium text-foreground mb-2">
                Temperature: {formData.temperature}
              </label>
              <input
                type="range"
                min="0"
                max="2"
                step="0.1"
                value={formData.temperature}
                onChange={(e) => setFormData({...formData, temperature: parseFloat(e.target.value)})}
                className="w-full"
              />
              <p className="text-xs text-muted mt-1">控制输出随机性，值越高越随机</p>
            </div>

            {/* Max Tokens */}
            <div>
              <label className="block text-sm font-medium text-foreground mb-2">
                Max Tokens
              </label>
              <input
                type="number"
                value={formData.max_tokens}
                onChange={(e) => setFormData({...formData, max_tokens: parseInt(e.target.value)})}
                className="w-full px-4 py-2 border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
              />
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex gap-3 pt-4">
            <button
              onClick={handleSaveConfig}
              disabled={isLoading}
              className="flex-1 px-6 py-3 bg-primary text-white rounded-lg hover:bg-primary/90 disabled:opacity-50 transition-smooth flex-center gap-2"
            >
              {isLoading && <Loader2 className="w-5 h-5 animate-spin" />}
              保存配置
            </button>

            <button
              onClick={handleTestLLM}
              disabled={isTesting || !currentConfig}
              className="px-6 py-3 border-2 border-primary text-primary rounded-lg hover:bg-primary/5 disabled:opacity-50 transition-smooth flex-center gap-2"
            >
              {isTesting && <Loader2 className="w-5 h-5 animate-spin" />}
              测试连接
            </button>
          </div>
        </div>
      )}

      {/* Test Result */}
      {testResult && (
        <div className={`border-2 rounded-lg p-4 ${
          testResult.success
            ? 'border-success/30 bg-success/10'
            : 'border-destructive/30 bg-destructive/10'
        }`}>
          <div className="flex items-start gap-2">
            {testResult.success ? (
              <Check className="w-5 h-5 text-success flex-shrink-0 mt-0.5" />
            ) : (
              <AlertCircle className="w-5 h-5 text-destructive flex-shrink-0 mt-0.5" />
            )}
            <div className="flex-1">
              <p className={`text-sm font-medium ${
                testResult.success ? 'text-success' : 'text-destructive'
              }`}>
                {testResult.success ? '测试成功' : '测试失败'}
              </p>
              <p className="text-xs text-muted mt-1">{testResult.message}</p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
