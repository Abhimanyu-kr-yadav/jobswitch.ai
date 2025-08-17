import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/Card';
import { Button } from '../ui/Button';
import { Badge } from '../ui/Badge';
import { Alert, AlertDescription } from '../ui/Alert';
import { Progress } from '../ui/Progress';
import { 
  Target, 
  TrendingUp, 
  AlertTriangle, 
  CheckCircle, 
  BarChart3,
  Lightbulb,
  Star,
  Clock,
  Briefcase
} from 'lucide-react';
import { resumeAPI } from '../../services/resumeAPI';

const AcceptanceProbabilityCalculator = ({ resumeId, jobId, onClose }) => {
  const [probabilityData, setProbabilityData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (resumeId && jobId) {
      calculateProbability();
    }
  }, [resumeId, jobId]);

  const calculateProbability = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await resumeAPI.calculateAcceptanceProbability(resumeId, jobId);
      if (response.success) {
        setProbabilityData(response.data);
      }
    } catch (err) {
      setError('Failed to calculate acceptance probability');
      console.error('Error calculating probability:', err);
    } finally {
      setLoading(false);
    }
  };

  const getProbabilityColor = (probability) => {
    if (probability >= 0.8) return 'text-green-600';
    if (probability >= 0.6) return 'text-yellow-600';
    if (probability >= 0.4) return 'text-orange-600';
    return 'text-red-600';
  };

  const getProbabilityBgColor = (probability) => {
    if (probability >= 0.8) return 'bg-green-100';
    if (probability >= 0.6) return 'bg-yellow-100';
    if (probability >= 0.4) return 'bg-orange-100';
    return 'bg-red-100';
  };

  const getConfidenceIcon = (confidence) => {
    switch (confidence.toLowerCase()) {
      case 'high':
        return <CheckCircle className="w-5 h-5 text-green-600" />;
      case 'medium':
        return <BarChart3 className="w-5 h-5 text-yellow-600" />;
      case 'low':
        return <AlertTriangle className="w-5 h-5 text-red-600" />;
      default:
        return <BarChart3 className="w-5 h-5 text-gray-600" />;
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-2 text-gray-600">Calculating acceptance probability...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <Alert variant="destructive">
        <AlertTriangle className="h-4 w-4" />
        <AlertDescription>{error}</AlertDescription>
      </Alert>
    );
  }

  if (!probabilityData) {
    return (
      <Card>
        <CardContent className="text-center py-12">
          <Target className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No Data Available</h3>
          <p className="text-gray-600">Unable to calculate acceptance probability</p>
        </CardContent>
      </Card>
    );
  }

  const analysis = probabilityData.probability_analysis;
  const probability = analysis.acceptance_probability;

  return (
    <div className="max-w-4xl mx-auto p-6">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h2 className="text-2xl font-bold text-gray-900 flex items-center">
            <Target className="w-6 h-6 mr-2" />
            Acceptance Probability Analysis
          </h2>
          <p className="text-gray-600">AI-powered assessment of your resume's success probability</p>
        </div>
        
        <Button variant="outline" onClick={onClose}>
          Close
        </Button>
      </div>

      {/* Main Probability Display */}
      <Card className={`mb-6 ${getProbabilityBgColor(probability)}`}>
        <CardContent className="text-center py-8">
          <div className={`text-6xl font-bold mb-2 ${getProbabilityColor(probability)}`}>
            {Math.round(probability * 100)}%
          </div>
          <div className="text-xl text-gray-700 mb-4">Acceptance Probability</div>
          
          <div className="flex items-center justify-center gap-2 mb-4">
            {getConfidenceIcon(analysis.confidence_level)}
            <span className="text-lg font-medium text-gray-700">
              {analysis.confidence_level} Confidence
            </span>
          </div>

          <Progress 
            value={probability * 100} 
            className="w-full max-w-md mx-auto h-3"
          />
          
          <div className="mt-4 text-gray-600">
            <Clock className="w-4 h-4 inline mr-1" />
            Calculated on {new Date(probabilityData.calculated_at).toLocaleDateString()}
          </div>
        </CardContent>
      </Card>

      {/* Overall Assessment */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle className="flex items-center">
            <Briefcase className="w-5 h-5 mr-2" />
            Overall Assessment
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-gray-700 text-lg leading-relaxed">
            {analysis.overall_assessment}
          </p>
        </CardContent>
      </Card>

      {/* Matching Factors */}
      {analysis.matching_factors && analysis.matching_factors.length > 0 && (
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="flex items-center">
              <BarChart3 className="w-5 h-5 mr-2" />
              Matching Factors Analysis
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {analysis.matching_factors.map((factor, index) => (
                <div key={index} className="border rounded-lg p-4">
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="font-semibold text-gray-900">{factor.factor}</h4>
                    <div className="flex items-center gap-2">
                      <Badge variant="outline">
                        Weight: {Math.round(factor.weight * 100)}%
                      </Badge>
                      <Badge variant={
                        factor.score >= 0.8 ? 'success' :
                        factor.score >= 0.6 ? 'warning' : 'destructive'
                      }>
                        {Math.round(factor.score * 100)}%
                      </Badge>
                    </div>
                  </div>
                  
                  <Progress 
                    value={factor.score * 100} 
                    className="mb-2 h-2"
                  />
                  
                  <p className="text-sm text-gray-600">{factor.details}</p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      <div className="grid md:grid-cols-2 gap-6">
        {/* Improvement Suggestions */}
        {analysis.improvement_suggestions && analysis.improvement_suggestions.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center text-green-700">
                <Lightbulb className="w-5 h-5 mr-2" />
                Improvement Suggestions
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="space-y-3">
                {analysis.improvement_suggestions.map((suggestion, index) => (
                  <li key={index} className="flex items-start gap-2">
                    <TrendingUp className="w-4 h-4 text-green-600 mt-0.5 flex-shrink-0" />
                    <span className="text-gray-700">{suggestion}</span>
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>
        )}

        {/* Risk Factors */}
        {analysis.risk_factors && analysis.risk_factors.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center text-red-700">
                <AlertTriangle className="w-5 h-5 mr-2" />
                Risk Factors
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="space-y-3">
                {analysis.risk_factors.map((risk, index) => (
                  <li key={index} className="flex items-start gap-2">
                    <AlertTriangle className="w-4 h-4 text-red-600 mt-0.5 flex-shrink-0" />
                    <span className="text-gray-700">{risk}</span>
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>
        )}
      </div>

      {/* Action Buttons */}
      <div className="mt-6 flex justify-center gap-4">
        <Button 
          onClick={calculateProbability}
          disabled={loading}
          className="bg-blue-600 hover:bg-blue-700"
        >
          <Target className="w-4 h-4 mr-2" />
          Recalculate
        </Button>
        
        <Button 
          variant="outline"
          onClick={() => {
            // Navigate to resume optimizer with suggestions
            console.log('Navigate to optimizer with suggestions');
          }}
        >
          <Star className="w-4 h-4 mr-2" />
          Optimize Resume
        </Button>
      </div>

      {/* Disclaimer */}
      <Card className="mt-6 bg-gray-50">
        <CardContent className="text-center py-4">
          <p className="text-sm text-gray-600">
            <strong>Disclaimer:</strong> This probability is an AI-generated estimate based on resume content and job requirements. 
            Actual hiring decisions depend on many factors not captured in this analysis.
          </p>
        </CardContent>
      </Card>
    </div>
  );
};

export default AcceptanceProbabilityCalculator;