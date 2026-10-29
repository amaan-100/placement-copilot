import type { ReactNode } from 'react';

type PanelProps = {
  title: string;
  description?: string;
  action?: ReactNode;
  children: ReactNode;
  className?: string;
  id?: string;
  step?: string;
};

export function Panel({ title, description, action, children, className, id, step }: PanelProps) {
  return (
    <section id={id} className={['panel', className].filter(Boolean).join(' ')}>
      <div className="panel-heading">
        <div className="panel-title-group">
          {step ? (
            <span className="panel-gate" aria-hidden="true">
              {step}
            </span>
          ) : null}
          <div>
            <h2>{title}</h2>
            {description ? <p>{description}</p> : null}
          </div>
        </div>
        {action ? <div className="panel-action">{action}</div> : null}
      </div>
      {children}
    </section>
  );
}
