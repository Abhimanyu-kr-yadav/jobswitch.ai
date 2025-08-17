/**
 * Goal Tracker Component
 * Manages career goals and milestones with progress tracking
 */
import React, { useState, useEffect } from 'react';
import { Input } from '../ui/Input';
import { Textarea } from '../ui/Textarea';
import { Select } from '../ui/Select';
import careerStrategyAPI from '../../services/careerStrategyAPI';

const GoalTracker = ({ goals = [], roadmaps = [], onGoalUpdated, onRefresh }) => {
  const [activeView, setActiveView] = useState('goals');
  const [milestones, setMilestones] = useState([]);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [editingGoal, setEditingGoal] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const [newGoal, setNewGoal] = useState({
    title: '',
    description: '',
    category: 'skill_development',
    priority: 1,
    timeline_months: 6,
    roadmap_id: ''
  });

  const categoryOptions = [
    { value: 'skill_development', label: 'Skill Development' },
    { value: 'experience', label: 'Experience' },
    { value: 'networking', label: 'Networking' },
    { value: 'education', label: 'Education' },
    { value: 'certification', label: 'Certification' }
  ];

  const priorityOptions = [
    { value: 1, label: 'High Priority' },
    { value: 2, label: 'Medium Priority' },
    { value: 3, label: 'Low Priority' }
  ];

  const statusOptions = [
    { value: 'not_started', label: 'Not Started' },
    { value: 'in_progress', label: 'In Progress' },
    { value: 'completed', label: 'Completed' },
    { value: 'on_hold', label: 'On Hold' }
  ];

  useEffect(() => {
    loadMilestones();
  }, []);

  const loadMilestones = async () => {
    try {
      const response = await careerStrategyAPI.getMilestones();
      if (response.success) {
        setMilestones(response.data.milestones || []);
      }
    } catch (error) {
      console.error('Error loading milestones:', error);
    }
  };

  const handleCreateGoal = async (e) => {
    e.preventDefault();
    
    if (!newGoal.title) {
      setError('Goal title is required');
      return;
    }

    try {
      setLoading(true);
      setError(null);

      const goalsRequest = {
        categories: [newGoal.category],
        timeline_months: parseInt(newGoal.timeline_months),
        roadmap_id: newGoal.roadmap_id || null
      };

      const response = await careerStrategyAPI.createGoals(goalsRequest);

      if (response.success) {
        setShowCreateForm(false);
        setNewGoal({
          title: '',
          description: '',
          category: 'skill_development',
          priority: 1,
          timeline_months: 6,
          roadmap_id: ''
        });
        if (onRefresh) onRefresh();
      } else {
        setError(response.error || 'Failed to create goal');
      }
    } catch (error) {
      console.error('Error creating goal:', error);
      setError('Failed to create goal. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateGoal = async (goalId, updateData) => {
    try {
      const response = await careerStrategyAPI.updateGoal(goalId, updateData);
      
      if (response.success && onGoalUpdated) {
        onGoalUpdated(response.data);
      }
    } catch (error) {
      console.error('Error updating goal:', error);
    }
  };

  const handleProgressUpdate = async (goalId, newProgress) => {
    await handleUpdateGoal(goalId, { progress_percentage: newProgress });
  };

  const getStatusColor = (status) => {
    return careerStrategyAPI.getStatusColor(status);
  };

  const getPriorityColor = (priority) => {
    return careerStrategyAPI.getPriorityColor(priority);
  };

  const formatStatus = (status) => {
    return careerStrategyAPI.formatStatus(status);
  };

  const groupedGoals = goals.reduce((acc, goal) => {
    const category = goal.category || 'other';
    if (!acc[category]) acc[category] = [];
    acc[category].push(goal);
    return acc;
  }, {});

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Goals & Milestones</h2>
          <p className="text-gray-600">
            Track your career goals and milestones with detailed progress monitoring.
          </p>
        </div>
        <button
          onClick={() => setShowCreateForm(true)}
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
        >
          Create Goal
        </button>
      </div>

      {/* View Toggle */}
      <div className="flex space-x-1 mb-6 bg-gray-100 rounded-lg p-1">
        <button
          onClick={() => setActiveView('goals')}
          className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
            activeView === 'goals'
              ? 'bg-white text-gray-900 shadow-sm'
              : 'text-gray-600 hover:text-gray-900'
          }`}
        >
          Goals ({goals.length})
        </button>
        <button
          onClick={() => setActiveView('milestones')}
          className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
            activeView === 'milestones'
              ? 'bg-white text-gray-900 shadow-sm'
              : 'text-gray-600 hover:text-gray-900'
          }`}
        >
          Milestones ({milestones.length})
        </button>
      </div>

      {/* Create Goal Form */}
      {showCreateForm && (
        <div className="bg-white border rounded-lg p-6 mb-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Create New Goal</h3>
          <form onSubmit={handleCreateGoal} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Goal Title *
                </label>
                <Input
                  value={newGoal.title}
                  onChange={(e) => setNewGoal(prev => ({ ...prev, title: e.target.value }))}
                  placeholder="e.g., Master React Development"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Category
                </label>
                <Select
                  value={newGoal.category}
                  onChange={(e) => setNewGoal(prev => ({ ...prev, category: e.target.value }))}
                  options={categoryOptions}
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Description
              </label>
              <Textarea
                value={newGoal.description}
                onChange={(e) => setNewGoal(prev => ({ ...prev, description: e.target.value }))}
                placeholder="Describe your goal and what you want to achieve..."
                rows={3}
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Priority
                </label>
                <Select
                  value={newGoal.priority}
                  onChange={(e) => setNewGoal(prev => ({ ...prev, priority: parseInt(e.target.value) }))}
                  options={priorityOptions}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Timeline (months)
                </label>
                <Input
                  type="number"
                  value={newGoal.timeline_months}
                  onChange={(e) => setNewGoal(prev => ({ ...prev, timeline_months: parseInt(e.target.value) }))}
                  min="1"
                  max="60"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Roadmap (Optional)
                </label>
                <Select
                  value={newGoal.roadmap_id}
                  onChange={(e) => setNewGoal(prev => ({ ...prev, roadmap_id: e.target.value }))}
                  options={[
                    { value: '', label: 'No roadmap' },
                    ...roadmaps.map(r => ({ value: r.roadmap_id, label: r.title }))
                  ]}
                />
              </div>
            </div>

            {error && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-3">
                <p className="text-red-800 text-sm">{error}</p>
              </div>
            )}

            <div className="flex justify-end space-x-3">
              <button
                type="button"
                onClick={() => setShowCreateForm(false)}
                className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50 transition-colors"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={loading}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 transition-colors"
              >
                {loading ? 'Creating...' : 'Create Goal'}
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Goals View */}
      {activeView === 'goals' && (
        <div className="space-y-6">
          {goals.length === 0 ? (
            <div className="text-center py-12">
              <div className="text-gray-400 text-6xl mb-4">🎯</div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">No Goals Yet</h3>
              <p className="text-gray-600 mb-4">
                Create your first career goal to start tracking your progress.
              </p>
              <button
                onClick={() => setShowCreateForm(true)}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
              >
                Create Your First Goal
              </button>
            </div>
          ) : (
            Object.entries(groupedGoals).map(([category, categoryGoals]) => (
              <div key={category} className="bg-white border rounded-lg p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4 capitalize">
                  {category.replace('_', ' ')} Goals
                </h3>
                <div className="space-y-4">
                  {categoryGoals.map((goal) => (
                    <div key={goal.goal_id} className="border rounded-lg p-4">
                      <div className="flex items-start justify-between mb-3">
                        <div className="flex-1">
                          <h4 className="font-medium text-gray-900 mb-1">{goal.title}</h4>
                          {goal.description && (
                            <p className="text-sm text-gray-600 mb-2">{goal.description}</p>
                          )}
                          <div className="flex items-center space-x-4">
                            <span 
                              className="text-xs px-2 py-1 rounded-full text-white"
                              style={{ backgroundColor: getPriorityColor(goal.priority) }}
                            >
                              Priority {goal.priority}
                            </span>
                            <span 
                              className="text-xs px-2 py-1 rounded-full text-white"
                              style={{ backgroundColor: getStatusColor(goal.status) }}
                            >
                              {formatStatus(goal.status)}
                            </span>
                            {goal.target_date && (
                              <span className="text-xs text-gray-500">
                                Due: {new Date(goal.target_date).toLocaleDateString()}
                              </span>
                            )}
                          </div>
                        </div>
                      </div>

                      {/* Progress Bar */}
                      <div className="mb-3">
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-sm font-medium text-gray-700">Progress</span>
                          <span className="text-sm text-gray-600">{goal.progress_percentage || 0}%</span>
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-2">
                          <div 
                            className="bg-blue-600 h-2 rounded-full transition-all duration-300" 
                            style={{ width: `${goal.progress_percentage || 0}%` }}
                          ></div>
                        </div>
                      </div>

                      {/* Progress Update */}
                      <div className="flex items-center space-x-2">
                        <input
                          type="range"
                          min="0"
                          max="100"
                          value={goal.progress_percentage || 0}
                          onChange={(e) => handleProgressUpdate(goal.goal_id, parseInt(e.target.value))}
                          className="flex-1 h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
                        />
                        <button
                          onClick={() => setEditingGoal(goal)}
                          className="text-blue-600 hover:text-blue-800 text-sm font-medium"
                        >
                          Edit
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ))
          )}
        </div>
      )}

      {/* Milestones View */}
      {activeView === 'milestones' && (
        <div className="space-y-6">
          {milestones.length === 0 ? (
            <div className="text-center py-12">
              <div className="text-gray-400 text-6xl mb-4">🏁</div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">No Milestones Yet</h3>
              <p className="text-gray-600 mb-4">
                Milestones will be created automatically when you generate a roadmap.
              </p>
            </div>
          ) : (
            <div className="bg-white border rounded-lg p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Career Milestones</h3>
              <div className="space-y-4">
                {milestones.map((milestone) => (
                  <div key={milestone.milestone_id} className="border-l-4 border-blue-500 pl-4 py-2">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <h4 className="font-medium text-gray-900">{milestone.title}</h4>
                        {milestone.description && (
                          <p className="text-sm text-gray-600 mt-1">{milestone.description}</p>
                        )}
                        <div className="flex items-center space-x-4 mt-2">
                          <span className="text-xs text-gray-500 capitalize">
                            {careerStrategyAPI.formatMilestoneType(milestone.milestone_type)}
                          </span>
                          <span 
                            className="text-xs px-2 py-1 rounded-full text-white"
                            style={{ backgroundColor: getStatusColor(milestone.status) }}
                          >
                            {formatStatus(milestone.status)}
                          </span>
                          {milestone.target_date && (
                            <span className="text-xs text-gray-500">
                              Target: {new Date(milestone.target_date).toLocaleDateString()}
                            </span>
                          )}
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="text-sm font-medium text-gray-900">
                          {milestone.progress_percentage || 0}%
                        </div>
                        <div className="w-16 bg-gray-200 rounded-full h-2 mt-1">
                          <div 
                            className="bg-green-600 h-2 rounded-full" 
                            style={{ width: `${milestone.progress_percentage || 0}%` }}
                          ></div>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default GoalTracker;