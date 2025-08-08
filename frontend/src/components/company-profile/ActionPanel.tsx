import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  CheckCircle,
  AlertCircle,
  Clock,
  Target,
  Check,
  Trash2,
} from "lucide-react";
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
import { getStatusBadge } from "@/lib/ui-utils";
import type { Company } from "@/services/api";

interface ActionPanelProps {
  company: Company;
  onUpdateStatus: (status: string) => void;
  updateStatusMutation: {
    isPending: boolean;
  };
}

export const ActionPanel = ({ 
  company, 
  onUpdateStatus, 
  updateStatusMutation 
}: ActionPanelProps) => {
  const [isRejectDialogOpen, setIsRejectDialogOpen] = useState(false);

  const handleStatusUpdate = (newStatus: string) => {
    onUpdateStatus(newStatus);
    if (newStatus === "rejected") {
      setIsRejectDialogOpen(false);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "qualified":
        return <CheckCircle className="h-4 w-4 text-green-600" />;
      case "rejected":
        return <AlertCircle className="h-4 w-4 text-red-600" />;
      case "in_review":
        return <Clock className="h-4 w-4 text-yellow-600" />;
      case "contacted":
        return <Target className="h-4 w-4 text-purple-600" />;
      default:
        return <Clock className="h-4 w-4 text-blue-600" />;
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Target className="h-5 w-5" />
          Acties
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium">Huidige status:</span>
          <div className="flex items-center gap-2">
            {getStatusIcon(company.status)}
            {getStatusBadge(company.status)}
          </div>
        </div>

        <div className="space-y-2">
          <h4 className="text-sm font-medium">Status bijwerken:</h4>
          <div className="grid grid-cols-2 gap-2">
            <Button
              variant={company.status === "in_review" ? "default" : "outline"}
              size="sm"
              onClick={() => handleStatusUpdate("in_review")}
              disabled={updateStatusMutation.isPending || company.status === "in_review"}
              className="flex items-center gap-2 text-xs"
            >
              <Clock className="h-3 w-3" />
              In Review
            </Button>
            
            <Button
              variant={company.status === "qualified" ? "default" : "outline"}
              size="sm"
              onClick={() => handleStatusUpdate("qualified")}
              disabled={updateStatusMutation.isPending || company.status === "qualified"}
              className="flex items-center gap-2 text-xs"
            >
              <Check className="h-3 w-3" />
              Kwalificeren
            </Button>
            
            <Button
              variant={company.status === "contacted" ? "default" : "outline"}
              size="sm"
              onClick={() => handleStatusUpdate("contacted")}
              disabled={updateStatusMutation.isPending || company.status === "contacted"}
              className="flex items-center gap-2 text-xs"
            >
              <Target className="h-3 w-3" />
              Benaderd
            </Button>
            
            <AlertDialog open={isRejectDialogOpen} onOpenChange={setIsRejectDialogOpen}>
              <AlertDialogTrigger asChild>
                <Button
                  variant="outline"
                  size="sm"
                  disabled={updateStatusMutation.isPending || company.status === "rejected"}
                  className="flex items-center gap-2 text-xs border-red-200 text-red-600 hover:bg-red-50"
                >
                  <Trash2 className="h-3 w-3" />
                  Afwijzen
                </Button>
              </AlertDialogTrigger>
              <AlertDialogContent>
                <AlertDialogHeader>
                  <AlertDialogTitle>Lead afwijzen</AlertDialogTitle>
                  <AlertDialogDescription>
                    Weet je zeker dat je "{company.company}" wilt afwijzen? Deze actie kan
                    ongedaan gemaakt worden door de status later te wijzigen.
                  </AlertDialogDescription>
                </AlertDialogHeader>
                <AlertDialogFooter>
                  <AlertDialogCancel>Annuleren</AlertDialogCancel>
                  <AlertDialogAction
                    onClick={() => handleStatusUpdate("rejected")}
                    className="bg-red-600 hover:bg-red-700"
                  >
                    Afwijzen
                  </AlertDialogAction>
                </AlertDialogFooter>
              </AlertDialogContent>
            </AlertDialog>
          </div>
        </div>

        {updateStatusMutation.isPending && (
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Clock className="h-4 w-4 animate-spin" />
            Status wordt bijgewerkt...
          </div>
        )}
      </CardContent>
    </Card>
  );
};