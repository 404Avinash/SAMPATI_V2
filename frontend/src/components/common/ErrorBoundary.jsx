import React from "react";

/**
 * Standard Error Boundary component for catching rendering errors
 * in React component subtrees and rendering a graceful fallback alert.
 */
export class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error("ErrorBoundary caught an unhandled rendering error:", error, errorInfo);
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null });
    if (this.props.onReset) {
      this.props.onReset();
    }
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return typeof this.props.fallback === "function"
          ? this.props.fallback({ error: this.state.error, reset: this.handleReset })
          : this.props.fallback;
      }

      return (
        <div className="p-6 m-4 bg-amber-50/80 border border-amber-200 rounded-xl text-ink-900 shadow-sm">
          <div className="flex items-start gap-3">
            <span className="text-2xl select-none" role="img" aria-label="warning">
              ⚠️
            </span>
            <div className="flex-1 min-w-0 space-y-2">
              <h3 className="font-serif font-bold text-base text-amber-900">
                {this.props.title || "Interface View Temporarily Unavailable"}
              </h3>
              <p className="text-xs text-amber-800 leading-relaxed font-mono">
                {this.state.error?.message || "An unexpected error occurred while rendering this component."}
              </p>
              <div className="pt-2 flex items-center gap-3">
                <button
                  type="button"
                  onClick={this.handleReset}
                  className="px-3 py-1.5 bg-amber-600 hover:bg-amber-700 text-white rounded font-mono text-xs font-semibold transition-colors shadow-xs"
                >
                  Reload Component
                </button>
                <button
                  type="button"
                  onClick={() => window.location.reload()}
                  className="px-3 py-1.5 bg-white hover:bg-slate-50 text-slate-700 border border-slate-300 rounded font-mono text-xs font-semibold transition-colors shadow-xs"
                >
                  Refresh Page
                </button>
              </div>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
