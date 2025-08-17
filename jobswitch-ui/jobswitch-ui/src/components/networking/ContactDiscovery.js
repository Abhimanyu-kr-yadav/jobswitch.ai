import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/Card';
import { Button } from '../ui/Button';
import { Input } from '../ui/Input';
import { Label } from '../ui/Label';
import { Badge } from '../ui/Badge';
import { Alert, AlertDescription } from '../ui/Alert';
import { Search, Users, Mail, Linkedin, ExternalLink, Star } from 'lucide-react';
import { networkingAPI } from '../../services/networkingAPI';

const ContactDiscovery = ({ onContactsDiscovered }) => {
  const [formData, setFormData] = useState({
    companyName: '',
    companyDomain: '',
    targetRole: ''
  });
  const [discoveredContacts, setDiscoveredContacts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleDiscoverContacts = async (e) => {
    e.preventDefault();
    
    if (!formData.companyName.trim()) {
      setError('Company name is required');
      return;
    }

    try {
      setLoading(true);
      setError('');
      setSuccess('');

      const response = await networkingAPI.discoverContacts({
        company_name: formData.companyName,
        company_domain: formData.companyDomain || null,
        target_role: formData.targetRole || null
      });

      if (response.success) {
        setDiscoveredContacts(response.data.contacts || []);
        setSuccess(`Discovered ${response.data.contacts_discovered} contacts at ${formData.companyName}`);
        
        // Notify parent component
        if (onContactsDiscovered) {
          onContactsDiscovered();
        }
      } else {
        setError(response.error || 'Failed to discover contacts');
      }
    } catch (error) {
      console.error('Error discovering contacts:', error);
      setError('An error occurred while discovering contacts');
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

  const getRelevanceStars = (score) => {
    const stars = Math.round(score * 5);
    return Array.from({ length: 5 }, (_, i) => (
      <Star
        key={i}
        className={`h-4 w-4 ${i < stars ? 'text-yellow-400 fill-current' : 'text-gray-300'}`}
      />
    ));
  };

  return (
    <div className="space-y-6">
      {/* Discovery Form */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Search className="h-5 w-5" />
            Discover Contacts
          </CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleDiscoverContacts} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="companyName">Company Name *</Label>
                <Input
                  id="companyName"
                  name="companyName"
                  value={formData.companyName}
                  onChange={handleInputChange}
                  placeholder="e.g., Google, Microsoft, Apple"
                  required
                />
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="companyDomain">Company Domain (Optional)</Label>
                <Input
                  id="companyDomain"
                  name="companyDomain"
                  value={formData.companyDomain}
                  onChange={handleInputChange}
                  placeholder="e.g., google.com"
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="targetRole">Target Role (Optional)</Label>
              <Input
                id="targetRole"
                name="targetRole"
                value={formData.targetRole}
                onChange={handleInputChange}
                placeholder="e.g., Software Engineer, Product Manager"
              />
            </div>

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

            <Button 
              type="submit" 
              disabled={loading}
              className="w-full md:w-auto"
            >
              {loading ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  Discovering Contacts...
                </>
              ) : (
                <>
                  <Search className="h-4 w-4 mr-2" />
                  Discover Contacts
                </>
              )}
            </Button>
          </form>
        </CardContent>
      </Card>

      {/* Discovered Contacts */}
      {discoveredContacts.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Users className="h-5 w-5" />
              Discovered Contacts ({discoveredContacts.length})
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {discoveredContacts.map((contact, index) => (
                <div key={contact.contact_id || index} className="border rounded-lg p-4 hover:bg-gray-50">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <h3 className="font-semibold text-gray-900">
                          {contact.full_name || 'Unknown Name'}
                        </h3>
                        <Badge className={getContactQualityColor(contact.contact_quality)}>
                          {contact.contact_quality} quality
                        </Badge>
                      </div>

                      <div className="space-y-1 text-sm text-gray-600">
                        {contact.current_title && (
                          <p className="font-medium">{contact.current_title}</p>
                        )}
                        {contact.current_company && (
                          <p>{contact.current_company}</p>
                        )}
                        {contact.location && (
                          <p>{contact.location}</p>
                        )}
                      </div>

                      {/* Contact Information */}
                      <div className="flex items-center gap-4 mt-3">
                        {contact.email && (
                          <div className="flex items-center gap-1 text-sm text-blue-600">
                            <Mail className="h-4 w-4" />
                            <span>{contact.email}</span>
                          </div>
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
                            <ExternalLink className="h-3 w-3" />
                          </a>
                        )}
                        {contact.github_url && (
                          <a
                            href={contact.github_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="flex items-center gap-1 text-sm text-gray-600 hover:underline"
                          >
                            GitHub
                            <ExternalLink className="h-3 w-3" />
                          </a>
                        )}
                      </div>

                      {/* Discovery Information */}
                      <div className="flex items-center gap-4 mt-2 text-xs text-gray-500">
                        <span>Source: {contact.discovery_source}</span>
                        {contact.discovery_method && (
                          <span>Method: {contact.discovery_method}</span>
                        )}
                      </div>
                    </div>

                    <div className="flex flex-col items-end gap-2">
                      {/* Relevance Score */}
                      <div className="flex items-center gap-1">
                        {getRelevanceStars(contact.relevance_score || 0)}
                        <span className="text-sm text-gray-600 ml-1">
                          {Math.round((contact.relevance_score || 0) * 100)}%
                        </span>
                      </div>

                      {/* Actions */}
                      <div className="flex gap-2">
                        <Button size="sm" variant="outline">
                          Save Contact
                        </Button>
                        <Button size="sm">
                          Start Outreach
                        </Button>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {/* Bulk Actions */}
            <div className="flex items-center justify-between mt-6 pt-4 border-t">
              <div className="flex items-center gap-2">
                <input type="checkbox" className="rounded" />
                <span className="text-sm text-gray-600">Select all contacts</span>
              </div>
              <div className="flex gap-2">
                <Button variant="outline" size="sm">
                  Save Selected
                </Button>
                <Button size="sm">
                  Create Campaign
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Tips */}
      <Card>
        <CardHeader>
          <CardTitle>Discovery Tips</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2 text-sm text-gray-600">
            <p>• <strong>Company Domain:</strong> Providing the company website helps find more contacts from team pages</p>
            <p>• <strong>Target Role:</strong> Specify a role to get more relevant contacts and better scoring</p>
            <p>• <strong>Quality Scoring:</strong> High-quality contacts have email addresses and LinkedIn profiles</p>
            <p>• <strong>Relevance Scoring:</strong> Based on your career goals, target role, and profile</p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default ContactDiscovery;