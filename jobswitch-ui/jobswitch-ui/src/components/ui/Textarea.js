import React from 'react';

export const Textarea = ({ 
  className = '', 
  disabled = false,
  rows = 3,
  ...props 
}) => {
  const baseClasses = 'block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-50 disabled:text-gray-500 resize-vertical';
  
  return (
    <textarea 
      rows={rows}
      className={`${baseClasses} ${className}`}
      disabled={disabled}
      {...props}
    />
  );
};