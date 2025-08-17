import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/Card';
import { Button } from '../ui/Button';
import { Progress } from '../ui/Progress';
import { Badge } from '../ui/Badge';
import { 
  BarChart3, 
  CheckCircle, 
  AlertCircle, 
  XCircle,
  TrendingUp,
  FileText,
  Target,
  Lightbulb
} from 'lucide-react';

const ATSAnalysis = ({ resume, analysis, onAnalyze, loading }) => {
  const [selectedJob, setSelectedJob] = useState(null);

  const getScoreColor = (score) => {
    if (score >= 0.8) return 'text-green-600';
    if (score >= 0.6) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getScoreIcon = (score) => {
    if (score >= 0.8) return <CheckCircle className="w-5 h-5 text-green-600" />;
    if (score >= 0.6) return <AlertCircle className="w-5 h-5 text-yellow-600" />;
    return <XCircle className="w-5 h-5 text-red-600" />;
  };

  const formatScore = (score) => {
    return Math.round(score * 100);
  };

  if (!analysis) {
    return (
      <Card>
        <CardContent className="text-center py-12">
          <BarChart3 className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">ATS Analysis</h3>
          <p className="text-gray-600 mb-4">
            Analyze your resume's compatibility with Applicant Tracking Systems
          </p>
          <Button onClick={onAnalyze} disabled={loading || !resume}>
            {loading ? 'Analyzing...' : 'Start ATS Analysis'}
          </Button>
        </CardContent>
      </Card>
    );
  }

  const { detailed_analysis } = analysis;

  return (
    <div className="space-y-6">
      {/* Overall Score */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <BarChart3 className="w-5 h-5" />
            Overall ATS Score
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              {getScoreIcon(analysis.ats_score)}
              <div>
                <div className={`text-3xl font-bold ${getScoreColor(analysis.ats_score)}`}>
                  {formatScore(analysis.ats_score)}%
                </div>
                <p className="text-sm text-gray-600">ATS Compatibility</p>
              </div>
            </div>
            <Button onClick={onAnalyze} disabled={loading} variant="outline">
              {loading ? 'Re-analyzing...' : 'Re-analyze'}
            </Button>
          </div>
          <Progress 
            value={analysis.ats_score * 100} 
            className="h-3"
          />
          <div className="mt-2 text-sm text-gray-600">
            {analysis.ats_score >= 0.8 && "Excellent! Your resume is highly ATS-friendly."}
            {analysis.ats_score >= 0.6 && analysis.ats_score < 0.8 && "Good, but there's room for improvement."}
            {analysis.ats_score < 0.6 && "Needs improvement to pass ATS screening."}
          </div>
        </CardContent>
      </Card>

      {/* Score Breakdown */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2 mb-2">
              <Target className="w-4 h-4 text-blue-600" />
              <span className="text-sm font-medium">Keywords</span>
            </div>
            <div className={`text-2xl font-bold ${getScoreColor(detailed_analysis.keyword_analysis.score)}`}>
              {formatScore(detailed_analysis.keyword_analysis.score)}%
            </div>
            <Progress value={detailed_analysis.keyword_analysis.score * 100} className="h-2 mt-2" />
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2 mb-2">
              <FileText className="w-4 h-4 text-green-600" />
              <span className="text-sm font-medium">Sections</span>
            </div>
            <div className={`text-2xl font-bold ${getScoreColor(detailed_analysis.section_analysis.score)}`}>
              {formatScore(detailed_analysis.section_analysis.score)}%
            </div>
            <Progress value={detailed_analysis.section_analysis.score * 100} className="h-2 mt-2" />
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2 mb-2">
              <TrendingUp className="w-4 h-4 text-purple-600" />
              <span className="text-sm font-medium">Formatting</span>
            </div>
            <div className={`text-2xl font-bold ${getScoreColor(detailed_analysis.formatting_analysis.score)}`}>
              {formatScore(detailed_analysis.formatting_analysis.score)}%
            </div>
            <Progress value={detailed_analysis.formatting_analysis.score * 100} className="h-2 mt-2" />
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2 mb-2">
              <CheckCircle className="w-4 h-4 text-orange-600" />
              <span className="text-sm font-medium">Overall</span>
            </div>
            <div className={`text-2xl font-bold ${getScoreColor(analysis.ats_score)}`}>
              {formatScore(analysis.ats_score)}%
            </div>
            <Progress value={analysis.ats_score * 100} className="h-2 mt-2" />
          </CardContent>
        </Card>
      </div>

      {/* Keyword Analysis */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Target className="w-5 h-5" />
            Keyword Analysis
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div>
              <h4 className="font-medium text-gray-900 mb-2">Action Verbs</h4>
              <div className="flex items-center gap-2">
                <span className="text-2xl font-bold text-blue-600">
                  {detailed_analysis.keyword_analysis.action_verbs}
                </span>
                <span className="text-sm text-gray-600">found</span>
              </div>
              <p className="text-xs text-gray-500 mt-1">
                Strong action verbs make your resume more impactful
              </p>
            </div>

            <div>
              <h4 className="font-medium text-gray-900 mb-2">Technical Skills</h4>
              <div className="flex items-center gap-2">
                <span className="text-2xl font-bold text-green-600">
                  {detailed_analysis.keyword_analysis.technical_skills}
                </span>
                <span className="text-sm text-gray-600">found</span>
              </div>
              <p className="text-xs text-gray-500 mt-1">
                Technical keywords help ATS match your skills
              </p>
            </div>

            <div>
              <h4 className="font-medium text-gray-900 mb-2">Keyword Density</h4>
              <div className="flex items-center gap-2">
                <span className="text-2xl font-bold text-purple-600">
                  {formatScore(detailed_analysis.keyword_analysis.density)}%
                </span>
                <span className="text-sm text-gray-600">density</span>
              </div>
              <p className="text-xs text-gray-500 mt-1">
                Optimal keyword density improves ATS ranking
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Section Analysis */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileText className="w-5 h-5" />
            Section Analysis
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="font-medium">Required Sections</span>
              <Badge variant={detailed_analysis.section_analysis.required_sections >= 4 ? "success" : "warning"}>
                {detailed_analysis.section_analysis.required_sections}/4 Complete
              </Badge>
            </div>

            <div className="flex items-center justify-between">
              <span className="font-medium">Optional Sections</span>
              <Badge variant="outline">
                {detailed_analysis.section_analysis.optional_sections}/3 Present
              </Badge>
            </div>

            {detailed_analysis.section_analysis.missing_sections?.length > 0 && (
              <div>
                <h4 className="font-medium text-red-600 mb-2">Missing Sections</h4>
                <div className="flex flex-wrap gap-2">
                  {detailed_analysis.section_analysis.missing_sections.map((section, index) => (
                    <Badge key={index} variant="destructive">
                      {section.replace('_', ' ').toUpperCase()}
                    </Badge>
                  ))}
                </div>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Recommendations */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Lightbulb className="w-5 h-5" />
            Improvement Recommendations
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {detailed_analysis.suggestions?.map((suggestion, index) => (
              <div key={index} className="flex items-start gap-3 p-3 bg-blue-50 rounded-lg">
                <Lightbulb className="w-5 h-5 text-blue-600 mt-0.5 flex-shrink-0" />
                <div>
                  <p className="text-sm text-gray-900">{suggestion}</p>
                </div>
              </div>
            ))}
            
            {(!detailed_analysis.suggestions || detailed_analysis.suggestions.length === 0) && (
              <div className="text-center py-4 text-gray-500">
                <CheckCircle className="w-8 h-8 mx-auto mb-2 text-green-600" />
                <p>Great job! No major improvements needed.</p>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Job-Specific Analysis */}
      <Card>
        <CardHeader>
          <CardTitle>Job-Specific Analysis</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Analyze against specific job posting
              </label>
              <div className="flex gap-2">
                <select
                  value={selectedJob || ''}
                  onChange={(e) => setSelectedJob(e.target.value)}
                  className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">Select a job posting...</option>
                  {/* Job options would be populated from saved/applied jobs */}
                </select>
                <Button 
                  onClick={() => onAnalyze(selectedJob)}
                  disabled={!selectedJob || loading}
                  variant="outline"
                >
                  Analyze
                </Button>
              </div>
            </div>
            
            <p className="text-sm text-gray-600">
              Get specific recommendations for how well your resume matches a particular job posting.
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default ATSAnalysis;