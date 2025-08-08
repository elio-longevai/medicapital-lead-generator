import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import {
  User,
  Mail,
  Phone,
  ExternalLink as LinkedinIcon,
  Crown,
  UserCheck,
  RefreshCw,
  CheckCircle,
  AlertCircle,
  Clock,
} from "lucide-react";
import type { Company, Contact } from "@/services/api";

interface ContactListCardProps {
  company: Company;
  isEnrichmentPending: boolean;
  enrichmentStatus: {
    data?: {
      status?: string;
      progress?: number;
      currentStep?: string;
      contactsFound?: number;
    };
  };
  onEnrichContacts: () => void;
}

export const ContactListCard = ({ 
  company, 
  isEnrichmentPending, 
  enrichmentStatus, 
  onEnrichContacts 
}: ContactListCardProps) => {
  const contacts = company.contactPersons || [];
  
  const getContactIcon = (contact: Contact) => {
    const title = contact.title?.toLowerCase() || '';
    if (title.includes('ceo') || title.includes('founder') || title.includes('owner') || title.includes('director')) {
      return <Crown className="h-4 w-4 text-yellow-600" />;
    }
    if (title.includes('manager') || title.includes('lead') || title.includes('head')) {
      return <UserCheck className="h-4 w-4 text-blue-600" />;
    }
    return <User className="h-4 w-4 text-gray-600" />;
  };

  const renderEnrichmentStatus = () => {
    const status = enrichmentStatus?.data?.status || company.contactEnrichmentStatus;
    const progress = enrichmentStatus?.data?.progress || 0;
    const currentStep = enrichmentStatus?.data?.currentStep;
    const contactsFound = enrichmentStatus?.data?.contactsFound || contacts.length;

    if (status === 'pending') {
      return (
        <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
          <div className="flex items-center gap-2 mb-2">
            <Clock className="h-4 w-4 text-blue-600" />
            <span className="text-sm font-medium text-blue-900">Contactverrijking bezig...</span>
          </div>
          {progress > 0 && (
            <>
              <Progress value={progress} className="h-2 mb-2" />
              <p className="text-xs text-blue-700">
                {Math.round(progress)}% voltooid
                {currentStep && ` - ${currentStep}`}
              </p>
            </>
          )}
        </div>
      );
    }

    if (status === 'completed') {
      return (
        <div className="mb-4 p-3 bg-green-50 border border-green-200 rounded-lg">
          <div className="flex items-center gap-2">
            <CheckCircle className="h-4 w-4 text-green-600" />
            <span className="text-sm font-medium text-green-900">
              Contactverrijking voltooid! {contactsFound} contacten gevonden.
            </span>
          </div>
        </div>
      );
    }

    if (status === 'failed') {
      return (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
          <div className="flex items-center gap-2">
            <AlertCircle className="h-4 w-4 text-red-600" />
            <span className="text-sm font-medium text-red-900">
              Contactverrijking mislukt. Probeer het opnieuw.
            </span>
          </div>
        </div>
      );
    }

    return null;
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <User className="h-5 w-5" />
            Contactpersonen ({contacts.length})
          </CardTitle>
          <Button
            variant="outline"
            size="sm"
            onClick={onEnrichContacts}
            disabled={isEnrichmentPending}
          >
            {isEnrichmentPending ? (
              <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
            ) : (
              <UserCheck className="h-4 w-4 mr-2" />
            )}
            {contacts.length > 0 ? 'Verrijken' : 'Contacten zoeken'}
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        {renderEnrichmentStatus()}
        
        {contacts.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground">
            <User className="h-12 w-12 mx-auto mb-4 opacity-50" />
            <p>Geen contactpersonen gevonden.</p>
            <p className="text-sm mt-1">Klik op "Contacten zoeken" om te beginnen met verrijking.</p>
          </div>
        ) : (
          <div className="max-h-96 overflow-y-auto space-y-3">
            {contacts.map((contact, index) => (
              <div
                key={index}
                className="p-4 border rounded-lg hover:bg-muted/50 transition-colors"
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-start gap-3">
                    {getContactIcon(contact)}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <h4 className="font-semibold text-sm truncate">
                          {contact.name}
                        </h4>
                        {contact.title && (
                          <Badge variant="secondary" className="text-xs">
                            {contact.title}
                          </Badge>
                        )}
                      </div>
                      
                      <div className="space-y-1">
                        {contact.email && (
                          <div className="flex items-center gap-2 text-xs text-muted-foreground">
                            <Mail className="h-3 w-3" />
                            <a
                              href={`mailto:${contact.email}`}
                              className="hover:text-primary hover:underline truncate"
                            >
                              {contact.email}
                            </a>
                          </div>
                        )}
                        
                        {contact.phone && (
                          <div className="flex items-center gap-2 text-xs text-muted-foreground">
                            <Phone className="h-3 w-3" />
                            <a
                              href={`tel:${contact.phone}`}
                              className="hover:text-primary hover:underline"
                            >
                              {contact.phone}
                            </a>
                          </div>
                        )}
                        
                        {contact.linkedin && (
                          <div className="flex items-center gap-2 text-xs text-muted-foreground">
                            <LinkedinIcon className="h-3 w-3" />
                            <a
                              href={contact.linkedin}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="hover:text-primary hover:underline"
                            >
                              LinkedIn
                            </a>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                  
                  <div className="flex gap-1 ml-2">
                    {contact.email && (
                      <Button variant="ghost" size="sm" asChild>
                        <a href={`mailto:${contact.email}`}>
                          <Mail className="h-3 w-3" />
                        </a>
                      </Button>
                    )}
                    {contact.linkedin && (
                      <Button variant="ghost" size="sm" asChild>
                        <a
                          href={contact.linkedin}
                          target="_blank"
                          rel="noopener noreferrer"
                        >
                          <LinkedinIcon className="h-3 w-3" />
                        </a>
                      </Button>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
};