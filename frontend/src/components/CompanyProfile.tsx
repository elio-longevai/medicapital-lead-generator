
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { 
  ArrowLeft, 
  ExternalLink, 
  Mail, 
  Phone, 
  MapPin, 
  Building2, 
  Users, 
  Calendar,
  TrendingUp,
  Star,
  CheckCircle,
  AlertCircle,
  Clock,
  Target,
  Euro,
  FileText,
  MessageSquare
} from "lucide-react";

export const CompanyProfile = ({ company, onBack }) => {
  if (!company) return null;

  const getStatusBadge = (status) => {
    const variants = {
      "Qualified": "bg-green-100 text-green-800",
      "In Review": "bg-yellow-100 text-yellow-800",
      "Discovered": "bg-gray-100 text-gray-800"
    };
    return <Badge className={variants[status]}>{status}</Badge>;
  };

  const getScoreColor = (score) => {
    if (score >= 85) return "text-green-600";
    if (score >= 70) return "text-yellow-600";
    return "text-red-600";
  };

  const qualificationAreas = [
    {
      name: "Financial Stability",
      score: company.qualificationScore?.financialStability || 0,
      icon: Euro,
      description: "Company financial health and payment capacity"
    },
    {
      name: "Equipment Need",
      score: company.qualificationScore?.equipmentNeed || 0,
      icon: Target,
      description: "Alignment with our equipment offerings"
    },
    {
      name: "Timing",
      score: company.qualificationScore?.timing || 0,
      icon: Clock,
      description: "Urgency and timeline for equipment acquisition"
    },
    {
      name: "Decision Authority",
      score: company.qualificationScore?.decisionAuthority || 0,
      icon: Users,
      description: "Access to key decision makers"
    }
  ];

  const activities = [
    {
      type: "note",
      title: "Initial qualification completed",
      description: "Company meets all basic criteria for equipment leasing",
      timestamp: "2 hours ago",
      icon: CheckCircle,
      color: "text-green-600"
    },
    {
      type: "research",
      title: "Company research updated",
      description: "Added recent news about expansion plans",
      timestamp: "4 hours ago",
      icon: FileText,
      color: "text-blue-600"
    },
    {
      type: "discovery",
      title: "Lead discovered",
      description: "Found through industry database search",
      timestamp: "1 day ago",
      icon: Star,
      color: "text-yellow-600"
    }
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between py-6">
            <div className="flex items-center">
              <Button variant="ghost" onClick={onBack} className="mr-4">
                <ArrowLeft className="h-4 w-4 mr-2" />
                Back to Leads
              </Button>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">
                  {company.company}
                </h1>
                <p className="text-gray-600 flex items-center mt-1">
                  <MapPin className="h-4 w-4 mr-1" />
                  {company.location} • {company.industry}
                </p>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <div className="text-right">
                <div className={`text-2xl font-bold ${getScoreColor(company.score)}`}>
                  {company.score}
                </div>
                <div className="text-sm text-gray-500">Lead Score</div>
              </div>
              {getStatusBadge(company.status)}
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Main Content */}
          <div className="lg:col-span-2 space-y-6">
            <Tabs defaultValue="overview" className="space-y-6">
              <TabsList>
                <TabsTrigger value="overview">Overview</TabsTrigger>
                <TabsTrigger value="qualification">Qualification</TabsTrigger>
                <TabsTrigger value="research">Research</TabsTrigger>
                <TabsTrigger value="outreach">Outreach</TabsTrigger>
              </TabsList>

              <TabsContent value="overview" className="space-y-6">
                {/* Company Information */}
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center">
                      <Building2 className="h-5 w-5 mr-2" />
                      Company Information
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <div className="space-y-4">
                        <div>
                          <label className="text-sm font-medium text-gray-500">Industry</label>
                          <p className="mt-1 text-gray-900">{company.industry}</p>
                        </div>
                        <div>
                          <label className="text-sm font-medium text-gray-500">Employees</label>
                          <p className="mt-1 text-gray-900">{company.employees}</p>
                        </div>
                        <div>
                          <label className="text-sm font-medium text-gray-500">Equipment Need</label>
                          <p className="mt-1 text-gray-900">{company.equipmentNeed}</p>
                        </div>
                      </div>
                      <div className="space-y-4">
                        <div>
                          <label className="text-sm font-medium text-gray-500">Estimated Value</label>
                          <p className="mt-1 text-2xl font-bold text-gray-900">{company.estimatedValue}</p>
                        </div>
                        <div>
                          <label className="text-sm font-medium text-gray-500">Website</label>
                          <div className="mt-1 flex items-center">
                            <a 
                              href={`${company.website}`} 
                              target="_blank" 
                              rel="noopener noreferrer"
                              className="text-blue-600 hover:text-blue-800 flex items-center"
                            >
                              {company.website}
                              <ExternalLink className="h-4 w-4 ml-1" />
                            </a>
                          </div>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                {/* Recent News */}
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center">
                      <TrendingUp className="h-5 w-5 mr-2" />
                      Recent News & Insights
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      <div className="p-4 bg-blue-50 rounded-lg">
                        <h4 className="font-medium text-blue-900 mb-2">Latest Update</h4>
                        <p className="text-blue-800">{company.recentNews}</p>
                        <p className="text-sm text-blue-600 mt-2">Source: Company website • {company.lastActivity}</p>
                      </div>
                      <div>
                        <h4 className="font-medium text-gray-900 mb-2">Analysis Notes</h4>
                        <p className="text-gray-700">{company.notes}</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </TabsContent>

              <TabsContent value="qualification" className="space-y-6">
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center">
                      <Target className="h-5 w-5 mr-2" />
                      Qualification Assessment
                    </CardTitle>
                    <CardDescription>
                      AI-driven qualification across key criteria
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-6">
                      {qualificationAreas.map((area, index) => (
                        <div key={index}>
                          <div className="flex items-center justify-between mb-2">
                            <div className="flex items-center">
                              <area.icon className="h-4 w-4 mr-2 text-gray-600" />
                              <span className="font-medium text-gray-900">{area.name}</span>
                            </div>
                            <span className={`font-bold ${getScoreColor(area.score)}`}>
                              {area.score}%
                            </span>
                          </div>
                          <Progress value={area.score} className="h-2 mb-2" />
                          <p className="text-sm text-gray-600">{area.description}</p>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle>Qualification Summary</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      <div className="text-center p-4 bg-green-50 rounded-lg">
                        <CheckCircle className="h-8 w-8 text-green-600 mx-auto mb-2" />
                        <p className="font-medium text-green-900">Strengths</p>
                        <p className="text-sm text-green-700">Strong financial position, clear equipment need</p>
                      </div>
                      <div className="text-center p-4 bg-yellow-50 rounded-lg">
                        <AlertCircle className="h-8 w-8 text-yellow-600 mx-auto mb-2" />
                        <p className="font-medium text-yellow-900">Considerations</p>
                        <p className="text-sm text-yellow-700">Timing may need validation</p>
                      </div>
                      <div className="text-center p-4 bg-blue-50 rounded-lg">
                        <Target className="h-8 w-8 text-blue-600 mx-auto mb-2" />
                        <p className="font-medium text-blue-900">Recommendation</p>
                        <p className="text-sm text-blue-700">Proceed with qualified outreach</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </TabsContent>

              <TabsContent value="research" className="space-y-6">
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center">
                      <FileText className="h-5 w-5 mr-2" />
                      Research & Intelligence
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      <div>
                        <h4 className="font-medium text-gray-900 mb-2">Market Position</h4>
                        <p className="text-gray-700">
                          Leading player in their sector with strong growth trajectory. 
                          Company shows consistent investment in modernization and expansion.
                        </p>
                      </div>
                      <div>
                        <h4 className="font-medium text-gray-900 mb-2">Financial Indicators</h4>
                        <ul className="list-disc list-inside text-gray-700 space-y-1">
                          <li>Revenue growth of 15% year-over-year</li>
                          <li>Recent funding rounds indicate healthy cash flow</li>
                          <li>Active investment in new equipment and facilities</li>
                        </ul>
                      </div>
                      <div>
                        <h4 className="font-medium text-gray-900 mb-2">Competitive Landscape</h4>
                        <p className="text-gray-700">
                          Operating in a competitive but growing market. Equipment modernization 
                          is a key differentiator for maintaining market position.
                        </p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </TabsContent>

              <TabsContent value="outreach" className="space-y-6">
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center">
                      <MessageSquare className="h-5 w-5 mr-2" />
                      Outreach Strategy
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      <div className="p-4 border border-gray-200 rounded-lg">
                        <h4 className="font-medium text-gray-900 mb-2">Recommended Approach</h4>
                        <p className="text-gray-700 mb-3">
                          Focus on equipment modernization benefits and financial flexibility. 
                          Highlight successful implementations in similar healthcare facilities.
                        </p>
                        <div className="flex space-x-2">
                          <Button size="sm">
                            <Mail className="h-4 w-4 mr-2" />
                            Generate Email
                          </Button>
                          <Button variant="outline" size="sm">
                            <Phone className="h-4 w-4 mr-2" />
                            Schedule Call
                          </Button>
                        </div>
                      </div>
                      <div>
                        <h4 className="font-medium text-gray-900 mb-2">Key Messaging Points</h4>
                        <ul className="list-disc list-inside text-gray-700 space-y-1">
                          <li>Financial flexibility through leasing vs. capital expenditure</li>
                          <li>Complete service package including maintenance and support</li>
                          <li>Proven track record in healthcare equipment leasing</li>
                          <li>Alignment with their expansion and modernization goals</li>
                        </ul>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </TabsContent>
            </Tabs>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Contact Information */}
            <Card>
              <CardHeader>
                <CardTitle>Contact Information</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center">
                  <Mail className="h-4 w-4 mr-3 text-gray-400" />
                  <a 
                    href={`mailto:${company.email}`}
                    className="text-blue-600 hover:text-blue-800"
                  >
                    {company.email}
                  </a>
                </div>
                <div className="flex items-center">
                  <Phone className="h-4 w-4 mr-3 text-gray-400" />
                  <a 
                    href={`tel:${company.phone}`}
                    className="text-blue-600 hover:text-blue-800"
                  >
                    {company.phone}
                  </a>
                </div>
                <div className="flex items-center">
                  <ExternalLink className="h-4 w-4 mr-3 text-gray-400" />
                  <a 
                    href={`https://${company.website}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-blue-600 hover:text-blue-800"
                  >
                    Visit Website
                  </a>
                </div>
              </CardContent>
            </Card>

            {/* Activity Timeline */}
            <Card>
              <CardHeader>
                <CardTitle>Activity Timeline</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {activities.map((activity, index) => (
                    <div key={index} className="flex items-start">
                      <activity.icon className={`h-4 w-4 mt-1 mr-3 ${activity.color}`} />
                      <div className="flex-1">
                        <p className="text-sm font-medium text-gray-900">
                          {activity.title}
                        </p>
                        <p className="text-sm text-gray-600">
                          {activity.description}
                        </p>
                        <p className="text-xs text-gray-500 mt-1">
                          {activity.timestamp}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Quick Actions */}
            <Card>
              <CardHeader>
                <CardTitle>Quick Actions</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                <Button className="w-full" size="sm">
                  <Mail className="h-4 w-4 mr-2" />
                  Send Email
                </Button>
                <Button variant="outline" className="w-full" size="sm">
                  <Phone className="h-4 w-4 mr-2" />
                  Schedule Call
                </Button>
                <Button variant="outline" className="w-full" size="sm">
                  <FileText className="h-4 w-4 mr-2" />
                  Add Note
                </Button>
                <Button variant="outline" className="w-full" size="sm">
                  <Star className="h-4 w-4 mr-2" />
                  Mark as Priority
                </Button>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
};
