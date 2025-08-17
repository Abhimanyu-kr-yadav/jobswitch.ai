import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/Card';
import { Button } from '../ui/Button';
import { Input } from '../ui/Input';
import { Label } from '../ui/Label';
import { Textarea } from '../ui/Textarea';
import { Badge } from '../ui/Badge';
import { Alert, AlertDescription } from '../ui/Alert';
import { 
  Plus, 
  Mail, 
  Play, 
  Pause, 
  Edit, 
  Trash2, 
  TrendingUp,
  Users,
  Calendar,
  Target,
  Eye,
  Settings,
  BarChart3
} from 'lucide-react';
import { networkingAPI } from '../../services/networkingAPI';
import EmailCampaignCreator from './EmailCampaignCreator';
import CampaignMonitor from './CampaignMonitor';

const CampaignManager = ({ onCampaignUpdated, selectedContacts = [] }) => {
  const [campaigns, setCampaigns] = useState([]);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [showEmailCampaignCreator, setShowEmailCampaignCreator] = useState(false);
  const [showCampaignMonitor, setShowCampaignMonitor] = useState(false);
  const [selectedCampaignId, setSelectedCampaignId] = useState(null);
  const [loading, setLoading] = useState(true);
  const [formData, setFormData] = useState({
    campaign_name: '',
    description: '',
    target_company: '',
    target_role: '',
    campaign_type: 'company_research',
    daily_limit: 10
  });
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  useEffect(() => {
    loadCampaigns();
  }, []);

  const loadCampaigns = async () => {
    try {
      setLoading(true);
      const response = await networkingAPI.getCampaigns();
      
      if (response.success) {
        setCampaigns(response.data.campaigns || []);
      }
    } catch (error) {
      console.error('Error loading campaigns:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleCreateCampaign = async (e) => {
    e.preventDefault();
    
    if (!formData.campaign_name.trim()) {
      setError('Campaign name is required');
      return;
    }

    try {
      setError('');
      setSuccess('');

      const response = await networkingAPI.createCampaign(formData);

      if (response.success) {
        setSuccess('Campaign created successfully');
        setShowCreateForm(false);
        setFormData({
          campaign_name: '',
          description: '',
          target_company: '',
          target_role: '',
          campaign_type: 'company_research',
          daily_limit: 10
        });
        loadCampaigns();
        
        if (onCampaignUpdated) {
          onCampaignUpdated();
        }
      } else {
        setError(response.error || 'Failed to create campaign');
      }
    } catch (error) {
      console.error('Error creating campaign:', error);
      setError('An error occurred while creating the campaign');
    }
  };

  const handleStartCampaign = async (campaignId) => {
    try {
      await networkingAPI.startCampaign(campaignId);
      loadCampaigns();
    } catch (error) {
      console.error('Error starting campaign:', error);
    }
  };

  const handlePauseCampaign = async (campaignId) => {
    try {
      await networkingAPI.pauseCampaign(campaignId);
      loadCampaigns();
    } catch (error) {
      console.error('Error pausing campaign:', error);
    }
  };

  const handleDeleteCampaign = async (campaignId) => {
    if (!window.confirm('Are you sure you want to delete this campaign?')) {
      return;
    }

    try {
      await networkingAPI.deleteCampaign(campaignId);
      loadCampaigns();
    } catch (error) {
      console.error('Error deleting campaign:', error);
    }
  };

  const handleCreateEmailCampaign = () => {
    setShowEmailCampaignCreator(true);
  };

  const handleEmailCampaignCreated = (campaign) => {
    setShowEmailCampaignCreator(false);
    setSuccess('Email campaign created and started successfully');
    loadCampaigns();
    
    if (onCampaignUpdated) {
      onCampaignUpdated();
    }
  };

  const handleViewCampaign = (campaignId) => {
    setSelectedCampaignId(campaignId);
    setShowCampaignMonitor(true);
  };

  const handleManageCampaign = async (campaignId, action) => {
    try {
      const response = await networkingAPI.manageCampaign({
        campaign_id: campaignId,
        campaign_action: action
      });

      if (response.success) {
        loadCampaigns();
        setSuccess(`Campaign ${action}d successfully`);
      } else {
        setError(response.error || `Failed to ${action} campaign`);
      }
    } catch (error) {
      console.error(`Error ${action} campaign:`, error);
      setError(`Failed to ${action} campaign`);
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'active': return 'bg-green-100 text-green-800';
      case 'paused': return 'bg-yellow-100 text-yellow-800';
      case 'completed': return 'bg-blue-100 text-blue-800';
      case 'draft': return 'bg-gray-100 text-gray-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getCampaignTypeColor = (type) => {
    switch (type) {
      case 'company_research': return 'bg-blue-100 text-blue-800';
      case 'role_specific': return 'bg-purple-100 text-purple-800';
      case 'industry_wide': return 'bg-orange-100 text-orange-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-32">
        <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Campaign Manager</h2>
          <p className="text-gray-600">Create and manage your networking campaigns</p>
        </div>
        <div className="flex gap-2">
          <Button 
            onClick={handleCreateEmailCampaign} 
            className="flex items-center gap-2"
            disabled={selectedContacts.length === 0}
          >
            <Mail className="h-4 w-4" />
            Email Campaign
          </Button>
          <Button 
            onClick={() => setShowCreateForm(true)} 
            variant="outline"
            className="flex items-center gap-2"
          >
            <Plus className="h-4 w-4" />
            New Campaign
          </Button>
        </div>
      </div>

      {/* Success/Error Messages */}
      {error && (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {success && (
        <Alert>
          <AlertDescription>{success}</AlertDescription>
        </Alert>
      )}

      {/* Email Campaign Creator Modal */}
      {showEmailCampaignCreator && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-6xl max-h-[90vh] overflow-y-auto w-full mx-4">
            <EmailCampaignCreator
              selectedContacts={selectedContacts}
              onCampaignCreated={handleEmailCampaignCreated}
              onClose={() => setShowEmailCampaignCreator(false)}
            />
          </div>
        </div>
      )}

      {/* Campaign Monitor Modal */}
      {showCampaignMonitor && selectedCampaignId && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-6xl max-h-[90vh] overflow-y-auto w-full mx-4">
            <CampaignMonitor
              campaignId={selectedCampaignId}
              onClose={() => {
                setShowCampaignMonitor(false);
                setSelectedCampaignId(null);
              }}
            />
          </div>
        </div>
      )}

      {/* Create Campaign Form */}
      {showCreateForm && (
        <Card>
          <CardHeader>
            <CardTitle>Create New Campaign</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleCreateCampaign} className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="campaign_name">Campaign Name *</Label>
                  <Input
                    id="campaign_name"
                    name="campaign_name"
                    value={formData.campaign_name}
                    onChange={handleInputChange}
                    placeholder="e.g., Google Outreach Campaign"
                    required
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="campaign_type">Campaign Type</Label>
                  <select
                    id="campaign_type"
                    name="campaign_type"
                    value={formData.campaign_type}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="company_research">Company Research</option>
                    <option value="role_specific">Role Specific</option>
                    <option value="industry_wide">Industry Wide</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="target_company">Target Company</Label>
                  <Input
                    id="target_company"
                    name="target_company"
                    value={formData.target_company}
                    onChange={handleInputChange}
                    placeholder="e.g., Google"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="target_role">Target Role</Label>
                  <Input
                    id="target_role"
                    name="target_role"
                    value={formData.target_role}
                    onChange={handleInputChange}
                    placeholder="e.g., Software Engineer"
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="description">Description</Label>
                <Textarea
                  id="description"
                  name="description"
                  value={formData.description}
                  onChange={handleInputChange}
                  placeholder="Describe the goals and strategy for this campaign..."
                  rows={3}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="daily_limit">Daily Outreach Limit</Label>
                <Input
                  id="daily_limit"
                  name="daily_limit"
                  type="number"
                  value={formData.daily_limit}
                  onChange={handleInputChange}
                  min="1"
                  max="50"
                />
              </div>

              <div className="flex gap-2">
                <Button type="submit">Create Campaign</Button>
                <Button 
                  type="button" 
                  variant="outline" 
                  onClick={() => setShowCreateForm(false)}
                >
                  Cancel
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      {/* Campaigns List */}
      <div className="space-y-4">
        {campaigns.length === 0 ? (
          <Card>
            <CardContent className="text-center py-8">
              <Mail className="h-12 w-12 mx-auto mb-4 text-gray-300" />
              <p className="text-gray-500">No campaigns created yet</p>
              <Button 
                onClick={() => setShowCreateForm(true)} 
                className="mt-4"
                variant="outline"
              >
                Create Your First Campaign
              </Button>
            </CardContent>
          </Card>
        ) : (
          campaigns.map((campaign) => (
            <Card key={campaign.campaign_id} className="hover:shadow-md transition-shadow">
              <CardContent className="p-6">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <h3 className="text-lg font-semibold text-gray-900">
                        {campaign.name}
                      </h3>
                      <Badge className={getStatusColor(campaign.status)}>
                        {campaign.status}
                      </Badge>
                      <Badge className={getCampaignTypeColor(campaign.campaign_type)}>
                        {campaign.campaign_type.replace('_', ' ')}
                      </Badge>
                    </div>

                    {campaign.description && (
                      <p className="text-gray-600 mb-3">{campaign.description}</p>
                    )}

                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                      <div className="flex items-center gap-2">
                        <Users className="h-4 w-4 text-gray-500" />
                        <div>
                          <p className="text-sm text-gray-600">Targeted</p>
                          <p className="font-semibold">{campaign.contacts_targeted}</p>
                        </div>
                      </div>

                      <div className="flex items-center gap-2">
                        <Mail className="h-4 w-4 text-gray-500" />
                        <div>
                          <p className="text-sm text-gray-600">Sent</p>
                          <p className="font-semibold">{campaign.emails_sent}</p>
                        </div>
                      </div>

                      <div className="flex items-center gap-2">
                        <TrendingUp className="h-4 w-4 text-gray-500" />
                        <div>
                          <p className="text-sm text-gray-600">Response Rate</p>
                          <p className="font-semibold">
                            {Math.round(campaign.response_rate * 100)}%
                          </p>
                        </div>
                      </div>

                      <div className="flex items-center gap-2">
                        <Target className="h-4 w-4 text-gray-500" />
                        <div>
                          <p className="text-sm text-gray-600">Daily Limit</p>
                          <p className="font-semibold">{campaign.daily_limit}</p>
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center gap-4 text-sm text-gray-600">
                      {campaign.target_company && (
                        <span>Company: {campaign.target_company}</span>
                      )}
                      {campaign.target_role && (
                        <span>Role: {campaign.target_role}</span>
                      )}
                      <span>
                        Created: {new Date(campaign.created_at).toLocaleDateString()}
                      </span>
                    </div>
                  </div>

                  <div className="flex flex-col gap-2">
                    <Button 
                      size="sm" 
                      onClick={() => handleViewCampaign(campaign.campaign_id)}
                      className="flex items-center gap-1"
                    >
                      <Eye className="h-3 w-3" />
                      Monitor
                    </Button>

                    {campaign.status === 'draft' && (
                      <Button 
                        size="sm" 
                        variant="outline"
                        onClick={() => handleManageCampaign(campaign.campaign_id, 'resume')}
                        className="flex items-center gap-1"
                      >
                        <Play className="h-3 w-3" />
                        Start
                      </Button>
                    )}

                    {campaign.status === 'active' && (
                      <Button 
                        size="sm" 
                        variant="outline"
                        onClick={() => handleManageCampaign(campaign.campaign_id, 'pause')}
                        className="flex items-center gap-1"
                      >
                        <Pause className="h-3 w-3" />
                        Pause
                      </Button>
                    )}

                    {campaign.status === 'paused' && (
                      <Button 
                        size="sm" 
                        variant="outline"
                        onClick={() => handleManageCampaign(campaign.campaign_id, 'resume')}
                        className="flex items-center gap-1"
                      >
                        <Play className="h-3 w-3" />
                        Resume
                      </Button>
                    )}

                    <Button size="sm" variant="outline">
                      <Settings className="h-3 w-3 mr-1" />
                      Settings
                    </Button>

                    <Button 
                      size="sm" 
                      variant="outline"
                      onClick={() => handleDeleteCampaign(campaign.campaign_id)}
                      className="text-red-600 hover:text-red-700"
                    >
                      <Trash2 className="h-3 w-3 mr-1" />
                      Delete
                    </Button>
                  </div>
                </div>

                {/* Progress Bar */}
                {campaign.status === 'active' && (
                  <div className="mt-4">
                    <div className="flex justify-between text-sm text-gray-600 mb-1">
                      <span>Campaign Progress</span>
                      <span>
                        {campaign.emails_sent} / {campaign.contacts_targeted} contacts reached
                      </span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div 
                        className="bg-blue-600 h-2 rounded-full" 
                        style={{ 
                          width: `${Math.min((campaign.emails_sent / campaign.contacts_targeted) * 100, 100)}%` 
                        }}
                      ></div>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          ))
        )}
      </div>
    </div>
  );
};

export default CampaignManager;