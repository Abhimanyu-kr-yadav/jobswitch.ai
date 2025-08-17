import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/Card';
import { Badge } from '../ui/Badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/Select';

const SkillsVisualization = ({ skills, skillsAnalysis }) => {
  const [filteredSkills, setFilteredSkills] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [selectedProficiency, setSelectedProficiency] = useState('all');

  const filterSkills = useCallback(() => {
    let filtered = skills || [];

    if (selectedCategory !== 'all') {
      filtered = filtered.filter(skill => skill.category === selectedCategory);
    }

    if (selectedProficiency !== 'all') {
      filtered = filtered.filter(skill => skill.proficiency === selectedProficiency);
    }

    setFilteredSkills(filtered);
  }, [skills, selectedCategory, selectedProficiency]);

  useEffect(() => {
    filterSkills();
  }, [filterSkills]);

  const getSkillsByCategory = () => {
    const categories = {};
    (skills || []).forEach(skill => {
      const category = skill.category || 'other';
      if (!categories[category]) {
        categories[category] = [];
      }
      categories[category].push(skill);
    });
    return categories;
  };

  const getProficiencyColor = (proficiency) => {
    switch (proficiency?.toLowerCase()) {
      case 'expert':
        return 'bg-green-100 text-green-800 border-green-200';
      case 'advanced':
        return 'bg-blue-100 text-blue-800 border-blue-200';
      case 'intermediate':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'beginner':
        return 'bg-gray-100 text-gray-800 border-gray-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getCategoryColor = (category) => {
    switch (category?.toLowerCase()) {
      case 'technical':
        return 'bg-purple-100 text-purple-800';
      case 'soft':
        return 'bg-green-100 text-green-800';
      case 'domain':
        return 'bg-blue-100 text-blue-800';
      case 'certifications':
        return 'bg-orange-100 text-orange-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const skillCategories = [...new Set((skills || []).map(skill => skill.category))];
  const proficiencyLevels = [...new Set((skills || []).map(skill => skill.proficiency))];

  return (
    <div className="space-y-6">
      {/* Filters */}
      <Card>
        <CardHeader>
          <CardTitle>Filter Skills</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-4">
            <div className="min-w-48">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Category
              </label>
              <Select value={selectedCategory} onValueChange={setSelectedCategory}>
                <SelectTrigger>
                  <SelectValue placeholder="Select category" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Categories</SelectItem>
                  {skillCategories.map(category => (
                    <SelectItem key={category} value={category}>
                      {category.charAt(0).toUpperCase() + category.slice(1)}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="min-w-48">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Proficiency
              </label>
              <Select value={selectedProficiency} onValueChange={setSelectedProficiency}>
                <SelectTrigger>
                  <SelectValue placeholder="Select proficiency" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Levels</SelectItem>
                  {proficiencyLevels.map(level => (
                    <SelectItem key={level} value={level}>
                      {level.charAt(0).toUpperCase() + level.slice(1)}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Skills Distribution Chart */}
      {skillsAnalysis?.skill_distribution && (
        <Card>
          <CardHeader>
            <CardTitle>Skills Distribution</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {Object.entries(skillsAnalysis.skill_distribution).map(([category, percentage]) => (
                <div key={category} className="space-y-2">
                  <div className="flex justify-between items-center">
                    <span className="text-sm font-medium capitalize">{category}</span>
                    <span className="text-sm text-gray-600">{percentage}%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                      style={{ width: `${percentage}%` }}
                    ></div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Skills by Category */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {Object.entries(getSkillsByCategory()).map(([category, categorySkills]) => (
          <Card key={category}>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Badge className={getCategoryColor(category)}>
                  {category.charAt(0).toUpperCase() + category.slice(1)}
                </Badge>
                <span className="text-sm text-gray-600">
                  ({categorySkills.length} skills)
                </span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {categorySkills.map((skill, index) => (
                  <div key={index} className="border rounded-lg p-3 bg-gray-50">
                    <div className="flex justify-between items-start mb-2">
                      <h4 className="font-semibold text-gray-900">{skill.name}</h4>
                      <Badge className={getProficiencyColor(skill.proficiency)}>
                        {skill.proficiency || 'Not specified'}
                      </Badge>
                    </div>
                    
                    <div className="text-sm text-gray-600 space-y-1">
                      {skill.subcategory && (
                        <p>Category: {skill.subcategory}</p>
                      )}
                      {skill.years_experience && (
                        <p>Experience: {skill.years_experience} years</p>
                      )}
                      {skill.source && (
                        <p>Source: {skill.source}</p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Filtered Skills List */}
      {(selectedCategory !== 'all' || selectedProficiency !== 'all') && (
        <Card>
          <CardHeader>
            <CardTitle>
              Filtered Skills ({filteredSkills.length} results)
            </CardTitle>
          </CardHeader>
          <CardContent>
            {filteredSkills.length > 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {filteredSkills.map((skill, index) => (
                  <div key={index} className="border rounded-lg p-3 bg-white">
                    <div className="flex justify-between items-start mb-2">
                      <h4 className="font-medium text-gray-900">{skill.name}</h4>
                      <Badge className={getProficiencyColor(skill.proficiency)}>
                        {skill.proficiency}
                      </Badge>
                    </div>
                    <div className="text-xs text-gray-500">
                      {skill.category} • {skill.subcategory}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-500 text-center py-8">
                No skills match the selected filters.
              </p>
            )}
          </CardContent>
        </Card>
      )}

      {/* Skills Radar Chart Placeholder */}
      <Card>
        <CardHeader>
          <CardTitle>Skills Proficiency Overview</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {['Expert', 'Advanced', 'Intermediate', 'Beginner'].map(level => {
              const count = (skills || []).filter(skill => 
                skill.proficiency?.toLowerCase() === level.toLowerCase()
              ).length;
              
              return (
                <div key={level} className="text-center p-4 border rounded-lg">
                  <div className={`text-2xl font-bold ${getProficiencyColor(level).split(' ')[1]}`}>
                    {count}
                  </div>
                  <div className="text-sm text-gray-600">{level}</div>
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* Skills Timeline */}
      {skills && skills.some(skill => skill.extracted_at) && (
        <Card>
          <CardHeader>
            <CardTitle>Recent Skills Added</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {skills
                .filter(skill => skill.extracted_at)
                .sort((a, b) => new Date(b.extracted_at) - new Date(a.extracted_at))
                .slice(0, 5)
                .map((skill, index) => (
                  <div key={index} className="flex items-center justify-between p-3 border rounded-lg">
                    <div>
                      <h4 className="font-medium">{skill.name}</h4>
                      <p className="text-sm text-gray-600">
                        {skill.category} • {skill.proficiency}
                      </p>
                    </div>
                    <div className="text-sm text-gray-500">
                      {new Date(skill.extracted_at).toLocaleDateString()}
                    </div>
                  </div>
                ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default SkillsVisualization;