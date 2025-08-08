import { Card, CardContent } from "@/components/ui/card";
import { Users, Target } from "lucide-react";
import { getIcpMetadata } from "@/lib/icp-utils";

interface DashboardData {
  totalLeads: number;
  leadsThisWeek: number;
  topIndustries: Array<{ industry: string }>;
}

interface DashboardMetricsProps {
  dashboardData?: DashboardData;
  dashboardLoading: boolean;
}

export const DashboardMetrics = ({ dashboardData, dashboardLoading }: DashboardMetricsProps) => {
  if (dashboardLoading) {
    return (
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {[...Array(2)].map((_, index) => (
          <Card
            key={`loading-metric-skeleton-${Date.now()}-${index}`}
            className="bg-white/80 backdrop-blur-sm border-0 shadow-xl"
          >
            <CardContent className="p-8">
              <div className="animate-pulse">
                <div className="h-6 bg-slate-200 rounded w-3/4 mb-6" />
                <div className="h-12 bg-slate-200 rounded w-1/2 mb-4" />
                <div className="h-4 bg-slate-200 rounded w-full" />
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
      <Card className="bg-gradient-to-br from-blue-50 via-indigo-50 to-blue-100 border-0 shadow-xl hover:shadow-2xl transition-all duration-300 overflow-hidden relative">
        <div className="absolute top-0 right-0 w-32 h-32 bg-blue-200/20 rounded-full -translate-y-16 translate-x-16" />
        <div className="absolute bottom-0 left-0 w-24 h-24 bg-blue-300/10 rounded-full translate-y-12 -translate-x-12" />
        <CardContent className="p-8 relative">
          <div className="flex items-start justify-between mb-6">
            <div className="flex items-center">
              <div className="p-4 bg-blue-100 rounded-2xl mr-4 shadow-sm">
                <Users className="h-8 w-8 text-blue-600" />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-blue-900 mb-1">
                  Totaal Leads Ontdekt
                </h3>
                <p className="text-sm text-blue-700">
                  Over alle doelgroepen verzameld
                </p>
              </div>
            </div>
          </div>
          <div className="mb-4">
            <div className="text-4xl font-bold text-slate-900 mb-2">
              {dashboardData?.totalLeads || 0}
            </div>
            <div className="flex items-center text-sm text-blue-700">
              <div className="w-2 h-2 bg-blue-500 rounded-full mr-2" />
              {dashboardData?.leadsThisWeek || 0} nieuwe leads deze week
            </div>
          </div>
          <div className="bg-white/60 backdrop-blur-sm rounded-xl p-4 border border-blue-200/50">
            <div className="grid grid-cols-3 gap-4 text-center">
              <div>
                <div className="text-lg font-bold text-slate-900">
                  {(dashboardData?.totalLeads || 0) - (dashboardData?.leadsThisWeek || 0)}
                </div>
                <div className="text-xs text-slate-600">
                  Bestaande Leads
                </div>
              </div>
              <div>
                <div className="text-lg font-bold text-slate-900">
                  {dashboardData?.leadsThisWeek || 0}
                </div>
                <div className="text-xs text-slate-600">
                  Deze Week
                </div>
              </div>
              <div>
                <div className="text-lg font-bold text-emerald-600">
                  +{dashboardData?.totalLeads && dashboardData?.leadsThisWeek 
                    ? Math.round((dashboardData.leadsThisWeek / dashboardData.totalLeads) * 100)
                    : 0}%
                </div>
                <div className="text-xs text-slate-600">Groei</div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card className="bg-gradient-to-br from-emerald-50 via-green-50 to-emerald-100 border-0 shadow-xl hover:shadow-2xl transition-all duration-300 overflow-hidden relative">
        <div className="absolute top-0 right-0 w-32 h-32 bg-emerald-200/20 rounded-full -translate-y-16 translate-x-16" />
        <div className="absolute bottom-0 left-0 w-24 h-24 bg-emerald-300/10 rounded-full translate-y-12 -translate-x-12" />
        <CardContent className="p-8 relative">
          <div className="flex items-start justify-between mb-6">
            <div className="flex items-center">
              <div className="p-4 bg-emerald-100 rounded-2xl mr-4 shadow-sm">
                <Target className="h-8 w-8 text-emerald-600" />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-emerald-900 mb-1">
                  Actieve Doelgroepen
                </h3>
                <p className="text-sm text-emerald-700">
                  Geautomatiseerde campagnes actief
                </p>
              </div>
            </div>
          </div>
          <div className="mb-4">
            <div className="text-4xl font-bold text-slate-900 mb-2">
              {dashboardData?.topIndustries.length || "3"}
            </div>
            <div className="flex items-center text-sm text-emerald-700">
              <div className="w-2 h-2 bg-emerald-500 rounded-full mr-2" />
              Campagnes draaien 24/7 automatisch
            </div>
          </div>
          <div className="bg-white/60 backdrop-blur-sm rounded-xl p-4 border border-emerald-200/50">
            <div className="grid grid-cols-3 gap-4 text-center">
              {dashboardData?.topIndustries &&
              dashboardData.topIndustries.length > 0 ? (
                dashboardData.topIndustries.map((icp) => {
                  const metadata = getIcpMetadata(icp.industry);
                  return (
                    <div key={icp.industry}>
                      <div className="text-lg font-bold">
                        {metadata.emoji}
                      </div>
                      <div className="text-xs text-slate-600 truncate">
                        {metadata.name}
                      </div>
                    </div>
                  );
                })
              ) : (
                <>
                  <div>
                    <div className="text-lg font-bold">🏥</div>
                    <div className="text-xs text-slate-600 truncate">
                      Zorgverlening
                    </div>
                  </div>
                  <div>
                    <div className="text-lg font-bold">🌱</div>
                    <div className="text-xs text-slate-600 truncate">
                      Duurzaamheid
                    </div>
                  </div>
                  <div>
                    <div className="text-lg font-bold">⚡️</div>
                    <div className="text-xs text-slate-600 truncate">
                      Energie
                    </div>
                  </div>
                </>
              )}
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};