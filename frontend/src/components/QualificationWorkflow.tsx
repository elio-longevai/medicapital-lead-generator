
import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { 
  Target,
  CheckCircle,
  Clock,
  AlertCircle,
  Euro,
  Users,
  Settings,
  Save,
  Play,
  Pause,
  RotateCcw
} from "lucide-react";

export const QualificationWorkflow = () => {
  const [isRunning, setIsRunning] = useState(true);
  const [criteria, setCriteria] = useState({
    minimumValue: "35000",
    industries: "Healthcare, Beauty & Wellness, Horeca",
    companySize: "10-1000",
    financialStability: "75",
    equipmentNeedScore: "70",
    timingScore: "65",
    decisionAuthorityScore: "70"
  });

  const qualificationStats = {
    totalProcessed: 1247,
    qualified: 342,
    inReview: 156,
    rejected: 749,
    qualificationRate: 27.4
  };

  const currentBatch = [
    {
      id: 1,
      company: "VitaHealth Clinic",
      industry: "Healthcare",
      status: "Processing",
      progress: 75,
      estimatedValue: "€67,000",
      preliminaryScore: 82
    },
    {
      id: 2,
      company: "Beauty Solutions BV",
      industry: "Beauty & Wellness",
      status: "Completed",
      progress: 100,
      estimatedValue: "€43,000",
      preliminaryScore: 76
    },
    {
      id: 3,
      company: "Restaurant Tech Group",
      industry: "Horeca",
      status: "Qualified",
      progress: 100,
      estimatedValue: "€55,000",
      preliminaryScore: 89
    },
    {
      id: 4,
      company: "MedDevice Innovations",
      industry: "Healthcare",
      status: "Processing",
      progress: 45,
      estimatedValue: "€125,000",
      preliminaryScore: 94
    }
  ];

  const getStatusBadge = (status) => {
    const variants = {
      "Processing": "bg-blue-100 text-blue-800",
      "Completed": "bg-gray-100 text-gray-800",
      "Qualified": "bg-green-100 text-green-800",
      "Rejected": "bg-red-100 text-red-800"
    };
    return <Badge className={variants[status] || "bg-gray-100 text-gray-800"}>{status}</Badge>;
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case "Processing":
        return <Clock className="h-4 w-4 text-blue-600" />;
      case "Qualified":
        return <CheckCircle className="h-4 w-4 text-green-600" />;
      case "Rejected":
        return <AlertCircle className="h-4 w-4 text-red-600" />;
      default:
        return <Clock className="h-4 w-4 text-gray-600" />;
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center">
                <Target className="h-5 w-5 mr-2" />
                AI Qualification Engine
              </CardTitle>
              <CardDescription>
                Automated lead qualification using AI-driven criteria analysis
              </CardDescription>
            </div>
            <div className="flex items-center space-x-2">
              <Badge variant={isRunning ? "default" : "secondary"}>
                {isRunning ? "Active" : "Paused"}
              </Badge>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setIsRunning(!isRunning)}
              >
                {isRunning ? (
                  <>
                    <Pause className="h-4 w-4 mr-2" />
                    Pause
                  </>
                ) : (
                  <>
                    <Play className="h-4 w-4 mr-2" />
                    Resume
                  </>
                )}
              </Button>
            </div>
          </div>
        </CardHeader>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Qualification Criteria */}
        <div className="lg:col-span-1 space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <Settings className="h-5 w-5 mr-2" />
                Qualification Criteria
              </CardTitle>
              <CardDescription>
                Configure AI qualification parameters
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Label htmlFor="minimumValue">Minimum Deal Value (€)</Label>
                <Input
                  id="minimumValue"
                  value={criteria.minimumValue}
                  onChange={(e) => setCriteria({...criteria, minimumValue: e.target.value})}
                />
              </div>

              <div>
                <Label htmlFor="industries">Target Industries</Label>
                <Textarea
                  id="industries"
                  value={criteria.industries}
                  onChange={(e) => setCriteria({...criteria, industries: e.target.value})}
                  rows={3}
                />
              </div>

              <div>
                <Label htmlFor="companySize">Company Size (Employees)</Label>
                <Input
                  id="companySize"
                  value={criteria.companySize}
                  onChange={(e) => setCriteria({...criteria, companySize: e.target.value})}
                />
              </div>

              <div className="space-y-3">
                <Label>Minimum Scores</Label>
                
                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <span>Financial Stability</span>
                    <span>{criteria.financialStability}%</span>
                  </div>
                  <input
                    type="range"
                    min="0"
                    max="100"
                    value={criteria.financialStability}
                    onChange={(e) => setCriteria({...criteria, financialStability: e.target.value})}
                    className="w-full"
                  />
                </div>

                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <span>Equipment Need</span>
                    <span>{criteria.equipmentNeedScore}%</span>
                  </div>
                  <input
                    type="range"
                    min="0"
                    max="100"
                    value={criteria.equipmentNeedScore}
                    onChange={(e) => setCriteria({...criteria, equipmentNeedScore: e.target.value})}
                    className="w-full"
                  />
                </div>

                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <span>Timing</span>
                    <span>{criteria.timingScore}%</span>
                  </div>
                  <input
                    type="range"
                    min="0"
                    max="100"
                    value={criteria.timingScore}
                    onChange={(e) => setCriteria({...criteria, timingScore: e.target.value})}
                    className="w-full"
                  />
                </div>

                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <span>Decision Authority</span>
                    <span>{criteria.decisionAuthorityScore}%</span>
                  </div>
                  <input
                    type="range"
                    min="0"
                    max="100"
                    value={criteria.decisionAuthorityScore}
                    onChange={(e) => setCriteria({...criteria, decisionAuthorityScore: e.target.value})}
                    className="w-full"
                  />
                </div>
              </div>

              <div className="pt-4 space-y-2">
                <Button className="w-full" size="sm">
                  <Save className="h-4 w-4 mr-2" />
                  Save Criteria
                </Button>
                <Button variant="outline" className="w-full" size="sm">
                  <RotateCcw className="h-4 w-4 mr-2" />
                  Reset to Default
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Stats Overview */}
          <Card>
            <CardHeader>
              <CardTitle>Qualification Statistics</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4 text-center">
                <div>
                  <div className="text-2xl font-bold text-gray-900">
                    {qualificationStats.qualified}
                  </div>
                  <div className="text-sm text-gray-600">Qualified</div>
                </div>
                <div>
                  <div className="text-2xl font-bold text-gray-900">
                    {qualificationStats.qualificationRate}%
                  </div>
                  <div className="text-sm text-gray-600">Success Rate</div>
                </div>
              </div>
              
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span>Total Processed</span>
                  <span className="font-medium">{qualificationStats.totalProcessed}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span>In Review</span>
                  <span className="font-medium">{qualificationStats.inReview}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span>Rejected</span>
                  <span className="font-medium">{qualificationStats.rejected}</span>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Processing Queue */}
        <div className="lg:col-span-2 space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Current Processing Queue</CardTitle>
              <CardDescription>
                Real-time qualification processing status
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {currentBatch.map((item) => (
                  <div key={item.id} className="border border-gray-200 rounded-lg p-4">
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center">
                        {getStatusIcon(item.status)}
                        <div className="ml-3">
                          <h4 className="font-medium text-gray-900">{item.company}</h4>
                          <p className="text-sm text-gray-600">{item.industry}</p>
                        </div>
                      </div>
                      <div className="flex items-center space-x-3">
                        <div className="text-right">
                          <div className="text-sm font-medium">{item.estimatedValue}</div>
                          <div className="text-xs text-gray-500">Est. Value</div>
                        </div>
                        {getStatusBadge(item.status)}
                      </div>
                    </div>

                    <div className="space-y-2">
                      <div className="flex justify-between text-sm">
                        <span>Processing Progress</span>
                        <span>{item.progress}%</span>
                      </div>
                      <Progress value={item.progress} className="h-2" />
                      
                      {item.preliminaryScore && (
                        <div className="flex justify-between text-sm">
                          <span>Preliminary Score</span>
                          <span className="font-bold text-blue-600">{item.preliminaryScore}</span>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Qualification Process Flow */}
          <Card>
            <CardHeader>
              <CardTitle>Qualification Process</CardTitle>
              <CardDescription>
                AI-driven multi-stage qualification workflow
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                  <div className="text-center p-4 bg-blue-50 rounded-lg">
                    <Users className="h-8 w-8 text-blue-600 mx-auto mb-2" />
                    <h4 className="font-medium text-blue-900">Data Collection</h4>
                    <p className="text-sm text-blue-700 mt-1">Company info, financial data, news</p>
                  </div>
                  <div className="text-center p-4 bg-yellow-50 rounded-lg">
                    <Target className="h-8 w-8 text-yellow-600 mx-auto mb-2" />
                    <h4 className="font-medium text-yellow-900">AI Analysis</h4>
                    <p className="text-sm text-yellow-700 mt-1">Scoring against criteria</p>
                  </div>
                  <div className="text-center p-4 bg-green-50 rounded-lg">
                    <CheckCircle className="h-8 w-8 text-green-600 mx-auto mb-2" />
                    <h4 className="font-medium text-green-900">Qualification</h4>
                    <p className="text-sm text-green-700 mt-1">Pass/fail determination</p>
                  </div>
                  <div className="text-center p-4 bg-purple-50 rounded-lg">
                    <Euro className="h-8 w-8 text-purple-600 mx-auto mb-2" />
                    <h4 className="font-medium text-purple-900">Prioritization</h4>
                    <p className="text-sm text-purple-700 mt-1">Value and urgency ranking</p>
                  </div>
                </div>

                <div className="p-4 bg-gray-50 rounded-lg">
                  <h4 className="font-medium text-gray-900 mb-2">Current Process Performance</h4>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                    <div>
                      <span className="text-gray-600">Average Processing Time:</span>
                      <span className="font-medium ml-2">2.3 minutes</span>
                    </div>
                    <div>
                      <span className="text-gray-600">Accuracy Rate:</span>
                      <span className="font-medium ml-2 text-green-600">94.2%</span>
                    </div>
                    <div>
                      <span className="text-gray-600">Daily Throughput:</span>
                      <span className="font-medium ml-2">~150 leads</span>
                    </div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};
