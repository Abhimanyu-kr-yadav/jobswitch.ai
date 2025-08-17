import api from './api';

export const networkingAPI = {
  // Contact Discovery
  async discoverContacts(data) {
    try {
      const response = await api.post('/agents/networking/discover-contacts', data);
      return response.data;
    } catch (error) {
      console.error('Error discovering contacts:', error);
      throw error;
    }
  },

  // Contact Scoring
  async scoreContacts(data) {
    try {
      const response = await api.post('/agents/networking/score-contacts', data);
      return response.data;
    } catch (error) {
      console.error('Error scoring contacts:', error);
      throw error;
    }
  },

  // Company Research
  async researchCompany(data) {
    try {
      const response = await api.post('/agents/networking/research-company', data);
      return response.data;
    } catch (error) {
      console.error('Error researching company:', error);
      throw error;
    }
  },

  // Campaign Management
  async createCampaign(data) {
    try {
      const response = await api.post('/agents/networking/create-campaign', data);
      return response.data;
    } catch (error) {
      console.error('Error creating campaign:', error);
      throw error;
    }
  },

  async getCampaigns() {
    try {
      const response = await api.get('/agents/networking/campaigns');
      return response.data;
    } catch (error) {
      console.error('Error getting campaigns:', error);
      throw error;
    }
  },

  // Recommendations
  async getRecommendations() {
    try {
      const response = await api.get('/agents/networking/recommendations');
      return response.data;
    } catch (error) {
      console.error('Error getting recommendations:', error);
      throw error;
    }
  },

  async getContactRecommendations(data) {
    try {
      const response = await api.post('/agents/networking/contact-recommendations', data);
      return response.data;
    } catch (error) {
      console.error('Error getting contact recommendations:', error);
      throw error;
    }
  },

  // Contacts Management
  async getContacts(params = {}) {
    try {
      const response = await api.get('/agents/networking/contacts', { params });
      return response.data;
    } catch (error) {
      console.error('Error getting contacts:', error);
      throw error;
    }
  },

  // Companies
  async getCompanies() {
    try {
      const response = await api.get('/agents/networking/companies');
      return response.data;
    } catch (error) {
      console.error('Error getting companies:', error);
      throw error;
    }
  },

  // Analytics
  async getAnalytics() {
    try {
      const response = await api.get('/agents/networking/analytics');
      return response.data;
    } catch (error) {
      console.error('Error getting analytics:', error);
      throw error;
    }
  },

  // Contact Actions
  async saveContact(contactId) {
    try {
      const response = await api.post(`/agents/networking/contacts/${contactId}/save`);
      return response.data;
    } catch (error) {
      console.error('Error saving contact:', error);
      throw error;
    }
  },

  async updateContactStatus(contactId, status) {
    try {
      const response = await api.patch(`/agents/networking/contacts/${contactId}/status`, {
        status
      });
      return response.data;
    } catch (error) {
      console.error('Error updating contact status:', error);
      throw error;
    }
  },

  async addContactNotes(contactId, notes) {
    try {
      const response = await api.patch(`/agents/networking/contacts/${contactId}/notes`, {
        notes
      });
      return response.data;
    } catch (error) {
      console.error('Error adding contact notes:', error);
      throw error;
    }
  },

  // Campaign Actions
  async updateCampaign(campaignId, data) {
    try {
      const response = await api.patch(`/agents/networking/campaigns/${campaignId}`, data);
      return response.data;
    } catch (error) {
      console.error('Error updating campaign:', error);
      throw error;
    }
  },

  async startCampaign(campaignId) {
    try {
      const response = await api.post(`/agents/networking/campaigns/${campaignId}/start`);
      return response.data;
    } catch (error) {
      console.error('Error starting campaign:', error);
      throw error;
    }
  },

  async pauseCampaign(campaignId) {
    try {
      const response = await api.post(`/agents/networking/campaigns/${campaignId}/pause`);
      return response.data;
    } catch (error) {
      console.error('Error pausing campaign:', error);
      throw error;
    }
  },

  async deleteCampaign(campaignId) {
    try {
      const response = await api.delete(`/agents/networking/campaigns/${campaignId}`);
      return response.data;
    } catch (error) {
      console.error('Error deleting campaign:', error);
      throw error;
    }
  },

  // Outreach
  async sendOutreach(data) {
    try {
      const response = await api.post('/agents/networking/outreach/send', data);
      return response.data;
    } catch (error) {
      console.error('Error sending outreach:', error);
      throw error;
    }
  },

  async getOutreachTemplates() {
    try {
      const response = await api.get('/agents/networking/outreach/templates');
      return response.data;
    } catch (error) {
      console.error('Error getting outreach templates:', error);
      throw error;
    }
  },

  async generateOutreachMessage(data) {
    try {
      const response = await api.post('/agents/networking/outreach/generate-message', data);
      return response.data;
    } catch (error) {
      console.error('Error generating outreach message:', error);
      throw error;
    }
  },

  // Search and Filters
  async searchContacts(query, filters = {}) {
    try {
      const response = await api.get('/agents/networking/contacts/search', {
        params: { query, ...filters }
      });
      return response.data;
    } catch (error) {
      console.error('Error searching contacts:', error);
      throw error;
    }
  },

  async searchCompanies(query, filters = {}) {
    try {
      const response = await api.get('/agents/networking/companies/search', {
        params: { query, ...filters }
      });
      return response.data;
    } catch (error) {
      console.error('Error searching companies:', error);
      throw error;
    }
  },

  // Bulk Operations
  async bulkSaveContacts(contactIds) {
    try {
      const response = await api.post('/agents/networking/contacts/bulk-save', {
        contact_ids: contactIds
      });
      return response.data;
    } catch (error) {
      console.error('Error bulk saving contacts:', error);
      throw error;
    }
  },

  async bulkUpdateContactStatus(contactIds, status) {
    try {
      const response = await api.post('/agents/networking/contacts/bulk-update-status', {
        contact_ids: contactIds,
        status
      });
      return response.data;
    } catch (error) {
      console.error('Error bulk updating contact status:', error);
      throw error;
    }
  },

  // Export/Import
  async exportContacts(format = 'csv', filters = {}) {
    try {
      const response = await api.get('/agents/networking/contacts/export', {
        params: { format, ...filters },
        responseType: 'blob'
      });
      return response.data;
    } catch (error) {
      console.error('Error exporting contacts:', error);
      throw error;
    }
  },

  async importContacts(file) {
    try {
      const formData = new FormData();
      formData.append('file', file);
      
      const response = await api.post('/agents/networking/contacts/import', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });
      return response.data;
    } catch (error) {
      console.error('Error importing contacts:', error);
      throw error;
    }
  },

  // Email Generation and Outreach
  async generateEmailTemplate(data) {
    try {
      const response = await api.post('/agents/networking/generate-email-template', data);
      return response.data;
    } catch (error) {
      console.error('Error generating email template:', error);
      throw error;
    }
  },

  async sendOutreachEmail(data) {
    try {
      const response = await api.post('/agents/networking/send-outreach-email', data);
      return response.data;
    } catch (error) {
      console.error('Error sending outreach email:', error);
      throw error;
    }
  },

  async startEmailCampaign(data) {
    try {
      const response = await api.post('/agents/networking/start-email-campaign', data);
      return response.data;
    } catch (error) {
      console.error('Error starting email campaign:', error);
      throw error;
    }
  },

  async manageCampaign(data) {
    try {
      const response = await api.post('/agents/networking/manage-campaign', data);
      return response.data;
    } catch (error) {
      console.error('Error managing campaign:', error);
      throw error;
    }
  },

  async getCampaignAnalytics(campaignId = null) {
    try {
      const params = campaignId ? { campaign_id: campaignId } : {};
      const response = await api.get('/agents/networking/campaign-analytics', { params });
      return response.data;
    } catch (error) {
      console.error('Error getting campaign analytics:', error);
      throw error;
    }
  },

  // Email Templates
  async getEmailTemplates() {
    try {
      const response = await api.get('/agents/networking/email-templates');
      return response.data;
    } catch (error) {
      console.error('Error getting email templates:', error);
      throw error;
    }
  },

  async saveEmailTemplate(data) {
    try {
      const response = await api.post('/agents/networking/email-templates', data);
      return response.data;
    } catch (error) {
      console.error('Error saving email template:', error);
      throw error;
    }
  },

  async updateEmailTemplate(templateId, data) {
    try {
      const response = await api.patch(`/agents/networking/email-templates/${templateId}`, data);
      return response.data;
    } catch (error) {
      console.error('Error updating email template:', error);
      throw error;
    }
  },

  async deleteEmailTemplate(templateId) {
    try {
      const response = await api.delete(`/agents/networking/email-templates/${templateId}`);
      return response.data;
    } catch (error) {
      console.error('Error deleting email template:', error);
      throw error;
    }
  },

  // Campaign Templates
  async getCampaignTemplates() {
    try {
      const response = await api.get('/agents/networking/campaign-templates');
      return response.data;
    } catch (error) {
      console.error('Error getting campaign templates:', error);
      throw error;
    }
  },

  // Follow-up Management
  async scheduleFollowUp(data) {
    try {
      const response = await api.post('/agents/networking/schedule-follow-up', data);
      return response.data;
    } catch (error) {
      console.error('Error scheduling follow-up:', error);
      throw error;
    }
  },

  async getFollowUps(params = {}) {
    try {
      const response = await api.get('/agents/networking/follow-ups', { params });
      return response.data;
    } catch (error) {
      console.error('Error getting follow-ups:', error);
      throw error;
    }
  },

  async markFollowUpComplete(followUpId) {
    try {
      const response = await api.patch(`/agents/networking/follow-ups/${followUpId}/complete`);
      return response.data;
    } catch (error) {
      console.error('Error marking follow-up complete:', error);
      throw error;
    }
  }
};