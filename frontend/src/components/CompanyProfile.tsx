import { useState } from "react";
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
  MessageSquare,
  Check,
  Trash2,
} from "lucide-react";
import { useUpdateCompanyStatus } from "@/hooks/useCompanies";
import { toast } from "sonner";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";

export const CompanyProfile = ({ company, onBack }) => {
  const [isRejectDialogOpen, setIsRejectDialogOpen] = useState(false);
  const updateStatusMutation = useUpdateCompanyStatus();

  if (!company) return null;

  const getStatusBadge = (status) => {
    const variants = {
      "qualified": "bg-green-100 text-green-800 border-green-200",
      "in_review": "bg-yellow-100 text-yellow-800",
      "discovered": "bg-gray-100 text-gray-800 border-gray-200",
      "contacted": "bg-blue-100 text-blue-800 border-blue-200",
      "rejected": "bg-red-100 text-red-800 border-red-200",
    };

    const normalizedStatus = status.toLowerCase().replace(/\s+/g, '_');
    const displayStatus = status.includes('_')
      ? status.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())
      : status.replace(/\b\w/g, l => l.toUpperCase());
      
    return (
      <Badge className={`${variants[normalizedStatus] || variants.discovered} border font-medium`}>{displayStatus}</Badge>
    );
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

  const handleContacted = () => {
    if (!company) return;
    updateStatusMutation.mutate(
      { id: company.id, status: "contacted" },
      {
        onSuccess: () => {
          toast.success(`${company.company} marked as contacted.`);
          onBack();
        },
        onError: (error) => {
          toast.error(`Failed to update status: ${error.message}`);
        },
      }
    );
  };

  const handleReject = () => {
    if (!company) return;
    updateStatusMutation.mutate(
      { id: company.id, status: "rejected" },
      {
        onSuccess: () => {
          toast.success(`${company.company} has been rejected.`);
          setIsRejectDialogOpen(false);
          onBack();
        },
        onError: (error) => {
          toast.error(`Failed to reject lead: ${error.message}`);
          setIsRejectDialogOpen(false);
        },
      }
    );
  };

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
                <TabsTrigger value="research" disabled className="opacity-50 cursor-not-allowed">Research</TabsTrigger>
                <TabsTrigger value="outreach" disabled className="opacity-50 cursor-not-allowed">Outreach</TabsTrigger>
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
                              href={
                                company.website && !company.website.startsWith('http')
                                ? `https://${company.website}`
                                : company.website
                              }
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
                      Recent News & Activity
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <ul className="space-y-4">
                      {activities.map((activity, index) => (
                        <li key={index} className="flex space-x-3">
                          <div className={`mt-1 h-5 w-5 flex-shrink-0 flex items-center justify-center rounded-full ${activity.color} bg-opacity-10`}>
                            <activity.icon className={`h-3 w-3 ${activity.color}`} />
                          </div>
                          <div>
                            <p className="text-sm font-medium text-gray-900">{activity.title}</p>
                            <p className="text-sm text-gray-500">{activity.description}</p>
                            <p className="text-xs text-gray-400 mt-1">{activity.timestamp}</p>
                          </div>
                        </li>
                      ))}
                    </ul>
                  </CardContent>
                </Card>
              </TabsContent>

              <TabsContent value="qualification">
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center">
                      <CheckCircle className="h-5 w-5 mr-2" />
                      Qualification Breakdown (future feature)
                    </CardTitle>
                    <CardDescription>
                      Scores are from 0-100, based on our internal qualification model.
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-6">
                      {qualificationAreas.map(area => (
                        <div key={area.name}>
                          <div className="flex items-center justify-between mb-2">
                            <div className="flex items-center">
                              <area.icon className="h-5 w-5 mr-2 text-gray-500" />
                              <span className="font-medium">{area.name}</span>
                            </div>
                            <span className="font-bold text-lg">{area.score}</span>
                          </div>
                          <Progress value={area.score} className="h-2" />
                          <p className="text-sm text-gray-500 mt-2">{area.description}</p>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              </TabsContent>
            </Tabs>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Contact Information</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex items-center">
                    <Mail className="h-4 w-4 mr-3 text-gray-500" />
                    <span className="text-gray-900">{company.email || "Not available"}</span>
                  </div>
                  <div className="flex items-center">
                    <Phone className="h-4 w-4 mr-3 text-gray-500" />
                    <span className="text-gray-900">{company.phone || "Not available"}</span>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Quick Actions</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                <Button className="w-full" size="sm" onClick={handleContacted} disabled={updateStatusMutation.isPending}>
                  <Check className="h-4 w-4 mr-2" />
                  Mark as Contacted
                </Button>
                <AlertDialog open={isRejectDialogOpen} onOpenChange={setIsRejectDialogOpen}>
                  <AlertDialogTrigger asChild>
                    <Button variant="destructive" className="w-full" size="sm">
                      <Trash2 className="h-4 w-4 mr-2" />
                      Reject Lead
                    </Button>
                  </AlertDialogTrigger>
                  <AlertDialogContent>
                    <AlertDialogHeader>
                      <AlertDialogTitle>Are you absolutely sure?</AlertDialogTitle>
                      <AlertDialogDescription>
                        This will mark "{company.company}" as rejected and remove it from active lead lists. This action cannot be easily undone.
                      </AlertDialogDescription>
                    </AlertDialogHeader>
                    <AlertDialogFooter>
                      <AlertDialogCancel>Cancel</AlertDialogCancel>
                      <AlertDialogAction onClick={handleReject} disabled={updateStatusMutation.isPending} className="bg-destructive text-destructive-foreground hover:bg-destructive/90">
                        {updateStatusMutation.isPending ? "Rejecting..." : "Yes, Reject Lead"}
                      </AlertDialogAction>
                    </AlertDialogFooter>
                  </AlertDialogContent>
                </AlertDialog>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
};
