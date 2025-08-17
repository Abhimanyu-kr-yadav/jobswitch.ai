import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { useAuth } from '../../contexts/AuthContext';
import JobCard from './JobCard';
import MobileJobCard from '../mobile/MobileJobCard';
import JobFilters from './JobFilters';
import useResponsive from '../../hooks/useResponsive';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';

const JobDiscovery = () => {
  const { token } = useAuth();
  const { isMobile, isSmallMobile } = useResponsive();
  const [recommendations, setRecommendations] = useState([]);
  const [searchResults, setSearchResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [filters, setFilters] = useState({});
  const [pagination, setPagination] = useState({
    offset: 0,
    limit: isMobile ? 5 : 10,
    hasMore: false,
    totalCount: 0
  });
  const [activeTab, setActiveTab] = useState('recommendations');

  const loadRecommendations = useCallback(async (offset = 0, append = false) => {
    try {
      setLoading(true);
      const params = {
        limit: pagination.limit,
        offset: offset,
        ...filters
      };
      
      const response = await axios.get(`${API_BASE_URL}/jobs/recommendations`, {
        params,
        headers: { Authorization: `Bearer ${token}` }
      });
      
      if (response.data.success) {
        const newRecommendations = response.data.recommendations;
        setRecommendations(prev => append ? [...prev, ...newRecommendations] : newRecommendations);
        setPagination(prev => ({
          ...prev,
          offset: offset,
          hasMore: response.data.has_more,
          totalCount: response.data.total_count
        }));
      }
    } catch (error) {
      console.error('Error loading recommendations:', error);
    } finally {
      setLoading(false);
    }
  }, [token, filters, pagination.limit]);

  useEffect(() => {
    loadRecommendations();
  }, [filters, loadRecommendations]);

  const discoverJobs = async () => {
    try {
      setLoading(true);
      const response = await axios.post(`${API_BASE_URL}/jobs/discover`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      if (response.data.success) {
        alert('Job discovery started! New jobs will be available shortly.');
        setTimeout(() => loadRecommendations(), 3000);
      }
    } catch (error) {
      console.error('Error discovering jobs:', error);
      alert('Failed to start job discovery');
    } finally {
      setLoading(false);
    }
  };

  const generateRecommendations = async () => {
    try {
      setLoading(true);
      const response = await axios.post(`${API_BASE_URL}/jobs/recommendations/generate`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      if (response.data.success) {
        alert('Generating new recommendations! Please check back in a moment.');
        setTimeout(() => loadRecommendations(), 3000);
      }
    } catch (error) {
      console.error('Error generating recommendations:', error);
      alert('Failed to generate recommendations');
    } finally {
      setLoading(false);
    }
  };

  const searchJobs = async (searchFilters = {}) => {
    try {
      setLoading(true);
      const params = {
        q: searchQuery,
        limit: 20,
        offset: 0,
        ...searchFilters
      };
      
      const response = await axios.get(`${API_BASE_URL}/jobs/search`, {
        params,
        headers: { Authorization: `Bearer ${token}` }
      });
      
      if (response.data.success) {
        setSearchResults(response.data.jobs);
        setActiveTab('search');
      }
    } catch (error) {
      console.error('Error searching jobs:', error);
      alert('Failed to search jobs');
    } finally {
      setLoading(false);
    }
  };

  const saveJob = async (jobId) => {
    try {
      const response = await axios.post(`${API_BASE_URL}/jobs/${jobId}/save`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      if (response.data.success) {
        alert('Job saved successfully!');
      }
    } catch (error) {
      console.error('Error saving job:', error);
      alert('Failed to save job');
    }
  };

  const provideFeedback = async (recommendationId, feedback) => {
    try {
      const response = await axios.post(
        `${API_BASE_URL}/jobs/recommendations/${recommendationId}/feedback`,
        { feedback },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      if (response.data.success) {
        alert('Feedback recorded!');
        loadRecommendations();
      }
    } catch (error) {
      console.error('Error providing feedback:', error);
    }
  };

  const handleFiltersChange = (newFilters) => {
    setFilters(newFilters);
    setPagination(prev => ({ ...prev, offset: 0 }));
  };

  const loadMore = () => {
    if (pagination.hasMore && !loading) {
      const newOffset = pagination.offset + pagination.limit;
      loadRecommendations(newOffset, true);
    }
  };



  const JobCardComponent = isMobile ? MobileJobCard : JobCard;

  return (
    <div className={`${isMobile ? 'p-4' : 'max-w-7xl mx-auto p-6'}`}>
      {/* Header */}
      <div className={`${isMobile ? 'mb-6' : 'mb-8'}`}>
        <h1 className={`font-bold text-gray-800 mb-4 ${isMobile ? 'text-2xl' : 'text-3xl'}`}>
          🔍 Job Discovery
        </h1>
        
        {/* Action Buttons */}
        <div className={`flex ${isMobile ? 'flex-col space-y-3' : 'flex-wrap gap-4'} mb-6`}>
          <button
            onClick={discoverJobs}
            disabled={loading}
            className={`bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors ${
              isMobile ? 'px-4 py-3 text-sm' : 'px-6 py-2'
            }`}
          >
            {loading ? '⏳ Processing...' : '🔍 Discover New Jobs'}
          </button>
          <button
            onClick={generateRecommendations}
            disabled={loading}
            className={`bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 transition-colors ${
              isMobile ? 'px-4 py-3 text-sm' : 'px-6 py-2'
            }`}
          >
            {loading ? '⏳ Processing...' : '🎯 Generate Recommendations'}
          </button>
        </div>
        
        {/* Search Bar */}
        <div className={`${isMobile ? 'flex flex-col space-y-2' : 'flex gap-2'} mb-6`}>
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder={isMobile ? "Search jobs..." : "Search for jobs, companies, or skills..."}
            className={`px-4 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
              isMobile ? 'py-3 text-base' : 'flex-1 py-3'
            }`}
            onKeyPress={(e) => e.key === 'Enter' && searchJobs()}
          />
          <button
            onClick={() => searchJobs()}
            disabled={loading || !searchQuery.trim()}
            className={`bg-gray-600 text-white rounded-lg hover:bg-gray-700 disabled:opacity-50 transition-colors ${
              isMobile ? 'px-4 py-3 text-sm' : 'px-6 py-3'
            }`}
          >
            🔍 Search
          </button>
        </div>

        {/* Tab Navigation */}
        <div className={`flex ${isMobile ? 'space-x-2' : 'space-x-1'} mb-6 ${isMobile ? 'overflow-x-auto' : ''}`}>
          <button
            onClick={() => setActiveTab('recommendations')}
            className={`${isMobile ? 'px-3 py-2 text-sm whitespace-nowrap' : 'px-4 py-2'} rounded-lg font-medium transition-colors ${
              activeTab === 'recommendations'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            🎯 {isMobile ? 'Recs' : 'Recommendations'} ({pagination.totalCount})
          </button>
          <button
            onClick={() => setActiveTab('search')}
            className={`${isMobile ? 'px-3 py-2 text-sm whitespace-nowrap' : 'px-4 py-2'} rounded-lg font-medium transition-colors ${
              activeTab === 'search'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            🔍 {isMobile ? 'Search' : 'Search Results'} ({searchResults.length})
          </button>
        </div>
      </div>

      {/* Filters */}
      {activeTab === 'recommendations' && (
        <JobFilters onFiltersChange={handleFiltersChange} initialFilters={filters} />
      )}

      {/* Content */}
      {activeTab === 'recommendations' ? (
        <div>
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-2xl font-semibold text-gray-800">
              Personalized Recommendations
            </h2>
            {pagination.totalCount > 0 && (
              <p className="text-gray-600">
                Showing {recommendations.length} of {pagination.totalCount} recommendations
              </p>
            )}
          </div>
          
          {loading && recommendations.length === 0 ? (
            <div className="text-center py-12">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
              <p className="mt-4 text-gray-600">Loading recommendations...</p>
            </div>
          ) : recommendations.length === 0 ? (
            <div className="text-center py-12 bg-gray-50 rounded-lg">
              <div className="text-6xl mb-4">🎯</div>
              <h3 className="text-xl font-semibold text-gray-800 mb-2">No recommendations found</h3>
              <p className="text-gray-600 mb-6 max-w-md mx-auto">
                Try adjusting your filters or click "Discover New Jobs" to find opportunities, 
                then "Generate Recommendations" to get personalized matches.
              </p>
              <div className="space-x-4">
                <button
                  onClick={discoverJobs}
                  className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700"
                >
                  Discover Jobs
                </button>
                <button
                  onClick={generateRecommendations}
                  className="bg-green-600 text-white px-6 py-2 rounded-lg hover:bg-green-700"
                >
                  Generate Recommendations
                </button>
              </div>
            </div>
          ) : (
            <>
              <div className={isMobile ? 'space-y-4' : 'space-y-6'}>
                {recommendations.map((rec) => (
                  <JobCardComponent 
                    key={rec.job.job_id} 
                    job={rec.job} 
                    recommendation={rec}
                    onSave={saveJob}
                    onFeedback={provideFeedback}
                  />
                ))}
              </div>
              
              {/* Load More Button */}
              {pagination.hasMore && (
                <div className="text-center mt-8">
                  <button
                    onClick={loadMore}
                    disabled={loading}
                    className="bg-blue-600 text-white px-8 py-3 rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
                  >
                    {loading ? '⏳ Loading...' : '📄 Load More Recommendations'}
                  </button>
                </div>
              )}
            </>
          )}
        </div>
      ) : (
        <div>
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-2xl font-semibold text-gray-800">
              Search Results
            </h2>
            {searchResults.length > 0 && (
              <p className="text-gray-600">
                Found {searchResults.length} jobs
              </p>
            )}
          </div>
          
          {searchResults.length === 0 ? (
            <div className="text-center py-12 bg-gray-50 rounded-lg">
              <div className="text-6xl mb-4">🔍</div>
              <h3 className="text-xl font-semibold text-gray-800 mb-2">No search results</h3>
              <p className="text-gray-600 mb-6">
                Try different keywords or check your spelling.
              </p>
            </div>
          ) : (
            <div className={isMobile ? 'space-y-4' : 'space-y-6'}>
              {searchResults.map((job) => (
                <JobCardComponent 
                  key={job.job_id} 
                  job={job}
                  onSave={saveJob}
                />
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default JobDiscovery;