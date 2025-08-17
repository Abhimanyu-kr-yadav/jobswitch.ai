/**
 * Notification Center Component
 * Displays and manages user notifications from AI agents
 */
import React, { useRef, useEffect } from 'react';
import useResponsive from '../../hooks/useResponsive';

const NotificationCenter = ({ 
  notifications, 
  onClose, 
  onMarkAsRead, 
  onMarkAllAsRead 
}) => {
  const panelRef = useRef(null);
  const { isMobile, isSmallMobile } = useResponsive();

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (panelRef.current && !panelRef.current.contains(event.target)) {
        onClose();
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [onClose]);

  const getNotificationIcon = (type) => {
    switch (type) {
      case 'job_recommendation':
        return { icon: '💼', color: 'text-blue-600' };
      case 'skill_gap':
        return { icon: '🎯', color: 'text-green-600' };
      case 'resume_optimization':
        return { icon: '📄', color: 'text-purple-600' };
      case 'interview_feedback':
        return { icon: '🎤', color: 'text-orange-600' };
      case 'networking_opportunity':
        return { icon: '🤝', color: 'text-pink-600' };
      case 'career_milestone':
        return { icon: '🚀', color: 'text-indigo-600' };
      case 'system':
        return { icon: '⚙️', color: 'text-gray-600' };
      default:
        return { icon: '📢', color: 'text-blue-600' };
    }
  };

  const formatTimestamp = (timestamp) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    
    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffMins < 1440) return `${Math.floor(diffMins / 60)}h ago`;
    return date.toLocaleDateString();
  };

  const getPriorityColor = (priority) => {
    switch (priority) {
      case 'high':
        return 'border-l-red-500';
      case 'medium':
        return 'border-l-yellow-500';
      case 'low':
        return 'border-l-green-500';
      default:
        return 'border-l-blue-500';
    }
  };

  const unreadNotifications = notifications.filter(n => !n.read);
  const readNotifications = notifications.filter(n => n.read);

  return (
    <div 
      ref={panelRef}
      className={`${
        isMobile 
          ? 'fixed inset-x-4 top-16 bottom-20 bg-white rounded-lg shadow-xl border border-gray-200 z-50 overflow-hidden'
          : 'absolute right-0 top-12 w-96 bg-white rounded-lg shadow-xl border border-gray-200 z-50 max-h-96 overflow-hidden'
      }`}
    >
      {/* Header */}
      <div className={`px-4 py-3 border-b border-gray-200 bg-gray-50 ${isMobile ? 'sticky top-0 z-10' : ''}`}>
        <div className="flex items-center justify-between">
          <h3 className={`font-semibold text-gray-900 ${isMobile ? 'text-base' : 'text-lg'}`}>
            Notifications
          </h3>
          <div className="flex items-center space-x-2">
            {unreadNotifications.length > 0 && (
              <button
                onClick={onMarkAllAsRead}
                className={`text-blue-600 hover:text-blue-800 font-medium ${isMobile ? 'text-xs' : 'text-sm'}`}
              >
                {isMobile ? 'Mark all' : 'Mark all read'}
              </button>
            )}
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>
        
        {unreadNotifications.length > 0 && (
          <p className={`text-gray-600 mt-1 ${isMobile ? 'text-xs' : 'text-sm'}`}>
            {unreadNotifications.length} unread notification{unreadNotifications.length !== 1 ? 's' : ''}
          </p>
        )}
      </div>

      {/* Notifications List */}
      <div className={`overflow-y-auto ${isMobile ? 'flex-1' : 'max-h-80'}`}>
        {notifications.length === 0 ? (
          <div className="p-8 text-center">
            <div className="text-gray-400 mb-4">
              <svg className="w-12 h-12 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-5 5v-5zM11 19H6.414a1 1 0 01-.707-.293L4 17V6a3 3 0 013-3h10a3 3 0 013 3v5" />
              </svg>
            </div>
            <h4 className="text-lg font-medium text-gray-900 mb-2">No Notifications</h4>
            <p className="text-gray-600 text-sm">
              You'll receive notifications here when your AI agents have updates for you.
            </p>
          </div>
        ) : (
          <div className="divide-y divide-gray-200">
            {/* Unread Notifications */}
            {unreadNotifications.map((notification) => {
              const { icon, color } = getNotificationIcon(notification.type);
              return (
                <div
                  key={notification.id}
                  className={`${isMobile ? 'p-3' : 'p-4'} hover:bg-gray-50 cursor-pointer border-l-4 ${getPriorityColor(notification.priority)} bg-blue-50`}
                  onClick={() => onMarkAsRead(notification.id)}
                >
                  <div className={`flex items-start ${isMobile ? 'space-x-2' : 'space-x-3'}`}>
                    <div className={`flex-shrink-0 ${isMobile ? 'text-lg' : 'text-xl'} ${color}`}>
                      {icon}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between">
                        <h4 className={`font-semibold text-gray-900 ${isMobile ? 'text-xs' : 'text-sm'}`}>
                          {isMobile && notification.title.length > 30 
                            ? `${notification.title.substring(0, 30)}...` 
                            : notification.title
                          }
                        </h4>
                        <div className="flex items-center space-x-2">
                          <span className="text-xs text-gray-500">
                            {formatTimestamp(notification.timestamp)}
                          </span>
                          <div className={`bg-blue-600 rounded-full ${isMobile ? 'w-1.5 h-1.5' : 'w-2 h-2'}`}></div>
                        </div>
                      </div>
                      <p className={`text-gray-700 mt-1 ${isMobile ? 'text-xs' : 'text-sm'}`}>
                        {isMobile && notification.message.length > 80
                          ? `${notification.message.substring(0, 80)}...`
                          : notification.message
                        }
                      </p>
                      {notification.agent && (
                        <p className="text-xs text-gray-500 mt-1">
                          From: {notification.agent.replace('_', ' ')}
                        </p>
                      )}
                      {notification.actionUrl && (
                        <button className="text-xs text-blue-600 hover:text-blue-800 mt-2 font-medium">
                          View Details →
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}

            {/* Read Notifications */}
            {readNotifications.slice(0, 10).map((notification) => {
              const { icon, color } = getNotificationIcon(notification.type);
              return (
                <div
                  key={notification.id}
                  className={`p-4 hover:bg-gray-50 border-l-4 ${getPriorityColor(notification.priority)} opacity-75`}
                >
                  <div className="flex items-start space-x-3">
                    <div className={`flex-shrink-0 text-xl ${color}`}>
                      {icon}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between">
                        <h4 className="text-sm font-medium text-gray-700">
                          {notification.title}
                        </h4>
                        <span className="text-xs text-gray-500">
                          {formatTimestamp(notification.timestamp)}
                        </span>
                      </div>
                      <p className="text-sm text-gray-600 mt-1">
                        {notification.message}
                      </p>
                      {notification.agent && (
                        <p className="text-xs text-gray-500 mt-1">
                          From: {notification.agent.replace('_', ' ')}
                        </p>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Footer */}
      {notifications.length > 10 && (
        <div className="px-4 py-3 border-t border-gray-200 bg-gray-50">
          <button className="text-sm text-blue-600 hover:text-blue-800 font-medium">
            View All Notifications
          </button>
        </div>
      )}
    </div>
  );
};

export default NotificationCenter;