/**
 * Todo Task List - TODO 任务列表组件
 * 展示任务执行步骤、状态、进度
 */
import { useState } from 'react'
import { ChevronDown, CheckCircle2, Clock, AlertCircle, Loader2, Tool } from 'lucide-react'
import { cn } from '@/lib/utils'

interface TaskStep {
  id: string
  title: string
  description?: string
  status: 'pending' | 'running' | 'completed' | 'failed'
  tool_name?: string
  tool_input?: any
  tool_output?: any
  error?: string
  retry_count?: number
  started_at?: string
  completed_at?: string
}

interface Task {
  id: string
  user_input: string
  status: string
  todo_list?: TaskStep[]
  current_step_index: number
  error_info?: string | null
}

interface TodoTaskListProps {
  task: Task
}

export default function TodoTaskList({ task }: TodoTaskListProps) {
  const [isExpanded, setIsExpanded] = useState(true)

  const steps = task.todo_list || []
  const completedCount = steps.filter((s) => s.status === 'completed').length
  const totalCount = steps.length
  const progressPercentage = totalCount > 0 ? (completedCount / totalCount) * 100 : 0

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle2 className="w-5 h-5 text-success" />
      case 'running':
        return <Loader2 className="w-5 h-5 text-info animate-spin" />
      case 'failed':
        return <AlertCircle className="w-5 h-5 text-destructive" />
      default:
        return <Clock className="w-5 h-5 text-muted" />
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-success/10 border-success/30'
      case 'running':
        return 'bg-info/10 border-info/30 ring-2 ring-info/20'
      case 'failed':
        return 'bg-destructive/10 border-destructive/30'
      default:
        return 'bg-muted/5 border-border'
    }
  }

  const getStatusText = (status: string) => {
    switch (status) {
      case 'completed':
        return '已完成'
      case 'running':
        return '执行中'
      case 'failed':
        return '失败'
      default:
        return '待执行'
    }
  }

  if (steps.length === 0) {
    return (
      <div className="text-center py-8 text-muted">
        <Clock className="w-12 h-12 mx-auto mb-2 opacity-50" />
        <p>等待任务规划...</p>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="flex items-center gap-2 text-sm font-semibold text-foreground hover:text-primary transition-smooth"
        >
          <ChevronDown
            className={cn(
              'w-4 h-4 transition-transform',
              !isExpanded && '-rotate-90'
            )}
          />
          <span>步骤 {completedCount}/{totalCount}</span>
        </button>

        {/* Status Badge */}
        <span className={cn(
          'px-3 py-1 rounded-full text-xs font-medium',
          task.status === 'success' && 'bg-success/20 text-success',
          task.status === 'failed' && 'bg-destructive/20 text-destructive',
          task.status === 'running' && 'bg-info/20 text-info'
        )}>
          {task.status === 'success' && '✓ 已完成'}
          {task.status === 'failed' && '✗ 失败'}
          {task.status === 'running' && '⚡ 进行中'}
          {task.status === 'pending' && '⏸️ 待执行'}
        </span>
      </div>

      {/* Progress Bar */}
      <div className="space-y-2">
        <div className="w-full bg-muted/20 rounded-full h-2 overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-primary to-accent transition-all duration-500 ease-out"
            style={{ width: `${progressPercentage}%` }}
          />
        </div>
        <p className="text-xs text-muted text-right">
          {progressPercentage.toFixed(0)}% 完成
        </p>
      </div>

      {/* Task Steps */}
      {isExpanded && (
        <div className="space-y-3">
          {steps.map((step, idx) => (
            <div
              key={step.id}
              className={cn(
                'p-4 rounded-lg border transition-smooth',
                getStatusColor(step.status),
                step.status === 'running' && 'shadow-md'
              )}
            >
              <div className="flex items-start gap-3">
                {/* Status Icon */}
                <div className="flex-shrink-0 mt-0.5">
                  {getStatusIcon(step.status)}
                </div>

                {/* Content */}
                <div className="flex-1 min-w-0">
                  {/* Title */}
                  <div className="flex items-center gap-2 mb-1">
                    <p className="text-sm font-medium text-foreground">
                      {step.title}
                    </p>
                    <span className="text-xs text-muted bg-muted/10 px-2 py-0.5 rounded">
                      #{idx + 1}
                    </span>
                  </div>

                  {/* Description */}
                  {step.description && (
                    <p className="text-xs text-muted mt-1">
                      {step.description}
                    </p>
                  )}

                  {/* Tool Info */}
                  {step.tool_name && (
                    <div className="flex items-center gap-1 mt-2">
                      <Tool className="w-3 h-3 text-muted" />
                      <p className="text-xs text-muted">
                        Tool: <span className="font-mono text-foreground">{step.tool_name}</span>
                      </p>
                    </div>
                  )}

                  {/* Error Message */}
                  {step.error && (
                    <div className="mt-2 p-2 bg-destructive/10 rounded text-xs text-destructive border border-destructive/30">
                      <strong>错误:</strong> {step.error}
                    </div>
                  )}

                  {/* Result */}
                  {step.tool_output && step.status === 'completed' && (
                    <div className="mt-2 p-2 bg-success/10 rounded text-xs text-success border border-success/30">
                      <strong>结果:</strong> {typeof step.tool_output === 'object'
                        ? JSON.stringify(step.tool_output, null, 2)
                        : String(step.tool_output)}
                    </div>
                  )}
                </div>

                {/* Retry Count */}
                {step.retry_count && step.retry_count > 0 && (
                  <div className="text-xs text-muted bg-muted/10 px-2 py-1 rounded">
                    重试 {step.retry_count}
                  </div>
                )}
              </div>

              {/* Status Label */}
              <div className="mt-2 flex items-center justify-between">
                <span className={cn(
                  'text-xs font-medium',
                  step.status === 'completed' && 'text-success',
                  step.status === 'running' && 'text-info',
                  step.status === 'failed' && 'text-destructive',
                  step.status === 'pending' && 'text-muted'
                )}>
                  {getStatusText(step.status)}
                </span>

                {/* Timestamps */}
                {step.started_at && (
                  <span className="text-xs text-muted">
                    {new Date(step.started_at).toLocaleTimeString()}
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Error Info (if task failed) */}
      {task.error_info && (
        <div className="mt-4 p-4 bg-destructive/10 rounded-lg border border-destructive/30">
          <div className="flex items-start gap-2">
            <AlertCircle className="w-5 h-5 text-destructive flex-shrink-0 mt-0.5" />
            <div>
              <h3 className="text-sm font-semibold text-destructive mb-1">任务失败</h3>
              <p className="text-xs text-destructive/80">{task.error_info}</p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
