import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/Card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/Tabs';
import { Button } from '../ui/Button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/Select';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar, PieChart, Pie, Cell } from 'recharts';
import { TrendingUp, TrendingDown, Activity, Target, Users, Clock } from 'lucide-react';
import { analyticsAPI } from '../../services/analyticsAPI';

const AnalyticsDashboard = () => {
  const [analyticsData, setAnalyticsData] = useState(null);
  const [jobSearchProgress, setJobSearchProgress] = useState(null);
  const [activityTimeline, setActivityTimeline] = useState(null);
  const [reports, setReports] = useState([]);
  const [selectedPeriod, setSelectedPeriod] = useState('30');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadAnalyticsData();
  }, [selectedPeriod]);

  const loadAnalyticsData = async () => {
    try {
      setLoading(true);
      setError(null);

      const [summaryResponse, progressResponse, timelineResponse, reportsResponse] = await Promise.all([
        analyticsAPI.getUserSummary(parseInt(selectedPeriod)),
        analyticsAPI.getJobSearchProgress(parseInt(selectedPeriod)),
        analyticsAPI.getActivityTimeline(7),
        analyticsAPI.getUserReports()
      ]);

      setAnalyticsData(summaryResponse.data);
      setJobSearchProgress(progressResponse.data);
      setActivityTimeline(timelineResponse.data);
      setReports(reportsResponse.data.reports);
    } catch (err) {
      console.error('Error loading analytics data:', err);
      setError('Failed to load analytics data');
    } finally {
      setLoading(false);
    }
  };

  const generateReport = async (reportType) => {
    try {
      await analyticsAPI.generateReport({ report_type: reportType });
      loadAnalyticsData(); // Refresh data
    } catch (err) {
      console.error('Error generating report:', err);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-8">
        <p className="text-red-600 mb-4">{error}</p>
        <Button onClick={loadAnalyticsData}>Retry</Button>
      </div>
    );
  }

  const jobSummary = analyticsData?.job_search_summary || {};
  const engagement = analyticsData?.engagement_metrics || {};
  const dailyData = jobSearchProgress?.daily_breakdown || [];

  // Prepare chart data
  const activityData = Object.entries(analyticsData?.activity_summary || {}).map(([key, value]) => ({
    name: key.replace('_', ' ').toUpperCase(),
    value
  }));

  const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8'];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Analytics Dashboard</h1>
          <p className="text-gray-600">Track your job search progress and performance</p>
        </div>
        <div className="flex gap-4">
          <Select value={selectedPeriod} onValueChange={setSelectedPeriod}>
            <SelectTrigger className="w-32">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="7">7 days</SelectItem>
              <SelectItem value="30">30 days</SelectItem>
              <SelectItem value="90">90 days</SelectItem>
            </SelectContent>
          </Select>
          <Button onClick={() => generateReport('weekly_progress')}>
            Generate Report
          </Button>
        </div>
      </div>

      {/* Key Metrics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Jobs Viewed</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{jobSummary.jobs_viewed || 0}</div>
            <p className="text-xs text-muted-foreground">
              Last {selectedPeriod} days
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Applications Sent</CardTitle>
            <Target className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{jobSummary.applications_sent || 0}</div>
            <p className="text-xs text-muted-foreground">
              {jobSummary.response_rate || 0}% response rate
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Interviews</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{jobSummary.interviews_completed || 0}</div>
            <p className="text-xs text-muted-foreground">
              {jobSummary.interview_rate || 0}% from applications
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Days</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{engagement.active_days || 0}</div>
            <p className="text-xs text-muted-foreground">
              Out of {selectedPeriod} days
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Main Content Tabs */}
      <Tabs defaultValue="progress" className="space-y-4">
        <TabsList>
          <TabsTrigger value="progress">Job Search Progress</TabsTrigger>
          <TabsTrigger value="activity">Activity Analysis</TabsTrigger>
          <TabsTrigger value="reports">Reports</TabsTrigger>
        </TabsList>

        <TabsContent value="progress" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Daily Progress Chart */}
            <Card>
              <CardHeader>
                <CardTitle>Daily Activity Trend</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={dailyData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="date" />
                    <YAxis />
                    <Tooltip />
                    <Line 
                      type="monotone" 
                      dataKey="jobs_viewed" 
                      stroke="#8884d8" 
                      name="Jobs Viewed"
                    />
                    <Line 
                      type="monotone" 
                      dataKey="applications_sent" 
                      stroke="#82ca9d" 
                      name="Applications Sent"
                    />
                    <Line 
                      type="monotone" 
                      dataKey="interviews_completed" 
                      stroke="#ffc658" 
                      name="Interviews"
                    />
                  </LineChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            {/* Success Rates */}
            <Card>
              <CardHeader>
                <CardTitle>Success Metrics</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span>Response Rate</span>
                    <span className="font-semibold">{jobSummary.response_rate || 0}%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div 
                      className="bg-blue-600 h-2 rounded-full" 
                      style={{ width: `${Math.min(jobSummary.response_rate || 0, 100)}%` }}
                    ></div>
                  </div>
                </div>

                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span>Interview Rate</span>
                    <span className="font-semibold">{jobSummary.interview_rate || 0}%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div 
                      className="bg-green-600 h-2 rounded-full" 
                      style={{ width: `${Math.min(jobSummary.interview_rate || 0, 100)}%` }}
                    ></div>
                  </div>
                </div>

                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span>Offer Rate</span>
                    <span className="font-semibold">{jobSummary.offer_rate || 0}%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div 
                      className="bg-yellow-600 h-2 rounded-full" 
                      style={{ width: `${Math.min(jobSummary.offer_rate || 0, 100)}%` }}
                    ></div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Trends and Insights */}
          <Card>
            <CardHeader>
              <CardTitle>Trends & Insights</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="flex items-center space-x-2">
                  {jobSearchProgress?.trends?.applications_trend === 'increasing' ? (
                    <TrendingUp className="h-5 w-5 text-green-600" />
                  ) : (
                    <TrendingDown className="h-5 w-5 text-red-600" />
                  )}
                  <span>Applications trend: {jobSearchProgress?.trends?.applications_trend || 'stable'}</span>
                </div>
                <div className="flex items-center space-x-2">
                  {jobSearchProgress?.trends?.interview_trend === 'increasing' ? (
                    <TrendingUp className="h-5 w-5 text-green-600" />
                  ) : (
                    <TrendingDown className="h-5 w-5 text-red-600" />
                  )}
                  <span>Interview trend: {jobSearchProgress?.trends?.interview_trend || 'stable'}</span>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="activity" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Activity Distribution */}
            <Card>
              <CardHeader>
                <CardTitle>Activity Distribution</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={activityData}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {activityData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            {/* Activity Bar Chart */}
            <Card>
              <CardHeader>
                <CardTitle>Feature Usage</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={activityData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="value" fill="#8884d8" />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>

          {/* Most Used Feature */}
          <Card>
            <CardHeader>
              <CardTitle>Engagement Summary</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="text-center">
                  <div className="text-2xl font-bold text-blue-600">{engagement.total_activities || 0}</div>
                  <div className="text-sm text-gray-600">Total Activities</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-green-600">{engagement.active_days || 0}</div>
                  <div className="text-sm text-gray-600">Active Days</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-purple-600">
                    {engagement.most_used_feature || 'N/A'}
                  </div>
                  <div className="text-sm text-gray-600">Most Used Feature</div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="reports" className="space-y-4">
          <div className="flex justify-between items-center">
            <h3 className="text-lg font-semibold">Generated Reports</h3>
            <div className="space-x-2">
              <Button 
                variant="outline" 
                onClick={() => generateReport('weekly_progress')}
              >
                Weekly Report
              </Button>
              <Button 
                variant="outline" 
                onClick={() => generateReport('monthly_summary')}
              >
                Monthly Report
              </Button>
            </div>
          </div>

          {/* Quick Links to Advanced Analytics */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
            <Card className="cursor-pointer hover:shadow-md transition-shadow">
              <CardHeader>
                <CardTitle className="text-base flex items-center gap-2">
                  <Activity className="h-5 w-5" />
                  Performance Monitoring
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-gray-600 mb-3">
                  Real-time system and AI agent performance metrics
                </p>
                <Button size="sm" className="w-full">
                  View Performance Dashboard
                </Button>
              </CardContent>
            </Card>

            <Card className="cursor-pointer hover:shadow-md transition-shadow">
              <CardHeader>
                <CardTitle className="text-base flex items-center gap-2">
                  <Target className="h-5 w-5" />
                  A/B Testing
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-gray-600 mb-3">
                  Optimize recommendation algorithms through experimentation
                </p>
                <Button size="sm" className="w-full">
                  Manage A/B Tests
                </Button>
              </CardContent>
            </Card>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {reports.map((report) => (
              <Card key={report.id} className="cursor-pointer hover:shadow-md transition-shadow">
                <CardHeader>
                  <CardTitle className="text-base">{report.title}</CardTitle>
                  <p className="text-sm text-gray-600">{report.report_type}</p>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    <div className="text-sm">
                      <span className="font-medium">Generated:</span> {' '}
                      {new Date(report.generated_at).toLocaleDateString()}
                    </div>
                    <div className="text-sm">
                      <span className="font-medium">Status:</span> {' '}
                      <span className={`px-2 py-1 rounded-full text-xs ${
                        report.status === 'viewed' ? 'bg-green-100 text-green-800' : 'bg-blue-100 text-blue-800'
                      }`}>
                        {report.status}
                      </span>
                    </div>
                    <Button 
                      size="sm" 
                      className="w-full mt-2"
                      onClick={() => window.open(`/analytics/reports/${report.id}`, '_blank')}
                    >
                      View Report
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>

          {reports.length === 0 && (
            <Card>
              <CardContent className="text-center py-8">
                <p className="text-gray-600 mb-4">No reports generated yet</p>
                <Button onClick={() => generateReport('weekly_progress')}>
                  Generate Your First Report
                </Button>
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default AnalyticsDashboard;