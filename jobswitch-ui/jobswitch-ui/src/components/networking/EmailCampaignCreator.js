import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/Card';
import { Button } from '../ui/Button';
import { Input } from '../ui/Input';
import { Textarea } from '../ui/Textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/Select';
import { Badge } from '../ui/Badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/Tabs';
import { 
  Mail, 
  Users, 
  Calendar, 
  Settings, 
  Play, 
  Save, 
  Plus,
  Trash2,
  CheckCircle,
  AlertCircle,
  Clock,
  Target,
  BarChart3
} from 'lucide-react';
import { networkingAPI } from '../../services/networkingAPI';
import EmailTemplateGenerator from './EmailTemplateGenerator';

const EmailCampaignCreator = ({ selectedContacts = [], onCampaignCreated, onClose }) => {
  const [activeTab, setActiveTab] = useState('setup');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  // Campaign Configuration
  const [campaignConfig, setCampaignConfig] = useState({
    name: '',
    description: '',
    target_company: '',
    target_role: '',
    campaign_type: 'company_research'
  });

  // Email Template
  const [emailTemplate, setEmailTemplate] = useState({
    subject: '',
    body: '',
    template_type: 'cold_outreach'
  });

  // Schedule Configuration
  const [scheduleConfig, setScheduleConfig] = useState({
    daily_limit: 10,
    start_time: '09:00',
    end_time: '17:00',
    timezone: 'UTC',
    start_date: new Date().toISOString().split('T')[0],
    follow_up_enabled: true,
    follow_up_delay_days: 7
  });

  // Selected contacts for campaign
  const [campaignContacts, setCampaignContacts] = useState(selectedContacts);
  const [showTemplateGenerator, setShowTemplateGenerator] = useState(false);

  const campaignTypes = [
    { value: 'company_research', label: 'Company Research', description: 'Target specific companies' },
    { value: 'role_specific', label: 'Role Specific', description: 'Target specific job roles' },
    { value: 'industry_wide', label: 'Industry Wide', description: 'Broad industry networking' }
  ];

  const timezones = [
    { value: 'UTC', label: 'UTC' },
    { value: 'America/New_York', label: 'Eastern Time' },
    { value: 'America/Chicago', label: 'Central Time' },
    { value: 'America/Denver', label: 'Mountain Time' },
    { value: 'America/Los_Angeles', label: 'Pacific Time' }
  ];

  useEffect(() => {
    setCampaignContacts(selectedContacts);
  }, [selectedContacts]);

  const handleConfigChange = (field, value) => {
    setCampaignConfig(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleScheduleChange = (field, value) => {
    setScheduleConfig(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleTemplateChange = (field, value) => {
    setEmailTemplate(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleTemplateGenerated = (template) => {
    setEmailTemplate(template);
    setShowTemplateGenerator(false);
    setActiveTab('template');
  };

  const removeContact = (contactId) => {
    setCampaignContacts(prev => prev.filter(contact => contact.contact_id !== contactId));
  };

  const validateCampaign = () => {
    const errors = [];
    
    if (!campaignConfig.name.trim()) {
      errors.push('Campaign name is required');
    }
    
    if (campaignContacts.length === 0) {
      errors.push('At least one contact is required');
    }
    
    if (!emailTemplate.subject.trim()) {
      errors.push('Email subject is required');
    }
    
    if (!emailTemplate.body.trim()) {
      errors.push('Email body is required');
    }
    
    if (scheduleConfig.daily_limit < 1 || scheduleConfig.daily_limit > 50) {
      errors.push('Daily limit must be between 1 and 50');
    }

    return errors;
  };

  const createCampaign = async () => {
    const validationErrors = validateCampaign();
    if (validationErrors.length > 0) {
      setError(validationErrors.join(', '));
      return;
    }

    try {
      setLoading(true);
      setError(null);

      const campaignId = `campaign_${Date.now()}`;
      
      const response = await networkingAPI.startEmailCampaign({
        campaign_id: campaignId,
        contacts: campaignContacts,
        template: emailTemplate,
        schedule_config: scheduleConfig
      });

      if (response.success) {
        // Also create the campaign record
        await networkingAPI.createCampaign({
          campaign_name: campaignConfig.name,
          description: campaignConfig.description,
          target_company: campaignConfig.target_company,
          target_role: campaignConfig.target_role,
          campaign_type: campaignConfig.campaign_type,
          daily_limit: scheduleConfig.daily_limit
        });

        if (onCampaignCreated) {
          onCampaignCreated({
            ...response.data,
            config: campaignConfig
          });
        }
      } else {
        setError(response.error || 'Failed to create campaign');
      }
    } catch (error) {
      console.error('Error creating campaign:', error);
      setError('Failed to create email campaign');
    } finally {
      setLoading(false);
    }
  };

  const estimatedDuration = Math.ceil(campaignContacts.length / scheduleConfig.daily_limit);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Create Email Campaign</h2>
          <p className="text-gray-600">Set up automated outreach to your selected contacts</p>
        </div>
        {onClose && (
          <Button variant="outline" onClick={onClose}>
            Close
          </Button>
        )}
      </div>

      {/* Progress Indicator */}
      <div className="flex items-center justify-center space-x-4 mb-6">
        {['setup', 'contacts', 'template', 'schedule', 'review'].map((tab, index) => (
          <div key={tab} className="flex items-center">
            <div className={`
              w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium
              ${activeTab === tab ? 'bg-blue-600 text-white' : 
                ['setup', 'contacts', 'template', 'schedule'].indexOf(activeTab) > index ? 
                'bg-green-600 text-white' : 'bg-gray-200 text-gray-600'}
            `}>
              {['setup', 'contacts', 'template', 'schedule'].indexOf(activeTab) > index ? (
                <CheckCircle className="h-4 w-4" />
              ) : (
                index + 1
              )}
            </div>
            {index < 4 && (
              <div className={`w-12 h-0.5 ${
                ['setup', 'contacts', 'template', 'schedule'].indexOf(activeTab) > index ? 
                'bg-green-600' : 'bg-gray-200'
              }`} />
            )}
          </div>
        ))}
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

      {/* Template Generator Modal */}
      {showTemplateGenerator && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-6xl max-h-[90vh] overflow-y-auto">
            <EmailTemplateGenerator
              contact={campaignContacts[0]}
              onTemplateGenerated={handleTemplateGenerated}
              onClose={() => setShowTemplateGenerator(false)}
            />
          </div>
        </div>
      )}

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="setup">Setup</TabsTrigger>
          <TabsTrigger value="contacts">Contacts</TabsTrigger>
          <TabsTrigger value="template">Template</TabsTrigger>
          <TabsTrigger value="schedule">Schedule</TabsTrigger>
          <TabsTrigger value="review">Review</TabsTrigger>
        </TabsList>

        {/* Campaign Setup */}
        <TabsContent value="setup" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Settings className="h-5 w-5" />
                Campaign Configuration
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Campaign Name *
                  </label>
                  <Input
                    value={campaignConfig.name}
                    onChange={(e) => handleConfigChange('name', e.target.value)}
                    placeholder="e.g., Tech Company Outreach Q1"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Campaign Type
                  </label>
                  <Select 
                    value={campaignConfig.campaign_type} 
                    onValueChange={(value) => handleConfigChange('campaign_type', value)}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {campaignTypes.map(type => (
                        <SelectItem key={type.value} value={type.value}>
                          <div>
                            <div className="font-medium">{type.label}</div>
                            <div className="text-sm text-gray-500">{type.description}</div>
                          </div>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Target Company
                  </label>
                  <Input
                    value={campaignConfig.target_company}
                    onChange={(e) => handleConfigChange('target_company', e.target.value)}
                    placeholder="e.g., Google, Microsoft"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Target Role
                  </label>
                  <Input
                    value={campaignConfig.target_role}
                    onChange={(e) => handleConfigChange('target_role', e.target.value)}
                    placeholder="e.g., Software Engineer, Product Manager"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Description
                </label>
                <Textarea
                  value={campaignConfig.description}
                  onChange={(e) => handleConfigChange('description', e.target.value)}
                  placeholder="Describe the purpose and goals of this campaign"
                  rows={3}
                />
              </div>

              <div className="flex justify-end">
                <Button onClick={() => setActiveTab('contacts')}>
                  Next: Select Contacts
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Contacts Selection */}
        <TabsContent value="contacts" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Users className="h-5 w-5" />
                Campaign Contacts ({campaignContacts.length})
              </CardTitle>
            </CardHeader>
            <CardContent>
              {campaignContacts.length === 0 ? (
                <div className="text-center py-8">
                  <Users className="h-12 w-12 mx-auto mb-4 text-gray-300" />
                  <p className="text-gray-500">No contacts selected for this campaign</p>
                  <p className="text-sm text-gray-400 mt-2">
                    Go back to the networking hub to select contacts
                  </p>
                </div>
              ) : (
                <div className="space-y-3">
                  {campaignContacts.map((contact) => (
                    <div key={contact.contact_id} className="flex items-center justify-between p-3 border rounded-lg">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
                          <span className="text-sm font-medium text-blue-600">
                            {contact.full_name?.charAt(0) || 'U'}
                          </span>
                        </div>
                        <div>
                          <div className="font-medium">{contact.full_name}</div>
                          <div className="text-sm text-gray-600">
                            {contact.current_title} at {contact.current_company}
                          </div>
                          <div className="text-xs text-gray-500">{contact.email}</div>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <Badge variant={contact.contact_quality === 'high' ? 'default' : 'secondary'}>
                          {contact.contact_quality}
                        </Badge>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => removeContact(contact.contact_id)}
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              )}

              <div className="flex justify-between mt-6">
                <Button variant="outline" onClick={() => setActiveTab('setup')}>
                  Previous
                </Button>
                <Button 
                  onClick={() => setActiveTab('template')}
                  disabled={campaignContacts.length === 0}
                >
                  Next: Create Template
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Email Template */}
        <TabsContent value="template" className="space-y-4">
          <Card>
            <CardHeader>
              <div className="flex justify-between items-center">
                <CardTitle className="flex items-center gap-2">
                  <Mail className="h-5 w-5" />
                  Email Template
                </CardTitle>
                <Button
                  variant="outline"
                  onClick={() => setShowTemplateGenerator(true)}
                  disabled={campaignContacts.length === 0}
                >
                  <Plus className="h-4 w-4 mr-2" />
                  Generate with AI
                </Button>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Subject Line *
                </label>
                <Input
                  value={emailTemplate.subject}
                  onChange={(e) => handleTemplateChange('subject', e.target.value)}
                  placeholder="Enter email subject"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Email Body *
                </label>
                <Textarea
                  value={emailTemplate.body}
                  onChange={(e) => handleTemplateChange('body', e.target.value)}
                  placeholder="Enter email content. Use {{contact_name}}, {{contact_company}}, etc. for personalization"
                  rows={12}
                />
              </div>

              <div className="bg-blue-50 p-3 rounded-lg">
                <h4 className="text-sm font-medium text-blue-900 mb-2">Available Placeholders</h4>
                <div className="flex flex-wrap gap-2 text-xs">
                  {['{{contact_name}}', '{{contact_first_name}}', '{{contact_title}}', '{{contact_company}}', '{{user_name}}', '{{user_title}}'].map(placeholder => (
                    <Badge key={placeholder} variant="secondary">{placeholder}</Badge>
                  ))}
                </div>
              </div>

              <div className="flex justify-between">
                <Button variant="outline" onClick={() => setActiveTab('contacts')}>
                  Previous
                </Button>
                <Button 
                  onClick={() => setActiveTab('schedule')}
                  disabled={!emailTemplate.subject.trim() || !emailTemplate.body.trim()}
                >
                  Next: Set Schedule
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Schedule Configuration */}
        <TabsContent value="schedule" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Calendar className="h-5 w-5" />
                Campaign Schedule
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Daily Email Limit
                  </label>
                  <Input
                    type="number"
                    min="1"
                    max="50"
                    value={scheduleConfig.daily_limit}
                    onChange={(e) => handleScheduleChange('daily_limit', parseInt(e.target.value))}
                  />
                  <p className="text-xs text-gray-500 mt-1">Recommended: 5-15 emails per day</p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Timezone
                  </label>
                  <Select 
                    value={scheduleConfig.timezone} 
                    onValueChange={(value) => handleScheduleChange('timezone', value)}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {timezones.map(tz => (
                        <SelectItem key={tz.value} value={tz.value}>
                          {tz.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Start Time
                  </label>
                  <Input
                    type="time"
                    value={scheduleConfig.start_time}
                    onChange={(e) => handleScheduleChange('start_time', e.target.value)}
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    End Time
                  </label>
                  <Input
                    type="time"
                    value={scheduleConfig.end_time}
                    onChange={(e) => handleScheduleChange('end_time', e.target.value)}
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Start Date
                  </label>
                  <Input
                    type="date"
                    value={scheduleConfig.start_date}
                    onChange={(e) => handleScheduleChange('start_date', e.target.value)}
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Follow-up Delay (days)
                  </label>
                  <Input
                    type="number"
                    min="1"
                    max="30"
                    value={scheduleConfig.follow_up_delay_days}
                    onChange={(e) => handleScheduleChange('follow_up_delay_days', parseInt(e.target.value))}
                  />
                </div>
              </div>

              <div className="bg-gray-50 p-4 rounded-lg">
                <h4 className="font-medium text-gray-900 mb-2">Campaign Estimate</h4>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="text-gray-600">Total Contacts:</span>
                    <span className="ml-2 font-medium">{campaignContacts.length}</span>
                  </div>
                  <div>
                    <span className="text-gray-600">Estimated Duration:</span>
                    <span className="ml-2 font-medium">{estimatedDuration} days</span>
                  </div>
                  <div>
                    <span className="text-gray-600">Daily Limit:</span>
                    <span className="ml-2 font-medium">{scheduleConfig.daily_limit} emails</span>
                  </div>
                  <div>
                    <span className="text-gray-600">Sending Hours:</span>
                    <span className="ml-2 font-medium">{scheduleConfig.start_time} - {scheduleConfig.end_time}</span>
                  </div>
                </div>
              </div>

              <div className="flex justify-between">
                <Button variant="outline" onClick={() => setActiveTab('template')}>
                  Previous
                </Button>
                <Button onClick={() => setActiveTab('review')}>
                  Next: Review & Launch
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Review & Launch */}
        <TabsContent value="review" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <BarChart3 className="h-5 w-5" />
                Campaign Review
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Campaign Summary */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <h4 className="font-medium text-gray-900 mb-3">Campaign Details</h4>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-gray-600">Name:</span>
                      <span className="font-medium">{campaignConfig.name}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Type:</span>
                      <span className="font-medium">{campaignConfig.campaign_type}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Target Company:</span>
                      <span className="font-medium">{campaignConfig.target_company || 'N/A'}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Target Role:</span>
                      <span className="font-medium">{campaignConfig.target_role || 'N/A'}</span>
                    </div>
                  </div>
                </div>

                <div>
                  <h4 className="font-medium text-gray-900 mb-3">Schedule Settings</h4>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-gray-600">Daily Limit:</span>
                      <span className="font-medium">{scheduleConfig.daily_limit} emails</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Sending Hours:</span>
                      <span className="font-medium">{scheduleConfig.start_time} - {scheduleConfig.end_time}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Start Date:</span>
                      <span className="font-medium">{scheduleConfig.start_date}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Estimated Duration:</span>
                      <span className="font-medium">{estimatedDuration} days</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Email Preview */}
              <div>
                <h4 className="font-medium text-gray-900 mb-3">Email Preview</h4>
                <div className="border rounded-lg p-4 bg-gray-50">
                  <div className="text-sm text-gray-600 mb-2">Subject:</div>
                  <div className="font-medium mb-4">{emailTemplate.subject}</div>
                  <div className="text-sm text-gray-600 mb-2">Body:</div>
                  <div className="text-sm whitespace-pre-wrap bg-white p-3 rounded border">
                    {emailTemplate.body}
                  </div>
                </div>
              </div>

              {/* Contacts Summary */}
              <div>
                <h4 className="font-medium text-gray-900 mb-3">
                  Target Contacts ({campaignContacts.length})
                </h4>
                <div className="max-h-40 overflow-y-auto border rounded-lg">
                  {campaignContacts.slice(0, 5).map((contact) => (
                    <div key={contact.contact_id} className="flex items-center justify-between p-2 border-b last:border-b-0">
                      <div className="text-sm">
                        <span className="font-medium">{contact.full_name}</span>
                        <span className="text-gray-600 ml-2">at {contact.current_company}</span>
                      </div>
                      <Badge variant="secondary" className="text-xs">
                        {contact.contact_quality}
                      </Badge>
                    </div>
                  ))}
                  {campaignContacts.length > 5 && (
                    <div className="p-2 text-sm text-gray-500 text-center">
                      +{campaignContacts.length - 5} more contacts
                    </div>
                  )}
                </div>
              </div>

              <div className="flex justify-between">
                <Button variant="outline" onClick={() => setActiveTab('schedule')}>
                  Previous
                </Button>
                <Button 
                  onClick={createCampaign}
                  disabled={loading}
                  className="bg-green-600 hover:bg-green-700"
                >
                  {loading ? (
                    <>
                      <Clock className="h-4 w-4 mr-2 animate-spin" />
                      Creating Campaign...
                    </>
                  ) : (
                    <>
                      <Play className="h-4 w-4 mr-2" />
                      Launch Campaign
                    </>
                  )}
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default EmailCampaignCreator;