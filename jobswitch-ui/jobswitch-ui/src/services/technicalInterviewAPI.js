import api from './api';

export const technicalInterviewAPI = {
  // Get available challenges with filtering
  getChallenges: async (filters = {}) => {
    try {
      const params = new URLSearchParams();
      if (filters.difficulty) params.append('difficulty', filters.difficulty);
      if (filters.category) params.append('category', filters.category);
      if (filters.company) params.append('company', filters.company);
      if (filters.limit) params.append('limit', filters.limit.toString());
      if (filters.offset) params.append('offset', filters.offset.toString());

      const response = await api.get(`/agents/technical-interview/challenges?${params}`);
      return response.data;
    } catch (error) {
      console.error('Get challenges error:', error);
      throw error;
    }
  },

  // Get challenge categories and difficulties
  getCategories: async () => {
    try {
      const response = await api.get('/agents/technical-interview/categories');
      return response.data;
    } catch (error) {
      console.error('Get categories error:', error);
      throw error;
    }
  },

  // Get specific challenge details
  getChallengeDetails: async (challengeId) => {
    try {
      const response = await api.get(`/agents/technical-interview/challenge/${challengeId}`);
      return response.data;
    } catch (error) {
      console.error('Get challenge details error:', error);
      throw error;
    }
  },

  // Start a new technical interview session
  startInterview: async (config) => {
    try {
      const response = await api.post('/agents/technical-interview/start-interview', config);
      return response.data;
    } catch (error) {
      console.error('Start interview error:', error);
      throw error;
    }
  },

  // Get current challenge for active session
  getCurrentChallenge: async (sessionId) => {
    try {
      const response = await api.get(`/agents/technical-interview/current-challenge?session_id=${sessionId}`);
      return response.data;
    } catch (error) {
      console.error('Get current challenge error:', error);
      throw error;
    }
  },

  // Execute code without submitting (for testing)
  executeCode: async (codeData) => {
    try {
      const response = await api.post('/agents/technical-interview/execute-code', codeData);
      return response.data;
    } catch (error) {
      console.error('Execute code error:', error);
      throw error;
    }
  },

  // Submit code solution for evaluation
  submitCode: async (submissionData) => {
    try {
      const response = await api.post('/agents/technical-interview/submit-code', submissionData);
      return response.data;
    } catch (error) {
      console.error('Submit code error:', error);
      throw error;
    }
  },

  // Get hint for current challenge
  getHint: async (sessionId, hintLevel = 1) => {
    try {
      const response = await api.get(`/agents/technical-interview/hint?session_id=${sessionId}&hint_level=${hintLevel}`);
      return response.data;
    } catch (error) {
      console.error('Get hint error:', error);
      throw error;
    }
  },

  // Skip current challenge
  skipChallenge: async (sessionId) => {
    try {
      const response = await api.post(`/agents/technical-interview/skip-challenge?session_id=${sessionId}`);
      return response.data;
    } catch (error) {
      console.error('Skip challenge error:', error);
      throw error;
    }
  },

  // End technical interview session
  endInterview: async (sessionId) => {
    try {
      const response = await api.post(`/agents/technical-interview/end-interview?session_id=${sessionId}`);
      return response.data;
    } catch (error) {
      console.error('End interview error:', error);
      throw error;
    }
  },

  // Get comprehensive feedback for completed interview
  getFeedback: async (feedbackRequest) => {
    try {
      const response = await api.post('/agents/technical-interview/feedback', feedbackRequest);
      return response.data;
    } catch (error) {
      console.error('Get feedback error:', error);
      throw error;
    }
  },

  // Get technical interview recommendations
  getRecommendations: async () => {
    try {
      const response = await api.get('/agents/technical-interview/recommendations');
      return response.data;
    } catch (error) {
      console.error('Get recommendations error:', error);
      throw error;
    }
  },

  // Practice specific challenge (standalone mode)
  practiceChallenge: async (challengeId, language = 'python') => {
    try {
      const challengeResponse = await api.get(`/agents/technical-interview/challenge/${challengeId}`);
      if (challengeResponse.data.success) {
        return {
          success: true,
          challenge: challengeResponse.data.data.challenge,
          starterCode: challengeResponse.data.data.challenge.starter_code?.[language] || ''
        };
      }
      return challengeResponse.data;
    } catch (error) {
      console.error('Practice challenge error:', error);
      throw error;
    }
  },

  // Get challenge statistics
  getChallengeStats: async (challengeId) => {
    try {
      // This would typically come from a separate endpoint
      // For now, return mock data
      return {
        success: true,
        data: {
          total_attempts: 1250,
          success_rate: 0.68,
          average_time: 1800, // seconds
          difficulty_rating: 4.2,
          tags: ['array', 'hash-table', 'two-pointers']
        }
      };
    } catch (error) {
      console.error('Get challenge stats error:', error);
      throw error;
    }
  },

  // Get user's coding progress
  getUserProgress: async () => {
    try {
      // This would typically come from user profile/progress endpoint
      // For now, return mock data
      return {
        success: true,
        data: {
          challenges_solved: 45,
          total_attempts: 78,
          success_rate: 0.58,
          favorite_language: 'python',
          strong_categories: ['arrays', 'strings'],
          weak_categories: ['dynamic_programming', 'graphs'],
          recent_sessions: []
        }
      };
    } catch (error) {
      console.error('Get user progress error:', error);
      throw error;
    }
  }
};