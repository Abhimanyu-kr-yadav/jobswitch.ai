import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/Card';
import { TrendingUp, TrendingDown, Award, Clock, Code, Zap, MessageSquare } from 'lucide-react';

const TechnicalFeedback = ({ feedback }) => {
  if (!feedback) {
    return (
      <Card>
        <CardContent className="p-8 text-center">
          <div className="text-gray-500">Loading feedback...</div>
        </CardContent>
      </Card>
    );
  }

  const getScoreColor = (score) => {
    if (score >= 80) return 'text-green-600';
    if (score >= 60) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getScoreBackground = (score) => {
    if (score >= 80) return 'bg-green-50 border-green-200';
    if (score >= 60) return 'bg-yellow-50 border-yellow-200';
    return 'bg-red-50 border-red-200';
  };

  const ScoreCard = ({ title, score, icon: Icon, description }) => (
    <Card className={`${getScoreBackground(score)} border`}>
      <CardContent className="p-4">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center space-x-2">
            <Icon className={`w-5 h-5 ${getScoreColor(score)}`} />
            <span className="font-medium text-gray-900">{title}</span>
          </div>
          <span className={`text-2xl font-bold ${getScoreColor(score)}`}>
            {score}
          </span>
        </div>
        {description && (
          <p className="text-sm text-gray-600">{description}</p>
        )}
      </CardContent>
    </Card>
  );

  return (
    <div className="space-y-6">
      {/* Overall Score */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Award className="w-6 h-6" />
            <span>Technical Interview Results</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center mb-6">
            <div className={`text-6xl font-bold mb-2 ${getScoreColor(feedback.overall_score)}`}>
              {feedback.overall_score}
            </div>
            <div className="text-lg text-gray-600">Overall Score</div>
            <div className="text-sm text-gray-500 mt-1">
              {feedback.overall_score >= 80 ? 'Excellent Performance!' :
               feedback.overall_score >= 60 ? 'Good Performance' :
               'Room for Improvement'}
            </div>
          </div>

          {/* Score Breakdown */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <ScoreCard
              title="Problem Solving"
              score={feedback.problem_solving_score}
              icon={Code}
              description="Algorithm correctness and logic"
            />
            <ScoreCard
              title="Code Quality"
              score={feedback.code_quality_score}
              icon={Zap}
              description="Code structure and readability"
            />
            <ScoreCard
              title="Efficiency"
              score={feedback.efficiency_score}
              icon={TrendingUp}
              description="Time and space complexity"
            />
            <ScoreCard
              title="Communication"
              score={feedback.communication_score}
              icon={MessageSquare}
              description="Problem approach explanation"
            />
          </div>
        </CardContent>
      </Card>

      {/* Strengths */}
      {feedback.strengths && feedback.strengths.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2 text-green-700">
              <TrendingUp className="w-5 h-5" />
              <span>Strengths</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="space-y-2">
              {feedback.strengths.map((strength, index) => (
                <li key={index} className="flex items-start space-x-2">
                  <div className="w-2 h-2 bg-green-500 rounded-full mt-2 flex-shrink-0" />
                  <span className="text-gray-700">{strength}</span>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}

      {/* Areas for Improvement */}
      {feedback.areas_for_improvement && feedback.areas_for_improvement.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2 text-orange-700">
              <TrendingDown className="w-5 h-5" />
              <span>Areas for Improvement</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="space-y-2">
              {feedback.areas_for_improvement.map((area, index) => (
                <li key={index} className="flex items-start space-x-2">
                  <div className="w-2 h-2 bg-orange-500 rounded-full mt-2 flex-shrink-0" />
                  <span className="text-gray-700">{area}</span>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}

      {/* Detailed Challenge Feedback */}
      {feedback.detailed_feedback && feedback.detailed_feedback.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Challenge-by-Challenge Breakdown</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {feedback.detailed_feedback.map((challengeFeedback, index) => (
                <div key={index} className="p-4 border rounded-lg">
                  <div className="flex justify-between items-start mb-3">
                    <div>
                      <h4 className="font-semibold text-lg">
                        {challengeFeedback.challenge_title}
                      </h4>
                      <div className="flex items-center space-x-2 mt-1">
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                          challengeFeedback.challenge_difficulty === 'easy' ? 'bg-green-100 text-green-800' :
                          challengeFeedback.challenge_difficulty === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                          'bg-red-100 text-red-800'
                        }`}>
                          {challengeFeedback.challenge_difficulty?.charAt(0).toUpperCase() + 
                           challengeFeedback.challenge_difficulty?.slice(1)}
                        </span>
                        <span className="text-sm text-gray-500">
                          {challengeFeedback.language?.toUpperCase()}
                        </span>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className={`text-lg font-bold ${
                        challengeFeedback.submission_status === 'accepted' ? 'text-green-600' : 'text-red-600'
                      }`}>
                        {challengeFeedback.submission_status === 'accepted' ? '✓ Passed' : '✗ Failed'}
                      </div>
                      {challengeFeedback.execution_time && (
                        <div className="text-sm text-gray-500">
                          {challengeFeedback.execution_time}ms
                        </div>
                      )}
                    </div>
                  </div>
                  
                  {challengeFeedback.feedback && (
                    <div className="text-sm text-gray-700 bg-gray-50 p-3 rounded">
                      {challengeFeedback.feedback}
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
            <CardTitle className="flex items-center space-x-2 text-blue-700">
              <Clock className="w-5 h-5" />
              <span>Recommendations for Improvement</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {feedback.recommendations.map((recommendation, index) => (
                <div key={index} className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
                  <div className="flex items-start space-x-3">
                    <div className="w-6 h-6 bg-blue-600 text-white rounded-full flex items-center justify-center text-sm font-bold flex-shrink-0 mt-0.5">
                      {index + 1}
                    </div>
                    <div className="text-blue-800">{recommendation}</div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Performance Summary */}
      <Card>
        <CardHeader>
          <CardTitle>Performance Summary</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="text-center p-4 bg-gray-50 rounded-lg">
              <div className="text-2xl font-bold text-gray-700">
                {feedback.detailed_feedback?.length || 0}
              </div>
              <div className="text-sm text-gray-600">Challenges Attempted</div>
            </div>
            <div className="text-center p-4 bg-gray-50 rounded-lg">
              <div className="text-2xl font-bold text-green-600">
                {feedback.detailed_feedback?.filter(f => f.submission_status === 'accepted').length || 0}
              </div>
              <div className="text-sm text-gray-600">Challenges Solved</div>
            </div>
            <div className="text-center p-4 bg-gray-50 rounded-lg">
              <div className="text-2xl font-bold text-blue-600">
                {feedback.detailed_feedback?.length > 0 
                  ? Math.round((feedback.detailed_feedback.filter(f => f.submission_status === 'accepted').length / feedback.detailed_feedback.length) * 100)
                  : 0}%
              </div>
              <div className="text-sm text-gray-600">Success Rate</div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Next Steps */}
      <Card>
        <CardHeader>
          <CardTitle>Next Steps</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
              <h4 className="font-semibold text-green-800 mb-2">Continue Practicing</h4>
              <p className="text-green-700 text-sm">
                Keep solving coding challenges to improve your problem-solving skills and algorithm knowledge.
              </p>
            </div>
            <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
              <h4 className="font-semibold text-blue-800 mb-2">Study Data Structures</h4>
              <p className="text-blue-700 text-sm">
                Review fundamental data structures and their time/space complexities to optimize your solutions.
              </p>
            </div>
            <div className="p-4 bg-purple-50 border border-purple-200 rounded-lg">
              <h4 className="font-semibold text-purple-800 mb-2">Mock Interviews</h4>
              <p className="text-purple-700 text-sm">
                Practice explaining your thought process during coding to improve communication skills.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default TechnicalFeedback;