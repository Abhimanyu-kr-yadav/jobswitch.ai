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
  Wand2, 
  Copy, 
  Save, 
  Eye, 
  RefreshCw, 
  CheckCircle, 
  AlertCircle,
  User,
  Building,
  Target
} from 'lucide-react';
import { networkingAPI } from '../../services/networkingAPI';

const EmailTemplateGenerator = ({ contact, onTemplateGenerated, onClose }) => {
  const [loading, setLoading] = useState(false);
  const [template, setTemplate] = useState(null);
  const [templateType, setTemplateType] = useState('cold_outreach');
  const [campaignContext, setCampaignContext] = useState({
    objective: 'networking',
    tone: 'professional',
    call_to_action: 'connect',
    personalization_level: 'medium'
  });
  const [previewMode, setPreviewMode] = useState(false);
  const [error, setError] = useState(null);

  const templateTypes = [
    { value: 'cold_outreach', label: 'Cold Outreach', description: 'Initial contact with new connections' },
    { value: 'referral_request', label: 'Referral Request', description: 'Ask for job referrals' },
    { value: 'informational_interview', label: 'Informational Interview', description: 'Request career insights' },
    { value: 'follow_up', label: 'Follow-up', description: 'Follow up on previous contact' }
  ];

  const toneOptions = [
    { value: 'professional', label: 'Professional' },
    { value: 'friendly', label: 'Friendly' },
    { value: 'casual', label: 'Casual' },
    { value: 'formal', label: 'Formal' }
  ];

  const objectiveOptions = [
    { value: 'networking', label: 'General Networking' },
    { value: 'job_search', label: 'Job Search' },
    { value: 'career_advice', label: 'Career Advice' },
    { value: 'industry_insights', label: 'Industry Insights' },
    { value: 'collaboration', label: 'Collaboration' }
  ];

  const callToActionOptions = [
    { value: 'connect', label: 'Connect on LinkedIn' },
    { value: 'coffee_chat', label: 'Coffee Chat' },
    { value: 'phone_call', label: 'Phone Call' },
    { value: 'video_call', label: 'Video Call' },
    { value: 'meeting', label: 'In-person Meeting' }
  ];

  const generateTemplate = async () => {
    if (!contact) {
      setError('Contact information is required');
      return;
    }

    try {
      setLoading(true);
      setError(null);

      const response = await networkingAPI.generateEmailTemplate({
        contact,
        campaign_context: campaignContext,
        template_type: templateType
      });

      if (response.success) {
        setTemplate(response.data.template);
      } else {
        setError(response.error || 'Failed to generate template');
      }
    } catch (error) {
      console.error('Error generating template:', error);
      setError('Failed to generate email template');
    } finally {
      setLoading(false);
    }
  };

  const handleContextChange = (field, value) => {
    setCampaignContext(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    // You could add a toast notification here
  };

  const handleSaveTemplate = () => {
    if (template && onTemplateGenerated) {
      onTemplateGenerated({
        ...template,
        template_type: templateType,
        campaign_context: campaignContext
      });
    }
  };

  useEffect(() => {
    if (contact) {
      // Auto-generate template when contact is provided
      generateTemplate();
    }
  }, [contact, templateType]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Email Template Generator</h2>
          <p className="text-gray-600">Generate personalized outreach emails using AI</p>
        </div>
        {onClose && (
          <Button variant="outline" onClick={onClose}>
            Close
          </Button>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Configuration Panel */}
        <div className="lg:col-span-1 space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Target className="h-5 w-5" />
                Template Configuration
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Template Type */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Template Type
                </label>
                <Select value={templateType} onValueChange={setTemplateType}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {templateTypes.map(type => (
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

              {/* Objective */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Objective
                </label>
                <Select 
                  value={campaignContext.objective} 
                  onValueChange={(value) => handleContextChange('objective', value)}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {objectiveOptions.map(option => (
                      <SelectItem key={option.value} value={option.value}>
                        {option.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {/* Tone */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Tone
                </label>
                <Select 
                  value={campaignContext.tone} 
                  onValueChange={(value) => handleContextChange('tone', value)}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {toneOptions.map(option => (
                      <SelectItem key={option.value} value={option.value}>
                        {option.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {/* Call to Action */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Call to Action
                </label>
                <Select 
                  value={campaignContext.call_to_action} 
                  onValueChange={(value) => handleContextChange('call_to_action', value)}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {callToActionOptions.map(option => (
                      <SelectItem key={option.value} value={option.value}>
                        {option.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {/* Generate Button */}
              <Button 
                onClick={generateTemplate} 
                disabled={loading || !contact}
                className="w-full"
              >
                {loading ? (
                  <>
                    <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                    Generating...
                  </>
                ) : (
                  <>
                    <Wand2 className="h-4 w-4 mr-2" />
                    Generate Template
                  </>
                )}
              </Button>
            </CardContent>
          </Card>

          {/* Contact Info */}
          {contact && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <User className="h-5 w-5" />
                  Target Contact
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  <div className="flex items-center gap-2">
                    <span className="font-medium">{contact.full_name}</span>
                    <Badge variant="secondary">{contact.contact_quality}</Badge>
                  </div>
                  <div className="text-sm text-gray-600">
                    {contact.current_title} at {contact.current_company}
                  </div>
                  <div className="text-sm text-gray-500">
                    {contact.email}
                  </div>
                </div>
              </CardContent>
            </Card>
          )}
        </div>

        {/* Template Display */}
        <div className="lg:col-span-2">
          <Card className="h-full">
            <CardHeader>
              <div className="flex justify-between items-center">
                <CardTitle className="flex items-center gap-2">
                  <Mail className="h-5 w-5" />
                  Generated Template
                </CardTitle>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setPreviewMode(!previewMode)}
                  >
                    <Eye className="h-4 w-4 mr-2" />
                    {previewMode ? 'Edit' : 'Preview'}
                  </Button>
                  {template && (
                    <>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => copyToClipboard(`${template.subject}\n\n${template.body}`)}
                      >
                        <Copy className="h-4 w-4 mr-2" />
                        Copy
                      </Button>
                      <Button
                        size="sm"
                        onClick={handleSaveTemplate}
                      >
                        <Save className="h-4 w-4 mr-2" />
                        Use Template
                      </Button>
                    </>
                  )}
                </div>
              </div>
            </CardHeader>
            <CardContent>
              {error && (
                <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md">
                  <div className="flex items-center gap-2 text-red-800">
                    <AlertCircle className="h-4 w-4" />
                    <span className="text-sm">{error}</span>
                  </div>
                </div>
              )}

              {loading && (
                <div className="flex items-center justify-center h-64">
                  <div className="text-center">
                    <RefreshCw className="h-8 w-8 animate-spin mx-auto mb-4 text-blue-600" />
                    <p className="text-gray-600">Generating personalized email template...</p>
                  </div>
                </div>
              )}

              {template && !loading && (
                <Tabs defaultValue="template" className="w-full">
                  <TabsList className="grid w-full grid-cols-2">
                    <TabsTrigger value="template">Template</TabsTrigger>
                    <TabsTrigger value="preview">Preview</TabsTrigger>
                  </TabsList>

                  <TabsContent value="template" className="space-y-4">
                    {/* Subject Line */}
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Subject Line
                      </label>
                      <Input
                        value={template.subject}
                        onChange={(e) => setTemplate(prev => ({ ...prev, subject: e.target.value }))}
                        placeholder="Email subject"
                      />
                    </div>

                    {/* Email Body */}
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Email Body
                      </label>
                      <Textarea
                        value={template.body}
                        onChange={(e) => setTemplate(prev => ({ ...prev, body: e.target.value }))}
                        rows={12}
                        placeholder="Email content"
                      />
                    </div>

                    {/* Template Stats */}
                    <div className="flex gap-4 text-sm text-gray-600">
                      <span>Word count: {template.word_count}</span>
                      <span>Read time: ~{template.estimated_read_time} min</span>
                      {template.quality_score && (
                        <span>Quality: {Math.round(template.quality_score * 100)}%</span>
                      )}
                    </div>

                    {/* Suggestions */}
                    {template.suggestions && template.suggestions.length > 0 && (
                      <div className="mt-4">
                        <h4 className="text-sm font-medium text-gray-700 mb-2">Suggestions</h4>
                        <div className="space-y-1">
                          {template.suggestions.map((suggestion, index) => (
                            <div key={index} className="text-sm text-amber-700 bg-amber-50 p-2 rounded">
                              {suggestion}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </TabsContent>

                  <TabsContent value="preview" className="space-y-4">
                    {/* Email Preview */}
                    <div className="border rounded-lg p-4 bg-white">
                      <div className="border-b pb-3 mb-4">
                        <div className="text-sm text-gray-600 mb-1">Subject:</div>
                        <div className="font-medium">{template.preview_body ? template.subject : template.subject}</div>
                      </div>
                      <div className="whitespace-pre-wrap text-sm leading-relaxed">
                        {template.preview_body || template.body}
                      </div>
                    </div>

                    {/* Placeholders Info */}
                    {template.placeholders && template.placeholders.length > 0 && (
                      <div className="bg-blue-50 p-3 rounded-lg">
                        <h4 className="text-sm font-medium text-blue-900 mb-2">Available Placeholders</h4>
                        <div className="flex flex-wrap gap-2">
                          {template.placeholders.map((placeholder, index) => (
                            <Badge key={index} variant="secondary" className="text-xs">
                              {placeholder}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    )}
                  </TabsContent>
                </Tabs>
              )}

              {!template && !loading && !error && (
                <div className="flex items-center justify-center h-64 text-gray-500">
                  <div className="text-center">
                    <Mail className="h-12 w-12 mx-auto mb-4 text-gray-300" />
                    <p>Select a contact and click "Generate Template" to get started</p>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default EmailTemplateGenerator;