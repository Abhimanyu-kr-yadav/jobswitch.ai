import React, { useState } from 'react';

const JobFilters = ({ onFiltersChange, initialFilters = {} }) => {
  const [filters, setFilters] = useState({
    location: '',
    remote_type: '',
    experience_level: '',
    employment_type: '',
    salary_min: '',
    min_score: 0.0,
    feedback_filter: '',
    sort_by: 'compatibility_score',
    ...initialFilters
  });

  const [isExpanded, setIsExpanded] = useState(false);

  const handleFilterChange = (key, value) => {
    const newFilters = { ...filters, [key]: value };
    setFilters(newFilters);
    onFiltersChange(newFilters);
  };

  const clearFilters = () => {
    const clearedFilters = {
      location: '',
      remote_type: '',
      experience_level: '',
      employment_type: '',
      salary_min: '',
      min_score: 0.0,
      feedback_filter: '',
      sort_by: 'compatibility_score'
    };
    setFilters(clearedFilters);
    onFiltersChange(clearedFilters);
  };

  const hasActiveFilters = Object.values(filters).some(value => 
    value !== '' && value !== 0.0 && value !== 'compatibility_score'
  );

  return (
    <div className="bg-white rounded-lg shadow-md p-4 mb-6">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold text-gray-800">Filters & Sorting</h3>
        <div className="flex items-center space-x-2">
          {hasActiveFilters && (
            <button
              onClick={clearFilters}
              className="text-sm text-red-600 hover:text-red-800"
            >
              Clear All
            </button>
          )}
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="text-blue-600 hover:text-blue-800 text-sm font-medium"
          >
            {isExpanded ? 'Hide Filters' : 'Show Filters'}
          </button>
        </div>
      </div>

      {/* Always visible: Sort and Score */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Sort By
          </label>
          <select
            value={filters.sort_by}
            onChange={(e) => handleFilterChange('sort_by', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="compatibility_score">Compatibility Score</option>
            <option value="created_at">Recently Added</option>
            <option value="skill_match_score">Skill Match</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Minimum Compatibility Score: {Math.round(filters.min_score * 100)}%
          </label>
          <input
            type="range"
            min="0"
            max="1"
            step="0.1"
            value={filters.min_score}
            onChange={(e) => handleFilterChange('min_score', parseFloat(e.target.value))}
            className="w-full"
          />
        </div>
      </div>

      {/* Expandable filters */}
      {isExpanded && (
        <div className="border-t border-gray-200 pt-4">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {/* Location */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Location
              </label>
              <input
                type="text"
                value={filters.location}
                onChange={(e) => handleFilterChange('location', e.target.value)}
                placeholder="City, State, or Country"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            {/* Remote Type */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Work Arrangement
              </label>
              <select
                value={filters.remote_type}
                onChange={(e) => handleFilterChange('remote_type', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">Any</option>
                <option value="remote">Remote</option>
                <option value="hybrid">Hybrid</option>
                <option value="onsite">On-site</option>
              </select>
            </div>

            {/* Experience Level */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Experience Level
              </label>
              <select
                value={filters.experience_level}
                onChange={(e) => handleFilterChange('experience_level', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">Any</option>
                <option value="entry">Entry Level</option>
                <option value="mid">Mid Level</option>
                <option value="senior">Senior Level</option>
                <option value="executive">Executive</option>
                <option value="lead">Lead</option>
              </select>
            </div>

            {/* Employment Type */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Employment Type
              </label>
              <select
                value={filters.employment_type}
                onChange={(e) => handleFilterChange('employment_type', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">Any</option>
                <option value="full-time">Full-time</option>
                <option value="part-time">Part-time</option>
                <option value="contract">Contract</option>
                <option value="freelance">Freelance</option>
                <option value="internship">Internship</option>
              </select>
            </div>

            {/* Minimum Salary */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Minimum Salary
              </label>
              <input
                type="number"
                value={filters.salary_min}
                onChange={(e) => handleFilterChange('salary_min', e.target.value)}
                placeholder="e.g., 80000"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            {/* Feedback Filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Feedback Status
              </label>
              <select
                value={filters.feedback_filter}
                onChange={(e) => handleFilterChange('feedback_filter', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">All</option>
                <option value="no_feedback">No Feedback</option>
                <option value="interested">Interested</option>
                <option value="not_interested">Not Interested</option>
                <option value="applied">Applied</option>
              </select>
            </div>
          </div>
        </div>
      )}

      {/* Active filters summary */}
      {hasActiveFilters && (
        <div className="mt-4 pt-4 border-t border-gray-200">
          <div className="flex flex-wrap gap-2">
            <span className="text-sm text-gray-600">Active filters:</span>
            {filters.location && (
              <span className="bg-blue-100 text-blue-800 px-2 py-1 rounded text-sm">
                📍 {filters.location}
              </span>
            )}
            {filters.remote_type && (
              <span className="bg-green-100 text-green-800 px-2 py-1 rounded text-sm">
                🏠 {filters.remote_type}
              </span>
            )}
            {filters.experience_level && (
              <span className="bg-purple-100 text-purple-800 px-2 py-1 rounded text-sm">
                📊 {filters.experience_level}
              </span>
            )}
            {filters.employment_type && (
              <span className="bg-yellow-100 text-yellow-800 px-2 py-1 rounded text-sm">
                ⏰ {filters.employment_type}
              </span>
            )}
            {filters.salary_min && (
              <span className="bg-green-100 text-green-800 px-2 py-1 rounded text-sm">
                💰 ${parseInt(filters.salary_min).toLocaleString()}+
              </span>
            )}
            {filters.min_score > 0 && (
              <span className="bg-red-100 text-red-800 px-2 py-1 rounded text-sm">
                🎯 {Math.round(filters.min_score * 100)}%+ match
              </span>
            )}
            {filters.feedback_filter && (
              <span className="bg-gray-100 text-gray-800 px-2 py-1 rounded text-sm">
                📝 {filters.feedback_filter.replace('_', ' ')}
              </span>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default JobFilters;