import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/Card';
import { Button } from '../ui/Button';
import { Badge } from '../ui/Badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/Tabs';
import { 
  Play, 
  Pause, 
  BarChart3, 
  Mail, 
  Users, 
  TrendingUp, 
  Clock,
  CheckCircle,
  AlertCircle,
  RefreshCw,
  Eye,
  Settings,
  Calendar,
  Target
} from 'lucide-react';
import { networkingAPI } from '../../services/networkingAPI';

const CampaignMonitor = ({ campaignId, onClose }) => {
  const [campaign, setCampaign] = useState(null);
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [error, setError] = useState(null);
  const [refreshInterval, setRefreshInterval] = useState(null);

  useEffect(() => {
    if (campaignId) {
      loadCampaignData();
      
      // Set up auto-refresh for active campaigns
      const interval = setInterval(loadCampaignData, 30000); // Refresh every 30 seconds
      setRefreshInterval(interval);
      
      return () => {
        if (interval) clearInterval(interval);
      };
    }
  }, [campaignId]);

  const loadCampaignData = async () => {
    try {
      setError(null);
      
      const [statusResponse, analyticsResponse] = await Promise.all([
        networkingAPI.manageCampaign({
          campaign_id: campaignId,
          campaign_action: 'status'
        }),
        networkingAPI.getCampaignAnalytics(campaignId)
      ]);

      if (statusResponse.success) {
        setCampaign(statusResponse.data);
      }

      if (analyticsResponse.success) {
        setAnalytics(analyticsResponse.data.analytics);
      }
    } catch (error) {
      console.error('Error loading campaign data:', error);
      setError('Failed to load campaign data');
    } finally {
      setLoading(false);
    }
  };

  const handleCampaignAction = async (action) => {
    try {
      setActionLoading(true);
      setError(null);

      const response = await networkingAPI.manageCampaign({
        campaign_id: campaignId,
        campaign_action: action
      });

      if (response.success) {
        setCampaign(response.data);
        // Refresh analytics after action
        setTimeout(loadCampaignData, 1000);
      } else {
        setError(response.error || `Failed to ${action} campaign`);
      }
    } catch (error) {
      console.error(`Error ${action} campaign:`, error);
      setError(`Failed to ${action} campaign`);
    } finally {
      setActionLoading(false);
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'active': return 'bg-green-100 text-green-800';
      case 'paused': return 'bg-yellow-100 text-yellow-800';
      case 'completed': return 'bg-blue-100 text-blue-800';
      case 'error': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'active': return <Play className="h-4 w-4" />;
      case 'paused': return <Pause className="h-4 w-4" />;
      case 'completed': return <CheckCircle className="h-4 w-4" />;
      case 'error': return <AlertCircle className="h-4 w-4" />;
      default: return <Clock className="h-4 w-4" />;
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <RefreshCw className="h-8 w-8 animate-spin mx-auto mb-4 text-blue-600" />
          <p className="text-gray-600">Loading campaign data...</p>
        </div>
      </div>
    );
  }

  if (!campaign) {
    return (
      <div className="text-center py-8">
        <AlertCircle className="h-12 w-12 mx-auto mb-4 text-gray-300" />
        <p className="text-gray-500">Campaign not found</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Campaign Monitor</h2>
          <p className="text-gray-600">Track your email campaign performance</p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={loadCampaignData}
            disabled={loading}
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          {onClose && (
            <Button variant="outline" onClick={onClose}>
              Close
            </Button>
          )}
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="p-3 bg-red-50 border border-red-200 rounded-md">
          <div className="flex items-center gap-2 text-red-800">
            <AlertCircle className="h-4 w-4" />
            <span className="text-sm">{error}</span>
          </div>
        </div>
      )}

      {/* Campaign Status Card */}
      <Card>
        <CardHeader>
          <div className="flex justify-between items-center">
            <CardTitle className="flex items-center gap-2">
              <Target className="h-5 w-5" />
              Campaign Status
            </CardTitle>
            <div className="flex items-center gap-2">
              <Badge className={getStatusColor(campaign.status)}>
                {getStatusIcon(campaign.status)}
                <span className="ml-1 capitalize">{campaign.status}</span>
              </Badge>
              {campaign.status === 'active' && (
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => handleCampaignAction('pause')}
                  disabled={actionLoading}
                >
                  <Pause className="h-4 w-4 mr-2" />
                  Pause
                </Button>
              )}
              {campaign.status === 'paused' && (
                <Button
                  size="sm"
                  onClick={() => handleCampaignAction('resume')}
                  disabled={actionLoading}
                >
                  <Play className="h-4 w-4 mr-2" />
                  Resume
                </Button>
              )}
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">{campaign.progress}%</div>
              <div className="text-sm text-gray-600">Progress</div>
              <div className="w-full bg-gray-200 rounded-full h-2 mt-2">
                <div 
                  className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${campaign.progress}%` }}
                />
              </div>
            </div>
            
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">{campaign.emails_sent}</div>
              <div className="text-sm text-gray-600">Emails Sent</div>
              <div className="text-xs text-gray-500 mt-1">
                of {campaign.total_emails} total
              </div>
            </div>
            
            <div className="text-center">
              <div className="text-2xl font-bold text-purple-600">{campaign.success_rate}%</div>
              <div className="text-sm text-gray-600">Success Rate</div>
              <div className="text-xs text-gray-500 mt-1">
                Delivery success
              </div>
            </div>
            
            <div className="text-center">
              <div className="text-2xl font-bold text-orange-600">{campaign.emails_sent_today}</div>
              <div className="text-sm text-gray-600">Today's Sent</div>
              <div className="text-xs text-gray-500 mt-1">
                of {campaign.daily_limit} limit
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Detailed Analytics */}
      <Tabs defaultValue="overview" className="w-full">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="performance">Performance</TabsTrigger>
          <TabsTrigger value="schedule">Schedule</TabsTrigger>
          <TabsTrigger value="insights">Insights</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Campaign Details */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Settings className="h-5 w-5" />
                  Campaign Details
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-gray-600">Campaign ID:</span>
                  <span className="font-medium text-sm">{campaign.campaign_id}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Started:</span>
                  <span className="font-medium">
                    {new Date(campaign.started_at).toLocaleDateString()}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Last Activity:</span>
                  <span className="font-medium">
                    {campaign.last_sent_date ? 
                      new Date(campaign.last_sent_date).toLocaleString() : 
                      'No activity yet'
                    }
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Remaining:</span>
                  <span className="font-medium">{campaign.emails_remaining} emails</span>
                </div>
              </CardContent>
            </Card>

            {/* Quick Stats */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <BarChart3 className="h-5 w-5" />
                  Quick Stats
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Mail className="h-4 w-4 text-blue-600" />
                    <span className="text-gray-600">Total Emails</span>
                  </div>
                  <span className="font-medium">{campaign.total_emails}</span>
                </div>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <CheckCircle className="h-4 w-4 text-green-600" />
                    <span className="text-gray-600">Delivered</span>
                  </div>
                  <span className="font-medium">{campaign.emails_sent}</span>
                </div>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Clock className="h-4 w-4 text-orange-600" />
                    <span className="text-gray-600">Pending</span>
                  </div>
                  <span className="font-medium">{campaign.emails_remaining}</span>
                </div>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <TrendingUp className="h-4 w-4 text-purple-600" />
                    <span className="text-gray-600">Success Rate</span>
                  </div>
                  <span className="font-medium">{campaign.success_rate}%</span>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="performance" className="space-y-4">
          {analytics && (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">Email Metrics</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <div className="flex justify-between">
                      <span className="text-gray-600">Sent:</span>
                      <span className="font-medium">{analytics.emails_sent || campaign.emails_sent}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Delivered:</span>
                      <span className="font-medium">{Math.round((analytics.emails_sent || campaign.emails_sent) * (campaign.success_rate / 100))}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Opened:</span>
                      <span className="font-medium">{analytics.emails_opened || 'N/A'}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Clicked:</span>
                      <span className="font-medium">{analytics.links_clicked || 'N/A'}</span>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">Response Metrics</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <div className="flex justify-between">
                      <span className="text-gray-600">Responses:</span>
                      <span className="font-medium">{analytics.responses_received || 0}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Response Rate:</span>
                      <span className="font-medium">{analytics.response_rate || 0}%</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Connections:</span>
                      <span className="font-medium">{analytics.connections_made || 0}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Meetings:</span>
                      <span className="font-medium">{analytics.meetings_scheduled || 0}</span>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">Engagement</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <div className="flex justify-between">
                      <span className="text-gray-600">Open Rate:</span>
                      <span className="font-medium">{analytics.open_rate || 'N/A'}%</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Click Rate:</span>
                      <span className="font-medium">{analytics.click_rate || 'N/A'}%</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Bounce Rate:</span>
                      <span className="font-medium">{analytics.bounce_rate || 'N/A'}%</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Unsubscribes:</span>
                      <span className="font-medium">{analytics.unsubscribes || 0}</span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}
        </TabsContent>

        <TabsContent value="schedule" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Calendar className="h-5 w-5" />
                Schedule Information
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <h4 className="font-medium text-gray-900 mb-3">Current Settings</h4>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-gray-600">Daily Limit:</span>
                      <span className="font-medium">{campaign.daily_limit} emails</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Today's Sent:</span>
                      <span className="font-medium">{campaign.emails_sent_today}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Remaining Today:</span>
                      <span className="font-medium">{campaign.daily_limit - campaign.emails_sent_today}</span>
                    </div>
                  </div>
                </div>

                <div>
                  <h4 className="font-medium text-gray-900 mb-3">Progress Estimate</h4>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-gray-600">Completion:</span>
                      <span className="font-medium">
                        {Math.ceil(campaign.emails_remaining / campaign.daily_limit)} days remaining
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Est. Finish Date:</span>
                      <span className="font-medium">
                        {new Date(Date.now() + (Math.ceil(campaign.emails_remaining / campaign.daily_limit) * 24 * 60 * 60 * 1000)).toLocaleDateString()}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="insights" className="space-y-4">
          {analytics && analytics.insights && (
            <div className="space-y-4">
              {analytics.insights.map((insight, index) => (
                <Card key={index}>
                  <CardContent className="p-4">
                    <div className="flex items-start gap-3">
                      <div className={`
                        w-8 h-8 rounded-full flex items-center justify-center
                        ${insight.type === 'positive' ? 'bg-green-100 text-green-600' :
                          insight.type === 'improvement' ? 'bg-yellow-100 text-yellow-600' :
                          insight.type === 'technical' ? 'bg-red-100 text-red-600' :
                          'bg-blue-100 text-blue-600'}
                      `}>
                        {insight.type === 'positive' ? <CheckCircle className="h-4 w-4" /> :
                         insight.type === 'improvement' ? <TrendingUp className="h-4 w-4" /> :
                         insight.type === 'technical' ? <AlertCircle className="h-4 w-4" /> :
                         <BarChart3 className="h-4 w-4" />}
                      </div>
                      <div className="flex-1">
                        <h4 className="font-medium text-gray-900">{insight.title}</h4>
                        <p className="text-sm text-gray-600 mt-1">{insight.description}</p>
                        <p className="text-sm text-blue-600 mt-2 font-medium">
                          💡 {insight.recommendation}
                        </p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}

          {(!analytics || !analytics.insights || analytics.insights.length === 0) && (
            <Card>
              <CardContent className="p-8 text-center">
                <BarChart3 className="h-12 w-12 mx-auto mb-4 text-gray-300" />
                <p className="text-gray-500">No insights available yet</p>
                <p className="text-sm text-gray-400 mt-2">
                  Insights will appear as your campaign progresses
                </p>
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default CampaignMonitor;