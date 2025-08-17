/**
 * Agent Activity Monitor Component
 * Shows real-time status of AI agents in the header
 */
import React, { useState } from 'react';

const AgentActivityMonitor = ({ activities }) => {
  const [showDetails, setShowDetails] = useState(false);

  const getActiveAgents = () => {
    return activities.filter(activity => 
      activity.status === 'active' || activity.status === 'processing'
    );
  };

  const getAgentIcon = (agentName) => {
    const icons = {
      job_discovery: '💼',
      skills_analysis: '🎯',
      resume_optimization: '📄',
      interview_preparation: '🎤',
      networking: '🤝',
      career_strategy: '🚀'
    };
    return icons[agentName] || '🤖';
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'active':
        return 'text-green-600 bg-green-100';
      case 'processing':
        return 'text-yellow-600 bg-yellow-100';
      case 'error':
        return 'text-red-600 bg-red-100';
      default:
        return 'text-gray-600 bg-gray-100';
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
    return `${Math.floor(diffMins / 60)}h ago`;
  };

  const activeAgents = getActiveAgents();

  return (
    <div className="relative">
      {/* Activity Indicator */}
      <button
        onClick={() => setShowDetails(!showDetails)}
        className="flex items-center space-x-2 px-3 py-2 rounded-lg hover:bg-gray-100 transition-colors"
      >
        <div className="relative">
          <div className="w-6 h-6 bg-gray-200 rounded-full flex items-center justify-center">
            <svg className="w-4 h-4 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
            </svg>
          </div>
          {activeAgents.length > 0 && (
            <div className="absolute -top-1 -right-1 w-3 h-3 bg-green-500 rounded-full animate-pulse"></div>
          )}
        </div>
        
        <div className="text-sm">
          <div className="text-gray-700 font-medium">
            {activeAgents.length > 0 ? `${activeAgents.length} Active` : 'All Idle'}
          </div>
        </div>
      </button>

      {/* Activity Details Panel */}
      {showDetails && (
        <div className="absolute right-0 top-12 w-80 bg-white rounded-lg shadow-xl border border-gray-200 z-50">
          <div className="px-4 py-3 border-b border-gray-200 bg-gray-50">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold text-gray-900">Agent Status</h3>
              <button
                onClick={() => setShowDetails(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          </div>

          <div className="max-h-64 overflow-y-auto">
            {activities.length === 0 ? (
              <div className="p-6 text-center">
                <div className="text-gray-400 mb-3">
                  <svg className="w-8 h-8 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                  </svg>
                </div>
                <p className="text-gray-600 text-sm">No agent activity yet</p>
              </div>
            ) : (
              <div className="divide-y divide-gray-200">
                {activities.map((activity, index) => (
                  <div key={index} className="p-4 hover:bg-gray-50">
                    <div className="flex items-center space-x-3">
                      <div className="flex-shrink-0">
                        <span className="text-lg">{getAgentIcon(activity.agent)}</span>
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between">
                          <h4 className="text-sm font-medium text-gray-900 capitalize">
                            {activity.agent.replace('_', ' ')}
                          </h4>
                          <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(activity.status)}`}>
                            {activity.status}
                          </span>
                        </div>
                        <p className="text-sm text-gray-600 mt-1">
                          {activity.message || 'Working...'}
                        </p>
                        <p className="text-xs text-gray-500 mt-1">
                          {formatTimestamp(activity.timestamp)}
                        </p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Quick Actions */}
          <div className="px-4 py-3 border-t border-gray-200 bg-gray-50">
            <div className="flex justify-between text-sm">
              <span className="text-gray-600">
                {activeAgents.length} of {activities.length} agents active
              </span>
              <button className="text-blue-600 hover:text-blue-800 font-medium">
                View Details
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AgentActivityMonitor;