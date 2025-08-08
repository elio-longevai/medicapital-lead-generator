import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Sparkles, Users, ArrowRight } from "lucide-react";
import { getScoreColorForDashboard, getStatusBadgeForDashboard } from "@/lib/ui-utils";

interface Company {
  id: number;
  company: string;
  industry: string;
  score: number;
  status: string;
}

interface TopProspectsProps {
  recentLeads: Company[];
  leadsLoading: boolean;
  onSelectCompany: (companyId: number) => void;
  onViewAllLeads: (tab: string) => void;
}

export const TopProspects = ({ recentLeads, leadsLoading, onSelectCompany, onViewAllLeads }: TopProspectsProps) => {
  return (
    <Card className="bg-white/80 backdrop-blur-sm border-0 shadow-xl">
      <CardHeader>
        <CardTitle className="flex items-center text-xl">
          <Sparkles className="h-6 w-6 mr-3 text-indigo-600" />
          Top Prospects
        </CardTitle>
        <CardDescription className="text-base">
          Hoogst scorende nieuwe leads
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        {leadsLoading ? (
          <div className="space-y-3">
            {[...Array(4)].map((_, index) => (
              <div
                key={`loading-lead-skeleton-${Date.now()}-${Math.random()}-${index}`}
                className="p-3 bg-slate-50 border border-slate-200 rounded-lg"
              >
                <div className="animate-pulse">
                  <div className="h-4 bg-slate-200 rounded w-3/4 mb-2" />
                  <div className="h-3 bg-slate-200 rounded w-1/2" />
                </div>
              </div>
            ))}
          </div>
        ) : recentLeads.length > 0 ? (
          <>
            {recentLeads.slice(0, 5).map((lead) => (
              <button
                key={lead.id}
                type="button"
                className="w-full p-3 bg-gradient-to-r from-slate-50 to-blue-50 border border-slate-200 rounded-lg hover:from-blue-50 hover:to-indigo-50 hover:border-blue-300 cursor-pointer transition-all duration-200 group text-left"
                onClick={() => onSelectCompany(lead.id)}
                aria-label={`Bekijk ${lead.company}`}
              >
                <div className="flex items-center justify-between mb-2">
                  <h4 className="font-semibold text-slate-900 group-hover:text-blue-900 truncate">
                    {lead.company}
                  </h4>
                  <div
                    className={`text-sm font-bold px-2 py-1 rounded-full ${getScoreColorForDashboard(lead.score)} border`}
                  >
                    {lead.score}
                  </div>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-slate-600 truncate">
                    {lead.industry}
                  </span>
                  {getStatusBadgeForDashboard(lead.status)}
                </div>
              </button>
            ))}
            <Button
              variant="outline"
              className="w-full mt-4 bg-gradient-to-r from-blue-50 to-indigo-50 hover:from-blue-100 hover:to-indigo-100 border-blue-200 text-blue-700"
              onClick={() => onViewAllLeads("leads")}
            >
              Alle Leads Bekijken
              <ArrowRight className="h-4 w-4 ml-2" />
            </Button>
          </>
        ) : (
          <div className="text-center py-8">
            <div className="w-16 h-16 bg-gradient-to-br from-slate-100 to-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <Users className="h-8 w-8 text-slate-400" />
            </div>
            <p className="text-slate-600 text-sm">
              Geen recente leads gevonden
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
};