import React from 'react';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger' | 'success';
  size?: 'sm' | 'md' | 'lg' | 'xl';
  isLoading?: boolean;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
}

export const Button: React.FC<ButtonProps> = ({
  children,
  variant = 'primary',
  size = 'md',
  isLoading = false,
  leftIcon,
  rightIcon,
  className = '',
  disabled,
  ...props
}) => {
  const baseStyles =
    'inline-flex items-center justify-center font-medium transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-sky-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed select-none rounded-xl active:scale-[0.98] cursor-pointer';

  const variantStyles = {
    primary:
      'bg-sky-600 text-white hover:bg-sky-700 shadow-sm hover:shadow active:bg-sky-800 border border-sky-600',
    secondary:
      'bg-slate-100 text-slate-800 hover:bg-slate-200 border border-slate-200 active:bg-slate-300',
    outline:
      'bg-white text-slate-700 hover:bg-slate-50 border border-slate-300 active:bg-slate-100 shadow-xs',
    ghost:
      'bg-transparent text-slate-600 hover:bg-slate-100 active:bg-slate-200',
    danger:
      'bg-rose-600 text-white hover:bg-rose-700 shadow-sm border border-rose-600',
    success:
      'bg-emerald-600 text-white hover:bg-emerald-700 shadow-sm border border-emerald-600',
  };

  const sizeStyles = {
    sm: 'text-xs px-3 py-1.5 gap-1.5 min-h-[32px]',
    md: 'text-sm px-4 py-2.5 gap-2 min-h-[40px]',
    lg: 'text-base px-6 py-3.5 gap-2.5 min-h-[48px]',
    xl: 'text-lg px-8 py-4 gap-3 min-h-[56px] font-semibold',
  };

  return (
    <button
      className={`${baseStyles} ${variantStyles[variant]} ${sizeStyles[size]} ${className}`}
      disabled={disabled || isLoading}
      {...props}
    >
      {isLoading ? (
        <svg
          className="animate-spin h-4 w-4 text-current"
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
        >
          <circle
            className="opacity-25"
            cx="12"
            cy="12"
            r="10"
            stroke="currentColor"
            strokeWidth="4"
          />
          <path
            className="opacity-75"
            fill="currentColor"
            d="M4 12a8 8 0 018-8v8H4z"
          />
        </svg>
      ) : (
        leftIcon
      )}
      {children}
      {!isLoading && rightIcon}
    </button>
  );
};
