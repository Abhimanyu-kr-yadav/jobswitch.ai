import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/Card';
import { Button } from '../ui/Button';
import { Select } from '../ui/Select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/Tabs';
import CodingChallenge from './CodingChallenge';
import TechnicalFeedback from './TechnicalFeedback';
import { technicalInterviewAPI } from '../../services/technicalInterviewAPI';

const TechnicalInterview = () => {
  const [currentView, setCurrentView] = useState('setup');
  const [sessionId, setSessionId] = useState(null);
  const [sessionData, setSessionData] = useState(null);
  const [currentChallenge, setCurrentChallenge] = useState(null);
  const [feedback, setFeedback] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Setup form state
  const [setupForm, setSetupForm] = useState({
    jobRole: 'Software Engineer',
    company: '',
    difficulty: 'medium',
    categories: [],
    challengeCount: 3,
    timeLimit: 3600
  });

  const [availableCategories, setAvailableCategories] = useState([]);
  const [availableDifficulties, setAvailableDifficulties] = useState([]);

  useEffect(() => {
    loadCategories();
  }, []);

  const loadCategories = async () => {
    try {
      const response = await technicalInterviewAPI.getCategories();
      if (response.success) {
        setAvailableCategories(response.data.categories || []);
        setAvailableDifficulties(response.data.difficulties || []);
      }
    } catch (error) {
      console.error('Failed to load categories:', error);
    }
  };

  const handleStartInterview = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await technicalInterviewAPI.startInterview({
        job_role: setupForm.jobRole,
        company: setupForm.company,
        difficulty: setupForm.difficulty,
        categories: setupForm.categories,
        challenge_count: setupForm.challengeCount,
        time_limit: setupForm.timeLimit
      });

      if (response.success) {
        setSessionId(response.data.session_id);
        setSessionData(response.data);
        setCurrentChallenge(response.data.current_challenge);
        setCurrentView('interview');
      } else {
        setError(response.error || 'Failed to start interview');
      }
    } catch (error) {
      setError('Failed to start technical interview');
      console.error('Start interview error:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleChallengeComplete = (challengeResult) => {
    if (challengeResult.interview_complete) {
      setCurrentView('feedback');
      loadFeedback();
    } else if (challengeResult.next_challenge) {
      setCurrentChallenge(challengeResult.next_challenge);
      setSessionData(prev => ({
        ...prev,
        progress: challengeResult.progress
      }));
    }
  };

  const handleEndInterview = async () => {
    if (!sessionId) return;

    try {
      await technicalInterviewAPI.endInterview(sessionId);
      setCurrentView('feedback');
      loadFeedback();
    } catch (error) {
      console.error('Failed to end interview:', error);
    }
  };

  const loadFeedback = async () => {
    if (!sessionId) return;

    try {
      const response = await technicalInterviewAPI.getFeedback({ session_id: sessionId });
      if (response.success) {
        setFeedback(response.data.feedback);
      }
    } catch (error) {
      console.error('Failed to load feedback:', error);
    }
  };

  const handleRestart = () => {
    setCurrentView('setup');
    setSessionId(null);
    setSessionData(null);
    setCurrentChallenge(null);
    setFeedback(null);
    setError(null);
  };

  const renderSetupView = () => (
    <div className="max-w-2xl mx-auto space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Technical Interview Setup</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-2">Job Role</label>
            <input
              type="text"
              value={setupForm.jobRole}
              onChange={(e) => setSetupForm(prev => ({ ...prev, jobRole: e.target.value }))}
              className="w-full p-2 border rounded-md"
              placeholder="e.g., Software Engineer"
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">Company (Optional)</label>
            <input
              type="text"
              value={setupForm.company}
              onChange={(e) => setSetupForm(prev => ({ ...prev, company: e.target.value }))}
              className="w-full p-2 border rounded-md"
              placeholder="e.g., Google"
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">Difficulty Level</label>
            <Select
              value={setupForm.difficulty}
              onValueChange={(value) => setSetupForm(prev => ({ ...prev, difficulty: value }))}
            >
              {availableDifficulties.map(difficulty => (
                <option key={difficulty} value={difficulty}>
                  {difficulty.charAt(0).toUpperCase() + difficulty.slice(1)}
                </option>
              ))}
            </Select>
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">Categories (Optional)</label>
            <div className="grid grid-cols-2 gap-2">
              {availableCategories.map(category => (
                <label key={category} className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    checked={setupForm.categories.includes(category)}
                    onChange={(e) => {
                      if (e.target.checked) {
                        setSetupForm(prev => ({
                          ...prev,
                          categories: [...prev.categories, category]
                        }));
                      } else {
                        setSetupForm(prev => ({
                          ...prev,
                          categories: prev.categories.filter(c => c !== category)
                        }));
                      }
                    }}
                  />
                  <span className="text-sm">
                    {category.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                  </span>
                </label>
              ))}
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">Number of Challenges</label>
            <Select
              value={setupForm.challengeCount.toString()}
              onValueChange={(value) => setSetupForm(prev => ({ ...prev, challengeCount: parseInt(value) }))}
            >
              <option value="1">1 Challenge</option>
              <option value="2">2 Challenges</option>
              <option value="3">3 Challenges</option>
              <option value="4">4 Challenges</option>
              <option value="5">5 Challenges</option>
            </Select>
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">Time Limit</label>
            <Select
              value={setupForm.timeLimit.toString()}
              onValueChange={(value) => setSetupForm(prev => ({ ...prev, timeLimit: parseInt(value) }))}
            >
              <option value="1800">30 minutes</option>
              <option value="2700">45 minutes</option>
              <option value="3600">1 hour</option>
              <option value="5400">1.5 hours</option>
              <option value="7200">2 hours</option>
            </Select>
          </div>

          {error && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-md text-red-700">
              {error}
            </div>
          )}

          <Button
            onClick={handleStartInterview}
            disabled={loading}
            className="w-full"
          >
            {loading ? 'Starting Interview...' : 'Start Technical Interview'}
          </Button>
        </CardContent>
      </Card>
    </div>
  );

  const renderInterviewView = () => (
    <div className="space-y-4">
      {/* Progress Header */}
      <Card>
        <CardContent className="p-4">
          <div className="flex justify-between items-center">
            <div>
              <h2 className="text-lg font-semibold">Technical Interview</h2>
              <p className="text-sm text-gray-600">
                {setupForm.jobRole} {setupForm.company && `at ${setupForm.company}`}
              </p>
            </div>
            <div className="text-right">
              <div className="text-sm text-gray-600">
                Progress: {sessionData?.progress?.current || 1} / {sessionData?.progress?.total || 1}
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={handleEndInterview}
                className="mt-2"
              >
                End Interview
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Current Challenge */}
      {currentChallenge && (
        <CodingChallenge
          challenge={currentChallenge}
          sessionId={sessionId}
          onComplete={handleChallengeComplete}
        />
      )}
    </div>
  );

  const renderFeedbackView = () => (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold">Interview Complete</h2>
        <Button onClick={handleRestart}>
          Start New Interview
        </Button>
      </div>

      {feedback && <TechnicalFeedback feedback={feedback} />}
    </div>
  );

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">Technical Interview Practice</h1>
        <p className="text-gray-600">
          Practice coding challenges and data structures & algorithms problems
        </p>
      </div>

      {currentView === 'setup' && renderSetupView()}
      {currentView === 'interview' && renderInterviewView()}
      {currentView === 'feedback' && renderFeedbackView()}
    </div>
  );
};

export default TechnicalInterview;