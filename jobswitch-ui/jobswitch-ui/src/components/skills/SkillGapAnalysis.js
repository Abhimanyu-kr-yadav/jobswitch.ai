import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/Card';
import { Button } from '../ui/Button';
import { Badge } from '../ui/Badge';
import { Textarea } from '../ui/Textarea';
import { Input } from '../ui/Input';
import { Alert, AlertDescription } from '../ui/Alert';
import { skillsAnalysisAPI } from '../../services/skillsAnalysisAPI';

const SkillGapAnalysis = ({ userSkills, onAnalysisComplete }) => {
  const [analysisType, setAnalysisType] = useState('job_description');
  const [jobDescription, setJobDescription] = useState('');
  const [jobTitle, setJobTitle] = useState('');
  const [targetRole, setTargetRole] = useState('');
  const [gapAnalysis, setGapAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleAnalyzeGaps = async () => {
    if (analysisType === 'job_description' && !jobDescription.trim()) {
      setError('Please provide a job description');
      return;
    }
    
    if (analysisType === 'target_role' && !targetRole.trim()) {
      setError('Please specify a target role');
      return;
    }

    try {
      setLoading(true);
      setError(null);

      const requestData = {
        target_role: analysisType === 'target_role' ? targetRole : null,
        job_description: analysisType === 'job_description' ? jobDescription : null,
        job_title: jobTitle || null
      };

      const response = await skillsAnalysisAPI.analyzeSkillGaps(requestData);

      if (response.success) {
        setGapAnalysis(response.data);
        if (onAnalysisComplete) {
          onAnalysisComplete(response.data);
        }
      } else {
        setError(response.error || 'Failed to analyze skill gaps');
      }
    } catch (err) {
      setError('Error analyzing skill gaps: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const getMatchStrengthColor = (strength) => {
    switch (strength?.toLowerCase()) {
      case 'strong':
        return 'bg-green-100 text-green-800 border-green-200';
      case 'moderate':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'weak':
        return 'bg-red-100 text-red-800 border-red-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getPriorityColor = (priority) => {
    switch (priority?.toLowerCase()) {
      case 'high':
        return 'bg-red-100 text-red-800 border-red-200';
      case 'medium':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'low':
        return 'bg-green-100 text-green-800 border-green-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  return (
    <div className="space-y-6">
      {/* Analysis Input */}
      <Card>
        <CardHeader>
          <CardTitle>Skill Gap Analysis</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Analysis Type Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Analysis Type
            </label>
            <div className="flex gap-4">
              <label className="flex items-center">
                <input
                  type="radio"
                  value="job_description"
                  checked={analysisType === 'job_description'}
                  onChange={(e) => setAnalysisType(e.target.value)}
                  className="mr-2"
                />
                Job Description
              </label>
              <label className="flex items-center">
                <input
                  type="radio"
                  value="target_role"
                  checked={analysisType === 'target_role'}
                  onChange={(e) => setAnalysisType(e.target.value)}
                  className="mr-2"
                />
                Target Role
              </label>
            </div>
          </div>

          {analysisType === 'job_description' && (
            <>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Job Title (Optional)
                </label>
                <Input
                  value={jobTitle}
                  onChange={(e) => setJobTitle(e.target.value)}
                  placeholder="e.g., Senior Software Engineer"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Job Description *
                </label>
                <Textarea
                  value={jobDescription}
                  onChange={(e) => setJobDescription(e.target.value)}
                  placeholder="Paste the job description here..."
                  rows={8}
                  className="w-full"
                />
              </div>
            </>
          )}

          {analysisType === 'target_role' && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Target Role *
              </label>
              <Input
                value={targetRole}
                onChange={(e) => setTargetRole(e.target.value)}
                placeholder="e.g., Data Scientist, Product Manager, DevOps Engineer"
              />
            </div>
          )}

          {error && (
            <Alert className="border-red-200 bg-red-50">
              <AlertDescription className="text-red-800">
                {error}
              </AlertDescription>
            </Alert>
          )}

          <Button
            onClick={handleAnalyzeGaps}
            disabled={loading}
            className="w-full bg-blue-600 hover:bg-blue-700"
          >
            {loading ? 'Analyzing...' : 'Analyze Skill Gaps'}
          </Button>
        </CardContent>
      </Card>

      {/* Analysis Results */}
      {gapAnalysis && (
        <>
          {/* Overall Readiness */}
          <Card>
            <CardHeader>
              <CardTitle>Overall Readiness</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center justify-between mb-4">
                <div>
                  <div className="text-3xl font-bold text-blue-600">
                    {gapAnalysis.overall_readiness?.percentage || 0}%
                  </div>
                  <div className="text-sm text-gray-600">
                    Readiness Level: {gapAnalysis.overall_readiness?.readiness_level || 'Unknown'}
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-sm text-gray-600">
                    Skills Matched: {gapAnalysis.metrics?.skills_matched || 0}
                  </div>
                  <div className="text-sm text-gray-600">
                    Critical Gaps: {gapAnalysis.metrics?.critical_gaps_count || 0}
                  </div>
                </div>
              </div>

              <div className="w-full bg-gray-200 rounded-full h-3 mb-4">
                <div
                  className="bg-blue-600 h-3 rounded-full transition-all duration-300"
                  style={{ width: `${gapAnalysis.overall_readiness?.percentage || 0}%` }}
                ></div>
              </div>

              {gapAnalysis.overall_readiness?.key_strengths && (
                <div className="mb-4">
                  <h4 className="font-semibold text-green-700 mb-2">Key Strengths</h4>
                  <ul className="text-sm space-y-1">
                    {gapAnalysis.overall_readiness.key_strengths.map((strength, index) => (
                      <li key={index} className="text-green-600">• {strength}</li>
                    ))}
                  </ul>
                </div>
              )}

              {gapAnalysis.overall_readiness?.main_concerns && (
                <div>
                  <h4 className="font-semibold text-red-700 mb-2">Main Concerns</h4>
                  <ul className="text-sm space-y-1">
                    {gapAnalysis.overall_readiness.main_concerns.map((concern, index) => (
                      <li key={index} className="text-red-600">• {concern}</li>
                    ))}
                  </ul>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Matching Skills */}
          {gapAnalysis.matching_skills && gapAnalysis.matching_skills.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="text-green-700">Matching Skills</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {gapAnalysis.matching_skills.map((skill, index) => (
                    <div key={index} className="border rounded-lg p-4 bg-green-50">
                      <div className="flex justify-between items-start mb-2">
                        <h4 className="font-semibold text-gray-900">{skill.name}</h4>
                        <Badge className={getMatchStrengthColor(skill.match_strength)}>
                          {skill.match_strength}
                        </Badge>
                      </div>
                      <div className="text-sm text-gray-600 space-y-1">
                        <p>Your Level: {skill.user_proficiency}</p>
                        <p>Required Level: {skill.required_level}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Critical Gaps */}
          {gapAnalysis.critical_gaps && gapAnalysis.critical_gaps.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="text-red-700">Critical Skill Gaps</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {gapAnalysis.critical_gaps.map((gap, index) => (
                    <div key={index} className="border rounded-lg p-4 bg-red-50">
                      <div className="flex justify-between items-start mb-2">
                        <h4 className="font-semibold text-gray-900">{gap.name}</h4>
                        <Badge className={getPriorityColor(gap.priority)}>
                          {gap.priority} Priority
                        </Badge>
                      </div>
                      <div className="text-sm text-gray-600 space-y-1">
                        <p>Required Level: {gap.required_level}</p>
                        {gap.estimated_learning_time && (
                          <p>Learning Time: {gap.estimated_learning_time}</p>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Nice-to-Have Gaps */}
          {gapAnalysis.nice_to_have_gaps && gapAnalysis.nice_to_have_gaps.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="text-yellow-700">Nice-to-Have Skills</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {gapAnalysis.nice_to_have_gaps.map((gap, index) => (
                    <div key={index} className="border rounded-lg p-4 bg-yellow-50">
                      <div className="flex justify-between items-start mb-2">
                        <h4 className="font-semibold text-gray-900">{gap.name}</h4>
                        <Badge className={getPriorityColor(gap.priority)}>
                          {gap.priority}
                        </Badge>
                      </div>
                      <div className="text-sm text-gray-600 space-y-1">
                        <p>Required Level: {gap.required_level}</p>
                        {gap.estimated_learning_time && (
                          <p>Learning Time: {gap.estimated_learning_time}</p>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Transferable Skills */}
          {gapAnalysis.transferable_skills && gapAnalysis.transferable_skills.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="text-blue-700">Transferable Skills</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {gapAnalysis.transferable_skills.map((skill, index) => (
                    <div key={index} className="border rounded-lg p-4 bg-blue-50">
                      <div className="flex justify-between items-start mb-2">
                        <h4 className="font-semibold text-gray-900">{skill.user_skill}</h4>
                        <Badge className="bg-blue-100 text-blue-800">
                          {skill.relevance} Relevance
                        </Badge>
                      </div>
                      <p className="text-sm text-gray-600">
                        Applicable to: {skill.applicable_to}
                      </p>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Development Priority */}
          {gapAnalysis.development_priority && gapAnalysis.development_priority.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>Development Priority</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {gapAnalysis.development_priority.map((item, index) => (
                    <div key={index} className="flex items-center justify-between p-3 border rounded-lg">
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="bg-blue-600 text-white rounded-full w-6 h-6 flex items-center justify-center text-sm font-bold">
                            {item.priority}
                          </span>
                          <h4 className="font-semibold">{item.skill}</h4>
                        </div>
                        <p className="text-sm text-gray-600 mt-1">{item.reason}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </>
      )}
    </div>
  );
};

export default SkillGapAnalysis;