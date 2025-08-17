import React, { useState } from 'react';

const JobCard = ({ job, recommendation = null, onSave, onFeedback, showActions = true }) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [isSaving, setIsSaving] = useState(false);

  const handleSave = async () => {
    if (isSaving) return;
    setIsSaving(true);
    try {
      await onSave(job.job_id);
    } finally {
      setIsSaving(false);
    }
  };

  const handleFeedback = async (feedback) => {
    if (recommendation && onFeedback) {
      await onFeedback(recommendation.recommendation_id, feedback);
    }
  };

  const formatSalary = (min, max, currency = 'USD') => {
    if (!min && !max) return null;
    const formatter = new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency,
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    });
    
    if (min && max) {
      return `${formatter.format(min)} - ${formatter.format(max)}`;
    }
    return formatter.format(min || max);
  };

  const getScoreColor = (score) => {
    if (score >= 0.8) return 'text-green-600 bg-green-100';
    if (score >= 0.6) return 'text-blue-600 bg-blue-100';
    if (score >= 0.4) return 'text-yellow-600 bg-yellow-100';
    return 'text-red-600 bg-red-100';
  };

  const getScoreLabel = (score) => {
    if (score >= 0.8) return 'Excellent Match';
    if (score >= 0.6) return 'Good Match';
    if (score >= 0.4) return 'Fair Match';
    return 'Poor Match';
  };

  return (
    <div className="bg-white rounded-lg shadow-md hover:shadow-lg transition-shadow duration-200 p-6 mb-4">
      {/* Header */}
      <div className="flex justify-between items-start mb-4">
        <div className="flex-1">
          <h3 className="text-xl font-semibold text-gray-800 mb-1">{job.title}</h3>
          <p className="text-lg text-gray-600 mb-1">{job.company}</p>
          <div className="flex items-center text-sm text-gray-500 space-x-4">
            <span>📍 {job.location}</span>
            {job.remote_type && (
              <span className="capitalize">🏠 {job.remote_type}</span>
            )}
            {job.posted_date && (
              <span>📅 {new Date(job.posted_date).toLocaleDateString()}</span>
            )}
          </div>
        </div>
        
        {/* Compatibility Score */}
        {recommendation && (
          <div className="text-right ml-4">
            <div className={`px-3 py-2 rounded-lg text-sm font-medium ${getScoreColor(recommendation.compatibility_score)}`}>
              {Math.round(recommendation.compatibility_score * 100)}% Match
            </div>
            <p className="text-xs text-gray-500 mt-1">
              {getScoreLabel(recommendation.compatibility_score)}
            </p>
          </div>
        )}
      </div>

      {/* Job Details */}
      <div className="mb-4">
        <div className="flex flex-wrap gap-2 mb-3">
          {job.experience_level && (
            <span className="bg-gray-100 text-gray-700 px-2 py-1 rounded text-sm">
              📊 {job.experience_level}
            </span>
          )}
          {job.employment_type && (
            <span className="bg-gray-100 text-gray-700 px-2 py-1 rounded text-sm">
              ⏰ {job.employment_type}
            </span>
          )}
          {job.industry && (
            <span className="bg-gray-100 text-gray-700 px-2 py-1 rounded text-sm">
              🏢 {job.industry}
            </span>
          )}
          {formatSalary(job.salary_min, job.salary_max, job.salary_currency) && (
            <span className="bg-green-100 text-green-700 px-2 py-1 rounded text-sm">
              💰 {formatSalary(job.salary_min, job.salary_max, job.salary_currency)}
            </span>
          )}
        </div>

        {/* Description */}
        <p className="text-gray-700 mb-3">
          {isExpanded 
            ? job.description 
            : `${job.description?.substring(0, 200)}${job.description?.length > 200 ? '...' : ''}`
          }
        </p>
        
        {job.description?.length > 200 && (
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="text-blue-600 hover:text-blue-800 text-sm font-medium"
          >
            {isExpanded ? 'Show Less' : 'Show More'}
          </button>
        )}
      </div>

      {/* Detailed Scores */}
      {recommendation?.detailed_scores && (
        <div className="mb-4 p-3 bg-gray-50 rounded-lg">
          <h4 className="text-sm font-medium text-gray-700 mb-2">Compatibility Breakdown</h4>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-2 text-xs">
            <div className="text-center">
              <div className="font-medium text-gray-600">Skills</div>
              <div className={`font-bold ${getScoreColor(recommendation.detailed_scores.skill_match).split(' ')[0]}`}>
                {Math.round(recommendation.detailed_scores.skill_match * 100)}%
              </div>
            </div>
            <div className="text-center">
              <div className="font-medium text-gray-600">Experience</div>
              <div className={`font-bold ${getScoreColor(recommendation.detailed_scores.experience_match).split(' ')[0]}`}>
                {Math.round(recommendation.detailed_scores.experience_match * 100)}%
              </div>
            </div>
            <div className="text-center">
              <div className="font-medium text-gray-600">Location</div>
              <div className={`font-bold ${getScoreColor(recommendation.detailed_scores.location_match).split(' ')[0]}`}>
                {Math.round(recommendation.detailed_scores.location_match * 100)}%
              </div>
            </div>
            <div className="text-center">
              <div className="font-medium text-gray-600">Salary</div>
              <div className={`font-bold ${getScoreColor(recommendation.detailed_scores.salary_match).split(' ')[0]}`}>
                {Math.round(recommendation.detailed_scores.salary_match * 100)}%
              </div>
            </div>
            <div className="text-center">
              <div className="font-medium text-gray-600">Growth</div>
              <div className={`font-bold ${getScoreColor(recommendation.detailed_scores.career_growth).split(' ')[0]}`}>
                {Math.round(recommendation.detailed_scores.career_growth * 100)}%
              </div>
            </div>
          </div>
        </div>
      )}

      {/* AI Insights */}
      {recommendation && (
        <div className="mb-4">
          {recommendation.strengths?.length > 0 && (
            <div className="mb-2">
              <h4 className="text-sm font-medium text-green-700 mb-1">✅ Strengths</h4>
              <ul className="text-sm text-green-600 list-disc list-inside">
                {recommendation.strengths.map((strength, index) => (
                  <li key={index}>{strength}</li>
                ))}
              </ul>
            </div>
          )}
          
          {recommendation.concerns?.length > 0 && (
            <div className="mb-2">
              <h4 className="text-sm font-medium text-yellow-700 mb-1">⚠️ Considerations</h4>
              <ul className="text-sm text-yellow-600 list-disc list-inside">
                {recommendation.concerns.map((concern, index) => (
                  <li key={index}>{concern}</li>
                ))}
              </ul>
            </div>
          )}

          {recommendation.reasoning && (
            <div className="bg-blue-50 p-3 rounded mb-2">
              <h4 className="text-sm font-medium text-blue-800 mb-1">🤖 AI Analysis</h4>
              <p className="text-sm text-blue-700">{recommendation.reasoning}</p>
            </div>
          )}

          {recommendation.ai_recommendation && (
            <div className="bg-purple-50 p-3 rounded">
              <h4 className="text-sm font-medium text-purple-800 mb-1">💡 Recommendation</h4>
              <p className="text-sm text-purple-700">{recommendation.ai_recommendation}</p>
            </div>
          )}
        </div>
      )}

      {/* Actions */}
      {showActions && (
        <div className="flex flex-wrap gap-2 pt-4 border-t border-gray-200">
          <button
            onClick={handleSave}
            disabled={isSaving}
            className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 disabled:opacity-50 text-sm"
          >
            {isSaving ? 'Saving...' : '💾 Save Job'}
          </button>
          
          {job.source_url && (
            <a
              href={job.source_url}
              target="_blank"
              rel="noopener noreferrer"
              className="bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700 text-sm"
            >
              🔗 Apply Now
            </a>
          )}
          
          {recommendation && (
            <>
              <button
                onClick={() => handleFeedback('interested')}
                className="bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700 text-sm"
                disabled={recommendation.user_feedback === 'interested'}
              >
                👍 Interested
              </button>
              <button
                onClick={() => handleFeedback('not_interested')}
                className="bg-gray-600 text-white px-4 py-2 rounded hover:bg-gray-700 text-sm"
                disabled={recommendation.user_feedback === 'not_interested'}
              >
                👎 Not Interested
              </button>
              <button
                onClick={() => handleFeedback('applied')}
                className="bg-purple-600 text-white px-4 py-2 rounded hover:bg-purple-700 text-sm"
                disabled={recommendation.user_feedback === 'applied'}
              >
                ✅ Applied
              </button>
            </>
          )}
          
          {recommendation?.user_feedback && (
            <span className="px-3 py-2 bg-gray-100 text-gray-600 rounded text-sm">
              Status: {recommendation.user_feedback.replace('_', ' ')}
            </span>
          )}
        </div>
      )}
    </div>
  );
};

export default JobCard;