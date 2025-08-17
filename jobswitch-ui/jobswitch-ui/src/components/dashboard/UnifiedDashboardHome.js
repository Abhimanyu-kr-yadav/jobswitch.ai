/**
 * Unified Dashboard Home Component
 * Central hub showing all agent activities and recommendations
 */
import React, { useState, useEffect } from 'react';
import { useAuth } from '../../contexts/AuthContext';

const UnifiedDashboardHome = ({ agentActivities, notifications, onTabChange }) => {
  const { user } = useAuth();
  const [dashboardStats, setDashboardStats] = useState({
    jobRecommendations: 0,
    skillGaps: 0,
    resumeOptimizations: 0,
    interviewSessions: 0,
    networkingContacts: 0,
    careerMilestones: 0
  });
  const [recentRecommendations, setRecentRecommendations] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      
      // Load dashboard statistics
      const token = localStorage.getItem('token');
      const headers = {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      };

      const statsResponse = await fetch('/api/v1/dashboard/stats', { headers });
      if (statsResponse.ok) {
        const statsData = await statsResponse.json();
        if (statsData.success) {
          setDashboardStats({
            jobRecommendations: statsData.data.job_recommendations || 0,
            skillGaps: statsData.data.skill_gaps || 0,
            resumeOptimizations: statsData.data.resume_optimizations || 0,
            interviewSessions: statsData.data.interview_sessions || 0,
            networkingContacts: statsData.data.networking_contacts || 0,
            careerMilestones: statsData.data.career_milestones || 0
          });
        }
      }

      // Load recent recommendations from notifications
      const notificationsResponse = await fetch('/api/v1/dashboard/notifications?limit=5', { headers });
      if (notificationsResponse.ok) {
        const notificationsData = await notificationsResponse.json();
        if (notificationsData.success) {
          const recommendations = notificationsData.data.notifications
            .filter(n => n.type === 'recommendation' || n.type.includes('recommendation'))
            .slice(0, 5);
          setRecentRecommendations(recommendations);
        }
      }

    } catch (error) {
      console.error('Error loading dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const getGreeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return 'Good morning';
    if (hour < 18) return 'Good afternoon';
    return 'Good evening';
  };

  const quickActions = [
    {
      title: 'Find Jobs',
      description: 'Discover new opportunities',
      icon: '💼',
      action: () => onTabChange('jobs'),
      color: 'bg-blue-500'
    },
    {
      title: 'Analyze Skills',
      description: 'Check skill gaps',
      icon: '🎯',
      action: () => onTabChange('skills'),
      color: 'bg-green-500'
    },
    {
      title: 'Optimize Resume',
      description: 'Improve your resume',
      icon: '📄',
      action: () => onTabChange('resume'),
      color: 'bg-purple-500'
    },
    {
      title: 'Practice Interview',
      description: 'Prepare for interviews',
      icon: '🎤',
      action: () => onTabChange('interview'),
      color: 'bg-orange-500'
    },
    {
      title: 'Network',
      description: 'Connect with professionals',
      icon: '🤝',
      action: () => onTabChange('networking'),
      color: 'bg-pink-500'
    },
    {
      title: 'Plan Career',
      description: 'Set career goals',
      icon: '🚀',
      action: () => onTabChange('career'),
      color: 'bg-indigo-500'
    }
  ];

  const agentStatusCards = [
    {
      name: 'Job Discovery',
      icon: '💼',
      status: agentActivities.find(a => a.agent === 'job_discovery')?.status || 'idle',
      lastActivity: agentActivities.find(a => a.agent === 'job_discovery')?.timestamp,
      count: dashboardStats.jobRecommendations
    },
    {
      name: 'Skills Analysis',
      icon: '🎯',
      status: agentActivities.find(a => a.agent === 'skills_analysis')?.status || 'idle',
      lastActivity: agentActivities.find(a => a.agent === 'skills_analysis')?.timestamp,
      count: dashboardStats.skillGaps
    },
    {
      name: 'Resume Optimization',
      icon: '📄',
      status: agentActivities.find(a => a.agent === 'resume_optimization')?.status || 'idle',
      lastActivity: agentActivities.find(a => a.agent === 'resume_optimization')?.timestamp,
      count: dashboardStats.resumeOptimizations
    },
    {
      name: 'Interview Prep',
      icon: '🎤',
      status: agentActivities.find(a => a.agent === 'interview_preparation')?.status || 'idle',
      lastActivity: agentActivities.find(a => a.agent === 'interview_preparation')?.timestamp,
      count: dashboardStats.interviewSessions
    },
    {
      name: 'Networking',
      icon: '🤝',
      status: agentActivities.find(a => a.agent === 'networking')?.status || 'idle',
      lastActivity: agentActivities.find(a => a.agent === 'networking')?.timestamp,
      count: dashboardStats.networkingContacts
    },
    {
      name: 'Career Strategy',
      icon: '🚀',
      status: agentActivities.find(a => a.agent === 'career_strategy')?.status || 'idle',
      lastActivity: agentActivities.find(a => a.agent === 'career_strategy')?.timestamp,
      count: dashboardStats.careerMilestones
    }
  ];

  const getStatusColor = (status) => {
    switch (status) {
      case 'active': return 'text-green-600 bg-green-100';
      case 'processing': return 'text-yellow-600 bg-yellow-100';
      case 'error': return 'text-red-600 bg-red-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const formatTimestamp = (timestamp) => {
    if (!timestamp) return 'Never';
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    
    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffMins < 1440) return `${Math.floor(diffMins / 60)}h ago`;
    return date.toLocaleDateString();
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-96">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading your dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Welcome Header */}
      <div className="bg-gradient-to-r from-blue-600 to-purple-600 rounded-lg p-8 text-white">
        <h1 className="text-3xl font-bold mb-2">
          {getGreeting()}, {user?.first_name}!
        </h1>
        <p className="text-blue-100 text-lg">
          Your AI career copilot is ready to help you achieve your professional goals.
        </p>
      </div>

      {/* Quick Actions */}
      <div>
        <h2 className="text-2xl font-bold text-gray-900 mb-6">Quick Actions</h2>
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
          {quickActions.map((action, index) => (
            <button
              key={index}
              onClick={action.action}
              className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow text-center group"
            >
              <div className={`${action.color} w-12 h-12 rounded-full flex items-center justify-center mx-auto mb-3 group-hover:scale-110 transition-transform`}>
                <span className="text-2xl text-white">{action.icon}</span>
              </div>
              <h3 className="font-semibold text-gray-900 mb-1">{action.title}</h3>
              <p className="text-sm text-gray-600">{action.description}</p>
            </button>
          ))}
        </div>
      </div>

      {/* Agent Status Overview */}
      <div>
        <h2 className="text-2xl font-bold text-gray-900 mb-6">AI Agent Status</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {agentStatusCards.map((agent, index) => (
            <div key={index} className="bg-white rounded-lg shadow-md p-6">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center space-x-3">
                  <span className="text-2xl">{agent.icon}</span>
                  <h3 className="font-semibold text-gray-900">{agent.name}</h3>
                </div>
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(agent.status)}`}>
                  {agent.status}
                </span>
              </div>
              
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">Items:</span>
                  <span className="font-medium">{agent.count}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">Last Activity:</span>
                  <span className="font-medium">{formatTimestamp(agent.lastActivity)}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Recent Recommendations */}
      <div>
        <h2 className="text-2xl font-bold text-gray-900 mb-6">Recent Recommendations</h2>
        <div className="bg-white rounded-lg shadow-md">
          {recentRecommendations.length > 0 ? (
            <div className="divide-y divide-gray-200">
              {recentRecommendations.map((recommendation, index) => (
                <div key={index} className="p-6 hover:bg-gray-50">
                  <div className="flex items-start space-x-4">
                    <div className="flex-shrink-0">
                      <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
                        <span className="text-blue-600 font-semibold">
                          {recommendation.agent?.charAt(0).toUpperCase()}
                        </span>
                      </div>
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between">
                        <h4 className="text-lg font-medium text-gray-900">
                          {recommendation.title}
                        </h4>
                        <span className="text-sm text-gray-500">
                          {formatTimestamp(recommendation.timestamp)}
                        </span>
                      </div>
                      <p className="text-gray-600 mt-1">{recommendation.message}</p>
                      {recommendation.data && (
                        <div className="mt-2">
                          <button className="text-blue-600 hover:text-blue-800 text-sm font-medium">
                            View Details →
                          </button>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="p-8 text-center">
              <div className="text-gray-400 mb-4">
                <svg className="w-12 h-12 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                </svg>
              </div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">No Recent Recommendations</h3>
              <p className="text-gray-600">
                Your AI agents will provide personalized recommendations as you use the platform.
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Recent Activity Feed */}
      <div>
        <h2 className="text-2xl font-bold text-gray-900 mb-6">Recent Activity</h2>
        <div className="bg-white rounded-lg shadow-md">
          {agentActivities.length > 0 ? (
            <div className="divide-y divide-gray-200">
              {agentActivities.slice(0, 5).map((activity, index) => (
                <div key={index} className="p-4 hover:bg-gray-50">
                  <div className="flex items-center space-x-3">
                    <div className={`w-3 h-3 rounded-full ${getStatusColor(activity.status).split(' ')[1]}`}></div>
                    <div className="flex-1">
                      <p className="text-sm text-gray-900">
                        <span className="font-medium">{activity.agent.replace('_', ' ')}</span> {activity.message}
                      </p>
                      <p className="text-xs text-gray-500">{formatTimestamp(activity.timestamp)}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="p-8 text-center">
              <div className="text-gray-400 mb-4">
                <svg className="w-12 h-12 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">No Recent Activity</h3>
              <p className="text-gray-600">
                Agent activities will appear here as they work on your behalf.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default UnifiedDashboardHome;