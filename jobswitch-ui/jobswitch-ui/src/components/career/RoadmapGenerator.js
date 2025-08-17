/**
 * Roadmap Generator Component
 * Creates comprehensive career roadmaps based on current and target roles
 */
import React, { useState } from 'react';
import { Input } from '../ui/Input';
import { Textarea } from '../ui/Textarea';
import { Select } from '../ui/Select';
import careerStrategyAPI from '../../services/careerStrategyAPI';

const RoadmapGenerator = ({ onRoadmapCreated, existingRoadmaps = [] }) => {
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    current_role: '',
    target_role: '',
    target_industry: '',
    target_company: '',
    timeline_months: 24
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [generatedRoadmap, setGeneratedRoadmap] = useState(null);

  const timelineOptions = [
    { value: 6, label: '6 months' },
    { value: 12, label: '1 year' },
    { value: 18, label: '1.5 years' },
    { value: 24, label: '2 years' },
    { value: 36, label: '3 years' },
    { value: 48, label: '4 years' }
  ];

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!formData.current_role || !formData.target_role) {
      setError('Please provide both current and target roles.');
      return;
    }

    try {
      setLoading(true);
      setError(null);

      const roadmapData = {
        ...formData,
        timeline_months: parseInt(formData.timeline_months)
      };

      const response = await careerStrategyAPI.generateRoadmap(roadmapData);

      if (response.success) {
        setGeneratedRoadmap(response.data);
        if (onRoadmapCreated) {
          onRoadmapCreated(response.data);
        }
      } else {
        setError(response.error || 'Failed to generate roadmap');
      }
    } catch (error) {
      console.error('Error generating roadmap:', error);
      setError('Failed to generate roadmap. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const resetForm = () => {
    setFormData({
      title: '',
      description: '',
      current_role: '',
      target_role: '',
      target_industry: '',
      target_company: '',
      timeline_months: 24
    });
    setGeneratedRoadmap(null);
    setError(null);
  };

  return (
    <div className="p-6">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Career Roadmap Generator</h2>
        <p className="text-gray-600">
          Create a comprehensive career roadmap with AI-powered insights and personalized milestones.
        </p>
      </div>

      {/* Existing Roadmaps */}
      {existingRoadmaps.length > 0 && (
        <div className="mb-8">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Your Existing Roadmaps</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {existingRoadmaps.map((roadmap) => (
              <div key={roadmap.roadmap_id} className="bg-gray-50 rounded-lg p-4 border">
                <h4 className="font-medium text-gray-900 mb-2">{roadmap.title}</h4>
                <p className="text-sm text-gray-600 mb-2">
                  {roadmap.current_role} → {roadmap.target_role}
                </p>
                <div className="flex items-center justify-between">
                  <span className="text-xs text-gray-500">
                    {roadmap.progress_percentage}% complete
                  </span>
                  <div className="w-20 bg-gray-200 rounded-full h-2">
                    <div 
                      className="bg-blue-600 h-2 rounded-full" 
                      style={{ width: `${roadmap.progress_percentage}%` }}
                    ></div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Roadmap Generation Form */}
      {!generatedRoadmap && (
        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Roadmap Title
              </label>
              <Input
                name="title"
                value={formData.title}
                onChange={handleInputChange}
                placeholder="e.g., Senior Developer Career Path"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Timeline
              </label>
              <Select
                name="timeline_months"
                value={formData.timeline_months}
                onChange={handleInputChange}
                options={timelineOptions}
                required
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Description (Optional)
            </label>
            <Textarea
              name="description"
              value={formData.description}
              onChange={handleInputChange}
              placeholder="Describe your career goals and aspirations..."
              rows={3}
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Current Role *
              </label>
              <Input
                name="current_role"
                value={formData.current_role}
                onChange={handleInputChange}
                placeholder="e.g., Software Developer"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Target Role *
              </label>
              <Input
                name="target_role"
                value={formData.target_role}
                onChange={handleInputChange}
                placeholder="e.g., Senior Software Engineer"
                required
              />
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Target Industry (Optional)
              </label>
              <Input
                name="target_industry"
                value={formData.target_industry}
                onChange={handleInputChange}
                placeholder="e.g., Technology, Finance, Healthcare"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Target Company (Optional)
              </label>
              <Input
                name="target_company"
                value={formData.target_company}
                onChange={handleInputChange}
                placeholder="e.g., Google, Microsoft, Startup"
              />
            </div>
          </div>

          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <div className="flex items-center">
                <div className="text-red-400 mr-3">
                  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                  </svg>
                </div>
                <p className="text-red-800 text-sm">{error}</p>
              </div>
            </div>
          )}

          <div className="flex justify-end space-x-4">
            <button
              type="button"
              onClick={resetForm}
              className="px-6 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50 transition-colors"
            >
              Reset
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {loading ? (
                <div className="flex items-center">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  Generating...
                </div>
              ) : (
                'Generate Roadmap'
              )}
            </button>
          </div>
        </form>
      )}

      {/* Generated Roadmap Display */}
      {generatedRoadmap && (
        <div className="mt-8">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-xl font-bold text-gray-900">Generated Roadmap</h3>
            <button
              onClick={resetForm}
              className="px-4 py-2 text-blue-600 hover:text-blue-800 text-sm font-medium"
            >
              Create Another Roadmap
            </button>
          </div>

          <div className="bg-green-50 border border-green-200 rounded-lg p-6 mb-6">
            <div className="flex items-center">
              <div className="text-green-400 mr-3">
                <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
              </div>
              <div>
                <h4 className="text-green-800 font-medium">Roadmap Generated Successfully!</h4>
                <p className="text-green-600 text-sm mt-1">
                  Your personalized career roadmap has been created with AI-powered insights.
                </p>
              </div>
            </div>
          </div>

          {/* Roadmap Overview */}
          <div className="bg-white border rounded-lg p-6 mb-6">
            <h4 className="text-lg font-semibold text-gray-900 mb-4">Roadmap Overview</h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h5 className="font-medium text-gray-700 mb-2">Transition Details</h5>
                <p className="text-sm text-gray-600 mb-1">
                  <span className="font-medium">From:</span> {formData.current_role}
                </p>
                <p className="text-sm text-gray-600 mb-1">
                  <span className="font-medium">To:</span> {formData.target_role}
                </p>
                <p className="text-sm text-gray-600 mb-1">
                  <span className="font-medium">Timeline:</span> {formData.timeline_months} months
                </p>
                {formData.target_industry && (
                  <p className="text-sm text-gray-600 mb-1">
                    <span className="font-medium">Industry:</span> {formData.target_industry}
                  </p>
                )}
              </div>
              <div>
                <h5 className="font-medium text-gray-700 mb-2">Success Metrics</h5>
                <div className="space-y-2">
                  <div className="flex items-center text-sm text-gray-600">
                    <div className="w-2 h-2 bg-green-500 rounded-full mr-2"></div>
                    Skill development milestones
                  </div>
                  <div className="flex items-center text-sm text-gray-600">
                    <div className="w-2 h-2 bg-blue-500 rounded-full mr-2"></div>
                    Experience requirements
                  </div>
                  <div className="flex items-center text-sm text-gray-600">
                    <div className="w-2 h-2 bg-purple-500 rounded-full mr-2"></div>
                    Networking goals
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Milestones */}
          {generatedRoadmap.milestones && generatedRoadmap.milestones.length > 0 && (
            <div className="bg-white border rounded-lg p-6 mb-6">
              <h4 className="text-lg font-semibold text-gray-900 mb-4">Key Milestones</h4>
              <div className="space-y-4">
                {generatedRoadmap.milestones.slice(0, 5).map((milestone, index) => (
                  <div key={index} className="flex items-start">
                    <div className="flex-shrink-0 w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center mr-4">
                      <span className="text-blue-600 text-sm font-medium">{index + 1}</span>
                    </div>
                    <div className="flex-1">
                      <h5 className="font-medium text-gray-900">{milestone.title}</h5>
                      <p className="text-sm text-gray-600 mt-1">{milestone.description}</p>
                      <div className="flex items-center mt-2 space-x-4">
                        <span className="text-xs text-gray-500">
                          Timeline: {milestone.timeline}
                        </span>
                        <span className={`text-xs px-2 py-1 rounded-full ${
                          milestone.priority === 'high' 
                            ? 'bg-red-100 text-red-800' 
                            : milestone.priority === 'medium'
                            ? 'bg-yellow-100 text-yellow-800'
                            : 'bg-green-100 text-green-800'
                        }`}>
                          {milestone.priority} priority
                        </span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Goals */}
          {generatedRoadmap.goals && generatedRoadmap.goals.length > 0 && (
            <div className="bg-white border rounded-lg p-6">
              <h4 className="text-lg font-semibold text-gray-900 mb-4">Career Goals</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {generatedRoadmap.goals.slice(0, 4).map((goal, index) => (
                  <div key={index} className="border rounded-lg p-4">
                    <h5 className="font-medium text-gray-900 mb-2">{goal.title}</h5>
                    <p className="text-sm text-gray-600 mb-3">{goal.description}</p>
                    <div className="flex items-center justify-between">
                      <span className="text-xs text-gray-500 capitalize">
                        {goal.category?.replace('_', ' ')}
                      </span>
                      <span className="text-xs text-blue-600 font-medium">
                        {goal.timeline_months} months
                      </span>
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

export default RoadmapGenerator;