import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/Card';
import { Button } from '../ui/Button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/Tabs';
import { Badge } from '../ui/Badge';
import { Clock, Play, BookOpen, Target } from 'lucide-react';
import QuestionGenerator from './QuestionGenerator';
import MockInterview from './MockInterview';
import InterviewFeedback from './InterviewFeedback';
import { interviewAPI } from '../../services/interviewAPI';

const InterviewPreparation = () => {
  const [activeTab, setActiveTab] = useState('overview');
  const [recommendations, setRecommendations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadRecommendations();
  }, []);

  const loadRecommendations = async () => {
    try {
      setLoading(true);
      const response = await interviewAPI.getRecommendations();
      if (response.success) {
        setRecommendations(response.data.recommendations);
      }
    } catch (err) {
      setError('Failed to load recommendations');
      console.error('Error loading recommendations:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleStartMockInterview = (role) => {
    setActiveTab('mock-interview');
    // The MockInterview component will handle the role parameter
  };

  const handleGenerateQuestions = (params) => {
    setActiveTab('questions');
    // The QuestionGenerator component will handle the parameters
  };

  const getPriorityColor = (priority) => {
    switch (priority) {
      case 'high': return 'bg-red-100 text-red-800';
      case 'medium': return 'bg-yellow-100 text-yellow-800';
      case 'low': return 'bg-green-100 text-green-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getTypeIcon = (type) => {
    switch (type) {
      case 'mock_interview': return <Play className="h-4 w-4" />;
      case 'skill_preparation': return <BookOpen className="h-4 w-4" />;
      case 'company_preparation': return <Target className="h-4 w-4" />;
      default: return <BookOpen className="h-4 w-4" />;
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Interview Preparation</h1>
          <p className="text-gray-600 mt-2">
            Practice interviews, generate questions, and get AI-powered feedback
          </p>
        </div>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="questions">Questions</TabsTrigger>
          <TabsTrigger value="mock-interview">Mock Interview</TabsTrigger>
          <TabsTrigger value="feedback">Feedback</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Target className="h-5 w-5" />
                Personalized Recommendations
              </CardTitle>
            </CardHeader>
            <CardContent>
              {error && (
                <div className="bg-red-50 border border-red-200 rounded-md p-4 mb-4">
                  <p className="text-red-800">{error}</p>
                </div>
              )}
              
              {recommendations.length === 0 ? (
                <div className="text-center py-8">
                  <BookOpen className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                  <p className="text-gray-600">No recommendations available</p>
                  <p className="text-sm text-gray-500 mt-2">
                    Complete your profile to get personalized interview preparation suggestions
                  </p>
                </div>
              ) : (
                <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                  {recommendations.map((rec, index) => (
                    <Card key={index} className="hover:shadow-md transition-shadow">
                      <CardContent className="p-4">
                        <div className="flex items-start justify-between mb-3">
                          <div className="flex items-center gap-2">
                            {getTypeIcon(rec.type)}
                            <Badge className={getPriorityColor(rec.priority)}>
                              {rec.priority}
                            </Badge>
                          </div>
                          <div className="flex items-center gap-1 text-sm text-gray-500">
                            <Clock className="h-3 w-3" />
                            {rec.estimated_time}
                          </div>
                        </div>
                        
                        <h3 className="font-semibold text-gray-900 mb-2">
                          {rec.title}
                        </h3>
                        
                        <p className="text-sm text-gray-600 mb-4">
                          {rec.description}
                        </p>
                        
                        <Button
                          size="sm"
                          className="w-full"
                          onClick={() => {
                            if (rec.action.type === 'start_mock_interview') {
                              handleStartMockInterview(rec.action.role);
                            } else if (rec.action.type === 'generate_questions') {
                              handleGenerateQuestions(rec.action);
                            }
                          }}
                        >
                          Start Practice
                        </Button>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          <div className="grid gap-6 md:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>Quick Actions</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <Button
                  variant="outline"
                  className="w-full justify-start"
                  onClick={() => setActiveTab('questions')}
                >
                  <BookOpen className="h-4 w-4 mr-2" />
                  Generate Interview Questions
                </Button>
                
                <Button
                  variant="outline"
                  className="w-full justify-start"
                  onClick={() => setActiveTab('mock-interview')}
                >
                  <Play className="h-4 w-4 mr-2" />
                  Start Mock Interview
                </Button>
                
                <Button
                  variant="outline"
                  className="w-full justify-start"
                  onClick={() => setActiveTab('feedback')}
                >
                  <Target className="h-4 w-4 mr-2" />
                  View Past Feedback
                </Button>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Interview Tips</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3 text-sm">
                  <div className="flex items-start gap-2">
                    <div className="w-2 h-2 bg-blue-500 rounded-full mt-2 flex-shrink-0"></div>
                    <p>Use the STAR method (Situation, Task, Action, Result) for behavioral questions</p>
                  </div>
                  <div className="flex items-start gap-2">
                    <div className="w-2 h-2 bg-blue-500 rounded-full mt-2 flex-shrink-0"></div>
                    <p>Research the company and role thoroughly before the interview</p>
                  </div>
                  <div className="flex items-start gap-2">
                    <div className="w-2 h-2 bg-blue-500 rounded-full mt-2 flex-shrink-0"></div>
                    <p>Practice your responses out loud to improve delivery</p>
                  </div>
                  <div className="flex items-start gap-2">
                    <div className="w-2 h-2 bg-blue-500 rounded-full mt-2 flex-shrink-0"></div>
                    <p>Prepare specific examples that demonstrate your skills</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="questions">
          <QuestionGenerator />
        </TabsContent>

        <TabsContent value="mock-interview">
          <MockInterview />
        </TabsContent>

        <TabsContent value="feedback">
          <InterviewFeedback />
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default InterviewPreparation;