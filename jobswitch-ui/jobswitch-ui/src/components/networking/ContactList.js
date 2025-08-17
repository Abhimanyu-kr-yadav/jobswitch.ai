import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/Card';
import { Button } from '../ui/Button';
import { Input } from '../ui/Input';
import { Badge } from '../ui/Badge';
import { 
  Users, 
  Search, 
  Mail, 
  Linkedin, 
  ExternalLink, 
  Star,
  Filter,
  MoreHorizontal,
  Edit,
  Trash2
} from 'lucide-react';
import { networkingAPI } from '../../services/networkingAPI';

const ContactList = ({ limit, showActions = true }) => {
  const [contacts, setContacts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedContacts, setSelectedContacts] = useState(new Set());
  const [filters, setFilters] = useState({
    company: '',
    quality: '',
    status: ''
  });

  useEffect(() => {
    loadContacts();
  }, [limit, filters]);

  const loadContacts = async () => {
    try {
      setLoading(true);
      const params = {
        limit: limit || 50,
        ...filters
      };
      
      const response = await networkingAPI.getContacts(params);
      
      if (response.success) {
        setContacts(response.data.contacts || []);
      }
    } catch (error) {
      console.error('Error loading contacts:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      loadContacts();
      return;
    }

    try {
      setLoading(true);
      const response = await networkingAPI.searchContacts(searchQuery, filters);
      
      if (response.success) {
        setContacts(response.data.contacts || []);
      }
    } catch (error) {
      console.error('Error searching contacts:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleContactSelect = (contactId) => {
    const newSelected = new Set(selectedContacts);
    if (newSelected.has(contactId)) {
      newSelected.delete(contactId);
    } else {
      newSelected.add(contactId);
    }
    setSelectedContacts(newSelected);
  };

  const handleSelectAll = () => {
    if (selectedContacts.size === contacts.length) {
      setSelectedContacts(new Set());
    } else {
      setSelectedContacts(new Set(contacts.map(c => c.contact_id)));
    }
  };

  const handleBulkSave = async () => {
    try {
      const contactIds = Array.from(selectedContacts);
      await networkingAPI.bulkSaveContacts(contactIds);
      setSelectedContacts(new Set());
      loadContacts();
    } catch (error) {
      console.error('Error bulk saving contacts:', error);
    }
  };

  const handleUpdateContactStatus = async (contactId, status) => {
    try {
      await networkingAPI.updateContactStatus(contactId, status);
      loadContacts();
    } catch (error) {
      console.error('Error updating contact status:', error);
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

  const getStatusColor = (status) => {
    switch (status) {
      case 'contacted': return 'bg-blue-100 text-blue-800';
      case 'responded': return 'bg-green-100 text-green-800';
      case 'connected': return 'bg-purple-100 text-purple-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getRelevanceStars = (score) => {
    const stars = Math.round(score * 5);
    return Array.from({ length: 5 }, (_, i) => (
      <Star
        key={i}
        className={`h-3 w-3 ${i < stars ? 'text-yellow-400 fill-current' : 'text-gray-300'}`}
      />
    ));
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-32">
        <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Search and Filters */}
      {showActions && (
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="flex-1 flex gap-2">
            <Input
              placeholder="Search contacts..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
            />
            <Button onClick={handleSearch} variant="outline">
              <Search className="h-4 w-4" />
            </Button>
          </div>
          
          <div className="flex gap-2">
            <Button variant="outline" size="sm">
              <Filter className="h-4 w-4 mr-2" />
              Filters
            </Button>
          </div>
        </div>
      )}

      {/* Bulk Actions */}
      {showActions && selectedContacts.size > 0 && (
        <div className="flex items-center justify-between p-3 bg-blue-50 rounded-lg">
          <span className="text-sm text-blue-800">
            {selectedContacts.size} contact{selectedContacts.size !== 1 ? 's' : ''} selected
          </span>
          <div className="flex gap-2">
            <Button size="sm" variant="outline" onClick={handleBulkSave}>
              Save Selected
            </Button>
            <Button size="sm" onClick={() => setSelectedContacts(new Set())}>
              Clear Selection
            </Button>
          </div>
        </div>
      )}

      {/* Contacts List */}
      <div className="space-y-3">
        {contacts.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <Users className="h-12 w-12 mx-auto mb-4 text-gray-300" />
            <p>No contacts found</p>
          </div>
        ) : (
          contacts.map((contact) => (
            <Card key={contact.contact_id} className="hover:shadow-md transition-shadow">
              <CardContent className="p-4">
                <div className="flex items-start gap-4">
                  {/* Selection Checkbox */}
                  {showActions && (
                    <input
                      type="checkbox"
                      checked={selectedContacts.has(contact.contact_id)}
                      onChange={() => handleContactSelect(contact.contact_id)}
                      className="mt-1 rounded"
                    />
                  )}

                  {/* Contact Info */}
                  <div className="flex-1">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2">
                          <h3 className="font-semibold text-gray-900">
                            {contact.full_name || 'Unknown Name'}
                          </h3>
                          <Badge className={getContactQualityColor(contact.contact_quality)}>
                            {contact.contact_quality}
                          </Badge>
                          <Badge className={getStatusColor(contact.contact_status)}>
                            {contact.contact_status}
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

                        {/* Contact Methods */}
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
                        </div>

                        {/* Tags and Notes */}
                        {contact.tags && contact.tags.length > 0 && (
                          <div className="flex gap-1 mt-2">
                            {contact.tags.slice(0, 3).map((tag, index) => (
                              <Badge key={index} variant="outline" className="text-xs">
                                {tag}
                              </Badge>
                            ))}
                          </div>
                        )}
                      </div>

                      {/* Relevance Score and Actions */}
                      <div className="flex flex-col items-end gap-2">
                        {/* Relevance Score */}
                        <div className="flex items-center gap-1">
                          {getRelevanceStars(contact.relevance_score || 0)}
                          <span className="text-xs text-gray-600 ml-1">
                            {Math.round((contact.relevance_score || 0) * 100)}%
                          </span>
                        </div>

                        {/* Actions */}
                        {showActions && (
                          <div className="flex gap-2">
                            <Button size="sm" variant="outline">
                              <Mail className="h-3 w-3 mr-1" />
                              Contact
                            </Button>
                            <Button size="sm" variant="outline">
                              <MoreHorizontal className="h-3 w-3" />
                            </Button>
                          </div>
                        )}
                      </div>
                    </div>

                    {/* Last Contact Info */}
                    {contact.last_contact_date && (
                      <div className="text-xs text-gray-500 mt-2">
                        Last contacted: {new Date(contact.last_contact_date).toLocaleDateString()}
                      </div>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          ))
        )}
      </div>

      {/* Load More */}
      {showActions && contacts.length >= (limit || 50) && (
        <div className="text-center">
          <Button variant="outline" onClick={loadContacts}>
            Load More Contacts
          </Button>
        </div>
      )}

      {/* Select All Toggle */}
      {showActions && contacts.length > 0 && (
        <div className="flex items-center justify-between pt-4 border-t">
          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={selectedContacts.size === contacts.length}
              onChange={handleSelectAll}
              className="rounded"
            />
            <span className="text-sm text-gray-600">
              Select all {contacts.length} contacts
            </span>
          </div>
          
          {selectedContacts.size > 0 && (
            <div className="flex gap-2">
              <Button size="sm" variant="outline">
                Export Selected
              </Button>
              <Button size="sm" onClick={handleBulkSave}>
                Save Selected
              </Button>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default ContactList;