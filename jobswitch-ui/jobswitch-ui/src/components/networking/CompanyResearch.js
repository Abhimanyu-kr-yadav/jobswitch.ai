import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/Card';
import { Button } from '../ui/Button';
import { Input } from '../ui/Input';
import { Label } from '../ui/Label';
import { Badge } from '../ui/Badge';
import { Alert, AlertDescription } from '../ui/Alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/Tabs';
import { 
  Building, 
  Search, 
  Users, 
  ExternalLink, 
  MapPin, 
  Globe, 
  Linkedin,
  TrendingUp,
  Target,
  Clock
} from 'lucide-react';
import { networkingAPI } from '../../services/networkingAPI';

const CompanyResearch = ({ onCompanyResearched }) => {
  const [companyName, setCompanyName] = useState('');
  const [researchData, setResearchData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleResearchCompany = async (e) => {
    e.preventDefault();
    
    if (!companyName.trim()) {
      setError('Company name is required');
      return;
    }

    try {
      setLoading(true);
      setError('');

      const response = await networkingAPI.researchCompany({
        company_name: companyName
      });

      if (response.success) {
        setResearchData(response.data);
        
        // Notify parent component
        if (onCompanyResearched) {
          onCompanyResearched();
        }
      } else {
        setError(response.error || 'Failed to research company');
      }
    } catch (error) {
      console.error('Error researching company:', error);
      setError('An error occurred while researching the company');
    } finally {
      setLoading(false);
    }
  };

  const getContactQualityColor = (quality) => {
    switch (quality) {
      case 'high': return 'bg-green-100 text-green-800';
      case 'medium': return 'bg-yellow-100 text-yellow-800';
      case 'low': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getPriorityColor = (priority) => {
    switch (priority) {
      case 'high': return 'bg-red-100 text-red-800';
      case 'medium': return 'bg-yellow-100 text-yellow-800';
      case 'low': return 'bg-green-100 text-green-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="space-y-6">
      {/* Research Form */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Search className="h-5 w-5" />
            Company Research
          </CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleResearchCompany} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="companyName">Company Name</Label>
              <Input
                id="companyName"
                value={companyName}
                onChange={(e) => setCompanyName(e.target.value)}
                placeholder="e.g., Google, Microsoft, Apple"
                required
              />
            </div>

            {error && (
              <Alert variant="destructive">
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}

            <Button 
              type="submit" 
              disabled={loading}
              className="w-full md:w-auto"
            >
              {loading ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  Researching Company...
                </>
              ) : (
                <>
                  <Building className="h-4 w-4 mr-2" />
                  Research Company
                </>
              )}
            </Button>
          </form>
        </CardContent>
      </Card>

      {/* Research Results */}
      {researchData && (
        <div className="space-y-6">
          {/* Company Overview */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Building className="h-5 w-5" />
                {researchData.company_info.name}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-4">
                  <div>
                    <h4 className="font-semibold text-gray-900 mb-2">Company Details</h4>
                    <div className="space-y-2 text-sm">
                      {researchData.company_info.industry && (
                        <div className="flex items-center gap-2">
                          <TrendingUp className="h-4 w-4 text-gray-500" />
                          <span>Industry: {researchData.company_info.industry}</span>
                        </div>
                      )}
                      {researchData.company_info.size && (
                        <div className="flex items-center gap-2">
                          <Users className="h-4 w-4 text-gray-500" />
                          <span>Size: {researchData.company_info.size}</span>
                        </div>
                      )}
                      {researchData.company_info.headquarters && (
                        <div className="flex items-center gap-2">
                          <MapPin className="h-4 w-4 text-gray-500" />
                          <span>HQ: {researchData.company_info.headquarters}</span>
                        </div>
                      )}
                      {researchData.company_info.website && (
                        <div className="flex items-center gap-2">
                          <Globe className="h-4 w-4 text-gray-500" />
                          <a 
                            href={researchData.company_info.website}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-blue-600 hover:underline flex items-center gap-1"
                          >
                            Website
                            <ExternalLink className="h-3 w-3" />
                          </a>
                        </div>
                      )}
                    </div>
                  </div>

                  {researchData.company_info.description && (
                    <div>
                      <h4 className="font-semibold text-gray-900 mb-2">Description</h4>
                      <p className="text-sm text-gray-600">{researchData.company_info.description}</p>
                    </div>
                  )}
                </div>

                <div className="space-y-4">
                  <div>
                    <h4 className="font-semibold text-gray-900 mb-2">Networking Stats</h4>
                    <div className="space-y-2">
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-gray-600">Contacts Found:</span>
                        <Badge variant="secondary">{researchData.total_contacts_found}</Badge>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-gray-600">High-Quality Contacts:</span>
                        <Badge variant="secondary">
                          {researchData.contacts.filter(c => c.contact_quality === 'high').length}
                        </Badge>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-gray-600">With Email:</span>
                        <Badge variant="secondary">
                          {researchData.contacts.filter(c => c.email).length}
                        </Badge>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Detailed Results Tabs */}
          <Tabs defaultValue="contacts" className="w-full">
            <TabsList className="grid w-full grid-cols-3">
              <TabsTrigger value="contacts">Key Contacts</TabsTrigger>
              <TabsTrigger value="strategy">Networking Strategy</TabsTrigger>
              <TabsTrigger value="recommendations">Recommendations</TabsTrigger>
            </TabsList>

            <TabsContent value="contacts" className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle>Key Contacts ({researchData.contacts.length})</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {researchData.contacts.map((contact, index) => (
                      <div key={contact.contact_id || index} className="border rounded-lg p-4">
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <div className="flex items-center gap-3 mb-2">
                              <h4 className="font-semibold text-gray-900">
                                {contact.full_name || 'Unknown Name'}
                              </h4>
                              <Badge className={getContactQualityColor(contact.contact_quality)}>
                                {contact.contact_quality}
                              </Badge>
                            </div>

                            <div className="space-y-1 text-sm text-gray-600">
                              {contact.current_title && (
                                <p className="font-medium">{contact.current_title}</p>
                              )}
                              {contact.location && (
                                <p>{contact.location}</p>
                              )}
                            </div>

                            <div className="flex items-center gap-4 mt-3">
                              {contact.email && (
                                <span className="text-sm text-blue-600">{contact.email}</span>
                              )}
                              {contact.linkedin_url && (
                                <a
                                  href={contact.linkedin_url}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="flex items-center gap-1 text-sm text-blue-600 hover:underline"
                                >
                                  <Linkedin className="h-4 w-4" />
                                  LinkedIn
                                </a>
                              )}
                            </div>
                          </div>

                          <div className="flex flex-col items-end gap-2">
                            <div className="text-sm text-gray-600">
                              Relevance: {Math.round((contact.relevance_score || 0) * 100)}%
                            </div>
                            <div className="flex gap-2">
                              <Button size="sm" variant="outline">
                                Save
                              </Button>
                              <Button size="sm">
                                Contact
                              </Button>
                            </div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="strategy" className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle>Networking Strategy</CardTitle>
                </CardHeader>
                <CardContent>
                  {researchData.networking_strategy && (
                    <div className="space-y-6">
                      <div>
                        <h4 className="font-semibold text-gray-900 mb-3">Recommended Approach</h4>
                        <Badge className={getPriorityColor('medium')}>
                          {researchData.networking_strategy.approach}
                        </Badge>
                      </div>

                      <div>
                        <h4 className="font-semibold text-gray-900 mb-3">Priority Contacts</h4>
                        <div className="space-y-2">
                          {researchData.networking_strategy.priority_contacts?.map((contact, index) => (
                            <div key={index} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                              <span className="font-medium">{contact.full_name}</span>
                              <span className="text-sm text-gray-600">{contact.current_title}</span>
                            </div>
                          ))}
                        </div>
                      </div>

                      <div>
                        <h4 className="font-semibold text-gray-900 mb-3">Recommended Sequence</h4>
                        <ol className="space-y-2">
                          {researchData.networking_strategy.recommended_sequence?.map((step, index) => (
                            <li key={index} className="flex items-start gap-3">
                              <span className="flex-shrink-0 w-6 h-6 bg-blue-100 text-blue-800 rounded-full flex items-center justify-center text-sm font-medium">
                                {index + 1}
                              </span>
                              <span className="text-sm text-gray-700">{step}</span>
                            </li>
                          ))}
                        </ol>
                      </div>

                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                          <h4 className="font-semibold text-gray-900 mb-2">Timeline</h4>
                          <div className="flex items-center gap-2">
                            <Clock className="h-4 w-4 text-gray-500" />
                            <span className="text-sm text-gray-600">
                              {researchData.networking_strategy.timeline}
                            </span>
                          </div>
                        </div>

                        <div>
                          <h4 className="font-semibold text-gray-900 mb-2">Success Metrics</h4>
                          <ul className="space-y-1">
                            {researchData.networking_strategy.success_metrics?.map((metric, index) => (
                              <li key={index} className="text-sm text-gray-600 flex items-center gap-2">
                                <Target className="h-3 w-3" />
                                {metric}
                              </li>
                            ))}
                          </ul>
                        </div>
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="recommendations" className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle>AI Recommendations</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {researchData.recommendations?.map((rec, index) => (
                      <div key={index} className="border rounded-lg p-4">
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <h4 className="font-semibold text-gray-900 mb-1">{rec.title}</h4>
                            <p className="text-sm text-gray-600 mb-2">{rec.description}</p>
                            {rec.company && (
                              <Badge variant="outline">{rec.company}</Badge>
                            )}
                          </div>
                          <div className="flex items-center gap-2">
                            <Badge className={getPriorityColor(rec.priority)}>
                              {rec.priority}
                            </Badge>
                            <Button size="sm">
                              Act
                            </Button>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>

          {/* Action Buttons */}
          <div className="flex gap-4">
            <Button className="flex-1">
              Create Networking Campaign
            </Button>
            <Button variant="outline" className="flex-1">
              Save Company Research
            </Button>
          </div>
        </div>
      )}
    </div>
  );
};

export default CompanyResearch;