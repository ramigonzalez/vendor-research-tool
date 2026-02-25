import type { StepStatus } from '../../lib/types'

interface PipelineStepperProps {
  stepStatuses: Record<string, StepStatus>
  elapsedTime: number
}

const steps = [
  { key: 'planning', label: 'Planning', icon: '\u{1F4DD}', color: 'bg-accent-primary' },
  { key: 'searching', label: 'Searching', icon: '\u{1F50D}', color: 'bg-status-searching' },
  { key: 'analyzing', label: 'Analyzing', icon: '\u{1F9E0}', color: 'bg-status-analyzing' },
  { key: 'scoring', label: 'Scoring', icon: '\u{1F4CA}', color: 'bg-status-searching' },
  { key: 'ranking', label: 'Ranking', icon: '\u{1F3C6}', color: 'bg-confidence-medium' },
  { key: 'writing', label: 'Writing', icon: '\u{270D}\uFE0F', color: 'bg-status-writing' },
  { key: 'complete', label: 'Complete', icon: '\u2705', color: 'bg-status-complete' },
] as const

function formatTime(seconds: number): string {
  const m = Math.floor(seconds / 60).toString().padStart(2, '0')
  const s = (seconds % 60).toString().padStart(2, '0')
  return `${m}:${s}`
}

export function PipelineStepper({ stepStatuses, elapsedTime }: PipelineStepperProps) {
  const activeIndex = steps.findIndex(s => stepStatuses[s.key] === 'active')

  return (
    <div className="my-4">
      {/* Desktop: horizontal stepper */}
      <div className="hidden md:flex items-center justify-between gap-1">
        {steps.map((step, i) => {
          const status = stepStatuses[step.key] || 'pending'
          const isComplete = status === 'complete'
          const isActive = status === 'active'

          return (
            <div key={step.key} className="flex items-center flex-1 last:flex-none">
              {/* Step circle */}
              <div className="flex flex-col items-center">
                <div
                  className={`w-9 h-9 rounded-full flex items-center justify-center text-sm transition-all duration-300
                    ${isComplete ? `${step.color} text-white` : ''}
                    ${isActive ? `${step.color} text-white animate-step-pulse` : ''}
                    ${!isComplete && !isActive ? 'bg-border-default text-text-tertiary' : ''}
                  `}
                >
                  {isComplete ? '\u2713' : step.icon}
                </div>
                <span className={`text-xs mt-1 ${isActive ? 'text-text-primary font-medium' : 'text-text-tertiary'}`}>
                  {step.label}
                </span>
              </div>

              {/* Connecting line */}
              {i < steps.length - 1 && (
                <div className="flex-1 h-0.5 mx-1 bg-border-default relative">
                  <div
                    className={`absolute inset-y-0 left-0 ${step.color} transition-all duration-300`}
                    style={{ width: isComplete ? '100%' : isActive ? '50%' : '0%' }}
                  />
                </div>
              )}
            </div>
          )
        })}

        {/* Timer */}
        <div className="ml-3 text-sm font-mono text-text-secondary whitespace-nowrap">
          {formatTime(elapsedTime)}
        </div>
      </div>

      {/* Mobile: condensed view */}
      <div className="md:hidden flex items-center gap-3 p-3 bg-bg-secondary rounded-sm">
        {activeIndex >= 0 ? (
          <>
            <span className="text-lg animate-step-pulse">{steps[activeIndex].icon}</span>
            <span className="text-sm font-medium">{steps[activeIndex].label}</span>
          </>
        ) : (
          <>
            <span className="text-lg">&#9203;</span>
            <span className="text-sm text-text-tertiary">Waiting...</span>
          </>
        )}
        <span className="ml-auto text-sm font-mono text-text-secondary">
          {formatTime(elapsedTime)}
        </span>
      </div>
    </div>
  )
}
