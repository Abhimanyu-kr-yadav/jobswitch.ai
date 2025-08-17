import React, { useState, useEffect, useRef } from 'react';
import { useAuth } from '../contexts/AuthContext';
import ProfileForm from './profile/ProfileForm';
import JobDiscovery from './jobs/JobDiscovery';
import SkillsAnalysisDashboard from './skills/SkillsAnalysisDashboard';
import ResumeBuilder from './resume/ResumeBuilder';
import InterviewPreparationHub from './interview/InterviewPreparationHub';
import NetworkingHub from './networking/NetworkingHub';
import CareerStrategyHub from './career/CareerStrategyHub';
import UnifiedDashboardHome from './dashboard/UnifiedDashboardHome';
import NotificationCenter from './dashboard/NotificationCenter';
import AgentActivityMonitor from './dashboard/AgentActivityMonitor';
import MobileNavigation from './mobile/MobileNavigation';
import MobileHeader from './mobile/MobileHeader';
import useResponsive from '../hooks/useResponsive';
import pushNotificationService from '../services/pushNotificationService';

const Dashboard = () => {
  const { user, logout } = useAuth();
  const [activeTab, setActiveTab] = useState('dashboard');
  const [notifications, setNotifications] = useState([]);
  const [agentActivities, setAgentActivities] = useState([]);
  const [showNotifications, setShowNotifications] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);
  const [pushNotificationsEnabled, setPushNotificationsEnabled] = useState(false);
  const wsRef = useRef(null);
  const { isMobile, isTablet, isDesktop } = useResponsive();

  // Initialize push notifications
  useEffect(() => {
    const initializePushNotifications = async () => {
      if (user?.user_id) {
        const initialized = await pushNotificationService.initialize();
        if (initialized) {
          const hasPermission = await pushNotificationService.requestPermission();
          if (hasPermission) {
            await pushNotificationService.subscribe(user.user_id);
            setPushNotificationsEnabled(true);
          }
        }
      }
    };

    initializePushNotifications();
  }, [user?.user_id]);

  // WebSocket connection for real-time updates
  useEffect(() => {
    const connectWebSocket = () => {
      const wsUrl = process.env.REACT_APP_WS_URL || 'ws://localhost:8000/ws';
      wsRef.current = new WebSocket(`${wsUrl}/${user?.user_id}`);

      wsRef.current.onopen = () => {
        console.log('WebSocket connected');
      };

      wsRef.current.onmessage = (event) => {
        const data = JSON.parse(event.data);
        handleWebSocketMessage(data);
      };

      wsRef.current.onclose = () => {
        console.log('WebSocket disconnected, attempting to reconnect...');
        setTimeout(connectWebSocket, 3000);
      };

      wsRef.current.onerror = (error) => {
        console.error('WebSocket error:', error);
      };
    };

    if (user?.user_id) {
      connectWebSocket();
    }

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [user?.user_id]);

  const handleWebSocketMessage = (data) => {
    switch (data.type) {
      case 'notification':
        addNotification(data.payload);
        break;
      case 'agent_activity':
        updateAgentActivity(data.payload);
        break;
      case 'recommendation_update':
        handleRecommendationUpdate(data.payload);
        break;
      default:
        console.log('Unknown message type:', data.type);
    }
  };

  const addNotification = (notification) => {
    const newNotification = {
      id: Date.now(),
      timestamp: new Date(),
      read: false,
      ...notification
    };
    
    setNotifications(prev => [newNotification, ...prev]);
    setUnreadCount(prev => prev + 1);

    // Show push notification if enabled and app is not in focus
    if (pushNotificationsEnabled && document.hidden) {
      pushNotificationService.showLocalNotification(
        notification.title || 'JobSwitch.ai',
        {
          body: notification.message,
          tag: notification.type,
          data: notification
        }
      );
    }
  };

  const updateAgentActivity = (activity) => {
    setAgentActivities(prev => {
      const updated = prev.filter(a => a.agent !== activity.agent);
      return [activity, ...updated].slice(0, 10); // Keep last 10 activities
    });
  };

  const handleRecommendationUpdate = (update) => {
    // Handle recommendation updates from various agents
    addNotification({
      type: 'recommendation',
      title: `New ${update.agent} Recommendation`,
      message: update.message,
      agent: update.agent,
      data: update.data
    });
  };

  const markNotificationAsRead = (notificationId) => {
    setNotifications(prev => 
      prev.map(n => n.id === notificationId ? { ...n, read: true } : n)
    );
    setUnreadCount(prev => Math.max(0, prev - 1));
  };

  const markAllNotificationsAsRead = () => {
    setNotifications(prev => prev.map(n => ({ ...n, read: true })));
    setUnreadCount(0);
  };

  const handleLogout = async () => {
    if (wsRef.current) {
      wsRef.current.close();
    }
    
    // Unsubscribe from push notifications
    if (pushNotificationsEnabled) {
      await pushNotificationService.unsubscribe();
    }
    
    logout();
  };

  const tabs = [
    { id: 'dashboard', name: 'Dashboard', icon: '🏠', badge: null },
    { id: 'profile', name: 'Profile', icon: '👤', badge: null },
    { id: 'jobs', name: 'Job Search', icon: '💼', badge: null },
    { id: 'skills', name: 'Skills', icon: '🎯', badge: null },
    { id: 'resume', name: 'Resume', icon: '📄', badge: null },
    { id: 'interview', name: 'Interview Prep', icon: '🎤', badge: null },
    { id: 'networking', name: 'Networking', icon: '🤝', badge: null },
    { id: 'career', name: 'Career Strategy', icon: '🚀', badge: null }
  ];

  const renderTabContent = () => {
    switch (activeTab) {
      case 'dashboard':
        return (
          <UnifiedDashboardHome 
            agentActivities={agentActivities}
            notifications={notifications}
            onTabChange={setActiveTab}
          />
        );
      case 'profile':
        return <ProfileForm />;
      case 'jobs':
        return <JobDiscovery />;
      case 'skills':
        return <SkillsAnalysisDashboard />;
      case 'resume':
        return <ResumeBuilder />;
      case 'interview':
        return <InterviewPreparationHub />;
      case 'networking':
        return <NetworkingHub />;
      case 'career':
        return <CareerStrategyHub />;
      default:
        return (
          <UnifiedDashboardHome 
            agentActivities={agentActivities}
            notifications={notifications}
            onTabChange={setActiveTab}
          />
        );
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Mobile Header */}
      {isMobile ? (
        <MobileHeader
          user={user}
          notifications={notifications}
          agentActivities={agentActivities}
          unreadCount={unreadCount}
          onLogout={handleLogout}
          onMarkNotificationAsRead={markNotificationAsRead}
          onMarkAllNotificationsAsRead={markAllNotificationsAsRead}
        />
      ) : (
        /* Desktop Header */
        <header className="bg-white shadow-sm border-b">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between items-center h-16">
              <div className="flex items-center">
                <h1 className="text-2xl font-bold text-blue-600">JobSwitch.ai</h1>
              </div>
              
              <div className="flex items-center space-x-4">
                {/* Agent Activity Monitor */}
                <AgentActivityMonitor activities={agentActivities} />
                
                {/* Notification Bell */}
                <div className="relative">
                  <button
                    onClick={() => setShowNotifications(!showNotifications)}
                    className="relative p-2 text-gray-600 hover:text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500 rounded-full"
                  >
                    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-5 5v-5zM11 19H6.414a1 1 0 01-.707-.293L4 17V6a3 3 0 013-3h10a3 3 0 013 3v5" />
                    </svg>
                    {unreadCount > 0 && (
                      <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full h-5 w-5 flex items-center justify-center">
                        {unreadCount > 9 ? '9+' : unreadCount}
                      </span>
                    )}
                  </button>
                  
                  {showNotifications && (
                    <NotificationCenter
                      notifications={notifications}
                      onClose={() => setShowNotifications(false)}
                      onMarkAsRead={markNotificationAsRead}
                      onMarkAllAsRead={markAllNotificationsAsRead}
                    />
                  )}
                </div>

                <div className="text-sm text-gray-700">
                  Welcome, {user?.first_name} {user?.last_name}
                </div>
                <button
                  onClick={handleLogout}
                  className="bg-gray-100 hover:bg-gray-200 text-gray-700 px-3 py-2 rounded-md text-sm font-medium"
                >
                  Sign Out
                </button>
              </div>
            </div>
          </div>
        </header>
      )}

      {/* Main Content Container */}
      <div className={`${isMobile ? 'px-4 py-4' : 'max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8'}`}>
        <div className={`${isMobile ? 'flex flex-col' : 'flex flex-col lg:flex-row gap-8'}`}>
          {/* Desktop Sidebar Navigation */}
          {!isMobile && (
            <div className="lg:w-64">
              <nav className="bg-white rounded-lg shadow-md p-4">
                <div className="space-y-2">
                  {tabs.map((tab) => (
                    <button
                      key={tab.id}
                      onClick={() => setActiveTab(tab.id)}
                      className={`w-full flex items-center justify-between px-3 py-2 rounded-md text-left transition-colors ${
                        activeTab === tab.id
                          ? 'bg-blue-100 text-blue-700 font-medium'
                          : 'text-gray-700 hover:bg-gray-100'
                      }`}
                    >
                      <div className="flex items-center space-x-3">
                        <span className="text-lg">{tab.icon}</span>
                        <span>{tab.name}</span>
                      </div>
                      {tab.badge && (
                        <span className="bg-red-500 text-white text-xs rounded-full h-5 w-5 flex items-center justify-center">
                          {tab.badge}
                        </span>
                      )}
                    </button>
                  ))}
                </div>
              </nav>
            </div>
          )}

          {/* Main Content */}
          <div className="flex-1">
            {renderTabContent()}
          </div>
        </div>
      </div>

      {/* Mobile Navigation */}
      {isMobile && (
        <MobileNavigation
          tabs={tabs}
          activeTab={activeTab}
          onTabChange={setActiveTab}
          unreadCount={unreadCount}
        />
      )}
    </div>
  );
};

export default Dashboard;