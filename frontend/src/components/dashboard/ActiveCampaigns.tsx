import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Building2, Users, Globe, TrendingUp } from "lucide-react";
import { getIcpMetadata } from "@/lib/icp-utils";

interface DashboardData {
  totalLeads: number;
  leadsThisWeek: number;
  topIndustries: Array<{ industry: string }>;
}

interface ActiveCampaignsProps {
  dashboardData?: DashboardData;
}

export const ActiveCampaigns = ({ dashboardData }: ActiveCampaignsProps) => {
  return (
    <Card className="bg-white/80 backdrop-blur-sm border-0 shadow-xl">
      <CardHeader>
        <CardTitle className="flex items-center text-xl">
          <Building2 className="h-6 w-6 mr-3 text-blue-600" />
          Actieve Campagnes
        </CardTitle>
        <CardDescription className="text-base">
          Geautomatiseerde leadgeneratie per doelgroep met real-time
          resultaten
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {dashboardData?.topIndustries &&
        dashboardData.topIndustries.length > 0 ? (
          <div className="grid grid-cols-1 gap-4">
            {dashboardData.topIndustries.map(
              ({ industry: icpName }) => {
                const metadata = getIcpMetadata(icpName);
                const Icon = metadata.icon;
                return (
                  <div
                    key={icpName}
                    className={`group p-4 bg-gradient-to-r ${metadata.colors.gradient} rounded-xl border ${metadata.colors.border} transition-all duration-200`}
                  >
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center">
                        <div
                          className={`p-2 ${metadata.colors.bg} rounded-lg mr-3`}
                        >
                          <Icon
                            className={`h-5 w-5 ${metadata.colors.iconText}`}
                          />
                        </div>
                        <div>
                          <h4
                            className={`font-semibold ${metadata.colors.text}`}
                          >
                            {metadata.name}
                          </h4>
                          <p
                            className={`text-sm ${metadata.colors.text}`}
                          >
                            {metadata.description}
                          </p>
                        </div>
                      </div>
                      <Badge
                        className={`${metadata.colors.badgeBg} ${metadata.colors.badgeText} ${metadata.colors.badgeBorder}`}
                      >
                        Actief
                      </Badge>
                    </div>
                  </div>
                );
              },
            )}
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-4">
            {/* Fallback campaigns when no data */}
            <div className="group p-4 bg-gradient-to-r from-purple-50 to-violet-50 rounded-xl border border-purple-200 hover:border-purple-300 transition-all duration-200">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center">
                  <div className="p-2 bg-purple-100 rounded-lg mr-3">
                    <Users className="h-5 w-5 text-purple-600" />
                  </div>
                  <div>
                    <h4 className="font-semibold text-purple-900">
                      Zorgverlening (Eindgebruikers)
                    </h4>
                    <p className="text-sm text-purple-700">
                      Klinieken, praktijken & zorgcentra
                    </p>
                  </div>
                </div>
                <Badge className="bg-purple-100 text-purple-800 border-purple-300">
                  Actief
                </Badge>
              </div>
            </div>
            <div className="group p-4 bg-gradient-to-r from-emerald-50 to-green-50 rounded-xl border border-emerald-200 hover:border-emerald-300 transition-all duration-200">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center">
                  <div className="p-2 bg-emerald-100 rounded-lg mr-3">
                    <Globe className="h-5 w-5 text-emerald-600" />
                  </div>
                  <div>
                    <h4 className="font-semibold text-emerald-900">
                      Duurzaamheid (Leveranciers)
                    </h4>
                    <p className="text-sm text-emerald-700">
                      Producenten & installateurs van groene
                      technologie
                    </p>
                  </div>
                </div>
                <Badge className="bg-emerald-100 text-emerald-800 border-emerald-300">
                  Actief
                </Badge>
              </div>
            </div>
            <div className="group p-4 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-xl border border-blue-200 hover:border-blue-300 transition-all duration-200">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center">
                  <div className="p-2 bg-blue-100 rounded-lg mr-3">
                    <TrendingUp className="h-5 w-5 text-blue-600" />
                  </div>
                  <div>
                    <h4 className="font-semibold text-blue-900">
                      Duurzaamheid (Eindgebruikers)
                    </h4>
                    <p className="text-sm text-blue-700">
                      MKB+ bedrijven met hoog energieverbruik
                    </p>
                  </div>
                </div>
                <Badge className="bg-blue-100 text-blue-800 border-blue-300">
                  Actief
                </Badge>
              </div>
            </div>
          </div>
        )}

        <div className="pt-4 border-t border-slate-200 bg-slate-50 rounded-xl px-4 py-3">
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div className="flex items-center justify-between">
              <span className="text-slate-600">
                Deze week:
              </span>
              <span className="font-semibold text-slate-900">
                {dashboardData?.totalLeads && dashboardData?.leadsThisWeek 
                  ? `${Math.round((dashboardData.leadsThisWeek / dashboardData.totalLeads) * 100)}% groei`
                  : "0% groei"}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-slate-600">
                Actieve doelgroepen:
              </span>
              <span className="font-semibold text-blue-600">
                {dashboardData?.topIndustries?.length || 0}
              </span>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};