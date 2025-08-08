import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Building2, Target, TrendingUp, FileText } from "lucide-react";
import type { Company } from "@/services/api";

interface CompanyInfoCardProps {
  company: Company;
}

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
            <Badge variant="secondary">{company.entityType}</Badge>
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

        {/* Qualification Score */}
        <div>
          <h4 className="font-semibold mb-3 flex items-center gap-2">
            <Target className="h-4 w-4" />
            Kwalificatiescore
          </h4>
          <div className="space-y-3">
            <div>
              <div className="flex justify-between items-center mb-1">
                <span className="text-sm font-medium">Financiële stabiliteit</span>
                <span className="text-sm text-muted-foreground">
                  {company.qualificationScore?.financialStability}%
                </span>
              </div>
              <Progress value={company.qualificationScore?.financialStability || 0} className="h-2" />
            </div>
            <div>
              <div className="flex justify-between items-center mb-1">
                <span className="text-sm font-medium">Apparatuurbehoefte</span>
                <span className="text-sm text-muted-foreground">
                  {company.qualificationScore?.equipmentNeed}%
                </span>
              </div>
              <Progress value={company.qualificationScore?.equipmentNeed || 0} className="h-2" />
            </div>
            <div>
              <div className="flex justify-between items-center mb-1">
                <span className="text-sm font-medium">Timing</span>
                <span className="text-sm text-muted-foreground">
                  {company.qualificationScore?.timing}%
                </span>
              </div>
              <Progress value={company.qualificationScore?.timing || 0} className="h-2" />
            </div>
            <div>
              <div className="flex justify-between items-center mb-1">
                <span className="text-sm font-medium">Beslissingsbevoegdheid</span>
                <span className="text-sm text-muted-foreground">
                  {company.qualificationScore?.decisionAuthority}%
                </span>
              </div>
              <Progress value={company.qualificationScore?.decisionAuthority || 0} className="h-2" />
            </div>
          </div>
        </div>

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