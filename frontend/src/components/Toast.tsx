export type ToastKind = 'success' | 'error' | 'info';

export type ToastMessage = {
  kind: ToastKind;
  text: string;
};

type ToastProps = {
  message: ToastMessage;
  onDismiss: () => void;
};

export function Toast({ message, onDismiss }: ToastProps) {
  return (
    <div
      className={`toast ${message.kind}`}
      role={message.kind === 'error' ? 'alert' : 'status'}
    >
      <span className="toast-dot" aria-hidden="true" />
      <p>{message.text}</p>
      <button type="button" className="toast-dismiss" onClick={onDismiss} aria-label="Dismiss message">
        Dismiss
      </button>
    </div>
  );
}
