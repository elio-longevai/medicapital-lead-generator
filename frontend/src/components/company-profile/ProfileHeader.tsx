import { Button } from "@/components/ui/button";
import { ArrowLeft, ExternalLink, Mail, Phone, MapPin, Users, Building2, Star, TrendingUp, Euro } from "lucide-react";
import { getStatusBadge, getScoreColor } from "@/lib/ui-utils";
import type { Company } from "@/services/api";

interface ProfileHeaderProps {
  company: Company;
  onBack: () => void;
}

export const ProfileHeader = ({ company, onBack }: ProfileHeaderProps) => {
  return (
    <div className="flex items-center justify-between mb-8">
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="sm" onClick={onBack}>
          <ArrowLeft className="h-4 w-4" />
          Terug
        </Button>
        <div className="flex flex-col">
          <div className="flex items-center gap-3">
            <h1 className="text-3xl font-bold tracking-tight">{company.company}</h1>
            {getStatusBadge(company.status)}
            <div className={`flex items-center gap-1 ${getScoreColor(company.score)}`}>
              <Star className="h-5 w-5 fill-current" />
              <span className="font-semibold text-lg">{company.score}</span>
            </div>
          </div>
          <div className="flex items-center gap-6 text-sm text-muted-foreground mt-2">
            <div className="flex items-center gap-1">
              <Building2 className="h-4 w-4" />
              <span>{company.industry}</span>
            </div>
            <div className="flex items-center gap-1">
              <MapPin className="h-4 w-4" />
              <span>{company.location}</span>
            </div>
            <div className="flex items-center gap-1">
              <Users className="h-4 w-4" />
              <span>{company.employees}</span>
            </div>
            {company.estimatedRevenue && (
              <div className="flex items-center gap-1">
                <Euro className="h-4 w-4" />
                <span>{company.estimatedRevenue}</span>
              </div>
            )}
          </div>
        </div>
      </div>
      <div className="flex items-center gap-2">
        {company.email && (
          <Button variant="outline" size="sm" asChild>
            <a href={`mailto:${company.email}`}>
              <Mail className="h-4 w-4 mr-2" />
              Email
            </a>
          </Button>
        )}
        {company.phone && (
          <Button variant="outline" size="sm" asChild>
            <a href={`tel:${company.phone}`}>
              <Phone className="h-4 w-4 mr-2" />
              Bellen
            </a>
          </Button>
        )}
        {company.website && (
          <Button variant="outline" size="sm" asChild>
            <a href={company.website} target="_blank" rel="noopener noreferrer">
              <ExternalLink className="h-4 w-4 mr-2" />
              Website
            </a>
          </Button>
        )}
      </div>
    </div>
  );
};