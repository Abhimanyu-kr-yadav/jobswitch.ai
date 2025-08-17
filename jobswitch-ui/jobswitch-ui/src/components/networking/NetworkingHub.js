import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/Card';
import { Button } from '../ui/Button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/Tabs';
import { Badge } from '../ui/Badge';
import { Users, Building, Mail, TrendingUp, Search, Plus } from 'lucide-react';
import ContactDiscovery from './ContactDiscovery';
import CompanyResearch from './CompanyResearch';
import CampaignManager from './CampaignManager';
import ContactList from './ContactList';
import NetworkingAnalytics from './NetworkingAnalytics';
import { networkingAPI } from '../../services/networkingAPI';

const NetworkingHub = () => {
  const [activeTab, setActiveTab] = useState('overview');
  const [analytics, setAnalytics] = useState(null);
  const [recommendations, setRecommendations] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadNetworkingData();
  }, []);

  const loadNetworkingData = async () => {
    try {
      setLoading(true);
      
      // Load analytics and recommendations in parallel
      const [analyticsResponse, recommendationsResponse] = await Promise.all([
        networkingAPI.getAnalytics(),
        networkingAPI.getRecommendations()
      ]);

      if (analyticsResponse.success) {
        setAnalytics(analyticsResponse.data);
      }

      if (recommendationsResponse.success) {
        setRecommendations(recommendationsResponse.data.recommendations || []);
      }
    } catch (error) {
      console.error('Error loading networking data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleTabChange = (value) => {
    setActiveTab(value);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Networking Hub</h1>
          <p className="text-gray-600 mt-1">
            Discover contacts, research companies, and manage outreach campaigns
          </p>
        </div>
        <Button onClick={() => setActiveTab('discovery')} className="flex items-center gap-2">
          <Search className="h-4 w-4" />
          Discover Contacts
        </Button>
      </div>

      {/* Quick Stats */}
      {analytics && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Total Contacts</p>
                  <p className="text-2xl font-bold text-gray-900">{analytics.total_contacts}</p>
                </div>
                <Users className="h-8 w-8 text-blue-600" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Companies Researched</p>
                  <p className="text-2xl font-bold text-gray-900">{analytics.total_companies_researched}</p>
                </div>
                <Building className="h-8 w-8 text-green-600" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Response Rate</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {Math.round(analytics.overall_response_rate * 100)}%
                  </p>
                </div>
                <TrendingUp className="h-8 w-8 text-purple-600" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Active Campaigns</p>
                  <p className="text-2xl font-bold text-gray-900">{analytics.active_campaigns}</p>
                </div>
                <Mail className="h-8 w-8 text-orange-600" />
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Recommendations */}
      {recommendations.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <TrendingUp className="h-5 w-5" />
              Networking Recommendations
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {recommendations.slice(0, 3).map((rec, index) => (
                <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div className="flex-1">
                    <h4 className="font-medium text-gray-900">{rec.title}</h4>
                    <p className="text-sm text-gray-600">{rec.description}</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge variant={rec.priority === 'high' ? 'destructive' : 'secondary'}>
                      {rec.priority}
                    </Badge>
                    <Button size="sm" variant="outline">
                      Act
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Main Content Tabs */}
      <Tabs value={activeTab} onValueChange={handleTabChange}>
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="discovery">Discovery</TabsTrigger>
          <TabsTrigger value="research">Research</TabsTrigger>
          <TabsTrigger value="campaigns">Campaigns</TabsTrigger>
          <TabsTrigger value="analytics">Analytics</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Recent Contacts */}
            <Card>
              <CardHeader>
                <CardTitle>Recent Contacts</CardTitle>
              </CardHeader>
              <CardContent>
                <ContactList limit={5} showActions={false} />
              </CardContent>
            </Card>

            {/* Top Companies */}
            <Card>
              <CardHeader>
                <CardTitle>Top Companies</CardTitle>
              </CardHeader>
              <CardContent>
                {analytics?.top_companies && (
                  <div className="space-y-3">
                    {analytics.top_companies.map((company, index) => (
                      <div key={index} className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                            <Building className="h-4 w-4 text-blue-600" />
                          </div>
                          <span className="font-medium">{company.name}</span>
                        </div>
                        <Badge variant="secondary">{company.contact_count} contacts</Badge>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="discovery">
          <ContactDiscovery onContactsDiscovered={loadNetworkingData} />
        </TabsContent>

        <TabsContent value="research">
          <CompanyResearch onCompanyResearched={loadNetworkingData} />
        </TabsContent>

        <TabsContent value="campaigns">
          <CampaignManager 
            onCampaignUpdated={loadNetworkingData}
            selectedContacts={[]} // This would be populated from contact selection
          />
        </TabsContent>

        <TabsContent value="analytics">
          <NetworkingAnalytics analytics={analytics} />
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default NetworkingHub;