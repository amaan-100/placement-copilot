import type { InterviewEvaluation, InterviewStart } from '../api/types';
import { Icon } from './Icon';
import { Panel } from './Panel';

type InterviewPanelProps = {
  goal: string;
  interview: InterviewStart | null;
  answer: string;
  starting: boolean;
  evaluating: boolean;
  evaluation: InterviewEvaluation | null;
  pastInterviews: number;
  onAnswerChange: (value: string) => void;
  onStart: () => void;
  onEvaluate: () => void;
};

export function InterviewPanel({
  goal,
  interview,
  answer,
  starting,
  evaluating,
  evaluation,
  pastInterviews,
  onAnswerChange,
  onStart,
  onEvaluate,
}: InterviewPanelProps) {
  const score = evaluation ? Math.max(0, Math.min(100, evaluation.score)) : 0;

  return (
    <Panel
      id="practice"
      step="04"
      title="Interview practice"
      description="Answer one question at a time and get rubric-based feedback you can act on."
      action={
        <button type="button" className="button-secondary" onClick={onStart} disabled={starting}>
          <Icon name="mic" size={14} />
          {starting ? 'Preparing…' : interview ? 'New question' : 'Start practice'}
        </button>
      }
    >
      {interview ? (
        <div className="interview-shell">
          <p className="interview-question">{interview.question}</p>
          <label className="field-label" htmlFor="interview-answer">
            Your answer
          </label>
          <textarea
            id="interview-answer"
            value={answer}
            onChange={(event) => onAnswerChange(event.target.value)}
            placeholder="Give context, your approach, the evidence you would collect, and the outcome."
          />
          <div className="answer-meta">
            <span>{answer.length} characters</span>
            <span>Goal: {goal}</span>
          </div>
          <div className="interview-actions">
            <span className="inline-hint">Structure beats length. Name the trade-off.</span>
            <button
              type="button"
              onClick={onEvaluate}
              disabled={evaluating || answer.trim().length === 0}
            >
              {evaluating ? 'Scoring…' : 'Score answer'}
            </button>
          </div>
          {evaluation ? (
            <div className="result" aria-live="polite">
              <div className="result-head">
                <strong className="result-score">{evaluation.score}/100</strong>
                <span className="result-label">Rubric score</span>
              </div>
              <div className="result-meter" aria-hidden="true">
                <span style={{ transform: `scaleX(${score / 100})` }} />
              </div>
              <p>{evaluation.feedback}</p>
            </div>
          ) : null}
        </div>
      ) : (
        <div className="empty">
          <strong>No active practice session</strong>
          {pastInterviews > 0
            ? `You already have ${pastInterviews} practice run${pastInterviews === 1 ? '' : 's'} in this session. Start another to keep rehearsing.`
            : 'Start a mock interview to get a role-specific question and feedback on your answer.'}
        </div>
      )}
    </Panel>
  );
}
