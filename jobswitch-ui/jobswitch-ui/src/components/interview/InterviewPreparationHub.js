import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/Card';
import { Button } from '../ui/Button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/Tabs';
import InterviewPreparation from './InterviewPreparation';
import TechnicalInterview from '../technical/TechnicalInterview';
import { Code, MessageCircle, Brain, Target } from 'lucide-react';

const InterviewPreparationHub = () => {
  const [activeTab, setActiveTab] = useState('overview');

  const renderOverview = () => (
    <div className="space-y-6">
      <div className="text-center mb-8">
        <h2 className="text-3xl font-bold text-gray-900 mb-4">Interview Preparation Hub</h2>
        <p className="text-lg text-gray-600 max-w-2xl mx-auto">
          Master both behavioral and technical interviews with AI-powered practice sessions, 
          real-time feedback, and personalized improvement recommendations.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Behavioral Interview Card */}
        <Card className="hover:shadow-lg transition-shadow cursor-pointer" 
              onClick={() => setActiveTab('behavioral')}>
          <CardHeader>
            <div className="flex items-center space-x-3">
              <div className="p-3 bg-blue-100 rounded-lg">
                <MessageCircle className="w-6 h-6 text-blue-600" />
              </div>
              <div>
                <CardTitle className="text-xl">Behavioral Interviews</CardTitle>
                <p className="text-gray-600 text-sm">Practice common behavioral questions</p>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div className="flex items-center space-x-2">
                <Target className="w-4 h-4 text-green-600" />
                <span className="text-sm">STAR method coaching</span>
              </div>
              <div className="flex items-center space-x-2">
                <Brain className="w-4 h-4 text-purple-600" />
                <span className="text-sm">AI-powered feedback</span>
              </div>
              <div className="flex items-center space-x-2">
                <MessageCircle className="w-4 h-4 text-blue-600" />
                <span className="text-sm">Video & audio practice</span>
              </div>
            </div>
            <Button className="w-full mt-4" onClick={() => setActiveTab('behavioral')}>
              Start Behavioral Practice
            </Button>
          </CardContent>
        </Card>

        {/* Technical Interview Card */}
        <Card className="hover:shadow-lg transition-shadow cursor-pointer"
              onClick={() => setActiveTab('technical')}>
          <CardHeader>
            <div className="flex items-center space-x-3">
              <div className="p-3 bg-green-100 rounded-lg">
                <Code className="w-6 h-6 text-green-600" />
              </div>
              <div>
                <CardTitle className="text-xl">Technical Interviews</CardTitle>
                <p className="text-gray-600 text-sm">Coding challenges & DSA practice</p>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div className="flex items-center space-x-2">
                <Code className="w-4 h-4 text-green-600" />
                <span className="text-sm">Live code execution</span>
              </div>
              <div className="flex items-center space-x-2">
                <Brain className="w-4 h-4 text-purple-600" />
                <span className="text-sm">AI code review</span>
              </div>
              <div className="flex items-center space-x-2">
                <Target className="w-4 h-4 text-orange-600" />
                <span className="text-sm">Company-specific problems</span>
              </div>
            </div>
            <Button className="w-full mt-4" onClick={() => setActiveTab('technical')}>
              Start Coding Practice
            </Button>
          </CardContent>
        </Card>
      </div>

      {/* Quick Stats */}
      <Card>
        <CardHeader>
          <CardTitle>Your Interview Progress</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="text-center p-4 bg-blue-50 rounded-lg">
              <div className="text-2xl font-bold text-blue-600">12</div>
              <div className="text-sm text-gray-600">Mock Interviews</div>
            </div>
            <div className="text-center p-4 bg-green-50 rounded-lg">
              <div className="text-2xl font-bold text-green-600">45</div>
              <div className="text-sm text-gray-600">Coding Problems</div>
            </div>
            <div className="text-center p-4 bg-purple-50 rounded-lg">
              <div className="text-2xl font-bold text-purple-600">78%</div>
              <div className="text-sm text-gray-600">Success Rate</div>
            </div>
            <div className="text-center p-4 bg-orange-50 rounded-lg">
              <div className="text-2xl font-bold text-orange-600">8.5</div>
              <div className="text-sm text-gray-600">Avg Score</div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Recent Activity */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Practice Sessions</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <div className="flex items-center space-x-3">
                <Code className="w-5 h-5 text-green-600" />
                <div>
                  <div className="font-medium">Two Sum Problem</div>
                  <div className="text-sm text-gray-600">Technical Interview • Python</div>
                </div>
              </div>
              <div className="text-right">
                <div className="text-green-600 font-medium">Solved</div>
                <div className="text-sm text-gray-600">2 hours ago</div>
              </div>
            </div>
            
            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <div className="flex items-center space-x-3">
                <MessageCircle className="w-5 h-5 text-blue-600" />
                <div>
                  <div className="font-medium">Tell me about yourself</div>
                  <div className="text-sm text-gray-600">Behavioral Interview • Video</div>
                </div>
              </div>
              <div className="text-right">
                <div className="text-blue-600 font-medium">8.2/10</div>
                <div className="text-sm text-gray-600">Yesterday</div>
              </div>
            </div>

            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <div className="flex items-center space-x-3">
                <Code className="w-5 h-5 text-green-600" />
                <div>
                  <div className="font-medium">Binary Tree Traversal</div>
                  <div className="text-sm text-gray-600">Technical Interview • JavaScript</div>
                </div>
              </div>
              <div className="text-right">
                <div className="text-yellow-600 font-medium">Partial</div>
                <div className="text-sm text-gray-600">2 days ago</div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );

  return (
    <div className="space-y-6">
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="behavioral">Behavioral</TabsTrigger>
          <TabsTrigger value="technical">Technical</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="mt-6">
          {renderOverview()}
        </TabsContent>

        <TabsContent value="behavioral" className="mt-6">
          <InterviewPreparation />
        </TabsContent>

        <TabsContent value="technical" className="mt-6">
          <TechnicalInterview />
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default InterviewPreparationHub;