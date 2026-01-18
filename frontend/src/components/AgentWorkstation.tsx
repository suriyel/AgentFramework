/**
 * Agent Workstation - 主工作台组件
 * Neo-Swiss 设计风格
 */
import { useState, useEffect, useRef } from 'react'
import { Plus, Send, Settings } from 'lucide-react'
import TodoTaskList from './TodoTaskList'
import LLMSettings from './LLMSettings'
import axios from 'axios'

interface Task {
  id: string
  conversation_id: string
  user_input: string
  status: string
  todo_list?: any[]
  current_step_index: number
  error_info?: string | null
}

interface Message {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  task?: Task
}

export default function AgentWorkstation() {
  const [conversationId, setConversationId] = useState<string | null>(null)
  const [messages, setMessages] = useState<Message[]>([])
  const [currentTask, setCurrentTask] = useState<Task | null>(null)
  const [inputValue, setInputValue] = useState('')
  const [isConnected, setIsConnected] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [showSettings, setShowSettings] = useState(false)

  const wsRef = useRef<WebSocket | null>(null)
  const userId = 'demo_user' // 实际应从认证系统获取

  // 初始化对话
  useEffect(() => {
    initializeConversation()
  }, [])

  const initializeConversation = async () => {
    try {
      const response = await axios.post('/api/v1/conversations', {
        user_id: userId,
        title: `Conversation ${new Date().toLocaleTimeString()}`
      })

      setConversationId(response.data.id)
      connectWebSocket(response.data.id)
    } catch (error) {
      console.error('Failed to create conversation:', error)
    }
  }

  const connectWebSocket = (convId: string) => {
    const ws = new WebSocket(`ws://localhost:8000/ws/${convId}`)

    ws.onopen = () => {
      console.log('WebSocket connected')
      setIsConnected(true)
    }

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data)
      handleWebSocketMessage(data)
    }

    ws.onerror = (error) => {
      console.error('WebSocket error:', error)
      setIsConnected(false)
    }

    ws.onclose = () => {
      console.log('WebSocket disconnected')
      setIsConnected(false)
      // 自动重连
      setTimeout(() => connectWebSocket(convId), 3000)
    }

    wsRef.current = ws
  }

  const handleWebSocketMessage = (data: any) => {
    console.log('Received:', data)

    switch (data.type) {
      case 'task_created':
        setIsLoading(true)
        break

      case 'state_update':
        // 更新任务状态
        const taskData = data.data
        setCurrentTask({
          id: taskData.conversation_id || 'unknown',
          conversation_id: taskData.conversation_id,
          user_input: taskData.user_input,
          status: taskData.final_status || 'running',
          todo_list: taskData.todo_list || [],
          current_step_index: taskData.current_step_index || 0,
          error_info: taskData.error_info
        })

        // 如果任务完成，添加 assistant 消息
        if (taskData.final_status === 'success' || taskData.final_status === 'failed') {
          setIsLoading(false)
          const resultMessage: Message = {
            id: Date.now().toString(),
            role: 'assistant',
            content: taskData.final_status === 'success'
              ? '任务已完成！'
              : `任务失败：${taskData.error_info || '未知错误'}`,
            task: currentTask
          }
          setMessages(prev => [...prev, resultMessage])
        }
        break

      case 'task_error':
        setIsLoading(false)
        alert(`任务错误: ${data.data.error}`)
        break
    }
  }

  const handleSendMessage = () => {
    if (!inputValue.trim() || !wsRef.current || !isConnected) return

    // 添加用户消息
    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: inputValue
    }
    setMessages(prev => [...prev, userMessage])

    // 发送到后端
    wsRef.current.send(JSON.stringify({
      type: 'start_task',
      user_input: inputValue,
      user_id: userId
    }))

    setInputValue('')
    setIsLoading(true)
  }

  // Show settings panel
  if (showSettings) {
    return (
      <div className="flex flex-col h-screen bg-background">
        <header className="border-b border-border bg-white px-6 py-4">
          <div className="flex items-center justify-between">
            <h1 className="text-2xl font-bold text-foreground">Agent Workstation</h1>
            <button
              onClick={() => setShowSettings(false)}
              className="px-4 py-2 text-sm border border-border rounded-lg hover:bg-muted/10 transition-smooth"
            >
              返回工作台
            </button>
          </div>
        </header>
        <div className="flex-1 overflow-y-auto">
          <LLMSettings />
        </div>
      </div>
    )
  }

  return (
    <div className="flex flex-col h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border bg-white px-6 py-4">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold text-foreground">Agent Workstation</h1>
          <div className="flex items-center gap-4">
            <button
              onClick={() => setShowSettings(true)}
              className="flex items-center gap-2 px-4 py-2 text-sm border border-border rounded-lg hover:bg-muted/10 transition-smooth"
            >
              <Settings className="w-4 h-4" />
              LLM 设置
            </button>
            <div className="flex items-center gap-2">
              <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-success' : 'bg-destructive'}`} />
              <span className="text-sm text-muted">
                {isConnected ? 'Connected' : 'Disconnected'}
              </span>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Chat Area */}
        <div className="flex-1 flex flex-col bg-background">
          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-6 space-y-4">
            {messages.length === 0 && (
              <div className="flex-center flex-col h-full text-center space-y-4">
                <div className="text-6xl">🤖</div>
                <h2 className="text-2xl font-bold text-foreground">欢迎使用 Agent Workstation</h2>
                <p className="text-muted max-w-md">
                  输入您的任务需求，AI Agent 将自动规划并执行步骤，实时展示进度。
                </p>
              </div>
            )}

            {messages.map((msg) => (
              <div
                key={msg.id}
                className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-2xl rounded-lg p-4 ${
                    msg.role === 'user'
                      ? 'bg-primary text-white'
                      : 'bg-white border border-border'
                  }`}
                >
                  <p className="text-sm">{msg.content}</p>
                </div>
              </div>
            ))}

            {/* Loading Indicator */}
            {isLoading && (
              <div className="flex justify-start">
                <div className="max-w-2xl rounded-lg p-4 bg-white border border-border">
                  <div className="flex items-center gap-2">
                    <div className="animate-spin w-4 h-4 border-2 border-primary border-t-transparent rounded-full" />
                    <span className="text-sm text-muted">AI Agent 正在处理...</span>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Input Area */}
          <div className="border-t border-border bg-white p-4">
            <div className="flex gap-2">
              <input
                type="text"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
                placeholder="输入任务需求，例如：帮我查询北京的天气..."
                className="flex-1 px-4 py-3 border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
                disabled={!isConnected || isLoading}
              />
              <button
                onClick={handleSendMessage}
                disabled={!isConnected || isLoading || !inputValue.trim()}
                className="px-6 py-3 bg-primary text-white rounded-lg hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed transition-smooth flex-center gap-2"
              >
                <Send className="w-5 h-5" />
              </button>
            </div>
          </div>
        </div>

        {/* Task Progress Panel */}
        {currentTask && (
          <div className="w-96 border-l border-border bg-white overflow-y-auto">
            <div className="p-6">
              <h2 className="text-lg font-bold text-foreground mb-4">Task Progress</h2>
              <TodoTaskList task={currentTask} />
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
