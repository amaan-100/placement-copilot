import type { SVGProps } from 'react';

export type IconName =
  | 'activity'
  | 'arrow'
  | 'briefcase'
  | 'check'
  | 'chevron'
  | 'clock'
  | 'file'
  | 'lock'
  | 'mic'
  | 'route'
  | 'search'
  | 'shield'
  | 'spark';

type IconProps = {
  name: IconName;
  size?: number;
  className?: string;
  strokeWidth?: number;
};

function shape(name: IconName): SVGProps<SVGPathElement>['d'] | null {
  switch (name) {
    case 'activity':
      return 'M3 12h4l2.5-7 5 14 2.5-7h4';
    case 'arrow':
      return 'M7 17 17 7M8 7h9v9';
    case 'briefcase':
      return 'M9 7V5h6v2M4 8h16v11H4zM4 12h16';
    case 'check':
      return 'm5 12 4 4L19 6';
    case 'chevron':
      return 'm9 6 6 6-6 6';
    case 'clock':
      return 'M12 8v4l2.5 2.5M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z';
    case 'file':
      return 'M14 3H6v18h12V7zM14 3v4h4M9 13h6M9 17h4';
    case 'lock':
      return 'M7 11V8a5 5 0 0 1 10 0v3M5 11h14v10H5zM12 15v2';
    case 'mic':
      return 'M12 4a3 3 0 0 1 3 3v5a3 3 0 1 1-6 0V7a3 3 0 0 1 3-3ZM5 11a7 7 0 0 0 14 0M12 18v3M9 21h6';
    case 'route':
      return 'M7 6a2 2 0 1 1-4 0 2 2 0 0 1 4 0ZM21 18a2 2 0 1 1-4 0 2 2 0 0 1 4 0ZM5 8v2a4 4 0 0 0 4 4h6a4 4 0 0 1 4 4';
    case 'search':
      return 'M11 19a8 8 0 1 0 0-16 8 8 0 0 0 0 16ZM21 21l-4.3-4.3';
    case 'shield':
      return 'M12 3 5 6v5c0 4.7 3 8 7 10 4-2 7-5.3 7-10V6zM9 12l2 2 4-4';
    case 'spark':
      return 'm12 3 1.8 5.2L19 10l-5.2 1.8L12 17l-1.8-5.2L5 10l5.2-1.8zM19 16l.8 2.2L22 19l-2.2.8L19 22l-.8-2.2L16 19l2.2-.8z';
    default:
      return null;
  }
}

export function Icon({ name, size = 18, className, strokeWidth = 1.8 }: IconProps) {
  const path = shape(name);

  return (
    <svg
      className={className}
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={strokeWidth}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      focusable="false"
    >
      {path ? <path d={path} /> : null}
    </svg>
  );
}
