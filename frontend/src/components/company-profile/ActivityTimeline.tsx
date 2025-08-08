import { useMemo } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Calendar,
  Star,
  FileText,
  MessageSquare,
  CheckCircle,
  UserCheck,
  TrendingUp,
} from "lucide-react";
import { formatDistanceToNow } from "date-fns";
import { nl } from "date-fns/locale";
import type { Company } from "@/services/api";

interface ActivityTimelineProps {
  company: Company;
}

// Amsterdam timezone
const AMSTERDAM_TZ = "Europe/Amsterdam";

export const ActivityTimeline = ({ company }: ActivityTimelineProps) => {
  const activities = useMemo(() => {
    if (!company) return [];

    const activityList = [];
    
    // Parse dates properly - handle both ISO strings and fallback to null
    const parseDate = (dateString) => {
      if (!dateString || dateString === "Onbekend") return null;
      try {
        // If it's already an ISO string, parse it directly
        const date = new Date(dateString);
        return isNaN(date.getTime()) ? null : date;
      } catch {
        return null;
      }
    };

    const createdAt = parseDate(company.createdAt);
    const updatedAt = parseDate(company.lastActivity);

    // Lead Discovered
    if (createdAt) {
      activityList.push({
        date: createdAt,
        type: "discovery",
        title: "Lead ontdekt",
        description: `Gevonden via bron: ${company.sourceUrl}`,
        icon: Star,
        color: "text-yellow-600",
      });
    }

    // Recent News
    if (company.recentNews && updatedAt) {
      activityList.push({
        date: updatedAt,
        type: "research",
        title: "Recent nieuws gevonden",
        description: company.recentNews,
        icon: FileText,
        color: "text-blue-600",
      });
    }

    // Initial Reasoning
    if (company.notes && createdAt) {
      activityList.push({
        date: createdAt,
        type: "analysis",
        title: "Initiële analyse",
        description: company.notes,
        icon: MessageSquare,
        color: "text-green-600",
      });
    }

    // Contact Enrichment
    if (company.contactEnrichedAt) {
      const enrichedDate = parseDate(company.contactEnrichedAt);
      if (enrichedDate) {
        const contactCount = company.contactPersons?.length || 0;
        activityList.push({
          date: enrichedDate,
          type: "enrichment",
          title: "Contactverrijking voltooid",
          description: `${contactCount} contactpersonen gevonden en toegevoegd`,
          icon: UserCheck,
          color: "text-purple-600",
        });
      }
    }

    // Status Changes (would need to be tracked separately in a real app)
    if (company.status === "qualified" && updatedAt) {
      activityList.push({
        date: updatedAt,
        type: "qualification",
        title: "Lead gekwalificeerd",
        description: `Kwalificatiescore: ${company.score}`,
        icon: CheckCircle,
        color: "text-green-600",
      });
    }

    // Qualification Score Analysis
    if (company.qualificationReasoning && updatedAt) {
      activityList.push({
        date: updatedAt,
        type: "analysis",
        title: "Kwalificatie analyse",
        description: company.qualificationReasoning,
        icon: TrendingUp,
        color: "text-indigo-600",
      });
    }

    // Sort by date, newest first
    return activityList.sort((a, b) => b.date.getTime() - a.date.getTime());
  }, [company]);

  const formatTimeAgo = (date: Date) => {
    try {
      // Convert to Amsterdam timezone for display
      const amsterdamDate = new Date(
        date.toLocaleString("en-US", { timeZone: AMSTERDAM_TZ })
      );
      return formatDistanceToNow(amsterdamDate, {
        addSuffix: true,
        locale: nl,
      });
    } catch (error) {
      console.warn("Date formatting error:", error);
      return "Onbekende tijd";
    }
  };

  const getActivityBadge = (type: string) => {
    const badges = {
      discovery: { color: "bg-yellow-100 text-yellow-700", label: "Ontdekking" },
      research: { color: "bg-blue-100 text-blue-700", label: "Onderzoek" },
      analysis: { color: "bg-green-100 text-green-700", label: "Analyse" },
      enrichment: { color: "bg-purple-100 text-purple-700", label: "Verrijking" },
      qualification: { color: "bg-emerald-100 text-emerald-700", label: "Kwalificatie" },
    };
    const badge = badges[type] || badges.analysis;
    return <Badge className={badge.color}>{badge.label}</Badge>;
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Calendar className="h-5 w-5" />
          Activiteitentijdlijn
        </CardTitle>
      </CardHeader>
      <CardContent>
        {activities.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground">
            <Calendar className="h-12 w-12 mx-auto mb-4 opacity-50" />
            <p>Geen activiteiten beschikbaar</p>
          </div>
        ) : (
          <div className="space-y-4">
            {activities.map((activity, index) => {
              const IconComponent = activity.icon;
              return (
                <div key={index} className="flex gap-4">
                  <div className="flex flex-col items-center">
                    <div className={`p-2 rounded-full border-2 border-background shadow-sm bg-background`}>
                      <IconComponent className={`h-4 w-4 ${activity.color}`} />
                    </div>
                    {index < activities.length - 1 && (
                      <div className="w-px h-8 bg-border mt-2" />
                    )}
                  </div>
                  <div className="flex-1 pb-4">
                    <div className="flex items-center justify-between mb-2">
                      <h4 className="font-semibold text-sm">{activity.title}</h4>
                      <div className="flex items-center gap-2">
                        {getActivityBadge(activity.type)}
                        <span className="text-xs text-muted-foreground">
                          {formatTimeAgo(activity.date)}
                        </span>
                      </div>
                    </div>
                    <p className="text-sm text-muted-foreground leading-relaxed">
                      {activity.description}
                    </p>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </CardContent>
    </Card>
  );
};