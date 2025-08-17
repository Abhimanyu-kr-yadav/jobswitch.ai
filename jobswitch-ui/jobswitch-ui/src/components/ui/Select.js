import React, { useState, createContext, useContext } from 'react';

const SelectContext = createContext();

export const Select = ({ children, value, onValueChange, defaultValue, ...props }) => {
  const [selectedValue, setSelectedValue] = useState(value || defaultValue || '');
  const [isOpen, setIsOpen] = useState(false);
  
  const handleValueChange = (newValue) => {
    if (onValueChange) {
      onValueChange(newValue);
    } else {
      setSelectedValue(newValue);
    }
    setIsOpen(false);
  };
  
  const currentValue = value !== undefined ? value : selectedValue;
  
  return (
    <SelectContext.Provider value={{ 
      selectedValue: currentValue, 
      setSelectedValue: handleValueChange,
      isOpen,
      setIsOpen
    }}>
      <div className="relative" {...props}>
        {children}
      </div>
    </SelectContext.Provider>
  );
};

export const SelectTrigger = ({ children, className = '', ...props }) => {
  const { isOpen, setIsOpen } = useContext(SelectContext);
  
  return (
    <button
      type="button"
      className={`flex h-10 w-full items-center justify-between rounded-md border border-gray-300 bg-white px-3 py-2 text-sm ring-offset-white placeholder:text-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 ${className}`}
      onClick={() => setIsOpen(!isOpen)}
      {...props}
    >
      {children}
      <svg
        className={`h-4 w-4 opacity-50 transition-transform ${isOpen ? 'rotate-180' : ''}`}
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
      </svg>
    </button>
  );
};

export const SelectValue = ({ placeholder = 'Select...', className = '', ...props }) => {
  const { selectedValue } = useContext(SelectContext);
  
  return (
    <span className={`block truncate ${className}`} {...props}>
      {selectedValue || placeholder}
    </span>
  );
};

export const SelectContent = ({ children, className = '', ...props }) => {
  const { isOpen } = useContext(SelectContext);
  
  if (!isOpen) return null;
  
  return (
    <div 
      className={`absolute top-full z-50 mt-1 max-h-60 w-full overflow-auto rounded-md border border-gray-200 bg-white py-1 text-base shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none sm:text-sm ${className}`}
      {...props}
    >
      {children}
    </div>
  );
};

export const SelectItem = ({ children, value, className = '', ...props }) => {
  const { selectedValue, setSelectedValue } = useContext(SelectContext);
  const isSelected = selectedValue === value;
  
  return (
    <div
      className={`relative cursor-pointer select-none py-2 pl-3 pr-9 hover:bg-gray-100 ${
        isSelected ? 'bg-blue-50 text-blue-900' : 'text-gray-900'
      } ${className}`}
      onClick={() => setSelectedValue(value)}
      {...props}
    >
      <span className={`block truncate ${isSelected ? 'font-medium' : 'font-normal'}`}>
        {children}
      </span>
      {isSelected && (
        <span className="absolute inset-y-0 right-0 flex items-center pr-4 text-blue-600">
          <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
          </svg>
        </span>
      )}
    </div>
  );
};