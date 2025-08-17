/**
 * Progress Visualization Component
 * Displays career progress with charts and analytics
 */
import React, { useState, useEffect } from 'react';
import { Select } from '../ui/Select';
import careerStrategyAPI from '../../services/careerStrategyAPI';

const ProgressVisualization = ({ roadmaps = [], goals = [], onRefresh }) => {
  const [selectedRoadmap, setSelectedRoadmap] = useState('');
  const [progressHistory, setProgressHistory] = useState([]);
  const [loading, setLoading] = useState(false);
  const [timeframe, setTimeframe] = useState('all');

  const timeframeOptions = [
    { value: 'all', label: 'All Time' },
    { value: '30', label: 'Last 30 Days' },
    { value: '90', label: 'Last 3 Months' },
    { value: '180', label: 'Last 6 Months' }
  ];

  useEffect(() => {
    if (selectedRoadmap) {
      loadProgressHistory();
    }
  }, [selectedRoadmap]);

  const loadProgressHistory = async () => {
    try {
      setLoading(true);
      const response = await careerStrategyAPI.getProgressHistory(selectedRoadmap);
      if (response.success) {
        setProgressHistory(response.data.progress_history || []);
      }
    } catch (error) {
      console.error('Error loading progress history:', error);
    } finally {
      setLoading(false);
    }
  };

  const calculateOverallProgress = () => {
    if (goals.length === 0) return 0;
    const totalProgress = goals.reduce((sum, goal) => sum + (goal.progress_percentage || 0), 0);
    return Math.round(totalProgress / goals.length);
  };

  const getGoalsByStatus = () => {
    return goals.reduce((acc, goal) => {
      const status = goal.status || 'not_started';
      acc[status] = (acc[status] || 0) + 1;
      return acc;
    }, {});
  };

  const getGoalsByCategory = () => {
    return goals.reduce((acc, goal) => {
      const category = goal.category || 'other';
      acc[category] = (acc[category] || 0) + 1;
      return acc;
    }, {});
  };

  const getCompletionRate = () => {
    if (goals.length === 0) return 0;
    const completedGoals = goals.filter(g => g.status === 'completed').length;
    return Math.round((completedGoals / goals.length) * 100);
  };

  const getAverageTimeToCompletion = () => {
    const completedGoals = goals.filter(g => g.status === 'completed' && g.completion_date && g.created_at);
    if (completedGoals.length === 0) return 'N/A';
    
    const totalDays = completedGoals.reduce((sum, goal) => {
      const start = new Date(goal.created_at);
      const end = new Date(goal.completion_date);
      return sum + Math.ceil((end - start) / (1000 * 60 * 60 * 24));
    }, 0);
    
    return Math.round(totalDays / completedGoals.length);
  };

  const overallProgress = calculateOverallProgress();
  const goalsByStatus = getGoalsByStatus();
  const goalsByCategory = getGoalsByCategory();
  const completionRate = getCompletionRate();
  const avgTimeToCompletion = getAverageTimeToCompletion();

  return (
    <div className="p-6">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Progress Tracking</h2>
        <p className="text-gray-600">
          Visualize your career progress with detailed analytics and insights.
        </p>
      </div>

      {/* Roadmap Selection */}
      {roadmaps.length > 0 && (
        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Select Roadmap for Detailed Analysis
          </label>
          <div className="flex space-x-4">
            <Select
              value={selectedRoadmap}
              onChange={(e) => setSelectedRoadmap(e.target.value)}
              options={[
                { value: '', label: 'Select a roadmap...' },
                ...roadmaps.map(r => ({ value: r.roadmap_id, label: r.title }))
              ]}
              className="flex-1"
            />
            <Select
              value={timeframe}
              onChange={(e) => setTimeframe(e.target.value)}
              options={timeframeOptions}
              className="w-48"
            />
          </div>
        </div>
      )}

      {/* Overall Progress Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="text-blue-600 text-2xl mr-3">📊</div>
            <div>
              <p className="text-sm font-medium text-gray-600">Overall Progress</p>
              <p className="text-2xl font-bold text-gray-900">{overallProgress}%</p>
            </div>
          </div>
          <div className="mt-4 w-full bg-gray-200 rounded-full h-2">
            <div 
              className="bg-blue-600 h-2 rounded-full transition-all duration-300" 
              style={{ width: `${overallProgress}%` }}
            ></div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="text-green-600 text-2xl mr-3">✅</div>
            <div>
              <p className="text-sm font-medium text-gray-600">Completion Rate</p>
              <p className="text-2xl font-bold text-gray-900">{completionRate}%</p>
            </div>
          </div>
          <p className="text-xs text-gray-500 mt-2">
            {goalsByStatus.completed || 0} of {goals.length} goals completed
          </p>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="text-purple-600 text-2xl mr-3">🚀</div>
            <div>
              <p className="text-sm font-medium text-gray-600">Active Goals</p>
              <p className="text-2xl font-bold text-gray-900">{goalsByStatus.in_progress || 0}</p>
            </div>
          </div>
          <p className="text-xs text-gray-500 mt-2">
            Currently in progress
          </p>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="text-orange-600 text-2xl mr-3">⏱️</div>
            <div>
              <p className="text-sm font-medium text-gray-600">Avg. Completion</p>
              <p className="text-2xl font-bold text-gray-900">
                {avgTimeToCompletion === 'N/A' ? 'N/A' : `${avgTimeToCompletion}d`}
              </p>
            </div>
          </div>
          <p className="text-xs text-gray-500 mt-2">
            Average days to complete
          </p>
        </div>
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        {/* Goals by Status Chart */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Goals by Status</h3>
          <div className="space-y-3">
            {Object.entries(goalsByStatus).map(([status, count]) => {
              const percentage = goals.length > 0 ? (count / goals.length) * 100 : 0;
              const color = careerStrategyAPI.getStatusColor(status);
              
              return (
                <div key={status} className="flex items-center">
                  <div className="flex-1">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm font-medium text-gray-700 capitalize">
                        {careerStrategyAPI.formatStatus(status)}
                      </span>
                      <span className="text-sm text-gray-600">{count}</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div 
                        className="h-2 rounded-full transition-all duration-300" 
                        style={{ 
                          width: `${percentage}%`,
                          backgroundColor: color
                        }}
                      ></div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Goals by Category Chart */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Goals by Category</h3>
          <div className="space-y-3">
            {Object.entries(goalsByCategory).map(([category, count]) => {
              const percentage = goals.length > 0 ? (count / goals.length) * 100 : 0;
              const colors = {
                skill_development: '#3b82f6',
                experience: '#10b981',
                networking: '#f59e0b',
                education: '#8b5cf6',
                certification: '#ef4444',
                other: '#6b7280'
              };
              
              return (
                <div key={category} className="flex items-center">
                  <div className="flex-1">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm font-medium text-gray-700 capitalize">
                        {category.replace('_', ' ')}
                      </span>
                      <span className="text-sm text-gray-600">{count}</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div 
                        className="h-2 rounded-full transition-all duration-300" 
                        style={{ 
                          width: `${percentage}%`,
                          backgroundColor: colors[category] || colors.other
                        }}
                      ></div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Progress Timeline */}
      {selectedRoadmap && (
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Progress Timeline</h3>
          {loading ? (
            <div className="flex items-center justify-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            </div>
          ) : progressHistory.length > 0 ? (
            <div className="space-y-4">
              {progressHistory.map((entry, index) => (
                <div key={entry.tracking_id} className="flex items-start">
                  <div className="flex-shrink-0 w-3 h-3 bg-blue-600 rounded-full mt-2 mr-4"></div>
                  <div className="flex-1">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm font-medium text-gray-900">
                        Progress Update
                      </span>
                      <span className="text-xs text-gray-500">
                        {new Date(entry.recorded_at).toLocaleDateString()}
                      </span>
                    </div>
                    <p className="text-sm text-gray-600 mb-2">{entry.notes}</p>
                    <div className="flex items-center space-x-4">
                      <span className="text-xs text-blue-600 font-medium">
                        {entry.progress_percentage}% complete
                      </span>
                      {entry.achievements && entry.achievements.length > 0 && (
                        <span className="text-xs text-green-600">
                          {entry.achievements.length} achievement(s)
                        </span>
                      )}
                      {entry.challenges && entry.challenges.length > 0 && (
                        <span className="text-xs text-orange-600">
                          {entry.challenges.length} challenge(s)
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8">
              <div className="text-gray-400 text-4xl mb-2">📈</div>
              <p className="text-gray-600">No progress history available for this roadmap.</p>
            </div>
          )}
        </div>
      )}

      {/* Recent Goals */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Recent Goal Activity</h3>
        {goals.length > 0 ? (
          <div className="space-y-4">
            {goals
              .sort((a, b) => new Date(b.updated_at || b.created_at) - new Date(a.updated_at || a.created_at))
              .slice(0, 5)
              .map((goal) => (
                <div key={goal.goal_id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div className="flex-1">
                    <h4 className="font-medium text-gray-900">{goal.title}</h4>
                    <div className="flex items-center space-x-2 mt-1">
                      <span 
                        className="text-xs px-2 py-1 rounded-full text-white"
                        style={{ backgroundColor: careerStrategyAPI.getStatusColor(goal.status) }}
                      >
                        {careerStrategyAPI.formatStatus(goal.status)}
                      </span>
                      <span className="text-xs text-gray-500 capitalize">
                        {goal.category?.replace('_', ' ')}
                      </span>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-sm font-medium text-gray-900">
                      {goal.progress_percentage || 0}%
                    </div>
                    <div className="w-16 bg-gray-200 rounded-full h-2 mt-1">
                      <div 
                        className="bg-blue-600 h-2 rounded-full" 
                        style={{ width: `${goal.progress_percentage || 0}%` }}
                      ></div>
                    </div>
                  </div>
                </div>
              ))}
          </div>
        ) : (
          <div className="text-center py-8">
            <div className="text-gray-400 text-4xl mb-2">🎯</div>
            <p className="text-gray-600">No goals to display. Create your first goal to get started!</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default ProgressVisualization;