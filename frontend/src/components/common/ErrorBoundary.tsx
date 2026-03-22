import { Component, type ReactNode, type ErrorInfo } from 'react'

interface Props {
  children: ReactNode
  fallback?: ReactNode
}

interface State {
  hasError: boolean
  error: Error | null
}

export class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false, error: null }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error('ErrorBoundary caught:', error, info.componentStack)
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null })
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) return this.props.fallback

      return (
        <div className="flex flex-col items-center justify-center h-full p-4 text-center">
          <p className="text-red-400 text-sm font-medium mb-2">Something went wrong</p>
          <p className="text-gray-500 text-xs mb-3 max-w-xs break-words">
            {this.state.error?.message}
          </p>
          <button
            onClick={this.handleReset}
            className="text-xs px-3 py-1 bg-gray-700 rounded hover:bg-gray-600 text-gray-300"
          >
            Retry
          </button>
        </div>
      )
    }

    return this.props.children
  }
}
