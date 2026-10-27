import type { InterviewEvaluation, InterviewStart } from '../api/types';
import { Panel } from './Panel';

type InterviewPanelProps = {
  goal: string;
  interview: InterviewStart | null;
  answer: string;
  starting: boolean;
  evaluating: boolean;
  evaluation: InterviewEvaluation | null;
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
  onAnswerChange,
  onStart,
  onEvaluate,
}: InterviewPanelProps) {
  return (
    <Panel
      title="Interview practice"
      description="Answer one question at a time and get rubric-based feedback you can act on."
      action={
        <button type="button" className="button-secondary" onClick={onStart} disabled={starting}>
          {starting ? 'Preparing…' : interview ? 'New question' : 'Start practice'}
        </button>
      }
    >
      {interview ? (
        <div>
          <p className="interview-question">{interview.question}</p>
          <textarea
            value={answer}
            onChange={(event) => onAnswerChange(event.target.value)}
            placeholder="Give context, your approach, the evidence you would collect, and the outcome."
            aria-label="Interview answer"
          />
          <div className="answer-meta">
            <span>{answer.length} characters</span>
            <span>Goal: {goal}</span>
          </div>
          <div className="interview-actions">
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
              <div className="result-score">{evaluation.score}/100</div>
              <p>{evaluation.feedback}</p>
            </div>
          ) : null}
        </div>
      ) : (
        <div className="empty">
          <strong>No practice session yet</strong>
          Start a mock interview to get a role-specific question and feedback on your answer.
        </div>
      )}
    </Panel>
  );
}
