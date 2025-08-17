import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/Card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/Tabs';
import { Button } from '../ui/Button';
import { Badge } from '../ui/Badge';
import { Input } from '../ui/Input';
import { Textarea } from '../ui/Textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/Select';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '../ui/Dialog';
import { Alert, AlertDescription } from '../ui/Alert';
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  LineChart, Line, PieChart, Pie, Cell 
} from 'recharts';
import { 
  Play, Pause, Square, TrendingUp, TrendingDown, Users, 
  Target, Zap, AlertTriangle, CheckCircle, Plus 
} from 'lucide-react';
import { analyticsAPI } from '../../services/analyticsAPI';

const ABTestingDashboard = () => {
  const [experiments, setExperiments] = useState([]);
  const [selectedExperiment, setSelectedExperiment] = useState(null);
  const [experimentResults, setExperimentResults] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [newExperiment, setNewExperiment] = useState({
    name: '',
    description: '',
    feature_name: '',
    control_algorithm: '',
    test_algorithm: '',
    traffic_split: 0.5,
    primary_metric: 'conversion_rate',
    secondary_metrics: []
  });

  useEffect(() => {
    loadExperiments();
  }, []);

  const loadExperiments = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await analyticsAPI.getABTestExperiments();
      setExperiments(response.data.experiments || []);
      
    } catch (err) {
      console.error('Error loading A/B test experiments:', err);
      setError('Failed to load A/B test experiments');
    } finally {
      setLoading(false);
    }
  };

  const loadExperimentResults = async (experimentId) => {
    try {
      const response = await analyticsAPI.getABTestResults(experimentId);
      setExperimentResults(response.data);
      setSelectedExperiment(experimentId);
    } catch (err) {
      console.error('Error loading experiment results:', err);
    }
  };

  const createExperiment = async () => {
    try {
      await analyticsAPI.createABTestExperiment(newExperiment);
      setShowCreateDialog(false);
      setNewExperiment({
        name: '',
        description: '',
        feature_name: '',
        control_algorithm: '',
        test_algorithm: '',
        traffic_split: 0.5,
        primary_metric: 'conversion_rate',
        secondary_metrics: []
      });
      loadExperiments();
    } catch (err) {
      console.error('Error creating experiment:', err);
    }
  };

  const startExperiment = async (experimentId) => {
    try {
      await analyticsAPI.startABTestExperiment(experimentId);
      loadExperiments();
    } catch (err) {
      console.error('Error starting experiment:', err);
    }
  };

  const stopExperiment = async (experimentId) => {
    try {
      await analyticsAPI.stopABTestExperiment(experimentId);
      loadExperiments();
    } catch (err) {
      console.error('Error stopping experiment:', err);
    }
  };

  const getStatusBadge = (status) => {
    const colors = {
      draft: 'bg-gray-100 text-gray-800',
      running: 'bg-green-100 text-green-800',
      paused: 'bg-yellow-100 text-yellow-800',
      completed: 'bg-blue-100 text-blue-800'
    };
    
    return (
      <Badge className={colors[status] || colors.draft}>
        {status?.toUpperCase() || 'DRAFT'}
      </Badge>
    );
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'running': return <Play className="h-4 w-4 text-green-600" />;
      case 'paused': return <Pause className="h-4 w-4 text-yellow-600" />;
      case 'completed': return <CheckCircle className="h-4 w-4 text-blue-600" />;
      default: return <Square className="h-4 w-4 text-gray-600" />;
    }
  };

  const calculateSignificance = (results) => {
    if (!results || !results.metrics) return 'Not enough data';
    
    const significance = results.metrics.statistical_significance;
    if (significance >= 0.95) return 'Statistically significant (95%+)';
    if (significance >= 0.90) return 'Likely significant (90%+)';
    return 'Not significant';
  };

  const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042'];

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-8">
        <Alert className="mb-4">
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
        <Button onClick={loadExperiments}>Retry</Button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">A/B Testing Dashboard</h1>
          <p className="text-gray-600">Optimize recommendation algorithms through experimentation</p>
        </div>
        <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="h-4 w-4 mr-2" />
              New Experiment
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-2xl">
            <DialogHeader>
              <DialogTitle>Create New A/B Test Experiment</DialogTitle>
            </DialogHeader>
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-2">Experiment Name</label>
                  <Input
                    value={newExperiment.name}
                    onChange={(e) => setNewExperiment({...newExperiment, name: e.target.value})}
                    placeholder="e.g., Job Recommendation Algorithm V2"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2">Feature Name</label>
                  <Select 
                    value={newExperiment.feature_name}
                    onValueChange={(value) => setNewExperiment({...newExperiment, feature_name: value})}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select feature" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="job_recommendations">Job Recommendations</SelectItem>
                      <SelectItem value="resume_optimization">Resume Optimization</SelectItem>
                      <SelectItem value="skills_analysis">Skills Analysis</SelectItem>
                      <SelectItem value="interview_questions">Interview Questions</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              
              <div>
                <label className="block text-sm font-medium mb-2">Description</label>
                <Textarea
                  value={newExperiment.description}
                  onChange={(e) => setNewExperiment({...newExperiment, description: e.target.value})}
                  placeholder="Describe what this experiment is testing..."
                  rows={3}
                />
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-2">Control Algorithm</label>
                  <Input
                    value={newExperiment.control_algorithm}
                    onChange={(e) => setNewExperiment({...newExperiment, control_algorithm: e.target.value})}
                    placeholder="e.g., current_algorithm_v1"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2">Test Algorithm</label>
                  <Input
                    value={newExperiment.test_algorithm}
                    onChange={(e) => setNewExperiment({...newExperiment, test_algorithm: e.target.value})}
                    placeholder="e.g., new_algorithm_v2"
                  />
                </div>
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-2">Traffic Split</label>
                  <Input
                    type="number"
                    min="0"
                    max="1"
                    step="0.1"
                    value={newExperiment.traffic_split}
                    onChange={(e) => setNewExperiment({...newExperiment, traffic_split: parseFloat(e.target.value)})}
                  />
                  <p className="text-xs text-gray-500 mt-1">Percentage of users in test group (0.0 - 1.0)</p>
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2">Primary Metric</label>
                  <Select 
                    value={newExperiment.primary_metric}
                    onValueChange={(value) => setNewExperiment({...newExperiment, primary_metric: value})}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="conversion_rate">Conversion Rate</SelectItem>
                      <SelectItem value="click_through_rate">Click Through Rate</SelectItem>
                      <SelectItem value="engagement_rate">Engagement Rate</SelectItem>
                      <SelectItem value="success_rate">Success Rate</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              
              <div className="flex justify-end space-x-2">
                <Button variant="outline" onClick={() => setShowCreateDialog(false)}>
                  Cancel
                </Button>
                <Button onClick={createExperiment}>
                  Create Experiment
                </Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      {/* Experiments Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Experiments</CardTitle>
            <Target className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{experiments.length}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Running</CardTitle>
            <Play className="h-4 w-4 text-green-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">
              {experiments.filter(e => e.status === 'running').length}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Completed</CardTitle>
            <CheckCircle className="h-4 w-4 text-blue-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-600">
              {experiments.filter(e => e.status === 'completed').length}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Success Rate</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {experiments.length > 0 ? 
                Math.round((experiments.filter(e => e.status === 'completed').length / experiments.length) * 100) : 0}%
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Main Content */}
      <Tabs defaultValue="experiments" className="space-y-4">
        <TabsList>
          <TabsTrigger value="experiments">Experiments</TabsTrigger>
          <TabsTrigger value="results">Results</TabsTrigger>
        </TabsList>

        <TabsContent value="experiments" className="space-y-4">
          <div className="grid grid-cols-1 gap-4">
            {experiments.map((experiment) => (
              <Card key={experiment.experiment_id} className="hover:shadow-md transition-shadow">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      {getStatusIcon(experiment.status)}
                      <div>
                        <CardTitle className="text-lg">{experiment.name}</CardTitle>
                        <p className="text-sm text-gray-600">{experiment.feature_name}</p>
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      {getStatusBadge(experiment.status)}
                      {experiment.status === 'draft' && (
                        <Button size="sm" onClick={() => startExperiment(experiment.experiment_id)}>
                          <Play className="h-4 w-4 mr-1" />
                          Start
                        </Button>
                      )}
                      {experiment.status === 'running' && (
                        <Button size="sm" variant="outline" onClick={() => stopExperiment(experiment.experiment_id)}>
                          <Square className="h-4 w-4 mr-1" />
                          Stop
                        </Button>
                      )}
                      <Button 
                        size="sm" 
                        variant="outline"
                        onClick={() => loadExperimentResults(experiment.experiment_id)}
                      >
                        View Results
                      </Button>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                    <div>
                      <div className="text-sm text-gray-600">Participants</div>
                      <div className="font-semibold">
                        {experiment.participants ? 
                          `${experiment.participants.control + experiment.participants.test}` : '0'}
                      </div>
                    </div>
                    <div>
                      <div className="text-sm text-gray-600">Traffic Split</div>
                      <div className="font-semibold">{Math.round(experiment.traffic_split * 100)}% test</div>
                    </div>
                    <div>
                      <div className="text-sm text-gray-600">Primary Metric</div>
                      <div className="font-semibold">{experiment.primary_metric}</div>
                    </div>
                    <div>
                      <div className="text-sm text-gray-600">Duration</div>
                      <div className="font-semibold">
                        {experiment.start_date ? 
                          `${Math.ceil((new Date() - new Date(experiment.start_date)) / (1000 * 60 * 60 * 24))} days` : 
                          'Not started'}
                      </div>
                    </div>
                  </div>
                  
                  {experiment.algorithms && (
                    <div className="mt-4 pt-4 border-t">
                      <div className="grid grid-cols-2 gap-4 text-sm">
                        <div>
                          <span className="text-gray-600">Control:</span> {experiment.algorithms.control}
                        </div>
                        <div>
                          <span className="text-gray-600">Test:</span> {experiment.algorithms.test}
                        </div>
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>
            ))}
          </div>

          {experiments.length === 0 && (
            <Card>
              <CardContent className="text-center py-8">
                <Target className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-600 mb-4">No A/B test experiments yet</p>
                <Button onClick={() => setShowCreateDialog(true)}>
                  Create Your First Experiment
                </Button>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="results" className="space-y-4">
          {experimentResults ? (
            <div className="space-y-6">
              {/* Results Header */}
              <Card>
                <CardHeader>
                  <CardTitle>{experimentResults.name} - Results</CardTitle>
                  <p className="text-gray-600">{calculateSignificance(experimentResults)}</p>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <div className="text-center">
                      <div className="text-2xl font-bold text-blue-600">
                        {experimentResults.participants?.total || 0}
                      </div>
                      <div className="text-sm text-gray-600">Total Participants</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-green-600">
                        {experimentResults.metrics?.lift?.toFixed(2) || 0}%
                      </div>
                      <div className="text-sm text-gray-600">Lift</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-purple-600">
                        {Math.round((experimentResults.metrics?.statistical_significance || 0) * 100)}%
                      </div>
                      <div className="text-sm text-gray-600">Confidence</div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Conversion Rates Comparison */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <Card>
                  <CardHeader>
                    <CardTitle>Conversion Rates</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <ResponsiveContainer width="100%" height={300}>
                      <BarChart data={[
                        {
                          name: 'Control',
                          rate: (experimentResults.metrics?.control_conversion_rate || 0) * 100,
                          participants: experimentResults.participants?.control || 0
                        },
                        {
                          name: 'Test',
                          rate: (experimentResults.metrics?.test_conversion_rate || 0) * 100,
                          participants: experimentResults.participants?.test || 0
                        }
                      ]}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="name" />
                        <YAxis />
                        <Tooltip formatter={(value, name) => [`${value.toFixed(2)}%`, 'Conversion Rate']} />
                        <Bar dataKey="rate" fill="#8884d8" />
                      </BarChart>
                    </ResponsiveContainer>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle>Participant Distribution</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <ResponsiveContainer width="100%" height={300}>
                      <PieChart>
                        <Pie
                          data={[
                            { name: 'Control', value: experimentResults.participants?.control || 0 },
                            { name: 'Test', value: experimentResults.participants?.test || 0 }
                          ]}
                          cx="50%"
                          cy="50%"
                          labelLine={false}
                          label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                          outerRadius={80}
                          fill="#8884d8"
                          dataKey="value"
                        >
                          {[0, 1].map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                          ))}
                        </Pie>
                        <Tooltip />
                      </PieChart>
                    </ResponsiveContainer>
                  </CardContent>
                </Card>
              </div>
            </div>
          ) : (
            <Card>
              <CardContent className="text-center py-8">
                <p className="text-gray-600">Select an experiment to view results</p>
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default ABTestingDashboard;