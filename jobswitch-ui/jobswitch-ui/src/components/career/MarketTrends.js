/**
 * Market Trends Component
 * Displays market insights and career recommendations
 */
import React, { useState, useEffect } from 'react';
import { Input } from '../ui/Input';
import { Select } from '../ui/Select';
import careerStrategyAPI from '../../services/careerStrategyAPI';

const MarketTrends = ({ recommendations = [], onRefresh }) => {
  const [marketData, setMarketData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [filters, setFilters] = useState({
    industry: 'Technology',
    targetRole: '',
    location: 'Global'
  });

  const industryOptions = [
    { value: 'Technology', label: 'Technology' },
    { value: 'Finance', label: 'Finance' },
    { value: 'Healthcare', label: 'Healthcare' },
    { value: 'Education', label: 'Education' },
    { value: 'Manufacturing', label: 'Manufacturing' },
    { value: 'Retail', label: 'Retail' },
    { value: 'Consulting', label: 'Consulting' }
  ];

  const locationOptions = [
    { value: 'Global', label: 'Global' },
    { value: 'United States', label: 'United States' },
    { value: 'Europe', label: 'Europe' },
    { value: 'Asia Pacific', label: 'Asia Pacific' },
    { value: 'Remote', label: 'Remote' }
  ];

  useEffect(() => {
    loadMarketTrends();
  }, []);

  const loadMarketTrends = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await careerStrategyAPI.analyzeMarketTrends(filters);

      if (response.success) {
        setMarketData(response.data);
      } else {
        setError(response.error || 'Failed to load market trends');
      }
    } catch (error) {
      console.error('Error loading market trends:', error);
      setError('Failed to load market trends. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleFilterChange = (e) => {
    const { name, value } = e.target;
    setFilters(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleAnalyze = () => {
    loadMarketTrends();
  };

  const getHealthColor = (health) => {
    switch (health) {
      case 'growing': return '#10b981'; // green
      case 'stable': return '#3b82f6'; // blue
      case 'declining': return '#ef4444'; // red
      default: return '#6b7280'; // gray
    }
  };

  const getDemandColor = (demand) => {
    switch (demand) {
      case 'high': return '#10b981'; // green
      case 'medium': return '#f59e0b'; // amber
      case 'low': return '#ef4444'; // red
      default: return '#6b7280'; // gray
    }
  };

  return (
    <div className="p-6">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Market Insights</h2>
        <p className="text-gray-600">
          Stay informed about market trends and get AI-powered career recommendations.
        </p>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Market Analysis Filters</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Industry
            </label>
            <Select
              name="industry"
              value={filters.industry}
              onChange={handleFilterChange}
              options={industryOptions}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Target Role (Optional)
            </label>
            <Input
              name="targetRole"
              value={filters.targetRole}
              onChange={handleFilterChange}
              placeholder="e.g., Senior Developer, Product Manager"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Location
            </label>
            <Select
              name="location"
              value={filters.location}
              onChange={handleFilterChange}
              options={locationOptions}
            />
          </div>
        </div>
        <button
          onClick={handleAnalyze}
          disabled={loading}
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 transition-colors"
        >
          {loading ? 'Analyzing...' : 'Analyze Market Trends'}
        </button>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
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

      {loading && (
        <div className="flex items-center justify-center py-12">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <p className="text-gray-600">Analyzing market trends...</p>
          </div>
        </div>
      )}

      {marketData && (
        <div className="space-y-6">
          {/* Market Overview */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Market Overview</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <div className="text-center">
                <div className="text-2xl mb-2">🏭</div>
                <p className="text-sm font-medium text-gray-600">Industry Health</p>
                <p 
                  className="text-lg font-bold capitalize"
                  style={{ color: getHealthColor(marketData.market_analysis?.industry_health) }}
                >
                  {marketData.market_analysis?.industry_health || 'Unknown'}
                </p>
              </div>
              <div className="text-center">
                <div className="text-2xl mb-2">📈</div>
                <p className="text-sm font-medium text-gray-600">Role Demand</p>
                <p 
                  className="text-lg font-bold capitalize"
                  style={{ color: getDemandColor(marketData.market_analysis?.role_demand) }}
                >
                  {marketData.market_analysis?.role_demand || 'Unknown'}
                </p>
              </div>
              <div className="text-center">
                <div className="text-2xl mb-2">💰</div>
                <p className="text-sm font-medium text-gray-600">Salary Trend</p>
                <p className="text-lg font-bold text-gray-900 capitalize">
                  {marketData.market_analysis?.salary_trend || 'Unknown'}
                </p>
              </div>
              <div className="text-center">
                <div className="text-2xl mb-2">🏠</div>
                <p className="text-sm font-medium text-gray-600">Remote Work</p>
                <p className="text-lg font-bold text-gray-900">
                  {marketData.market_analysis?.remote_work_adoption || 0}%
                </p>
              </div>
            </div>
          </div>

          {/* Trending Skills */}
          {marketData.trending_skills && marketData.trending_skills.length > 0 && (
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Trending Skills</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {marketData.trending_skills.slice(0, 6).map((skill, index) => (
                  <div key={index} className="border rounded-lg p-4">
                    <div className="flex items-center justify-between mb-2">
                      <h4 className="font-medium text-gray-900">{skill.skill}</h4>
                      <span className="text-sm text-green-600 font-medium">
                        +{skill.demand_growth}%
                      </span>
                    </div>
                    <div className="flex items-center justify-between text-sm text-gray-600">
                      <span>Salary Impact: +{skill.salary_impact}%</span>
                      <span className={`px-2 py-1 rounded-full text-xs ${
                        skill.urgency === 'high' 
                          ? 'bg-red-100 text-red-800'
                          : skill.urgency === 'medium'
                          ? 'bg-yellow-100 text-yellow-800'
                          : 'bg-green-100 text-green-800'
                      }`}>
                        {skill.urgency} urgency
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Declining Skills */}
          {marketData.declining_skills && marketData.declining_skills.length > 0 && (
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Declining Skills</h3>
              <div className="space-y-3">
                {marketData.declining_skills.slice(0, 4).map((skill, index) => (
                  <div key={index} className="flex items-center justify-between p-3 bg-red-50 rounded-lg">
                    <div>
                      <h4 className="font-medium text-gray-900">{skill.skill}</h4>
                      <p className="text-sm text-gray-600">
                        Replacement timeline: {skill.replacement_timeline}
                      </p>
                    </div>
                    <span className="text-red-600 font-medium">
                      {skill.decline_rate}%
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Salary Insights */}
          {marketData.salary_insights && (
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Salary Insights</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <h4 className="font-medium text-gray-700 mb-3">Current Range</h4>
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600">Minimum:</span>
                      <span className="font-medium">${marketData.salary_insights.current_range?.min?.toLocaleString()}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600">Median:</span>
                      <span className="font-medium">${marketData.salary_insights.current_range?.median?.toLocaleString()}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600">Maximum:</span>
                      <span className="font-medium">${marketData.salary_insights.current_range?.max?.toLocaleString()}</span>
                    </div>
                  </div>
                </div>
                <div>
                  <h4 className="font-medium text-gray-700 mb-3">Projected Range</h4>
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600">Minimum:</span>
                      <span className="font-medium text-green-600">${marketData.salary_insights.projected_range?.min?.toLocaleString()}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600">Median:</span>
                      <span className="font-medium text-green-600">${marketData.salary_insights.projected_range?.median?.toLocaleString()}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600">Maximum:</span>
                      <span className="font-medium text-green-600">${marketData.salary_insights.projected_range?.max?.toLocaleString()}</span>
                    </div>
                  </div>
                </div>
              </div>
              {marketData.salary_insights.growth_factors && (
                <div className="mt-4">
                  <h4 className="font-medium text-gray-700 mb-2">Growth Factors</h4>
                  <div className="flex flex-wrap gap-2">
                    {marketData.salary_insights.growth_factors.map((factor, index) => (
                      <span key={index} className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm">
                        {factor}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Career Recommendations */}
          {marketData.career_recommendations && marketData.career_recommendations.length > 0 && (
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">AI Career Recommendations</h3>
              <div className="space-y-4">
                {marketData.career_recommendations.map((rec, index) => (
                  <div key={index} className="border-l-4 border-blue-500 pl-4 py-2">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <h4 className="font-medium text-gray-900">{rec.recommendation}</h4>
                        <p className="text-sm text-gray-600 mt-1">{rec.rationale}</p>
                        <div className="flex items-center space-x-4 mt-2">
                          <span className={`text-xs px-2 py-1 rounded-full ${
                            rec.priority === 'high' 
                              ? 'bg-red-100 text-red-800'
                              : rec.priority === 'medium'
                              ? 'bg-yellow-100 text-yellow-800'
                              : 'bg-green-100 text-green-800'
                          }`}>
                            {rec.priority} priority
                          </span>
                          <span className="text-xs text-gray-500">
                            Timeline: {rec.timeline}
                          </span>
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

      {/* General Recommendations */}
      {recommendations.length > 0 && (
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Your Personalized Recommendations</h3>
          <div className="space-y-4">
            {recommendations.slice(0, 5).map((rec, index) => (
              <div key={index} className="flex items-start">
                <div className="flex-shrink-0 w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center mr-4">
                  <span className="text-blue-600 text-sm font-medium">{index + 1}</span>
                </div>
                <div className="flex-1">
                  <h4 className="font-medium text-gray-900">{rec.title}</h4>
                  <p className="text-sm text-gray-600 mt-1">{rec.description}</p>
                  <div className="flex items-center space-x-4 mt-2">
                    <span className={`text-xs px-2 py-1 rounded-full ${
                      rec.priority === 'high' 
                        ? 'bg-red-100 text-red-800'
                        : rec.priority === 'medium'
                        ? 'bg-yellow-100 text-yellow-800'
                        : 'bg-green-100 text-green-800'
                    }`}>
                      {rec.priority} priority
                    </span>
                    {rec.timeline && (
                      <span className="text-xs text-gray-500">
                        Timeline: {rec.timeline}
                      </span>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {!marketData && !loading && (
        <div className="text-center py-12">
          <div className="text-gray-400 text-6xl mb-4">📈</div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">Market Analysis</h3>
          <p className="text-gray-600 mb-4">
            Get AI-powered insights about market trends and career opportunities.
          </p>
          <button
            onClick={handleAnalyze}
            className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
          >
            Analyze Market Trends
          </button>
        </div>
      )}
    </div>
  );
};

export default MarketTrends;