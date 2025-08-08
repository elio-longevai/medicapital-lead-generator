import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Building2, Target, TrendingUp, FileText } from "lucide-react";
import type { Company } from "@/services/api";

interface CompanyInfoCardProps {
  company: Company;
}

const getEntityTypeLabel = (entityType: string): string => {
  switch (entityType) {
    case 'end_user':
      return 'Eindgebruiker';
    case 'supplier':
      return 'Leverancier';
    default:
      return entityType;
  }
};

export const CompanyInfoCard = ({ company }: CompanyInfoCardProps) => {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Building2 className="h-5 w-5" />
          Bedrijfsinformatie
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {company.description && (
          <div>
            <h4 className="font-semibold mb-2">Beschrijving</h4>
            <p className="text-sm text-muted-foreground">{company.description}</p>
          </div>
        )}
        
        <div>
          <h4 className="font-semibold mb-2">Apparatuurbehoeften</h4>
          <p className="text-sm text-muted-foreground">{company.equipmentNeed}</p>
        </div>

        {company.entityType && (
          <div>
            <h4 className="font-semibold mb-2">Entiteitstype</h4>
            <Badge variant="secondary">{getEntityTypeLabel(company.entityType)}</Badge>
          </div>
        )}

        {company.subIndustry && (
          <div>
            <h4 className="font-semibold mb-2">Sub-industrie</h4>
            <Badge variant="outline">{company.subIndustry}</Badge>
          </div>
        )}

        {company.recentNews && (
          <div>
            <h4 className="font-semibold mb-2 flex items-center gap-2">
              <FileText className="h-4 w-4" />
              Recent nieuws
            </h4>
            <p className="text-sm text-muted-foreground">{company.recentNews}</p>
          </div>
        )}


        {company.qualificationReasoning && (
          <div>
            <h4 className="font-semibold mb-2 flex items-center gap-2">
              <TrendingUp className="h-4 w-4" />
              Kwalificatie redenering
            </h4>
            <p className="text-sm text-muted-foreground">{company.qualificationReasoning}</p>
          </div>
        )}

        {company.notes && (
          <div>
            <h4 className="font-semibold mb-2">Initiële redenering</h4>
            <p className="text-sm text-muted-foreground">{company.notes}</p>
          </div>
        )}
      </CardContent>
    </Card>
  );
};