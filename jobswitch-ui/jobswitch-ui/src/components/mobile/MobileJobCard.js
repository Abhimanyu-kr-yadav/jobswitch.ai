import React, { useState } from 'react';
import useResponsive from '../../hooks/useResponsive';

const MobileJobCard = ({ job, recommendation = null, onSave, onFeedback, showActions = true }) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [showScores, setShowScores] = useState(false);
  const [showInsights, setShowInsights] = useState(false);
  const { isMobile, isSmallMobile } = useResponsive();

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
      maximumFractionDigits: 0,
      notation: isSmallMobile ? 'compact' : 'standard'
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

  const truncateText = (text, maxLength) => {
    if (!text) return '';
    return text.length > maxLength ? `${text.substring(0, maxLength)}...` : text;
  };

  return (
    <div className="bg-white rounded-lg shadow-md hover:shadow-lg transition-shadow duration-200 mb-4 overflow-hidden">
      {/* Header */}
      <div className="p-4 pb-2">
        <div className="flex justify-between items-start mb-2">
          <div className="flex-1 min-w-0">
            <h3 className={`font-semibold text-gray-800 mb-1 ${isSmallMobile ? 'text-lg' : 'text-xl'}`}>
              {truncateText(job.title, isSmallMobile ? 30 : 50)}
            </h3>
            <p className={`text-gray-600 mb-1 ${isSmallMobile ? 'text-base' : 'text-lg'}`}>
              {truncateText(job.company, isSmallMobile ? 25 : 40)}
            </p>
          </div>
          
          {/* Compatibility Score */}
          {recommendation && (
            <div className="ml-2 flex-shrink-0">
              <div className={`px-2 py-1 rounded-lg text-xs font-medium ${getScoreColor(recommendation.compatibility_score)}`}>
                {Math.round(recommendation.compatibility_score * 100)}%
              </div>
            </div>
          )}
        </div>

        {/* Location and Date */}
        <div className="flex flex-wrap items-center text-sm text-gray-500 gap-2 mb-3">
          <span className="flex items-center">
            📍 {truncateText(job.location, isSmallMobile ? 15 : 25)}
          </span>
          {job.remote_type && (
            <span className="flex items-center capitalize">
              🏠 {job.remote_type}
            </span>
          )}
          {job.posted_date && (
            <span className="flex items-center">
              📅 {new Date(job.posted_date).toLocaleDateString('en-US', { 
                month: 'short', 
                day: 'numeric' 
              })}
            </span>
          )}
        </div>

        {/* Tags */}
        <div className="flex flex-wrap gap-1 mb-3">
          {job.experience_level && (
            <span className="bg-gray-100 text-gray-700 px-2 py-1 rounded text-xs">
              📊 {job.experience_level}
            </span>
          )}
          {job.employment_type && (
            <span className="bg-gray-100 text-gray-700 px-2 py-1 rounded text-xs">
              ⏰ {job.employment_type}
            </span>
          )}
          {formatSalary(job.salary_min, job.salary_max, job.salary_currency) && (
            <span className="bg-green-100 text-green-700 px-2 py-1 rounded text-xs">
              💰 {formatSalary(job.salary_min, job.salary_max, job.salary_currency)}
            </span>
          )}
        </div>
      </div>

      {/* Description */}
      <div className="px-4 pb-2">
        <p className="text-gray-700 text-sm">
          {isExpanded 
            ? job.description 
            : truncateText(job.description, isSmallMobile ? 100 : 150)
          }
        </p>
        
        {job.description?.length > (isSmallMobile ? 100 : 150) && (
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="text-blue-600 hover:text-blue-800 text-sm font-medium mt-1"
          >
            {isExpanded ? 'Show Less' : 'Show More'}
          </button>
        )}
      </div>

      {/* Compatibility Breakdown - Collapsible on mobile */}
      {recommendation?.detailed_scores && (
        <div className="px-4 pb-2">
          <button
            onClick={() => setShowScores(!showScores)}
            className="text-sm font-medium text-gray-700 mb-2 flex items-center"
          >
            Compatibility Breakdown
            <svg 
              className={`w-4 h-4 ml-1 transform transition-transform ${showScores ? 'rotate-180' : ''}`}
              fill="none" 
              stroke="currentColor" 
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>
          
          {showScores && (
            <div className="grid grid-cols-3 gap-2 text-xs bg-gray-50 p-2 rounded">
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
            </div>
          )}
        </div>
      )}

      {/* AI Insights - Collapsible */}
      {recommendation && (recommendation.strengths?.length > 0 || recommendation.concerns?.length > 0) && (
        <div className="px-4 pb-2">
          <button
            onClick={() => setShowInsights(!showInsights)}
            className="text-sm font-medium text-gray-700 mb-2 flex items-center"
          >
            AI Insights
            <svg 
              className={`w-4 h-4 ml-1 transform transition-transform ${showInsights ? 'rotate-180' : ''}`}
              fill="none" 
              stroke="currentColor" 
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>
          
          {showInsights && (
            <div className="space-y-2">
              {recommendation.strengths?.length > 0 && (
                <div>
                  <h4 className="text-xs font-medium text-green-700 mb-1">✅ Strengths</h4>
                  <ul className="text-xs text-green-600 list-disc list-inside space-y-1">
                    {recommendation.strengths.slice(0, 2).map((strength, index) => (
                      <li key={index}>{strength}</li>
                    ))}
                  </ul>
                </div>
              )}
              
              {recommendation.concerns?.length > 0 && (
                <div>
                  <h4 className="text-xs font-medium text-yellow-700 mb-1">⚠️ Considerations</h4>
                  <ul className="text-xs text-yellow-600 list-disc list-inside space-y-1">
                    {recommendation.concerns.slice(0, 2).map((concern, index) => (
                      <li key={index}>{concern}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Actions */}
      {showActions && (
        <div className="px-4 py-3 bg-gray-50 border-t border-gray-200">
          <div className="flex flex-wrap gap-2">
            <button
              onClick={handleSave}
              disabled={isSaving}
              className="flex-1 bg-blue-600 text-white px-3 py-2 rounded hover:bg-blue-700 disabled:opacity-50 text-sm font-medium"
            >
              {isSaving ? 'Saving...' : '💾 Save'}
            </button>
            
            {job.source_url && (
              <button
                onClick={() => window.open(job.source_url, '_blank')}
                className="flex-1 bg-green-600 text-white px-3 py-2 rounded hover:bg-green-700 text-sm font-medium"
              >
                🔗 Apply
              </button>
            )}
          </div>
          
          {/* Feedback buttons for recommendations */}
          {recommendation && (
            <div className="flex gap-1 mt-2">
              <button
                onClick={() => handleFeedback('interested')}
                className="flex-1 bg-green-100 text-green-700 px-2 py-1 rounded hover:bg-green-200 text-xs font-medium"
                disabled={recommendation.user_feedback === 'interested'}
              >
                👍 Interested
              </button>
              <button
                onClick={() => handleFeedback('not_interested')}
                className="flex-1 bg-gray-100 text-gray-700 px-2 py-1 rounded hover:bg-gray-200 text-xs font-medium"
                disabled={recommendation.user_feedback === 'not_interested'}
              >
                👎 Not for me
              </button>
              <button
                onClick={() => handleFeedback('applied')}
                className="flex-1 bg-purple-100 text-purple-700 px-2 py-1 rounded hover:bg-purple-200 text-xs font-medium"
                disabled={recommendation.user_feedback === 'applied'}
              >
                ✅ Applied
              </button>
            </div>
          )}
          
          {recommendation?.user_feedback && (
            <div className="mt-2 text-center">
              <span className="px-2 py-1 bg-gray-100 text-gray-600 rounded text-xs">
                Status: {recommendation.user_feedback.replace('_', ' ')}
              </span>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default MobileJobCard;