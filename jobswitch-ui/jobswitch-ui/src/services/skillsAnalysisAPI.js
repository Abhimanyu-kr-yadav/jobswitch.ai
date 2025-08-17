import api from './api';

export const skillsAnalysisAPI = {
  /**
   * Extract skills from resume text
   */
  async extractSkillsFromResume(data) {
    try {
      const response = await api.post('/agents/skills-analysis/extract-resume-skills', data);
      return response.data;
    } catch (error) {
      console.error('Error extracting skills from resume:', error);
      throw error;
    }
  },

  /**
   * Extract skills from job description
   */
  async extractSkillsFromJob(data) {
    try {
      const response = await api.post('/agents/skills-analysis/extract-job-skills', data);
      return response.data;
    } catch (error) {
      console.error('Error extracting skills from job:', error);
      throw error;
    }
  },

  /**
   * Analyze skill gaps between user profile and target job/role
   */
  async analyzeSkillGaps(data) {
    try {
      const response = await api.post('/agents/skills-analysis/analyze-skill-gaps', data);
      return response.data;
    } catch (error) {
      console.error('Error analyzing skill gaps:', error);
      throw error;
    }
  },

  /**
   * Get personalized learning path recommendations
   */
  async recommendLearningPaths(data) {
    try {
      const response = await api.post('/agents/skills-analysis/recommend-learning-paths', data);
      return response.data;
    } catch (error) {
      console.error('Error getting learning path recommendations:', error);
      throw error;
    }
  },

  /**
   * Analyze user's current skills comprehensively
   */
  async analyzeUserSkills() {
    try {
      const response = await api.get('/agents/skills-analysis/analyze-user-skills');
      return response.data;
    } catch (error) {
      console.error('Error analyzing user skills:', error);
      throw error;
    }
  },

  /**
   * Get personalized skills development recommendations
   */
  async getRecommendations() {
    try {
      const response = await api.get('/agents/skills-analysis/recommendations');
      return response.data;
    } catch (error) {
      console.error('Error getting skills recommendations:', error);
      throw error;
    }
  },

  /**
   * Get available skill categories
   */
  async getSkillCategories() {
    try {
      const response = await api.get('/agents/skills-analysis/skills-categories');
      return response.data;
    } catch (error) {
      console.error('Error getting skill categories:', error);
      throw error;
    }
  },

  /**
   * Get Skills Analysis Agent status
   */
  async getAgentStatus() {
    try {
      const response = await api.get('/agents/skills-analysis/agent-status');
      return response.data;
    } catch (error) {
      console.error('Error getting agent status:', error);
      throw error;
    }
  }
};