import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/Card';
import { Button } from '../ui/Button';
import { Input } from '../ui/Input';
import { Label } from '../ui/Label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/Select';
import { Badge } from '../ui/Badge';
import { Textarea } from '../ui/Textarea';
import { BookOpen, Clock, Target, Lightbulb, Copy, Check } from 'lucide-react';
import { interviewAPI } from '../../services/interviewAPI';

const QuestionGenerator = () => {
  const [formData, setFormData] = useState({
    job_role: '',
    company: '',
    skills: '',
    question_count: 10,
    categories: ['behavioral', 'technical']
  });
  
  const [questions, setQuestions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [copiedQuestions, setCopiedQuestions] = useState(new Set());

  const categories = [
    { value: 'behavioral', label: 'Behavioral' },
    { value: 'technical', label: 'Technical' },
    { value: 'company', label: 'Company-specific' },
    { value: 'general', label: 'General' }
  ];

  const handleInputChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleCategoryToggle = (category) => {
    setFormData(prev => ({
      ...prev,
      categories: prev.categories.includes(category)
        ? prev.categories.filter(c => c !== category)
        : [...prev.categories, category]
    }));
  };

  const handleGenerateQuestions = async () => {
    if (!formData.job_role.trim()) {
      setError('Job role is required');
      return;
    }

    if (formData.categories.length === 0) {
      setError('Please select at least one question category');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      
      const skillsArray = formData.skills
        ? formData.skills.split(',').map(s => s.trim()).filter(s => s)
        : [];

      const response = await interviewAPI.generateQuestions({
        job_role: formData.job_role,
        company: formData.company,
        skills: skillsArray,
        question_count: formData.question_count,
        categories: formData.categories
      });

      if (response.success) {
        setQuestions(response.data.questions);
      } else {
        setError('Failed to generate questions');
      }
    } catch (err) {
      setError('Failed to generate questions. Please try again.');
      console.error('Error generating questions:', err);
    } finally {
      setLoading(false);
    }
  };

  const copyQuestion = async (questionId, questionText) => {
    try {
      await navigator.clipboard.writeText(questionText);
      setCopiedQuestions(prev => new Set([...prev, questionId]));
      setTimeout(() => {
        setCopiedQuestions(prev => {
          const newSet = new Set(prev);
          newSet.delete(questionId);
          return newSet;
        });
      }, 2000);
    } catch (err) {
      console.error('Failed to copy question:', err);
    }
  };

  const getDifficultyColor = (difficulty) => {
    switch (difficulty) {
      case 'easy': return 'bg-green-100 text-green-800';
      case 'medium': return 'bg-yellow-100 text-yellow-800';
      case 'hard': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getCategoryColor = (category) => {
    switch (category) {
      case 'behavioral': return 'bg-blue-100 text-blue-800';
      case 'technical': return 'bg-purple-100 text-purple-800';
      case 'company': return 'bg-orange-100 text-orange-800';
      case 'general': return 'bg-gray-100 text-gray-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <BookOpen className="h-5 w-5" />
            Generate Interview Questions
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="job_role">Job Role *</Label>
              <Input
                id="job_role"
                placeholder="e.g., Software Engineer, Product Manager"
                value={formData.job_role}
                onChange={(e) => handleInputChange('job_role', e.target.value)}
              />
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="company">Company (Optional)</Label>
              <Input
                id="company"
                placeholder="e.g., Google, Microsoft"
                value={formData.company}
                onChange={(e) => handleInputChange('company', e.target.value)}
              />
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="skills">Relevant Skills (Optional)</Label>
            <Input
              id="skills"
              placeholder="e.g., JavaScript, Python, React (comma-separated)"
              value={formData.skills}
              onChange={(e) => handleInputChange('skills', e.target.value)}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="question_count">Number of Questions</Label>
            <Select
              value={formData.question_count.toString()}
              onValueChange={(value) => handleInputChange('question_count', parseInt(value))}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {[5, 10, 15, 20].map(count => (
                  <SelectItem key={count} value={count.toString()}>
                    {count} questions
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label>Question Categories</Label>
            <div className="flex flex-wrap gap-2">
              {categories.map(category => (
                <Button
                  key={category.value}
                  variant={formData.categories.includes(category.value) ? "default" : "outline"}
                  size="sm"
                  onClick={() => handleCategoryToggle(category.value)}
                >
                  {category.label}
                </Button>
              ))}
            </div>
          </div>

          {error && (
            <div className="bg-red-50 border border-red-200 rounded-md p-4">
              <p className="text-red-800">{error}</p>
            </div>
          )}

          <Button
            onClick={handleGenerateQuestions}
            disabled={loading}
            className="w-full"
          >
            {loading ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                Generating Questions...
              </>
            ) : (
              'Generate Questions'
            )}
          </Button>
        </CardContent>
      </Card>

      {questions.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <span>Generated Questions ({questions.length})</span>
              <div className="text-sm text-gray-500">
                Generated for: {formData.job_role}
                {formData.company && ` at ${formData.company}`}
              </div>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {questions.map((question, index) => (
                <Card key={question.id} className="border-l-4 border-l-blue-500">
                  <CardContent className="p-4">
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-gray-700">Q{index + 1}</span>
                        <Badge className={getCategoryColor(question.category)}>
                          {question.category}
                        </Badge>
                        <Badge className={getDifficultyColor(question.difficulty)}>
                          {question.difficulty}
                        </Badge>
                        <div className="flex items-center gap-1 text-sm text-gray-500">
                          <Clock className="h-3 w-3" />
                          {Math.floor(question.time_limit / 60)}m
                        </div>
                      </div>
                      
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => copyQuestion(question.id, question.question)}
                      >
                        {copiedQuestions.has(question.id) ? (
                          <Check className="h-4 w-4 text-green-600" />
                        ) : (
                          <Copy className="h-4 w-4" />
                        )}
                      </Button>
                    </div>

                    <p className="text-gray-900 font-medium mb-3">
                      {question.question}
                    </p>

                    {question.key_points && question.key_points.length > 0 && (
                      <div className="mb-3">
                        <div className="flex items-center gap-2 mb-2">
                          <Target className="h-4 w-4 text-blue-600" />
                          <span className="text-sm font-medium text-gray-700">Key Points to Address:</span>
                        </div>
                        <ul className="text-sm text-gray-600 space-y-1">
                          {question.key_points.map((point, idx) => (
                            <li key={idx} className="flex items-start gap-2">
                              <div className="w-1.5 h-1.5 bg-blue-500 rounded-full mt-2 flex-shrink-0"></div>
                              {point}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {question.answer_structure && (
                      <div>
                        <div className="flex items-center gap-2 mb-2">
                          <Lightbulb className="h-4 w-4 text-yellow-600" />
                          <span className="text-sm font-medium text-gray-700">Answer Structure:</span>
                        </div>
                        <p className="text-sm text-gray-600 bg-yellow-50 p-3 rounded-md">
                          {question.answer_structure}
                        </p>
                      </div>
                    )}
                  </CardContent>
                </Card>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default QuestionGenerator;