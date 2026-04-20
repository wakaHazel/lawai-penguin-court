import { Component, type ErrorInfo, type ReactNode } from "react";

interface TrialSimulationErrorBoundaryProps {
  children: ReactNode;
}

interface TrialSimulationErrorBoundaryState {
  hasError: boolean;
}

export class TrialSimulationErrorBoundary extends Component<
  TrialSimulationErrorBoundaryProps,
  TrialSimulationErrorBoundaryState
> {
  state: TrialSimulationErrorBoundaryState = {
    hasError: false,
  };

  static getDerivedStateFromError(): TrialSimulationErrorBoundaryState {
    return {
      hasError: true,
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    console.error("TrialSimulationErrorBoundary", error, errorInfo);
  }

  render(): ReactNode {
    if (this.state.hasError) {
      return (
        <section className="trial-simulation-page__error" role="alert">
          庭审模拟组件出现异常，请刷新页面后重试。
        </section>
      );
    }

    return this.props.children;
  }
}
