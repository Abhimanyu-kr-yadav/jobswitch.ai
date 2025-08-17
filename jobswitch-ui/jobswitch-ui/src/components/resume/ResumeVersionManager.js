import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/Card';
import { Button } from '../ui/Button';
import { Badge } from '../ui/Badge';
import { Alert, AlertDescription } from '../ui/Alert';
import { 
  GitBranch, 
  Clock, 
  TrendingUp, 
  TrendingDown, 
  Eye, 
  Copy, 
  Trash2,
  Star,
  BarChart3,
  ArrowRight,
  FileText,
  Zap
} from 'lucide-react';
import { resumeAPI } from '../../services/resumeAPI';

const ResumeVersionManager = ({ resumeId, onVersionSelect, onClose }) => {
  const [versions, setVersions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [selectedVersions, setSelectedVersions] = useState([]);
  const [comparisonData, setComparisonData] = useState(null);
  const [showComparison, setShowComparison] = useState(false);

  useEffect(() => {
    if (resumeId) {
      loadVersions();
    }
  }, [resumeId]);

  const loadVersions = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await resumeAPI.getResumeVersions(resumeId);
      if (response.success) {
        setVersions(response.data);
      }
    } catch (err) {
      setError('Failed to load resume versions');
      console.error('Error loading versions:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleVersionSelect = (version) => {
    if (selectedVersions.length < 2) {
      setSelectedVersions([...selectedVersions, version]);
    } else {
      setSelectedVersions([selectedVersions[1], version]);
    }
  };

  const handleCompareVersions = async () => {
    if (selectedVersions.length !== 2) return;
    
    try {
      setLoading(true);
      setError(null);
      
      const response = await resumeAPI.compareResumeVersions(
        selectedVersions[0].resume_id,
        selectedVersions[1].resume_id
      );
      
      if (response.success) {
        setComparisonData(response.data);
        setShowComparison(true);
      }
    } catch (err) {
      setError('Failed to compare resume versions');
      console.error('Error comparing versions:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateVersion = async (baseVersionId) => {
    try {
      setLoading(true);
      setError(null);
      
      // Get the base version content
      const baseVersion = versions.find(v => v.resume_id === baseVersionId);
      if (!baseVersion) return;
      
      const response = await resumeAPI.createResumeVersion(
        baseVersionId,
        baseVersion.content,
        `${baseVersion.title} - Copy`
      );
      
      if (response.success) {
        await loadVersions();
      }
    } catch (err) {
      setError('Failed to create resume version');
      console.error('Error creating version:', err);
    } finally {
      setLoading(false);
    }
  };

  const getScoreColor = (score) => {
    if (score >= 0.8) return 'text-green-600';
    if (score >= 0.6) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getScoreBadgeVariant = (score) => {
    if (score >= 0.8) return 'success';
    if (score >= 0.6) return 'warning';
    return 'destructive';
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (loading && versions.length === 0) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-2 text-gray-600">Loading versions...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto p-6">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h2 className="text-2xl font-bold text-gray-900 flex items-center">
            <GitBranch className="w-6 h-6 mr-2" />
            Resume Version Manager
          </h2>
          <p className="text-gray-600">Manage and compare different versions of your resume</p>
        </div>
        
        <div className="flex gap-2">
          {selectedVersions.length === 2 && (
            <Button 
              onClick={handleCompareVersions}
              disabled={loading}
              className="bg-blue-600 hover:bg-blue-700"
            >
              <BarChart3 className="w-4 h-4 mr-2" />
              Compare Selected
            </Button>
          )}
          
          <Button variant="outline" onClick={onClose}>
            Close
          </Button>
        </div>
      </div>

      {error && (
        <Alert variant="destructive" className="mb-6">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {selectedVersions.length > 0 && (
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="text-lg">Selected for Comparison</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex gap-4">
              {selectedVersions.map((version, index) => (
                <div key={version.resume_id} className="flex items-center gap-2 p-2 bg-blue-50 rounded-lg">
                  <FileText className="w-4 h-4 text-blue-600" />
                  <span className="text-sm font-medium">{version.title}</span>
                  <Badge variant="outline">v{version.version}</Badge>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => setSelectedVersions(selectedVersions.filter((_, i) => i !== index))}
                  >
                    ×
                  </Button>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Version List */}
      <div className="grid gap-4">
        {versions.map((version) => (
          <Card 
            key={version.resume_id} 
            className={`transition-all duration-200 ${
              selectedVersions.some(v => v.resume_id === version.resume_id)
                ? 'ring-2 ring-blue-500 bg-blue-50'
                : 'hover:shadow-md'
            }`}
          >
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className="flex items-center gap-2">
                    <FileText className="w-5 h-5 text-gray-600" />
                    <div>
                      <h3 className="font-semibold text-gray-900">{version.title}</h3>
                      <div className="flex items-center gap-2 text-sm text-gray-600">
                        <Clock className="w-4 h-4" />
                        {formatDate(version.created_at)}
                        <Badge variant="outline">v{version.version}</Badge>
                        {version.is_original && (
                          <Badge variant="secondary">
                            <Star className="w-3 h-3 mr-1" />
                            Original
                          </Badge>
                        )}
                      </div>
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-4">
                  {/* ATS Score */}
                  {version.ats_score && (
                    <div className="text-center">
                      <div className={`text-lg font-bold ${getScoreColor(version.ats_score)}`}>
                        {Math.round(version.ats_score * 100)}%
                      </div>
                      <div className="text-xs text-gray-500">ATS Score</div>
                    </div>
                  )}

                  {/* Score Improvement */}
                  {version.score_improvement && (
                    <div className="flex items-center gap-1">
                      {version.score_improvement > 0 ? (
                        <TrendingUp className="w-4 h-4 text-green-600" />
                      ) : (
                        <TrendingDown className="w-4 h-4 text-red-600" />
                      )}
                      <span className={`text-sm font-medium ${
                        version.score_improvement > 0 ? 'text-green-600' : 'text-red-600'
                      }`}>
                        {version.score_improvement > 0 ? '+' : ''}{Math.round(version.score_improvement * 100)}%
                      </span>
                    </div>
                  )}

                  {/* Optimization Type */}
                  {version.optimization_type && (
                    <Badge variant="outline">
                      <Zap className="w-3 h-3 mr-1" />
                      {version.optimization_type}
                    </Badge>
                  )}

                  {/* Actions */}
                  <div className="flex gap-2">
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleVersionSelect(version)}
                      disabled={selectedVersions.length >= 2 && !selectedVersions.some(v => v.resume_id === version.resume_id)}
                    >
                      {selectedVersions.some(v => v.resume_id === version.resume_id) ? (
                        'Selected'
                      ) : (
                        'Select'
                      )}
                    </Button>
                    
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => onVersionSelect(version)}
                    >
                      <Eye className="w-4 h-4 mr-1" />
                      View
                    </Button>
                    
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleCreateVersion(version.resume_id)}
                      disabled={loading}
                    >
                      <Copy className="w-4 h-4 mr-1" />
                      Copy
                    </Button>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Comparison Modal */}
      {showComparison && comparisonData && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto m-4">
            <div className="p-6">
              <div className="flex justify-between items-center mb-6">
                <h3 className="text-xl font-bold">Resume Comparison</h3>
                <Button variant="outline" onClick={() => setShowComparison(false)}>
                  Close
                </Button>
              </div>

              <div className="grid md:grid-cols-2 gap-6 mb-6">
                <Card>
                  <CardHeader>
                    <CardTitle className="text-lg">{comparisonData.resume1.title}</CardTitle>
                    <div className="flex items-center gap-2">
                      <Badge variant="outline">v{comparisonData.resume1.version}</Badge>
                      {comparisonData.resume1.ats_score && (
                        <Badge variant={getScoreBadgeVariant(comparisonData.resume1.ats_score)}>
                          {Math.round(comparisonData.resume1.ats_score * 100)}% ATS
                        </Badge>
                      )}
                    </div>
                  </CardHeader>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle className="text-lg">{comparisonData.resume2.title}</CardTitle>
                    <div className="flex items-center gap-2">
                      <Badge variant="outline">v{comparisonData.resume2.version}</Badge>
                      {comparisonData.resume2.ats_score && (
                        <Badge variant={getScoreBadgeVariant(comparisonData.resume2.ats_score)}>
                          {Math.round(comparisonData.resume2.ats_score * 100)}% ATS
                        </Badge>
                      )}
                    </div>
                  </CardHeader>
                </Card>
              </div>

              {comparisonData.comparison && (
                <div className="space-y-6">
                  <Card>
                    <CardHeader>
                      <CardTitle>Summary</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <p className="text-gray-700">{comparisonData.comparison.summary}</p>
                    </CardContent>
                  </Card>

                  {comparisonData.comparison.detailed_changes && (
                    <Card>
                      <CardHeader>
                        <CardTitle>Detailed Changes</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="space-y-4">
                          {comparisonData.comparison.detailed_changes.map((change, index) => (
                            <div key={index} className="border-l-4 border-blue-500 pl-4">
                              <div className="flex items-center gap-2 mb-2">
                                <Badge variant="outline">{change.section}</Badge>
                                <Badge variant={
                                  change.impact === 'Positive' ? 'success' :
                                  change.impact === 'Negative' ? 'destructive' : 'secondary'
                                }>
                                  {change.impact}
                                </Badge>
                              </div>
                              <div className="text-sm space-y-2">
                                <div>
                                  <span className="font-medium text-red-600">Before:</span>
                                  <p className="text-gray-600 bg-red-50 p-2 rounded mt-1">{change.before}</p>
                                </div>
                                <ArrowRight className="w-4 h-4 text-gray-400 mx-auto" />
                                <div>
                                  <span className="font-medium text-green-600">After:</span>
                                  <p className="text-gray-600 bg-green-50 p-2 rounded mt-1">{change.after}</p>
                                </div>
                              </div>
                            </div>
                          ))}
                        </div>
                      </CardContent>
                    </Card>
                  )}

                  {comparisonData.comparison.recommendations && (
                    <Card>
                      <CardHeader>
                        <CardTitle>Recommendations</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <ul className="space-y-2">
                          {comparisonData.comparison.recommendations.map((rec, index) => (
                            <li key={index} className="flex items-start gap-2">
                              <div className="w-2 h-2 bg-blue-500 rounded-full mt-2 flex-shrink-0"></div>
                              <span className="text-gray-700">{rec}</span>
                            </li>
                          ))}
                        </ul>
                      </CardContent>
                    </Card>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ResumeVersionManager;