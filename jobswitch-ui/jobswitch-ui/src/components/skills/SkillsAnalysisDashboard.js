import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/Card';
import { Button } from '../ui/Button';
import { Alert, AlertDescription } from '../ui/Alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/Tabs';
import SkillsVisualization from './SkillsVisualization';
import SkillGapAnalysis from './SkillGapAnalysis';
import LearningPathRecommendations from './LearningPathRecommendations';
import ResumeSkillExtractor from './ResumeSkillExtractor';
import { skillsAnalysisAPI } from '../../services/skillsAnalysisAPI';

const SkillsAnalysisDashboard = () => {
  const [userSkills, setUserSkills] = useState([]);
  const [skillsAnalysis, setSkillsAnalysis] = useState(null);
  const [recommendations, setRecommendations] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');

  useEffect(() => {
    loadUserSkillsAnalysis();
    loadRecommendations();
  }, []);

  const loadUserSkillsAnalysis = async () => {
    try {
      setLoading(true);
      const response = await skillsAnalysisAPI.analyzeUserSkills();
      
      if (response.success) {
        setSkillsAnalysis(response.data);
        setUserSkills(response.data.user_skills || []);
      } else {
        setError(response.error || 'Failed to load skills analysis');
      }
    } catch (err) {
      setError('Error loading skills analysis: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const loadRecommendations = async () => {
    try {
      const recommendations = await skillsAnalysisAPI.getRecommendations();
      setRecommendations(recommendations);
    } catch (err) {
      console.error('Error loading recommendations:', err);
    }
  };

  const handleSkillsExtracted = (extractedSkills) => {
    // Update user skills with newly extracted skills
    setUserSkills(prev => [...prev, ...extractedSkills]);
    // Reload analysis with updated skills
    loadUserSkillsAnalysis();
  };

  const handleGapAnalysisComplete = (gapAnalysis) => {
    // Update recommendations based on gap analysis
    if (gapAnalysis.recommendations) {
      setRecommendations(prev => [...prev, ...gapAnalysis.recommendations]);
    }
  };

  if (loading && !skillsAnalysis) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <span className="ml-2">Loading skills analysis...</span>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto p-6 space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold text-gray-900">Skills Analysis</h1>
        <Button 
          onClick={loadUserSkillsAnalysis}
          disabled={loading}
          className="bg-blue-600 hover:bg-blue-700"
        >
          {loading ? 'Refreshing...' : 'Refresh Analysis'}
        </Button>
      </div>

      {error && (
        <Alert className="border-red-200 bg-red-50">
          <AlertDescription className="text-red-800">
            {error}
          </AlertDescription>
        </Alert>
      )}

      {/* Quick Stats */}
      {skillsAnalysis && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardContent className="p-4">
              <div className="text-2xl font-bold text-blue-600">
                {skillsAnalysis.metrics?.total_skills || 0}
              </div>
              <div className="text-sm text-gray-600">Total Skills</div>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent className="p-4">
              <div className="text-2xl font-bold text-green-600">
                {Math.round(skillsAnalysis.metrics?.skill_diversity_score * 100) || 0}%
              </div>
              <div className="text-sm text-gray-600">Skill Diversity</div>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent className="p-4">
              <div className="text-2xl font-bold text-purple-600">
                {skillsAnalysis.strengths?.length || 0}
              </div>
              <div className="text-sm text-gray-600">Strength Areas</div>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent className="p-4">
              <div className="text-2xl font-bold text-orange-600">
                {skillsAnalysis.improvement_areas?.length || 0}
              </div>
              <div className="text-sm text-gray-600">Growth Areas</div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Main Content Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="visualization">Skills Map</TabsTrigger>
          <TabsTrigger value="gap-analysis">Gap Analysis</TabsTrigger>
          <TabsTrigger value="learning-paths">Learning Paths</TabsTrigger>
          <TabsTrigger value="extract-skills">Extract Skills</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Strengths */}
            <Card>
              <CardHeader>
                <CardTitle className="text-green-700">Your Strengths</CardTitle>
              </CardHeader>
              <CardContent>
                {skillsAnalysis?.strengths?.length > 0 ? (
                  <div className="space-y-3">
                    {skillsAnalysis.strengths.map((strength, index) => (
                      <div key={index} className="border-l-4 border-green-500 pl-4">
                        <h4 className="font-semibold text-gray-900">
                          {strength.category}
                        </h4>
                        <p className="text-sm text-gray-600">
                          Skills: {strength.skills?.join(', ')}
                        </p>
                        <p className="text-xs text-green-600">
                          Market Demand: {strength.market_demand}
                        </p>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-gray-500">No strengths analysis available yet.</p>
                )}
              </CardContent>
            </Card>

            {/* Improvement Areas */}
            <Card>
              <CardHeader>
                <CardTitle className="text-orange-700">Areas for Growth</CardTitle>
              </CardHeader>
              <CardContent>
                {skillsAnalysis?.improvement_areas?.length > 0 ? (
                  <div className="space-y-3">
                    {skillsAnalysis.improvement_areas.map((area, index) => (
                      <div key={index} className="border-l-4 border-orange-500 pl-4">
                        <h4 className="font-semibold text-gray-900">
                          {area.category}
                        </h4>
                        <p className="text-sm text-gray-600">
                          Current Level: {area.current_level}
                        </p>
                        <p className="text-sm text-gray-600">
                          Importance: {area.importance}
                        </p>
                        <p className="text-xs text-orange-600">
                          {area.reason}
                        </p>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-gray-500">No improvement areas identified yet.</p>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Market Analysis */}
          {skillsAnalysis?.market_analysis && (
            <Card>
              <CardHeader>
                <CardTitle>Market Analysis</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <h4 className="font-semibold text-green-700 mb-2">High Demand Skills</h4>
                    <ul className="text-sm space-y-1">
                      {skillsAnalysis.market_analysis.high_demand_skills?.map((skill, index) => (
                        <li key={index} className="text-green-600">• {skill}</li>
                      ))}
                    </ul>
                  </div>
                  
                  <div>
                    <h4 className="font-semibold text-blue-700 mb-2">Emerging Skills</h4>
                    <ul className="text-sm space-y-1">
                      {skillsAnalysis.market_analysis.emerging_skills?.map((skill, index) => (
                        <li key={index} className="text-blue-600">• {skill}</li>
                      ))}
                    </ul>
                  </div>
                  
                  <div>
                    <h4 className="font-semibold text-red-700 mb-2">Declining Skills</h4>
                    <ul className="text-sm space-y-1">
                      {skillsAnalysis.market_analysis.declining_skills?.map((skill, index) => (
                        <li key={index} className="text-red-600">• {skill}</li>
                      ))}
                    </ul>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Recommendations */}
          {recommendations.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>Recommendations</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {recommendations.slice(0, 3).map((rec, index) => (
                    <div key={index} className="border rounded-lg p-4 bg-blue-50">
                      <h4 className="font-semibold text-blue-900">{rec.title}</h4>
                      <p className="text-sm text-gray-700 mt-1">{rec.description}</p>
                      {rec.action_items && (
                        <ul className="text-xs text-gray-600 mt-2 space-y-1">
                          {rec.action_items.map((item, idx) => (
                            <li key={idx}>• {item}</li>
                          ))}
                        </ul>
                      )}
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="visualization">
          <SkillsVisualization 
            skills={userSkills}
            skillsAnalysis={skillsAnalysis}
          />
        </TabsContent>

        <TabsContent value="gap-analysis">
          <SkillGapAnalysis 
            userSkills={userSkills}
            onAnalysisComplete={handleGapAnalysisComplete}
          />
        </TabsContent>

        <TabsContent value="learning-paths">
          <LearningPathRecommendations 
            userSkills={userSkills}
            skillsAnalysis={skillsAnalysis}
          />
        </TabsContent>

        <TabsContent value="extract-skills">
          <ResumeSkillExtractor 
            onSkillsExtracted={handleSkillsExtracted}
          />
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default SkillsAnalysisDashboard;