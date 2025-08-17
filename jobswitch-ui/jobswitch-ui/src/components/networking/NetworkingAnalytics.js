import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/Card';
import { Badge } from '../ui/Badge';
import { 
  TrendingUp, 
  Users, 
  Mail, 
  Building, 
  Target,
  Calendar,
  BarChart3,
  PieChart
} from 'lucide-react';

const NetworkingAnalytics = ({ analytics }) => {
  if (!analytics) {
    return (
      <div className="flex items-center justify-center h-32">
        <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  const responseRatePercentage = Math.round(analytics.overall_response_rate * 100);
  const connectionRate = analytics.total_contacts > 0 
    ? Math.round((analytics.connections_made / analytics.total_contacts) * 100)
    : 0;

  return (
    <div className="space-y-6">
      {/* Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Total Contacts</p>
                <p className="text-2xl font-bold text-gray-900">{analytics.total_contacts}</p>
                <p className="text-xs text-green-600">+{analytics.monthly_activity.contacts_discovered} this month</p>
              </div>
              <Users className="h-8 w-8 text-blue-600" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Response Rate</p>
                <p className="text-2xl font-bold text-gray-900">{responseRatePercentage}%</p>
                <p className="text-xs text-gray-500">Industry avg: 15-25%</p>
              </div>
              <TrendingUp className="h-8 w-8 text-green-600" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Connections Made</p>
                <p className="text-2xl font-bold text-gray-900">{analytics.connections_made}</p>
                <p className="text-xs text-blue-600">+{analytics.monthly_activity.connections_made} this month</p>
              </div>
              <Target className="h-8 w-8 text-purple-600" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Companies</p>
                <p className="text-2xl font-bold text-gray-900">{analytics.total_companies_researched}</p>
                <p className="text-xs text-gray-500">Researched</p>
              </div>
              <Building className="h-8 w-8 text-orange-600" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Detailed Metrics */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Outreach Performance */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Mail className="h-5 w-5" />
              Outreach Performance
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Total Outreach Sent</span>
                <span className="font-semibold">{analytics.total_outreach_sent}</span>
              </div>
              
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Total Responses</span>
                <span className="font-semibold">{analytics.total_responses}</span>
              </div>
              
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Meetings Scheduled</span>
                <span className="font-semibold">{analytics.meetings_scheduled}</span>
              </div>

              {/* Response Rate Visualization */}
              <div className="mt-4">
                <div className="flex justify-between text-sm text-gray-600 mb-2">
                  <span>Response Rate</span>
                  <span>{responseRatePercentage}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-3">
                  <div 
                    className="bg-green-600 h-3 rounded-full" 
                    style={{ width: `${Math.min(responseRatePercentage, 100)}%` }}
                  ></div>
                </div>
              </div>

              {/* Connection Rate */}
              <div className="mt-4">
                <div className="flex justify-between text-sm text-gray-600 mb-2">
                  <span>Connection Rate</span>
                  <span>{connectionRate}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-3">
                  <div 
                    className="bg-blue-600 h-3 rounded-full" 
                    style={{ width: `${Math.min(connectionRate, 100)}%` }}
                  ></div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Top Companies */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Building className="h-5 w-5" />
              Top Companies
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {analytics.top_companies?.map((company, index) => (
                <div key={index} className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                      <span className="text-sm font-medium text-blue-800">
                        {index + 1}
                      </span>
                    </div>
                    <span className="font-medium">{company.name}</span>
                  </div>
                  <Badge variant="secondary">
                    {company.contact_count} contacts
                  </Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Monthly Activity */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Calendar className="h-5 w-5" />
            This Month's Activity
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center">
              <p className="text-2xl font-bold text-blue-600">
                {analytics.monthly_activity.contacts_discovered}
              </p>
              <p className="text-sm text-gray-600">Contacts Discovered</p>
            </div>
            
            <div className="text-center">
              <p className="text-2xl font-bold text-green-600">
                {analytics.monthly_activity.emails_sent}
              </p>
              <p className="text-sm text-gray-600">Emails Sent</p>
            </div>
            
            <div className="text-center">
              <p className="text-2xl font-bold text-purple-600">
                {analytics.monthly_activity.responses_received}
              </p>
              <p className="text-sm text-gray-600">Responses Received</p>
            </div>
            
            <div className="text-center">
              <p className="text-2xl font-bold text-orange-600">
                {analytics.monthly_activity.connections_made}
              </p>
              <p className="text-sm text-gray-600">Connections Made</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Campaign Performance */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <BarChart3 className="h-5 w-5" />
            Campaign Performance
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Active Campaigns</span>
              <Badge variant="secondary">{analytics.active_campaigns}</Badge>
            </div>
            
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Average Response Rate</span>
              <span className="font-semibold">{responseRatePercentage}%</span>
            </div>
            
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Best Performing Campaign</span>
              <span className="font-semibold">Company Research</span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Insights and Recommendations */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <TrendingUp className="h-5 w-5" />
            Insights & Recommendations
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {responseRatePercentage > 25 && (
              <div className="p-3 bg-green-50 border border-green-200 rounded-lg">
                <p className="text-sm text-green-800">
                  <strong>Great job!</strong> Your response rate of {responseRatePercentage}% is above industry average.
                </p>
              </div>
            )}
            
            {responseRatePercentage < 15 && (
              <div className="p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                <p className="text-sm text-yellow-800">
                  <strong>Tip:</strong> Your response rate could be improved. Try personalizing your messages more or targeting higher-quality contacts.
                </p>
              </div>
            )}
            
            {analytics.total_contacts < 50 && (
              <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
                <p className="text-sm text-blue-800">
                  <strong>Grow your network:</strong> Consider discovering more contacts to expand your networking opportunities.
                </p>
              </div>
            )}
            
            {analytics.meetings_scheduled > 0 && (
              <div className="p-3 bg-purple-50 border border-purple-200 rounded-lg">
                <p className="text-sm text-purple-800">
                  <strong>Success!</strong> You've scheduled {analytics.meetings_scheduled} meetings. Keep building those relationships!
                </p>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default NetworkingAnalytics;