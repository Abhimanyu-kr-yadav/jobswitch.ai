import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/Card';
import { Button } from '../ui/Button';
import { Input } from '../ui/Input';
import { Label } from '../ui/Label';
import { Badge } from '../ui/Badge';
import { 
  TrendingUp, 
  TrendingDown, 
  Target, 
  Lightbulb, 
  Clock,
  Star,
  AlertCircle,
  CheckCircle,
  Mic
} from 'lucide-react';
import { interviewAPI } from '../../services/interviewAPI';

const InterviewFeedback = () => {
  const [sessionId, setSessionId] = useState('');
  const [feedback, setFeedback] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleGetFeedback = async () => {
    if (!sessionId.trim()) {
      setError('Please enter a session ID');
      return;
    }

    try {
      setLoading(true);
      setError(null);

      const response = await interviewAPI.getFeedback({
        session_id: sessionId
      });

      if (response.success) {
        setFeedback(response.data.feedback);
      } else {
        setError('Failed to get feedback. Please check the session ID.');
      }
    } catch (err) {
      setError('Failed to get feedback. Please try again.');
      console.error('Error getting feedback:', err);
    } finally {
      setLoading(false);
    }
  };

  const getScoreColor = (score) => {
    if (score >= 80) return 'text-green-600';
    if (score >= 60) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getScoreBackground = (score) => {
    if (score >= 80) return 'bg-green-100';
    if (score >= 60) return 'bg-yellow-100';
    return 'bg-red-100';
  };

  const renderScoreCircle = (score) => {
    const circumference = 2 * Math.PI * 45;
    const strokeDasharray = circumference;
    const strokeDashoffset = circumference - (score / 100) * circumference;

    return (
      <div className="relative w-32 h-32">
        <svg className="w-32 h-32 transform -rotate-90" viewBox="0 0 100 100">
          <circle
            cx="50"
            cy="50"
            r="45"
            stroke="currentColor"
            strokeWidth="8"
            fill="transparent"
            className="text-gray-200"
          />
          <circle
            cx="50"
            cy="50"
            r="45"
            stroke="currentColor"
            strokeWidth="8"
            fill="transparent"
            strokeDasharray={strokeDasharray}
            strokeDashoffset={strokeDashoffset}
            className={getScoreColor(score)}
            strokeLinecap="round"
          />
        </svg>
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="text-center">
            <div className={`text-2xl font-bold ${getScoreColor(score)}`}>
              {score}
            </div>
            <div className="text-xs text-gray-500">out of 100</div>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Target className="h-5 w-5" />
            Interview Feedback
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="session_id">Session ID</Label>
            <div className="flex gap-2">
              <Input
                id="session_id"
                placeholder="Enter your interview session ID"
                value={sessionId}
                onChange={(e) => setSessionId(e.target.value)}
                className="flex-1"
              />
              <Button
                onClick={handleGetFeedback}
                disabled={loading}
              >
                {loading ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                    Loading...
                  </>
                ) : (
                  'Get Feedback'
                )}
              </Button>
            </div>
          </div>

          {error && (
            <div className="bg-red-50 border border-red-200 rounded-md p-4">
              <div className="flex items-center gap-2">
                <AlertCircle className="h-4 w-4 text-red-600" />
                <p className="text-red-800">{error}</p>
              </div>
            </div>
          )}

          {!feedback && !loading && (
            <div className="text-center py-8">
              <Target className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-600">Enter a session ID to view feedback</p>
              <p className="text-sm text-gray-500 mt-2">
                You'll receive a session ID after completing a mock interview
              </p>
            </div>
          )}
        </CardContent>
      </Card>

      {feedback && (
        <div className="space-y-6">
          {/* Overall Score */}
          <Card>
            <CardHeader>
              <CardTitle>Overall Performance</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center justify-center mb-6">
                {renderScoreCircle(feedback.overall_score)}
              </div>
              
              <div className="text-center">
                <h3 className="text-lg font-semibold text-gray-900 mb-2">
                  Overall Score: {feedback.overall_score}/100
                </h3>
                <p className="text-gray-600">
                  {feedback.overall_score >= 80 && "Excellent performance! You demonstrated strong interview skills."}
                  {feedback.overall_score >= 60 && feedback.overall_score < 80 && "Good performance with room for improvement."}
                  {feedback.overall_score < 60 && "Keep practicing! Focus on the areas for improvement below."}
                </p>
              </div>
            </CardContent>
          </Card>

          {/* Strengths and Areas for Improvement */}
          <div className="grid gap-6 md:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-green-700">
                  <TrendingUp className="h-5 w-5" />
                  Strengths
                </CardTitle>
              </CardHeader>
              <CardContent>
                {feedback.strengths && feedback.strengths.length > 0 ? (
                  <ul className="space-y-2">
                    {feedback.strengths.map((strength, index) => (
                      <li key={index} className="flex items-start gap-2">
                        <CheckCircle className="h-4 w-4 text-green-600 mt-0.5 flex-shrink-0" />
                        <span className="text-sm text-gray-700">{strength}</span>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-gray-500 text-sm">No specific strengths identified</p>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-orange-700">
                  <TrendingDown className="h-5 w-5" />
                  Areas for Improvement
                </CardTitle>
              </CardHeader>
              <CardContent>
                {feedback.areas_for_improvement && feedback.areas_for_improvement.length > 0 ? (
                  <ul className="space-y-2">
                    {feedback.areas_for_improvement.map((area, index) => (
                      <li key={index} className="flex items-start gap-2">
                        <AlertCircle className="h-4 w-4 text-orange-600 mt-0.5 flex-shrink-0" />
                        <span className="text-sm text-gray-700">{area}</span>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-gray-500 text-sm">No specific areas for improvement identified</p>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Enhanced Speaking Patterns Analysis */}
          {feedback.speaking_analysis && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Mic className="h-5 w-5" />
                  Speaking Patterns Analysis
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid gap-6 md:grid-cols-2">
                  {/* Basic Metrics */}
                  <div className="space-y-3">
                    <h4 className="text-sm font-semibold text-gray-800 mb-3">Response Metrics</h4>
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium text-gray-700">Total Responses:</span>
                      <span className="text-sm text-gray-900">{feedback.speaking_analysis.total_responses}</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium text-gray-700">Audio Responses:</span>
                      <span className="text-sm text-gray-900">{feedback.speaking_analysis.audio_responses}</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium text-gray-700">Avg Response Time:</span>
                      <span className="text-sm text-gray-900">{Math.round(feedback.speaking_analysis.average_response_time)}s</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium text-gray-700">Response Consistency:</span>
                      <Badge variant={feedback.speaking_analysis.response_consistency === 'good' ? 'default' : 'secondary'}>
                        {feedback.speaking_analysis.response_consistency}
                      </Badge>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium text-gray-700">Overall Confidence:</span>
                      <Badge variant={
                        feedback.speaking_analysis.overall_confidence === 'high' ? 'default' : 
                        feedback.speaking_analysis.overall_confidence === 'moderate' ? 'secondary' : 'outline'
                      }>
                        {feedback.speaking_analysis.overall_confidence}
                      </Badge>
                    </div>
                  </div>
                  
                  {/* Enhanced Speech Metrics */}
                  {feedback.speaking_analysis.average_speaking_rate && (
                    <div className="space-y-3">
                      <h4 className="text-sm font-semibold text-gray-800 mb-3">Speech Quality</h4>
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-medium text-gray-700">Speaking Rate:</span>
                        <span className="text-sm text-gray-900">{Math.round(feedback.speaking_analysis.average_speaking_rate)} WPM</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-medium text-gray-700">Clarity Score:</span>
                        <div className="flex items-center gap-2">
                          <span className="text-sm text-gray-900">{(feedback.speaking_analysis.average_clarity_score * 100).toFixed(0)}%</span>
                          <div className="w-16 h-2 bg-gray-200 rounded-full">
                            <div 
                              className="h-2 bg-green-500 rounded-full" 
                              style={{ width: `${feedback.speaking_analysis.average_clarity_score * 100}%` }}
                            ></div>
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-medium text-gray-700">Filler Words:</span>
                        <span className="text-sm text-gray-900">{feedback.speaking_analysis.total_filler_words || 0}</span>
                      </div>
                      {feedback.speaking_analysis.speech_quality_score && (
                        <div className="flex items-center justify-between">
                          <span className="text-sm font-medium text-gray-700">Speech Quality:</span>
                          <div className="flex items-center gap-2">
                            <span className="text-sm text-gray-900">{Math.round(feedback.speaking_analysis.speech_quality_score)}%</span>
                            <div className="w-16 h-2 bg-gray-200 rounded-full">
                              <div 
                                className="h-2 bg-blue-500 rounded-full" 
                                style={{ width: `${feedback.speaking_analysis.speech_quality_score}%` }}
                              ></div>
                            </div>
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>
                
                {/* Communication Analysis */}
                <div className="grid gap-4 md:grid-cols-2 mt-6">
                  <div>
                    <h4 className="text-sm font-medium text-gray-700 mb-2">Communication Strengths:</h4>
                    {feedback.speaking_analysis.communication_strengths?.length > 0 ? (
                      <ul className="space-y-1">
                        {feedback.speaking_analysis.communication_strengths.map((strength, index) => (
                          <li key={index} className="flex items-start gap-2">
                            <CheckCircle className="h-3 w-3 text-green-600 mt-0.5 flex-shrink-0" />
                            <span className="text-xs text-gray-600">{strength}</span>
                          </li>
                        ))}
                      </ul>
                    ) : (
                      <p className="text-xs text-gray-500">No specific strengths identified</p>
                    )}
                  </div>
                  
                  <div>
                    <h4 className="text-sm font-medium text-gray-700 mb-2">Areas to Improve:</h4>
                    {feedback.speaking_analysis.communication_improvements?.length > 0 ? (
                      <ul className="space-y-1">
                        {feedback.speaking_analysis.communication_improvements.map((improvement, index) => (
                          <li key={index} className="flex items-start gap-2">
                            <AlertCircle className="h-3 w-3 text-orange-600 mt-0.5 flex-shrink-0" />
                            <span className="text-xs text-gray-600">{improvement}</span>
                          </li>
                        ))}
                      </ul>
                    ) : (
                      <p className="text-xs text-gray-500">No specific improvements identified</p>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Detailed Question Feedback */}
          {feedback.detailed_feedback && feedback.detailed_feedback.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>Question-by-Question Feedback</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {feedback.detailed_feedback.map((item, index) => (
                    <div key={index} className="border-l-4 border-l-blue-500 pl-4 py-2">
                      <div className="flex items-center justify-between mb-2">
                        <h4 className="font-medium text-gray-900">
                          Question {item.question_index + 1}
                        </h4>
                        <div className="flex items-center gap-2">
                          <Badge className={getScoreBackground(item.score)}>
                            <Star className="h-3 w-3 mr-1" />
                            {item.score}/100
                          </Badge>
                        </div>
                      </div>
                      <p className="text-sm text-gray-600 mb-3">{item.feedback}</p>
                      
                      {/* Enhanced Speech Analysis for Individual Question */}
                      {item.speech_analysis && (
                        <div className="bg-gray-50 rounded-lg p-3 mt-2">
                          <h5 className="text-xs font-medium text-gray-700 mb-2">Response Analysis:</h5>
                          <div className="grid gap-2 md:grid-cols-2 text-xs">
                            <div className="flex items-center justify-between">
                              <span className="text-gray-600">Response Time:</span>
                              <span className="text-gray-900">{item.speech_analysis.response_time}s</span>
                            </div>
                            <div className="flex items-center justify-between">
                              <span className="text-gray-600">Word Count:</span>
                              <span className="text-gray-900">{item.speech_analysis.response_length}</span>
                            </div>
                            <div className="flex items-center justify-between">
                              <span className="text-gray-600">Pacing:</span>
                              <Badge variant="outline" className="text-xs">
                                {item.speech_analysis.pace_analysis}
                              </Badge>
                            </div>
                            <div className="flex items-center justify-between">
                              <span className="text-gray-600">Has Audio:</span>
                              <span className={item.speech_analysis.has_audio ? "text-green-600" : "text-gray-500"}>
                                {item.speech_analysis.has_audio ? "Yes" : "No"}
                              </span>
                            </div>
                            {item.speech_analysis.clarity_score && (
                              <div className="flex items-center justify-between">
                                <span className="text-gray-600">Clarity Score:</span>
                                <span className="text-gray-900">{(item.speech_analysis.clarity_score * 100).toFixed(0)}%</span>
                              </div>
                            )}
                          </div>
                          
                          {/* Enhanced Audio Analysis Details */}
                          {item.speech_analysis.audio_analysis && (
                            <div className="mt-2 pt-2 border-t border-gray-200">
                              <h6 className="text-xs font-medium text-gray-700 mb-1">Audio Analysis:</h6>
                              <div className="grid gap-1 md:grid-cols-2 text-xs">
                                <div className="flex items-center justify-between">
                                  <span className="text-gray-600">Speaking Rate:</span>
                                  <span className="text-gray-900">{item.speech_analysis.audio_analysis.speaking_rate} WPM</span>
                                </div>
                                <div className="flex items-center justify-between">
                                  <span className="text-gray-600">Clarity:</span>
                                  <Badge variant="outline" className="text-xs">
                                    {item.speech_analysis.audio_analysis.clarity_rating}
                                  </Badge>
                                </div>
                                <div className="flex items-center justify-between">
                                  <span className="text-gray-600">Filler Words:</span>
                                  <span className="text-gray-900">{item.speech_analysis.audio_analysis.filler_word_count}</span>
                                </div>
                                <div className="flex items-center justify-between">
                                  <span className="text-gray-600">Pauses:</span>
                                  <span className="text-gray-900">{item.speech_analysis.audio_analysis.pause_frequency}</span>
                                </div>
                                {item.speech_analysis.audio_analysis.pronunciation_clarity && (
                                  <div className="flex items-center justify-between">
                                    <span className="text-gray-600">Pronunciation:</span>
                                    <span className="text-gray-900">{(item.speech_analysis.audio_analysis.pronunciation_clarity * 100).toFixed(0)}%</span>
                                  </div>
                                )}
                                {item.speech_analysis.audio_analysis.volume_consistency && (
                                  <div className="flex items-center justify-between">
                                    <span className="text-gray-600">Volume:</span>
                                    <Badge variant="outline" className="text-xs">
                                      {item.speech_analysis.audio_analysis.volume_consistency}
                                    </Badge>
                                  </div>
                                )}
                              </div>
                              
                              {/* Filler Words Details */}
                              {item.speech_analysis.audio_analysis.filler_words && item.speech_analysis.audio_analysis.filler_words.length > 0 && (
                                <div className="mt-2 pt-2 border-t border-gray-200">
                                  <h6 className="text-xs font-medium text-gray-700 mb-1">Filler Words Used:</h6>
                                  <div className="flex flex-wrap gap-1">
                                    {item.speech_analysis.audio_analysis.filler_words.map((word, idx) => (
                                      <Badge key={idx} variant="outline" className="text-xs">
                                        {word}
                                      </Badge>
                                    ))}
                                  </div>
                                </div>
                              )}
                            </div>
                          )}
                          
                          {/* Individual Question Strengths and Improvements */}
                          {(item.strengths?.length > 0 || item.improvements?.length > 0) && (
                            <div className="mt-2 pt-2 border-t border-gray-200">
                              <div className="grid gap-2 md:grid-cols-2">
                                {item.strengths?.length > 0 && (
                                  <div>
                                    <h6 className="text-xs font-medium text-green-700 mb-1">Strengths:</h6>
                                    <ul className="space-y-1">
                                      {item.strengths.map((strength, idx) => (
                                        <li key={idx} className="flex items-start gap-1">
                                          <CheckCircle className="h-2 w-2 text-green-600 mt-0.5 flex-shrink-0" />
                                          <span className="text-xs text-gray-600">{strength}</span>
                                        </li>
                                      ))}
                                    </ul>
                                  </div>
                                )}
                                
                                {item.improvements?.length > 0 && (
                                  <div>
                                    <h6 className="text-xs font-medium text-orange-700 mb-1">Improvements:</h6>
                                    <ul className="space-y-1">
                                      {item.improvements.map((improvement, idx) => (
                                        <li key={idx} className="flex items-start gap-1">
                                          <AlertCircle className="h-2 w-2 text-orange-600 mt-0.5 flex-shrink-0" />
                                          <span className="text-xs text-gray-600">{improvement}</span>
                                        </li>
                                      ))}
                                    </ul>
                                  </div>
                                )}
                              </div>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Recommendations */}
          {feedback.recommendations && feedback.recommendations.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Lightbulb className="h-5 w-5" />
                  Recommendations for Improvement
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid gap-3 md:grid-cols-2">
                  {feedback.recommendations.map((recommendation, index) => (
                    <div key={index} className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                      <div className="flex items-start gap-2">
                        <Lightbulb className="h-4 w-4 text-blue-600 mt-0.5 flex-shrink-0" />
                        <p className="text-sm text-blue-800">{recommendation}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Action Items */}
          <Card>
            <CardHeader>
              <CardTitle>Next Steps</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <Button className="w-full justify-start" variant="outline">
                  <Target className="h-4 w-4 mr-2" />
                  Practice Another Mock Interview
                </Button>
                
                <Button className="w-full justify-start" variant="outline">
                  <Lightbulb className="h-4 w-4 mr-2" />
                  Generate More Practice Questions
                </Button>
                
                <Button className="w-full justify-start" variant="outline">
                  <Clock className="h-4 w-4 mr-2" />
                  Review Interview Tips and Strategies
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
};

export default InterviewFeedback;