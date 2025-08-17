import api from './api';

export const analyticsAPI = {
  // User analytics
  getUserSummary: async (days = 30) => {
    const response = await api.get(`/analytics/user/summary?days=${days}`);
    return response.data;
  },

  getJobSearchProgress: async (days = 30) => {
    const response = await api.get(`/analytics/user/job-search-progress?days=${days}`);
    return response.data;
  },

  getActivityTimeline: async (days = 7, activityType = null) => {
    const params = new URLSearchParams({ days: days.toString() });
    if (activityType) {
      params.append('activity_type', activityType);
    }
    const response = await api.get(`/analytics/user/activity-timeline?${params}`);
    return response.data;
  },

  trackActivity: async (activityData) => {
    const response = await api.post('/analytics/user/track-activity', activityData);
    return response.data;
  },

  updateJobMetrics: async (metricsData) => {
    const response = await api.post('/analytics/user/update-job-metrics', metricsData);
    return response.data;
  },

  // Reports
  getUserReports: async (limit = 10) => {
    const response = await api.get(`/analytics/user/reports?limit=${limit}`);
    return response.data;
  },

  getReportDetails: async (reportId) => {
    const response = await api.get(`/analytics/user/reports/${reportId}`);
    return response.data;
  },

  generateReport: async (reportConfig) => {
    const response = await api.post('/analytics/user/generate-report', reportConfig);
    return response.data;
  },

  // System analytics (admin only)
  getSystemPerformance: async (hours = 24) => {
    const response = await api.get(`/analytics/system/performance?hours=${hours}`);
    return response.data;
  },

  getAgentPerformance: async (agentName = null, hours = 24) => {
    const params = new URLSearchParams({ hours: hours.toString() });
    if (agentName) {
      params.append('agent_name', agentName);
    }
    const response = await api.get(`/analytics/system/agent-performance?${params}`);
    return response.data;
  },

  // Real-time monitoring
  getRealTimeMetrics: async () => {
    const response = await api.get('/analytics/system/real-time-metrics');
    return response.data;
  },

  getPerformanceAlerts: async (hours = 24) => {
    const response = await api.get(`/analytics/system/performance-alerts?hours=${hours}`);
    return response.data;
  },

  getSystemHealth: async () => {
    const response = await api.get('/analytics/system/health-check');
    return response.data;
  },

  // A/B Testing
  getABTestExperiments: async (status = null) => {
    const params = new URLSearchParams();
    if (status) {
      params.append('status', status);
    }
    const response = await api.get(`/ab-testing/experiments?${params}`);
    return response.data;
  },

  createABTestExperiment: async (experimentData) => {
    const response = await api.post('/ab-testing/experiments', experimentData);
    return response.data;
  },

  startABTestExperiment: async (experimentId) => {
    const response = await api.post(`/ab-testing/experiments/${experimentId}/start`);
    return response.data;
  },

  stopABTestExperiment: async (experimentId) => {
    const response = await api.post(`/ab-testing/experiments/${experimentId}/stop`);
    return response.data;
  },

  getABTestResults: async (experimentId) => {
    const response = await api.get(`/ab-testing/experiments/${experimentId}/results`);
    return response.data;
  },

  getUserABTestAssignment: async (featureName) => {
    const response = await api.get(`/ab-testing/user/assignment/${featureName}`);
    return response.data;
  },

  recordABTestEvent: async (experimentId, eventData) => {
    const response = await api.post(`/ab-testing/experiments/${experimentId}/events`, eventData);
    return response.data;
  }
};

// Activity tracking helpers
export const trackUserActivity = async (activityType, activitySubtype = null, metadata = null, duration = null) => {
  try {
    await analyticsAPI.trackActivity({
      activity_type: activityType,
      activity_subtype: activitySubtype,
      metadata: metadata,
      duration_seconds: duration,
      success: true
    });
  } catch (error) {
    console.error('Failed to track activity:', error);
  }
};

export const trackJobSearchAction = async (action, jobId = null, metadata = null) => {
  const activityData = {
    activity_type: 'job_search',
    activity_subtype: action,
    metadata: {
      job_id: jobId,
      ...metadata
    }
  };

  try {
    await analyticsAPI.trackActivity(activityData);
    
    // Also update job metrics
    const metricsUpdate = {};
    switch (action) {
      case 'job_viewed':
        metricsUpdate.jobs_viewed = 1;
        break;
      case 'job_saved':
        metricsUpdate.jobs_saved = 1;
        break;
      case 'application_sent':
        metricsUpdate.applications_sent = 1;
        break;
      case 'interview_scheduled':
        metricsUpdate.interviews_scheduled = 1;
        break;
      case 'interview_completed':
        metricsUpdate.interviews_completed = 1;
        break;
      case 'offer_received':
        metricsUpdate.offers_received = 1;
        break;
    }

    if (Object.keys(metricsUpdate).length > 0) {
      await analyticsAPI.updateJobMetrics(metricsUpdate);
    }
  } catch (error) {
    console.error('Failed to track job search action:', error);
  }
};

export const trackFeatureUsage = async (feature, action, duration = null, metadata = null) => {
  try {
    await analyticsAPI.trackActivity({
      activity_type: feature,
      activity_subtype: action,
      duration_seconds: duration,
      metadata: metadata,
      success: true
    });
  } catch (error) {
    console.error('Failed to track feature usage:', error);
  }
};

// Session tracking
let sessionStartTime = null;
let currentSessionId = null;

export const startSession = () => {
  sessionStartTime = Date.now();
  currentSessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  
  trackUserActivity('session', 'started', { session_id: currentSessionId });
};

export const endSession = () => {
  if (sessionStartTime && currentSessionId) {
    const duration = Math.floor((Date.now() - sessionStartTime) / 1000);
    trackUserActivity('session', 'ended', { session_id: currentSessionId }, duration);
    
    sessionStartTime = null;
    currentSessionId = null;
  }
};

export const getCurrentSessionId = () => currentSessionId;

// Page view tracking
export const trackPageView = (pageName, metadata = null) => {
  trackUserActivity('page_view', pageName, {
    session_id: currentSessionId,
    timestamp: new Date().toISOString(),
    ...metadata
  });
};

export default analyticsAPI;