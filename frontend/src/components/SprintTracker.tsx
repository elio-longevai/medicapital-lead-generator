
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { 
  Calendar,
  CheckCircle,
  Clock,
  Target,
  Users,
  Mail,
  TrendingUp,
  AlertCircle,
  Euro,
  FileText,
  Rocket
} from "lucide-react";

export const SprintTracker = () => {
  const sprints = [
    {
      id: 1,
      title: "Foundation & ICP Development",
      subtitle: "Comprehensive Ideal Customer Profile(s) + Initial Lead Generation Setup",
      week: "Week 1",
      price: "€2,000",
      status: "Completed",
      progress: 100,
      startDate: "2024-06-03",
      endDate: "2024-06-10",
      deliverables: [
        "Detailed ICP definitions for up to 3 target industries",
        "Initial lead discovery rules and configuration",
        "First batch of leads ready for review"
      ],
      benefits: [
        "Clear target market definition for systematic prospecting",
        "Immediate access to relevant leads in your sectors",
        "Foundation for all subsequent automation"
      ],
      risks: [
        "Minimal risk as this establishes core targeting criteria",
        "May require 1-2 refinement cycles to perfect ICP definitions"
      ]
    },
    {
      id: 2,
      title: "Data Enrichment & Qualification Setup",
      subtitle: "Enhanced Lead Data + Qualification Framework Setup",
      week: "Week 2",
      price: "€2,000",
      status: "In Progress",
      progress: 75,
      startDate: "2024-06-10",
      endDate: "2024-06-17",
      deliverables: [
        "Qualification criteria workshop and framework definition",
        "Data enrichment from multiple internet sources",
        "Enhanced lead database with qualification-ready information",
        "Basic dashboard/overview showing enriched lead data"
      ],
      benefits: [
        "Identify leads at the right time (expansions, new funding, equipment needs)",
        "Rich context about each company beyond basic contact information",
        "Foundation for intelligent lead scoring and prioritization"
      ],
      risks: [
        "Qualification criteria might need calibration to focus on converting leads",
        "Data quality depends on available public information"
      ]
    },
    {
      id: 3,
      title: "Intelligent Qualification System",
      subtitle: "AI Lead Qualification + Advanced Dashboard Overview",
      week: "Week 3",
      price: "€2,000",
      status: "Planned",
      progress: 0,
      startDate: "2024-06-17",
      endDate: "2024-06-24",
      deliverables: [
        "Collaborative definition of lead qualification criteria",
        "AI-powered lead scoring and qualification automation",
        "Enhanced dashboard with qualification information and scores",
        "Qualified leads ready for targeted outreach"
      ],
      benefits: [
        "Focus sales efforts on highest-potential prospects automatically",
        "Eliminate time wasted on unqualified leads",
        "Data-driven prioritization of sales activities"
      ],
      risks: [
        "Initial qualification criteria may need refinement based on sales team feedback",
        "AI scoring accuracy improves over time with more data"
      ]
    },
    {
      id: 4,
      title: "Automated Outreach Engine",
      subtitle: "AI-Generated Personalized Email System",
      week: "Week 4",
      price: "€2,000",
      status: "Planned",
      progress: 0,
      startDate: "2024-06-24",
      endDate: "2024-07-01",
      deliverables: [
        "AI-generated personalized outreach emails based on enriched lead data",
        "Workflow for generating, reviewing, and editing emails",
        "Email campaign management and tracking system"
      ],
      benefits: [
        "Consistent, professional outreach at scale",
        "Context-aware messaging that resonates with prospects",
        "Systematic lead nurturing without manual email writing"
      ],
      risks: [
        "Email deliverability depends on domain reputation and setup",
        "Message personalization quality improves with feedback cycles"
      ]
    }
  ];

  const getStatusBadge = (status) => {
    const variants = {
      "Completed": "bg-green-100 text-green-800",
      "In Progress": "bg-blue-100 text-blue-800",
      "Planned": "bg-gray-100 text-gray-800"
    };
    return <Badge className={variants[status]}>{status}</Badge>;
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case "Completed":
        return <CheckCircle className="h-5 w-5 text-green-600" />;
      case "In Progress":
        return <Clock className="h-5 w-5 text-blue-600" />;
      case "Planned":
        return <Target className="h-5 w-5 text-gray-600" />;
      default:
        return <Clock className="h-5 w-5 text-gray-600" />;
    }
  };

  const totalInvestment = sprints.reduce((sum, sprint) => sum + parseInt(sprint.price.replace(/[€,]/g, "")), 0);
  const completedSprints = sprints.filter(s => s.status === "Completed").length;
  const currentSprint = sprints.find(s => s.status === "In Progress");

  return (
    <div className="space-y-6">
      {/* Overview */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <Rocket className="h-5 w-5 mr-2" />
            Sprint Roadmap & Progress
          </CardTitle>
          <CardDescription>
            Modular implementation approach with weekly deliverables
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="text-center p-4 bg-blue-50 rounded-lg">
              <div className="text-2xl font-bold text-blue-900">{completedSprints}</div>
              <div className="text-sm text-blue-700">Sprints Completed</div>
            </div>
            <div className="text-center p-4 bg-green-50 rounded-lg">
              <div className="text-2xl font-bold text-green-900">€{totalInvestment.toLocaleString()}</div>
              <div className="text-sm text-green-700">Total Investment</div>
            </div>
            <div className="text-center p-4 bg-yellow-50 rounded-lg">
              <div className="text-2xl font-bold text-yellow-900">4</div>
              <div className="text-sm text-yellow-700">Weeks Timeline</div>
            </div>
            <div className="text-center p-4 bg-purple-50 rounded-lg">
              <div className="text-2xl font-bold text-purple-900">Low Risk</div>
              <div className="text-sm text-purple-700">Modular Approach</div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Current Sprint Highlight */}
      {currentSprint && (
        <Card className="border-blue-200 bg-blue-50">
          <CardHeader>
            <CardTitle className="flex items-center text-blue-900">
              <Clock className="h-5 w-5 mr-2" />
              Current Sprint: {currentSprint.title}
            </CardTitle>
            <CardDescription className="text-blue-700">
              {currentSprint.subtitle}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <span className="text-sm font-medium text-blue-900">Progress</span>
                <span className="text-sm font-bold text-blue-900">{currentSprint.progress}%</span>
              </div>
              <Progress value={currentSprint.progress} className="h-3" />
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-blue-700">Start Date:</span>
                  <span className="font-medium ml-2 text-blue-900">{currentSprint.startDate}</span>
                </div>
                <div>
                  <span className="text-blue-700">Target Completion:</span>
                  <span className="font-medium ml-2 text-blue-900">{currentSprint.endDate}</span>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Sprint Details */}
      <div className="space-y-6">
        {sprints.map((sprint, index) => (
          <Card key={sprint.id} className={sprint.status === "In Progress" ? "border-blue-200" : ""}>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div className="flex items-center">
                  {getStatusIcon(sprint.status)}
                  <div className="ml-3">
                    <CardTitle className="text-lg">
                      Sprint {sprint.id}: {sprint.title}
                    </CardTitle>
                    <CardDescription className="text-base">
                      {sprint.subtitle}
                    </CardDescription>
                  </div>
                </div>
                <div className="flex items-center space-x-3">
                  <div className="text-right">
                    <div className="text-lg font-bold text-gray-900">{sprint.price}</div>
                    <div className="text-sm text-gray-600">{sprint.week}</div>
                  </div>
                  {getStatusBadge(sprint.status)}
                </div>
              </div>
              {sprint.status === "In Progress" && (
                <div className="mt-4">
                  <div className="flex justify-between text-sm mb-2">
                    <span>Sprint Progress</span>
                    <span>{sprint.progress}%</span>
                  </div>
                  <Progress value={sprint.progress} className="h-2" />
                </div>
              )}
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div>
                  <h4 className="font-medium text-gray-900 mb-3 flex items-center">
                    <FileText className="h-4 w-4 mr-2" />
                    Deliverables
                  </h4>
                  <ul className="space-y-2">
                    {sprint.deliverables.map((item, idx) => (
                      <li key={idx} className="text-sm text-gray-700 flex items-start">
                        <CheckCircle className="h-3 w-3 mt-1 mr-2 text-green-600 flex-shrink-0" />
                        {item}
                      </li>
                    ))}
                  </ul>
                </div>

                <div>
                  <h4 className="font-medium text-gray-900 mb-3 flex items-center">
                    <TrendingUp className="h-4 w-4 mr-2" />
                    Benefits
                  </h4>
                  <ul className="space-y-2">
                    {sprint.benefits.map((item, idx) => (
                      <li key={idx} className="text-sm text-gray-700 flex items-start">
                        <Target className="h-3 w-3 mt-1 mr-2 text-blue-600 flex-shrink-0" />
                        {item}
                      </li>
                    ))}
                  </ul>
                </div>

                <div>
                  <h4 className="font-medium text-gray-900 mb-3 flex items-center">
                    <AlertCircle className="h-4 w-4 mr-2" />
                    Risk Considerations
                  </h4>
                  <ul className="space-y-2">
                    {sprint.risks.map((item, idx) => (
                      <li key={idx} className="text-sm text-gray-700 flex items-start">
                        <AlertCircle className="h-3 w-3 mt-1 mr-2 text-yellow-600 flex-shrink-0" />
                        {item}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>

              <div className="mt-6 pt-4 border-t flex justify-between items-center">
                <div className="text-sm text-gray-600">
                  Duration: {sprint.startDate} - {sprint.endDate}
                </div>
                {sprint.status === "Planned" && (
                  <Button variant="outline" size="sm">
                    <Calendar className="h-4 w-4 mr-2" />
                    Schedule Sprint
                  </Button>
                )}
                {sprint.status === "In Progress" && (
                  <Button size="sm">
                    <Users className="h-4 w-4 mr-2" />
                    View Progress
                  </Button>
                )}
                {sprint.status === "Completed" && (
                  <Button variant="outline" size="sm">
                    <FileText className="h-4 w-4 mr-2" />
                    View Results
                  </Button>
                )}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Next Steps */}
      <Card className="border-green-200 bg-green-50">
        <CardHeader>
          <CardTitle className="text-green-900">Next Steps & Timeline</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <h4 className="font-medium text-green-900 mb-2">Immediate Actions</h4>
                <ul className="space-y-1 text-sm text-green-800">
                  <li className="flex items-center">
                    <CheckCircle className="h-3 w-3 mr-2" />
                    Kick-off meeting scheduled for next week
                  </li>
                  <li className="flex items-center">
                    <Clock className="h-3 w-3 mr-2" />
                    ICP preparation by Hans & Peter
                  </li>
                  <li className="flex items-center">
                    <Users className="h-3 w-3 mr-2" />
                    ICP definition workshop (1.5-2 hours)
                  </li>
                </ul>
              </div>
              <div>
                <h4 className="font-medium text-green-900 mb-2">Administrative</h4>
                <ul className="space-y-1 text-sm text-green-800">
                  <li className="flex items-center">
                    <FileText className="h-3 w-3 mr-2" />
                    Contract & admin with Cosmina
                  </li>
                  <li className="flex items-center">
                    <Euro className="h-3 w-3 mr-2" />
                    Payment schedule setup
                  </li>
                  <li className="flex items-center">
                    <Mail className="h-3 w-3 mr-2" />
                    Project communication channels
                  </li>
                </ul>
              </div>
            </div>
            
            <div className="pt-4 border-t border-green-200">
              <Button className="bg-green-700 hover:bg-green-800">
                <Rocket className="h-4 w-4 mr-2" />
                Start Sprint 1
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
