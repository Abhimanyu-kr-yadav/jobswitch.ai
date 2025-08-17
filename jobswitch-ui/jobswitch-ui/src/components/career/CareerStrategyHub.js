/**
 * Career Strategy Hub Component
 * Main dashboard for career strategy planning and tracking
 */
import React, { useState, useEffect } from 'react';
import { Tabs } from '../ui/Tabs';
import RoadmapGenerator from './RoadmapGenerator';
import GoalTracker from './GoalTracker';
import ProgressVisualization from './ProgressVisualization';
import MarketTrends from './MarketTrends';
import careerStrategyAPI from '../../services/careerStrategyAPI';

const CareerStrategyHub = () => {
  const [activeTab, setActiveTab] = useState('roadmap');
  const [roadmaps, setRoadmaps] = useState([]);
  const [goals, setGoals] = useState([]);
  const [recommendations, setRecommendations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadCareerData();
  }, []);

  const loadCareerData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Load user roadmaps, goals, and recommendations in parallel
      const [roadmapsResponse, goalsResponse, recommendationsResponse] = await Promise.all([
        careerStrategyAPI.getUserRoadmaps(),
        careerStrategyAPI.getGoals(),
        careerStrategyAPI.getCareerRecommendations()
      ]);

      if (roadmapsResponse.success) {
        setRoadmaps(roadmapsResponse.data.roadmaps || []);
      }

      if (goalsResponse.success) {
        setGoals(goalsResponse.data.goals || []);
      }

      if (recommendationsResponse.success) {
        setRecommendations(recommendationsResponse.data.recommendations || []);
      }
    } catch (error) {
      console.error('Error loading career data:', error);
      setError('Failed to load career data. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleRoadmapCreated = (newRoadmap) => {
    setRoadmaps(prev => [...prev, newRoadmap]);
    setActiveTab('progress'); // Switch to progress tab to show the new roadmap
  };

  const handleGoalUpdated = (updatedGoal) => {
    setGoals(prev => prev.map(goal => 
      goal.goal_id === updatedGoal.goal_id ? updatedGoal : goal
    ));
  };

  const tabs = [
    {
      id: 'roadmap',
      label: 'Career Roadmap',
      icon: '🗺️',
      content: (
        <RoadmapGenerator 
          onRoadmapCreated={handleRoadmapCreated}
          existingRoadmaps={roadmaps}
        />
      )
    },
    {
      id: 'goals',
      label: 'Goals & Milestones',
      icon: '🎯',
      content: (
        <GoalTracker 
          goals={goals}
          roadmaps={roadmaps}
          onGoalUpdated={handleGoalUpdated}
          onRefresh={loadCareerData}
        />
      )
    },
    {
      id: 'progress',
      label: 'Progress Tracking',
      icon: '📊',
      content: (
        <ProgressVisualization 
          roadmaps={roadmaps}
          goals={goals}
          onRefresh={loadCareerData}
        />
      )
    },
    {
      id: 'trends',
      label: 'Market Insights',
      icon: '📈',
      content: (
        <MarketTrends 
          recommendations={recommendations}
          onRefresh={loadCareerData}
        />
      )
    }
  ];

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-96">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading your career strategy...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-6">
        <div className="flex items-center">
          <div className="text-red-400 mr-3">
            <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
            </svg>
          </div>
          <div>
            <h3 className="text-red-800 font-medium">Error Loading Career Data</h3>
            <p className="text-red-600 text-sm mt-1">{error}</p>
            <button 
              onClick={loadCareerData}
              className="mt-3 text-red-600 hover:text-red-800 text-sm font-medium"
            >
              Try Again
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto p-6">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Career Strategy</h1>
        <p className="text-gray-600">
          Plan your career journey, set goals, and track your progress with AI-powered insights.
        </p>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="text-blue-600 text-2xl mr-3">🗺️</div>
            <div>
              <p className="text-sm font-medium text-gray-600">Active Roadmaps</p>
              <p className="text-2xl font-bold text-gray-900">{roadmaps.length}</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="text-green-600 text-2xl mr-3">🎯</div>
            <div>
              <p className="text-sm font-medium text-gray-600">Active Goals</p>
              <p className="text-2xl font-bold text-gray-900">
                {goals.filter(g => g.status === 'in_progress').length}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="text-purple-600 text-2xl mr-3">✅</div>
            <div>
              <p className="text-sm font-medium text-gray-600">Completed Goals</p>
              <p className="text-2xl font-bold text-gray-900">
                {goals.filter(g => g.status === 'completed').length}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="text-orange-600 text-2xl mr-3">💡</div>
            <div>
              <p className="text-sm font-medium text-gray-600">Recommendations</p>
              <p className="text-2xl font-bold text-gray-900">{recommendations.length}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content Tabs */}
      <div className="bg-white rounded-lg shadow">
        <Tabs
          tabs={tabs}
          activeTab={activeTab}
          onTabChange={setActiveTab}
          className="min-h-96"
        />
      </div>

      {/* Quick Actions */}
      {roadmaps.length === 0 && (
        <div className="mt-8 bg-blue-50 border border-blue-200 rounded-lg p-6">
          <div className="flex items-center">
            <div className="text-blue-400 mr-3">
              <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
              </svg>
            </div>
            <div>
              <h3 className="text-blue-800 font-medium">Get Started with Your Career Strategy</h3>
              <p className="text-blue-600 text-sm mt-1">
                Create your first career roadmap to start planning your professional journey.
              </p>
              <button 
                onClick={() => setActiveTab('roadmap')}
                className="mt-3 bg-blue-600 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-blue-700 transition-colors"
              >
                Create Roadmap
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default CareerStrategyHub;