
import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { 
  Search, 
  Download, 
  Star, 
  Building2, 
  MapPin, 
  Calendar,
  ExternalLink,
  ChevronRight,
  Sparkles,
  Target,
  TrendingUp
} from "lucide-react";

export const LeadDatabase = ({ onSelectCompany }) => {
  const [searchTerm, setSearchTerm] = useState("");
  const [industryFilter, setIndustryFilter] = useState("all");
  const [statusFilter, setStatusFilter] = useState("all");
  const [sortBy, setSortBy] = useState("score");

  const leads = [
    {
      id: 1,
      company: "Amsterdam Medical Center",
      industry: "Healthcare",
      location: "Amsterdam, NL",
      score: 92,
      status: "Qualified",
      lastActivity: "2024-06-14",
      equipmentNeed: "Diagnostic Equipment",
      estimatedValue: "€85,000",
      employees: "500-1000",
      website: "www.amc.nl",
      email: "procurement@amc.nl",
      phone: "+31 20 566 9111",
      notes: "Expanding cardiac unit, looking for new ultrasound systems",
      recentNews: "Announced €2M investment in new cardiac wing",
      qualificationScore: {
        financialStability: 95,
        equipmentNeed: 90,
        timing: 88,
        decisionAuthority: 94
      }
    },
    {
      id: 2,
      company: "Beauty Clinic Rotterdam",
      industry: "Beauty & Wellness",
      location: "Rotterdam, NL",
      score: 88,
      status: "In Review",
      lastActivity: "2024-06-13",
      equipmentNeed: "Laser Systems",
      estimatedValue: "€45,000",
      employees: "10-50",
      website: "www.beautyclinic-rotterdam.nl",
      email: "info@beautyclinic-rotterdam.nl",
      phone: "+31 10 123 4567",
      notes: "Multiple locations, standardizing equipment across clinics",
      recentNews: "Opening two new locations in Q3 2024",
      qualificationScore: {
        financialStability: 85,
        equipmentNeed: 92,
        timing: 90,
        decisionAuthority: 85
      }
    },
    {
      id: 3,
      company: "Restaurant Group Utrecht",
      industry: "Horeca",
      location: "Utrecht, NL",
      score: 76,
      status: "Discovered",
      lastActivity: "2024-06-12",
      equipmentNeed: "Kitchen Equipment",
      estimatedValue: "€32,000",
      employees: "50-100",
      website: "www.restaurantgroup-utrecht.nl",
      email: "operations@restaurantgroup-utrecht.nl",
      phone: "+31 30 987 6543",
      notes: "Chain of 8 restaurants, modernizing kitchen equipment",
      recentNews: "Received sustainability certification for all locations",
      qualificationScore: {
        financialStability: 78,
        equipmentNeed: 80,
        timing: 75,
        decisionAuthority: 72
      }
    },
    {
      id: 4,
      company: "TechMed Innovations",
      industry: "Healthcare",
      location: "Eindhoven, NL",
      score: 94,
      status: "Qualified",
      lastActivity: "2024-06-14",
      equipmentNeed: "Laboratory Equipment",
      estimatedValue: "€125,000",
      employees: "100-250",
      website: "www.techmed-innovations.nl",
      email: "finance@techmed-innovations.nl",
      phone: "+31 40 123 7890",
      notes: "Medical device manufacturer expanding R&D lab",
      recentNews: "Secured €5M funding round for expansion",
      qualificationScore: {
        financialStability: 96,
        equipmentNeed: 95,
        timing: 92,
        decisionAuthority: 93
      }
    },
    {
      id: 5,
      company: "Wellness Spa Den Haag",
      industry: "Beauty & Wellness",
      location: "Den Haag, NL",
      score: 71,
      status: "In Review",
      lastActivity: "2024-06-11",
      equipmentNeed: "Wellness Equipment",
      estimatedValue: "€28,000",
      employees: "10-25",
      website: "www.wellness-spa-denhaag.nl",
      email: "management@wellness-spa-denhaag.nl",
      phone: "+31 70 456 1234",
      notes: "Premium spa looking to upgrade massage and therapy equipment",
      recentNews: "Won 'Best Spa Experience' award 2024",
      qualificationScore: {
        financialStability: 75,
        equipmentNeed: 85,
        timing: 68,
        decisionAuthority: 70
      }
    },
    {
      id: 6,
      company: "Solar Kitchen Solutions",
      industry: "Horeca",
      location: "Groningen, NL",
      score: 83,
      status: "Qualified",
      lastActivity: "2024-06-13",
      equipmentNeed: "Sustainable Kitchen Equipment",
      estimatedValue: "€67,000",
      employees: "25-50",
      website: "www.solarkitchen.nl",
      email: "procurement@solarkitchen.nl",
      phone: "+31 50 789 0123",
      notes: "Sustainable restaurant equipment supplier, expanding product line",
      recentNews: "Partnership with major restaurant chain announced",
      qualificationScore: {
        financialStability: 82,
        equipmentNeed: 88,
        timing: 85,
        decisionAuthority: 80
      }
    }
  ];

  const filteredLeads = leads.filter(lead => {
    const matchesSearch = lead.company.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         lead.equipmentNeed.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesIndustry = industryFilter === "all" || lead.industry === industryFilter;
    const matchesStatus = statusFilter === "all" || lead.status === statusFilter;
    
    return matchesSearch && matchesIndustry && matchesStatus;
  });

  const parseEstimatedValue = (value: string): number => {
    return parseInt(value.replace(/[€,]/g, ""), 10) || 0;
  };

  const sortedLeads = [...filteredLeads].sort((a, b) => {
    switch (sortBy) {
      case "score":
        return b.score - a.score;
      case "company":
        return a.company.localeCompare(b.company);
      case "value":
        return parseEstimatedValue(b.estimatedValue) - parseEstimatedValue(a.estimatedValue);
      case "activity":
        return new Date(b.lastActivity).getTime() - new Date(a.lastActivity).getTime();
      default:
        return 0;
    }
  });

  const getStatusBadge = (status) => {
    const colors = {
      "Qualified": "bg-emerald-100 text-emerald-800 border-emerald-200",
      "In Review": "bg-amber-100 text-amber-800 border-amber-200", 
      "Discovered": "bg-slate-100 text-slate-800 border-slate-200"
    };
    return (
      <Badge className={`${colors[status]} border font-medium`}>
        {status}
      </Badge>
    );
  };

  const getScoreColor = (score) => {
    if (score >= 85) return "text-emerald-600 bg-emerald-50";
    if (score >= 70) return "text-amber-600 bg-amber-50";
    return "text-red-600 bg-red-50";
  };

  const getIndustryIcon = (industry) => {
    switch (industry) {
      case "Healthcare":
        return "🏥";
      case "Beauty & Wellness":
        return "✨";
      case "Horeca":
        return "🍽️";
      default:
        return "🏢";
    }
  };

  return (
    <div className="space-y-8">
      {/* Header with Search and Filters */}
      <Card className="bg-white/80 backdrop-blur-sm border-0 shadow-xl">
        <CardHeader>
          <CardTitle className="flex items-center text-2xl">
            <Building2 className="h-7 w-7 mr-3 text-blue-600" />
            Lead Database
          </CardTitle>
          <CardDescription className="text-base">
            {sortedLeads.length} qualified prospects • Discover and manage potential customers
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col lg:flex-row gap-6">
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 h-5 w-5 text-slate-400" />
                <Input
                  placeholder="Search companies, equipment needs, locations..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-12 h-12 text-base border-slate-200 focus:border-blue-400 focus:ring-blue-400"
                />
              </div>
            </div>
            <div className="flex gap-3">
              <Select value={industryFilter} onValueChange={setIndustryFilter}>
                <SelectTrigger className="w-48 h-12 border-slate-200 focus:border-blue-400">
                  <SelectValue placeholder="Industry" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Industries</SelectItem>
                  <SelectItem value="Healthcare">🏥 Healthcare</SelectItem>
                  <SelectItem value="Beauty & Wellness">✨ Beauty & Wellness</SelectItem>
                  <SelectItem value="Horeca">🍽️ Horeca</SelectItem>
                </SelectContent>
              </Select>
              
              <Select value={statusFilter} onValueChange={setStatusFilter}>
                <SelectTrigger className="w-40 h-12 border-slate-200 focus:border-blue-400">
                  <SelectValue placeholder="Status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Status</SelectItem>
                  <SelectItem value="Qualified">Qualified</SelectItem>
                  <SelectItem value="In Review">In Review</SelectItem>
                  <SelectItem value="Discovered">Discovered</SelectItem>
                </SelectContent>
              </Select>

              <Select value={sortBy} onValueChange={setSortBy}>
                <SelectTrigger className="w-40 h-12 border-slate-200 focus:border-blue-400">
                  <SelectValue placeholder="Sort by" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="score">Score</SelectItem>
                  <SelectItem value="company">Company</SelectItem>
                  <SelectItem value="value">Value</SelectItem>
                  <SelectItem value="activity">Activity</SelectItem>
                </SelectContent>
              </Select>

              <Button variant="outline" size="lg" className="border-slate-200 hover:border-slate-300 shadow-sm">
                <Download className="h-4 w-4 mr-2" />
                Export
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Leads Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
        {sortedLeads.map((lead) => (
          <Card 
            key={lead.id} 
            className="group bg-white/80 backdrop-blur-sm border-0 shadow-lg hover:shadow-2xl transition-all duration-300 cursor-pointer hover:-translate-y-1 border-l-4 border-l-blue-500 hover:border-l-blue-600"
            onClick={() => onSelectCompany(lead)}
          >
            <CardHeader className="pb-4">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center mb-2">
                    <span className="text-2xl mr-2">{getIndustryIcon(lead.industry)}</span>
                    <CardTitle className="text-xl group-hover:text-blue-900 transition-colors">
                      {lead.company}
                    </CardTitle>
                  </div>
                  <div className="flex items-center text-sm text-slate-600 mb-3">
                    <MapPin className="h-4 w-4 mr-1" />
                    {lead.location}
                  </div>
                </div>
                <div className="flex flex-col items-end space-y-3">
                  <div className={`px-3 py-2 rounded-full text-base font-bold ${getScoreColor(lead.score)} border`}>
                    {lead.score}
                  </div>
                  {getStatusBadge(lead.status)}
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="bg-gradient-to-r from-slate-50 to-blue-50 p-4 rounded-xl border border-slate-100">
                  <p className="text-sm font-semibold text-slate-700 mb-1">Equipment Need</p>
                  <p className="text-base text-slate-900 font-medium">{lead.equipmentNeed}</p>
                </div>
                
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="text-slate-600 block">Est. Value</span>
                    <span className="font-bold text-slate-900 text-lg">{lead.estimatedValue}</span>
                  </div>
                  <div>
                    <span className="text-slate-600 block">Industry</span>
                    <span className="font-semibold text-slate-900">{lead.industry}</span>
                  </div>
                </div>

                <div className="pt-3 border-t border-slate-200">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs font-semibold text-slate-600 uppercase tracking-wide">Recent Activity</span>
                    <div className="flex items-center text-xs text-slate-500">
                      <Calendar className="h-3 w-3 mr-1" />
                      {lead.lastActivity}
                    </div>
                  </div>
                  <p className="text-sm text-slate-700 line-clamp-2 leading-relaxed">{lead.recentNews}</p>
                </div>

                <div className="flex items-center justify-between pt-3">
                  <div className="flex items-center space-x-1">
                    <Star className="h-4 w-4 text-amber-500" />
                    <span className="text-sm font-medium text-slate-700">High Priority</span>
                  </div>
                  <ChevronRight className="h-5 w-5 text-slate-400 group-hover:text-blue-600 transition-colors" />
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {sortedLeads.length === 0 && (
        <Card className="bg-white/80 backdrop-blur-sm border-0 shadow-xl">
          <CardContent className="text-center py-16">
            <div className="flex justify-center mb-6">
              <div className="h-20 w-20 bg-gradient-to-br from-slate-100 to-blue-100 rounded-full flex items-center justify-center">
                <Search className="h-10 w-10 text-slate-400" />
              </div>
            </div>
            <h3 className="text-xl font-semibold text-slate-900 mb-3">No leads found</h3>
            <p className="text-slate-600 text-base max-w-md mx-auto">
              Try adjusting your search criteria or filters to discover more potential customers.
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
};
