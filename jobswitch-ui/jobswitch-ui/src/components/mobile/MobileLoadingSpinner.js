import React from 'react';
import useResponsive from '../../hooks/useResponsive';

const MobileLoadingSpinner = ({ 
  size = 'medium', 
  message = 'Loading...', 
  fullScreen = false,
  overlay = false 
}) => {
  const { isMobile, isSmallMobile } = useResponsive();

  const getSizeClasses = () => {
    if (isSmallMobile) {
      switch (size) {
        case 'small': return 'h-4 w-4';
        case 'large': return 'h-10 w-10';
        default: return 'h-6 w-6';
      }
    } else {
      switch (size) {
        case 'small': return 'h-6 w-6';
        case 'large': return 'h-12 w-12';
        default: return 'h-8 w-8';
      }
    }
  };

  const getTextSize = () => {
    if (isSmallMobile) {
      return 'text-sm';
    }
    return 'text-base';
  };

  const spinner = (
    <div className="flex flex-col items-center justify-center space-y-3">
      <div className={`animate-spin rounded-full border-b-2 border-blue-600 ${getSizeClasses()}`}></div>
      {message && (
        <p className={`text-gray-600 ${getTextSize()} text-center`}>
          {message}
        </p>
      )}
    </div>
  );

  if (fullScreen) {
    return (
      <div className={`${
        overlay ? 'fixed' : 'absolute'
      } inset-0 bg-white bg-opacity-90 flex items-center justify-center z-50`}>
        {spinner}
      </div>
    );
  }

  if (overlay) {
    return (
      <div className="absolute inset-0 bg-white bg-opacity-75 flex items-center justify-center z-10">
        {spinner}
      </div>
    );
  }

  return (
    <div className={`flex items-center justify-center ${isMobile ? 'py-8' : 'py-12'}`}>
      {spinner}
    </div>
  );
};

// Skeleton loading component for better UX
export const MobileSkeleton = ({ 
  lines = 3, 
  avatar = false, 
  card = false,
  className = '' 
}) => {
  const { isMobile } = useResponsive();

  if (card) {
    return (
      <div className={`bg-white rounded-lg shadow-md p-4 mb-4 animate-pulse ${className}`}>
        <div className="flex items-start space-x-3">
          {avatar && (
            <div className="w-12 h-12 bg-gray-300 rounded-full flex-shrink-0"></div>
          )}
          <div className="flex-1 space-y-2">
            <div className="h-4 bg-gray-300 rounded w-3/4"></div>
            <div className="h-3 bg-gray-300 rounded w-1/2"></div>
            <div className="space-y-1">
              {Array.from({ length: lines }).map((_, index) => (
                <div 
                  key={index}
                  className={`h-3 bg-gray-300 rounded ${
                    index === lines - 1 ? 'w-2/3' : 'w-full'
                  }`}
                ></div>
              ))}
            </div>
          </div>
        </div>
        
        {/* Action buttons skeleton */}
        <div className="flex space-x-2 mt-4 pt-3 border-t border-gray-200">
          <div className="h-8 bg-gray-300 rounded flex-1"></div>
          <div className="h-8 bg-gray-300 rounded flex-1"></div>
        </div>
      </div>
    );
  }

  return (
    <div className={`animate-pulse ${className}`}>
      <div className="flex items-start space-x-3">
        {avatar && (
          <div className={`bg-gray-300 rounded-full flex-shrink-0 ${
            isMobile ? 'w-8 h-8' : 'w-10 h-10'
          }`}></div>
        )}
        <div className="flex-1 space-y-2">
          {Array.from({ length: lines }).map((_, index) => (
            <div 
              key={index}
              className={`h-3 bg-gray-300 rounded ${
                index === 0 ? 'w-3/4' : 
                index === lines - 1 ? 'w-1/2' : 'w-full'
              }`}
            ></div>
          ))}
        </div>
      </div>
    </div>
  );
};

// Pulse loading for buttons
export const MobileButtonLoader = ({ children, loading, ...props }) => {
  return (
    <button {...props} disabled={loading || props.disabled}>
      {loading ? (
        <div className="flex items-center justify-center space-x-2">
          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
          <span>Loading...</span>
        </div>
      ) : (
        children
      )}
    </button>
  );
};

export default MobileLoadingSpinner;