import React, { useState, useEffect, useRef } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/Card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/Tabs';
import { Button } from '../ui/Button';
import { Badge } from '../ui/Badge';
import { Alert, AlertDescription } from '../ui/Alert';
import { 
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  AreaChart, Area, BarChart, Bar, PieChart, Pie, Cell 
} from 'recharts';
import { 
  Activity, AlertTriangle, CheckCircle, XCircle, Clock, 
  Cpu, HardDrive, Wifi, Database, Zap, TrendingUp, TrendingDown 
} from 'lucide-react';
import { analyticsAPI } from '../../services/analyticsAPI';

const PerformanceMonitoringDashboard = () => {
  const [realTimeMetrics, setRealTimeMetrics] = useState(null);
  const [performanceAlerts, setPerformanceAlerts] = useState([]);
  const [systemHealth, setSystemHealth] = useState(null);
  const [agentPerformance, setAgentPerformance] = useState({});
  const [historicalData, setHistoricalData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const intervalRef = useRef(null);

  useEffect(() => {
    loadPerformanceData();
    
    if (autoRefresh) {
      intervalRef.current = setInterval(loadRealTimeData, 30000); // Refresh every 30 seconds
    }
    
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [autoRefresh]);

  const loadPerformanceData = async () => {
    try {
      setLoading(true);
      setError(null);

      const [metricsResponse, alertsResponse, healthResponse, agentResponse] = await Promise.all([
        analyticsAPI.getRealTimeMetrics(),
        analyticsAPI.getPerformanceAlerts(24),
        analyticsAPI.getSystemHealth(),
        analyticsAPI.getAgentPerformance(null, 24)
      ]);

      setRealTimeMetrics(metricsResponse.data);
      setPerformanceAlerts(alertsResponse.data.alerts || []);
      setSystemHealth(healthResponse.data);
      setAgentPerformance(agentResponse.data);
      
      // Generate historical data for charts (mock data for demo)
      generateHistoricalData();
      
    } catch (err) {
      console.error('Error loading performance data:', err);
      setError('Failed to load performance monitoring data');
    } finally {
      setLoading(false);
    }
  };

  const loadRealTimeData = async () => {
    try {
      const [metricsResponse, alertsResponse] = await Promise.all([
        analyticsAPI.getRealTimeMetrics(),
        analyticsAPI.getPerformanceAlerts(1) // Last hour alerts
      ]);

      setRealTimeMetrics(metricsResponse.data);
      
      // Only update alerts if there are new ones
      const newAlerts = alertsResponse.data.alerts || [];
      if (newAlerts.length > 0) {
        setPerformanceAlerts(prev => [...newAlerts, ...prev].slice(0, 50));
      }
      
    } catch (err) {
      console.error('Error loading real-time data:', err);
    }
  };

  const generateHistoricalData = () => {
    // Generate mock historical data for the last 24 hours
    const data = [];
    const now = new Date();
    
    for (let i = 23; i >= 0; i--) {
      const time = new Date(now.getTime() - i * 60 * 60 * 1000);
      data.push({
        time: time.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        cpu: Math.random() * 80 + 10,
        memory: Math.random() * 70 + 20,
        responseTime: Math.random() * 1000 + 200,
        errorRate: Math.random() * 5,
        requests: Math.floor(Math.random() * 1000 + 100)
      });
    }
    
    setHistoricalData(data);
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'healthy': return 'text-green-600';
      case 'warning': return 'text-yellow-600';
      case 'critical': return 'text-red-600';
      default: return 'text-gray-600';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'healthy': return <CheckCircle className="h-4 w-4 text-green-600" />;
      case 'warning': return <AlertTriangle className="h-4 w-4 text-yellow-600" />;
      case 'critical': return <XCircle className="h-4 w-4 text-red-600" />;
      default: return <Activity className="h-4 w-4 text-gray-600" />;
    }
  };

  const getSeverityBadge = (severity) => {
    const colors = {
      high: 'bg-red-100 text-red-800',
      medium: 'bg-yellow-100 text-yellow-800',
      low: 'bg-blue-100 text-blue-800'
    };
    
    return (
      <Badge className={colors[severity] || colors.low}>
        {severity?.toUpperCase() || 'LOW'}
      </Badge>
    );
  };

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
        <Button onClick={loadPerformanceData}>Retry</Button>
      </div>
    );
  }

  const systemMetrics = realTimeMetrics?.system || {};
  const agentMetrics = realTimeMetrics?.agents || {};

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Performance Monitoring</h1>
          <p className="text-gray-600">Real-time system and AI agent performance metrics</p>
        </div>
        <div className="flex gap-4">
          <Button
            variant={autoRefresh ? "default" : "outline"}
            onClick={() => setAutoRefresh(!autoRefresh)}
          >
            {autoRefresh ? 'Auto-refresh ON' : 'Auto-refresh OFF'}
          </Button>
          <Button onClick={loadPerformanceData}>
            Refresh Now
          </Button>
        </div>
      </div>

      {/* System Health Overview */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Activity className="h-5 w-5" />
            System Health Overview
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="flex items-center space-x-3">
              {getStatusIcon(systemHealth?.overall_status)}
              <div>
                <div className="font-semibold">Overall Status</div>
                <div className={`text-sm ${getStatusColor(systemHealth?.overall_status)}`}>
                  {systemHealth?.overall_status?.toUpperCase() || 'UNKNOWN'}
                </div>
              </div>
            </div>
            
            {systemHealth?.components && Object.entries(systemHealth.components).map(([component, status]) => (
              <div key={component} className="flex items-center space-x-3">
                {getStatusIcon(status)}
                <div>
                  <div className="font-semibold">{component.replace('_', ' ').toUpperCase()}</div>
                  <div className={`text-sm ${getStatusColor(status)}`}>
                    {status?.toUpperCase() || 'UNKNOWN'}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Real-time Metrics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">CPU Usage</CardTitle>
            <Cpu className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{systemMetrics.cpu_usage?.toFixed(1) || 0}%</div>
            <div className="w-full bg-gray-200 rounded-full h-2 mt-2">
              <div 
                className={`h-2 rounded-full ${
                  (systemMetrics.cpu_usage || 0) > 80 ? 'bg-red-600' : 
                  (systemMetrics.cpu_usage || 0) > 60 ? 'bg-yellow-600' : 'bg-green-600'
                }`}
                style={{ width: `${Math.min(systemMetrics.cpu_usage || 0, 100)}%` }}
              ></div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Memory Usage</CardTitle>
            <HardDrive className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{systemMetrics.memory_usage?.toFixed(1) || 0}%</div>
            <div className="w-full bg-gray-200 rounded-full h-2 mt-2">
              <div 
                className={`h-2 rounded-full ${
                  (systemMetrics.memory_usage || 0) > 85 ? 'bg-red-600' : 
                  (systemMetrics.memory_usage || 0) > 70 ? 'bg-yellow-600' : 'bg-green-600'
                }`}
                style={{ width: `${Math.min(systemMetrics.memory_usage || 0, 100)}%` }}
              ></div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Response Time</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{systemMetrics.response_time?.toFixed(0) || 0}ms</div>
            <p className="text-xs text-muted-foreground">
              {(systemMetrics.response_time || 0) < 1000 ? 'Excellent' : 
               (systemMetrics.response_time || 0) < 2000 ? 'Good' : 'Needs attention'}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Error Rate</CardTitle>
            <AlertTriangle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{systemMetrics.error_rate?.toFixed(2) || 0}%</div>
            <p className="text-xs text-muted-foreground">
              {(systemMetrics.error_rate || 0) < 1 ? 'Excellent' : 
               (systemMetrics.error_rate || 0) < 5 ? 'Good' : 'High'}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Main Content Tabs */}
      <Tabs defaultValue="metrics" className="space-y-4">
        <TabsList>
          <TabsTrigger value="metrics">System Metrics</TabsTrigger>
          <TabsTrigger value="agents">AI Agents</TabsTrigger>
          <TabsTrigger value="alerts">Alerts</TabsTrigger>
        </TabsList>

        <TabsContent value="metrics" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* CPU and Memory Chart */}
            <Card>
              <CardHeader>
                <CardTitle>System Resources (24h)</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <AreaChart data={historicalData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="time" />
                    <YAxis />
                    <Tooltip />
                    <Area 
                      type="monotone" 
                      dataKey="cpu" 
                      stackId="1" 
                      stroke="#8884d8" 
                      fill="#8884d8" 
                      name="CPU %"
                    />
                    <Area 
                      type="monotone" 
                      dataKey="memory" 
                      stackId="2" 
                      stroke="#82ca9d" 
                      fill="#82ca9d" 
                      name="Memory %"
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            {/* Response Time Chart */}
            <Card>
              <CardHeader>
                <CardTitle>Response Time & Error Rate</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={historicalData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="time" />
                    <YAxis yAxisId="left" />
                    <YAxis yAxisId="right" orientation="right" />
                    <Tooltip />
                    <Line 
                      yAxisId="left"
                      type="monotone" 
                      dataKey="responseTime" 
                      stroke="#ffc658" 
                      name="Response Time (ms)"
                    />
                    <Line 
                      yAxisId="right"
                      type="monotone" 
                      dataKey="errorRate" 
                      stroke="#ff7300" 
                      name="Error Rate (%)"
                    />
                  </LineChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>

          {/* Request Volume */}
          <Card>
            <CardHeader>
              <CardTitle>Request Volume (24h)</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={historicalData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="time" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="requests" fill="#8884d8" name="Requests" />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="agents" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {Object.entries(agentMetrics).map(([agentName, metrics]) => (
              <Card key={agentName}>
                <CardHeader>
                  <CardTitle className="flex items-center justify-between">
                    <span>{agentName.replace('_', ' ').toUpperCase()}</span>
                    {getStatusIcon(metrics.status)}
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span>Success Rate</span>
                      <span className="font-semibold">{metrics.success_rate?.toFixed(1) || 0}%</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div 
                        className={`h-2 rounded-full ${
                          (metrics.success_rate || 0) >= 95 ? 'bg-green-600' : 
                          (metrics.success_rate || 0) >= 90 ? 'bg-yellow-600' : 'bg-red-600'
                        }`}
                        style={{ width: `${Math.min(metrics.success_rate || 0, 100)}%` }}
                      ></div>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <div className="text-gray-600">Response Time</div>
                      <div className="font-semibold">{metrics.response_time?.toFixed(0) || 0}ms</div>
                    </div>
                    <div>
                      <div className="text-gray-600">CPU Usage</div>
                      <div className="font-semibold">{metrics.cpu_usage?.toFixed(1) || 0}%</div>
                    </div>
                  </div>

                  <div className="text-sm">
                    <div className="text-gray-600">Memory Usage</div>
                    <div className="font-semibold">{metrics.memory_usage?.toFixed(1) || 0} MB</div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>

          {Object.keys(agentMetrics).length === 0 && (
            <Card>
              <CardContent className="text-center py-8">
                <p className="text-gray-600">No agent performance data available</p>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="alerts" className="space-y-4">
          <div className="space-y-4">
            {performanceAlerts.map((alert, index) => (
              <Alert key={index} className={`border-l-4 ${
                alert.severity === 'high' ? 'border-l-red-500' : 
                alert.severity === 'medium' ? 'border-l-yellow-500' : 'border-l-blue-500'
              }`}>
                <div className="flex items-start justify-between">
                  <div className="flex items-start space-x-3">
                    <AlertTriangle className={`h-4 w-4 mt-0.5 ${
                      alert.severity === 'high' ? 'text-red-600' : 
                      alert.severity === 'medium' ? 'text-yellow-600' : 'text-blue-600'
                    }`} />
                    <div>
                      <AlertDescription className="font-medium">
                        {alert.message}
                      </AlertDescription>
                      <div className="text-sm text-gray-600 mt-1">
                        {alert.type === 'agent' && `Agent: ${alert.agent}`}
                        {alert.metric && ` • Metric: ${alert.metric}`}
                        {alert.value && ` • Value: ${alert.value}`}
                      </div>
                      <div className="text-xs text-gray-500 mt-1">
                        {new Date(alert.timestamp).toLocaleString()}
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    {getSeverityBadge(alert.severity)}
                  </div>
                </div>
              </Alert>
            ))}
          </div>

          {performanceAlerts.length === 0 && (
            <Card>
              <CardContent className="text-center py-8">
                <CheckCircle className="h-12 w-12 text-green-600 mx-auto mb-4" />
                <p className="text-gray-600">No performance alerts in the last 24 hours</p>
                <p className="text-sm text-gray-500 mt-2">System is running smoothly</p>
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default PerformanceMonitoringDashboard;