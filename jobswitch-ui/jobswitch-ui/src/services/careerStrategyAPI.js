/**
 * Career Strategy API Service
 * Handles API calls for career roadmaps, goals, milestones, and progress tracking
 */
import api from './api';

class CareerStrategyAPI {
  // Roadmap endpoints
  async generateRoadmap(roadmapData) {
    try {
      const response = await api.post('/agents/career-strategy/roadmap', roadmapData);
      return response.data;
    } catch (error) {
      console.error('Error generating roadmap:', error);
      throw error;
    }
  }

  async getRoadmap(roadmapId) {
    try {
      const response = await api.get(`/agents/career-strategy/roadmap/${roadmapId}`);
      return response.data;
    } catch (error) {
      console.error('Error fetching roadmap:', error);
      throw error;
    }
  }

  async getUserRoadmaps() {
    try {
      const response = await api.get('/agents/career-strategy/roadmaps');
      return response.data;
    } catch (error) {
      console.error('Error fetching user roadmaps:', error);
      throw error;
    }
  }

  async updateRoadmap(roadmapId, updateData) {
    try {
      const response = await api.put(`/agents/career-strategy/roadmap/${roadmapId}`, updateData);
      return response.data;
    } catch (error) {
      console.error('Error updating roadmap:', error);
      throw error;
    }
  }

  // Goals endpoints
  async createGoals(goalsRequest) {
    try {
      const response = await api.post('/agents/career-strategy/goals', goalsRequest);
      return response.data;
    } catch (error) {
      console.error('Error creating goals:', error);
      throw error;
    }
  }

  async getGoals(filters = {}) {
    try {
      const params = new URLSearchParams();
      if (filters.roadmapId) params.append('roadmap_id', filters.roadmapId);
      if (filters.status) params.append('status', filters.status);
      
      const response = await api.get(`/agents/career-strategy/goals?${params}`);
      return response.data;
    } catch (error) {
      console.error('Error fetching goals:', error);
      throw error;
    }
  }

  async updateGoal(goalId, updateData) {
    try {
      const response = await api.put(`/agents/career-strategy/goals/${goalId}`, updateData);
      return response.data;
    } catch (error) {
      console.error('Error updating goal:', error);
      throw error;
    }
  }

  // Milestones endpoints
  async createMilestone(milestoneData) {
    try {
      const response = await api.post('/agents/career-strategy/milestones', milestoneData);
      return response.data;
    } catch (error) {
      console.error('Error creating milestone:', error);
      throw error;
    }
  }

  async getMilestones(filters = {}) {
    try {
      const params = new URLSearchParams();
      if (filters.roadmapId) params.append('roadmap_id', filters.roadmapId);
      if (filters.goalId) params.append('goal_id', filters.goalId);
      if (filters.status) params.append('status', filters.status);
      
      const response = await api.get(`/agents/career-strategy/milestones?${params}`);
      return response.data;
    } catch (error) {
      console.error('Error fetching milestones:', error);
      throw error;
    }
  }

  async updateMilestone(milestoneId, updateData) {
    try {
      const response = await api.put(`/agents/career-strategy/milestones/${milestoneId}`, updateData);
      return response.data;
    } catch (error) {
      console.error('Error updating milestone:', error);
      throw error;
    }
  }

  // Progress tracking endpoints
  async trackProgress(progressRequest) {
    try {
      const response = await api.post('/agents/career-strategy/progress', progressRequest);
      return response.data;
    } catch (error) {
      console.error('Error tracking progress:', error);
      throw error;
    }
  }

  async getProgressHistory(roadmapId) {
    try {
      const response = await api.get(`/agents/career-strategy/progress/${roadmapId}`);
      return response.data;
    } catch (error) {
      console.error('Error fetching progress history:', error);
      throw error;
    }
  }

  // Market trends and recommendations
  async analyzeMarketTrends(filters = {}) {
    try {
      const params = new URLSearchParams();
      if (filters.industry) params.append('industry', filters.industry);
      if (filters.targetRole) params.append('target_role', filters.targetRole);
      if (filters.location) params.append('location', filters.location);
      
      const response = await api.get(`/agents/career-strategy/market-trends?${params}`);
      return response.data;
    } catch (error) {
      console.error('Error analyzing market trends:', error);
      throw error;
    }
  }

  async getCareerRecommendations() {
    try {
      const response = await api.get('/agents/career-strategy/recommendations');
      return response.data;
    } catch (error) {
      console.error('Error fetching career recommendations:', error);
      throw error;
    }
  }

  // Utility methods
  formatTimelineDate(months) {
    const date = new Date();
    date.setMonth(date.getMonth() + months);
    return date.toISOString().split('T')[0];
  }

  calculateProgress(milestones) {
    if (!milestones || milestones.length === 0) return 0;
    
    const totalProgress = milestones.reduce((sum, milestone) => {
      return sum + (milestone.progress_percentage || 0);
    }, 0);
    
    return Math.round(totalProgress / milestones.length);
  }

  getPriorityColor(priority) {
    switch (priority) {
      case 1:
      case 'high':
        return '#ef4444'; // red-500
      case 2:
      case 'medium':
        return '#f59e0b'; // amber-500
      case 3:
      case 'low':
        return '#10b981'; // emerald-500
      default:
        return '#6b7280'; // gray-500
    }
  }

  getStatusColor(status) {
    switch (status) {
      case 'completed':
        return '#10b981'; // emerald-500
      case 'in_progress':
        return '#3b82f6'; // blue-500
      case 'on_hold':
        return '#f59e0b'; // amber-500
      case 'cancelled':
        return '#ef4444'; // red-500
      case 'not_started':
      default:
        return '#6b7280'; // gray-500
    }
  }

  formatStatus(status) {
    return status.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase());
  }

  formatMilestoneType(type) {
    return type.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase());
  }
}

export default new CareerStrategyAPI();