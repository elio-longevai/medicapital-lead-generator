
import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { 
  TrendingUp, 
  Users, 
  Target, 
  Building2, 
  CheckCircle,
  Star,
  ArrowRight,
  Plus,
  Sparkles,
  Globe,
  Filter
} from "lucide-react";
import { LeadDatabase } from "@/components/LeadDatabase";
import { CompanyProfile } from "@/components/CompanyProfile";
import { QualificationWorkflow } from "@/components/QualificationWorkflow";

const Index = () => {
  const [activeTab, setActiveTab] = useState("dashboard");
  const [selectedCompany, setSelectedCompany] = useState(null);

  const dashboardMetrics = [
    {
      title: "Total Leads Discovered",
      value: "1,247",
      change: "+156 this week",
      changeType: "positive",
      icon: Users,
      description: "Across all target industries"
    },
    {
      title: "Target Industries",
      value: "3",
      change: "Healthcare, Beauty, Horeca",
      changeType: "neutral",
      icon: Target,
      description: "Defined ICPs with qualification criteria"
    },
    {
      title: "High-Quality Prospects",
      value: "342",
      change: "+47 this week",
      changeType: "positive",
      icon: TrendingUp,
      description: "Meeting initial qualification criteria"
    },
    {
      title: "Ready for Outreach",
      value: "156",
      change: "Data enriched & qualified",
      changeType: "positive",
      icon: Sparkles,
      description: "Prospects with complete profiles"
    }
  ];

  const recentLeads = [
    {
      id: 1,
      company: "Amsterdam Medical Center",
      industry: "Healthcare",
      score: 92,
      status: "Qualified",
      lastActivity: "2 hours ago",
      equipmentNeed: "Diagnostic Equipment",
      value: "€85,000",
      location: "Amsterdam, NL"
    },
    {
      id: 2,
      company: "Beauty Clinic Rotterdam",
      industry: "Beauty & Wellness",
      score: 88,
      status: "In Review",
      lastActivity: "4 hours ago",
      equipmentNeed: "Laser Systems",
      value: "€45,000",
      location: "Rotterdam, NL"
    },
    {
      id: 3,
      company: "TechMed Innovations",
      industry: "Healthcare",
      score: 94,
      status: "Qualified",
      lastActivity: "6 hours ago",
      equipmentNeed: "Laboratory Equipment",
      value: "€125,000",
      location: "Eindhoven, NL"
    }
  ];

  const getStatusBadge = (status) => {
    const variants = {
      "Qualified": "bg-emerald-100 text-emerald-800 border-emerald-200",
      "In Review": "bg-amber-100 text-amber-800 border-amber-200",
      "Discovered": "bg-slate-100 text-slate-800 border-slate-200"
    };
    return <Badge className={`${variants[status]} border font-medium`}>{status}</Badge>;
  };

  const getScoreColor = (score) => {
    if (score >= 85) return "text-emerald-600";
    if (score >= 70) return "text-amber-600";
    return "text-red-600";
  };

  if (selectedCompany) {
    return (
      <CompanyProfile 
        company={selectedCompany} 
        onBack={() => setSelectedCompany(null)} 
      />
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50">
      {/* Header */}
      <div className="bg-white/80 backdrop-blur-sm border-b border-slate-200/60">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-8">
            <div>
              <h1 className="text-4xl font-bold bg-gradient-to-r from-slate-900 via-blue-900 to-indigo-900 bg-clip-text text-transparent">
                AI Lead Generation Engine
              </h1>
              <p className="text-slate-600 mt-2 text-lg">
                MediCapital Solutions - Intelligent Prospecting System
              </p>
            </div>
            <div className="flex items-center space-x-4">
              <Button variant="outline" size="lg" className="shadow-sm border-slate-200 hover:border-slate-300">
                <Filter className="h-4 w-4 mr-2" />
                Advanced Filters
              </Button>
              <Button size="lg" className="bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 shadow-lg">
                <Plus className="h-4 w-4 mr-2" />
                New Campaign
              </Button>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-8">
          <TabsList className="grid w-full grid-cols-3 lg:w-fit bg-white/60 backdrop-blur-sm border border-slate-200/60 shadow-lg">
            <TabsTrigger value="dashboard" className="data-[state=active]:bg-white data-[state=active]:shadow-sm">
              Overview
            </TabsTrigger>
            <TabsTrigger value="leads" className="data-[state=active]:bg-white data-[state=active]:shadow-sm">
              Lead Database
            </TabsTrigger>
            <TabsTrigger value="qualification" className="data-[state=active]:bg-white data-[state=active]:shadow-sm">
              Qualification
            </TabsTrigger>
          </TabsList>

          <TabsContent value="dashboard" className="space-y-8">
            {/* Metrics Overview */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              {dashboardMetrics.map((metric, index) => (
                <Card key={index} className="bg-white/80 backdrop-blur-sm border-0 shadow-xl hover:shadow-2xl transition-all duration-300 hover:-translate-y-1">
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-3">
                    <CardTitle className="text-sm font-semibold text-slate-700">
                      {metric.title}
                    </CardTitle>
                    <div className="h-10 w-10 rounded-full bg-gradient-to-br from-blue-100 to-indigo-100 flex items-center justify-center">
                      <metric.icon className="h-5 w-5 text-blue-600" />
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="text-3xl font-bold text-slate-900 mb-2">
                      {metric.value}
                    </div>
                    <div className="flex items-center text-sm mb-1">
                      <span className={`font-medium ${
                        metric.changeType === 'positive' 
                          ? 'text-emerald-600' 
                          : metric.changeType === 'neutral'
                          ? 'text-slate-600'
                          : 'text-red-600'
                      }`}>
                        {metric.change}
                      </span>
                    </div>
                    <p className="text-xs text-slate-500">
                      {metric.description}
                    </p>
                  </CardContent>
                </Card>
              ))}
            </div>

            {/* ICP Status & Recent Leads */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              {/* ICP Development Status */}
              <Card className="bg-white/80 backdrop-blur-sm border-0 shadow-xl">
                <CardHeader>
                  <CardTitle className="flex items-center text-xl">
                    <Target className="h-6 w-6 mr-3 text-blue-600" />
                    Ideal Customer Profiles
                  </CardTitle>
                  <CardDescription className="text-base">
                    Defined target markets with qualification criteria
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                  <div className="space-y-4">
                    <div className="flex items-center justify-between p-4 bg-gradient-to-r from-emerald-50 to-green-50 rounded-xl border border-emerald-200">
                      <div className="flex items-center">
                        <CheckCircle className="h-5 w-5 text-emerald-600 mr-3" />
                        <div>
                          <h4 className="font-semibold text-emerald-900">Healthcare</h4>
                          <p className="text-sm text-emerald-700">Medical devices & diagnostic equipment</p>
                        </div>
                      </div>
                      <Badge className="bg-emerald-100 text-emerald-800 border-emerald-200">Active</Badge>
                    </div>
                    
                    <div className="flex items-center justify-between p-4 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-xl border border-blue-200">
                      <div className="flex items-center">
                        <CheckCircle className="h-5 w-5 text-blue-600 mr-3" />
                        <div>
                          <h4 className="font-semibold text-blue-900">Beauty & Wellness</h4>
                          <p className="text-sm text-blue-700">Laser systems & wellness equipment</p>
                        </div>
                      </div>
                      <Badge className="bg-blue-100 text-blue-800 border-blue-200">Active</Badge>
                    </div>
                    
                    <div className="flex items-center justify-between p-4 bg-gradient-to-r from-amber-50 to-orange-50 rounded-xl border border-amber-200">
                      <div className="flex items-center">
                        <CheckCircle className="h-5 w-5 text-amber-600 mr-3" />
                        <div>
                          <h4 className="font-semibold text-amber-900">Horeca</h4>
                          <p className="text-sm text-amber-700">Kitchen robotics & hospitality equipment</p>
                        </div>
                      </div>
                      <Badge className="bg-amber-100 text-amber-800 border-amber-200">Active</Badge>
                    </div>
                  </div>

                  <div className="pt-4 border-t border-slate-200">
                    <div className="flex items-center justify-between mb-4">
                      <h4 className="font-semibold text-slate-900">Lead Discovery Status</h4>
                      <Badge className="bg-blue-100 text-blue-800 border-blue-200">
                        <Globe className="h-3 w-3 mr-1" />
                        Scanning Active
                      </Badge>
                    </div>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-slate-600">Daily discovery rate</span>
                        <span className="font-semibold text-slate-900">25-35 leads</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-600">Quality threshold</span>
                        <span className="font-semibold text-emerald-600">85%+ match</span>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Recent High-Quality Leads */}
              <Card className="bg-white/80 backdrop-blur-sm border-0 shadow-xl">
                <CardHeader>
                  <CardTitle className="flex items-center text-xl">
                    <Sparkles className="h-6 w-6 mr-3 text-indigo-600" />
                    Recent High-Quality Leads
                  </CardTitle>
                  <CardDescription className="text-base">
                    Latest prospects meeting ICP criteria
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  {recentLeads.map((lead) => (
                    <div 
                      key={lead.id}
                      className="flex items-center justify-between p-5 bg-gradient-to-r from-slate-50 to-blue-50 border border-slate-200 rounded-xl hover:shadow-lg cursor-pointer transition-all duration-200 hover:border-blue-300 group"
                      onClick={() => setSelectedCompany(lead)}
                    >
                      <div className="flex-1">
                        <div className="flex items-center justify-between mb-3">
                          <h4 className="font-semibold text-slate-900 text-lg group-hover:text-blue-900 transition-colors">
                            {lead.company}
                          </h4>
                          <div className="flex items-center space-x-2">
                            <div className={`flex items-center font-bold text-lg ${getScoreColor(lead.score)}`}>
                              {lead.score}
                              <Star className="h-4 w-4 ml-1 text-amber-500" />
                            </div>
                          </div>
                        </div>
                        <div className="flex items-center justify-between text-sm mb-2">
                          <span className="text-slate-600 font-medium">{lead.industry}</span>
                          {getStatusBadge(lead.status)}
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="text-slate-700 font-medium">{lead.equipmentNeed}</span>
                          <span className="font-bold text-slate-900 text-lg">{lead.value}</span>
                        </div>
                        <div className="flex items-center justify-between mt-2 text-xs text-slate-500">
                          <span>{lead.location}</span>
                          <span>{lead.lastActivity}</span>
                        </div>
                      </div>
                      <ArrowRight className="h-5 w-5 text-slate-400 ml-4 group-hover:text-blue-600 transition-colors" />
                    </div>
                  ))}
                  
                  <Button 
                    variant="outline" 
                    className="w-full mt-4 border-dashed border-2 border-slate-300 hover:border-blue-400 hover:bg-blue-50 transition-all"
                    onClick={() => setActiveTab("leads")}
                  >
                    View All Leads
                    <ArrowRight className="h-4 w-4 ml-2" />
                  </Button>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          <TabsContent value="leads">
            <LeadDatabase onSelectCompany={setSelectedCompany} />
          </TabsContent>

          <TabsContent value="qualification">
            <QualificationWorkflow />
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
};

export default Index;
