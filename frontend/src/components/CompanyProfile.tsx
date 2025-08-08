import { useState, useRef, useEffect } from "react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useUpdateCompanyStatus, useEnrichCompanyContacts, useCompany } from "@/hooks/useCompanies";
import { useContactEnrichmentStatus } from "@/hooks/useContactEnrichmentStatus";
import { toast } from "sonner";
import type { Company } from "@/services/api";
import {
  ProfileHeader,
  CompanyInfoCard,
  ContactListCard,
  ActivityTimeline,
  ActionPanel,
} from "./company-profile";

interface CompanyProfileProps {
	companyId: number;
	onBack: () => void;
}

export const CompanyProfile = ({ companyId, onBack }: CompanyProfileProps) => {
	const updateStatusMutation = useUpdateCompanyStatus();
	const enrichContactsMutation = useEnrichCompanyContacts();
	
	// Fetch fresh company data
	const { data: company, isLoading, error } = useCompany(companyId);
	
	// Real-time enrichment status polling
	const enrichmentStatus = useContactEnrichmentStatus(companyId);
	
	// Helper function to check if enrichment is pending
	const isEnrichmentPending = () => {
		return enrichContactsMutation.isPending || 
			   enrichmentStatus.data?.status === 'pending' ||
			   company?.contactEnrichmentStatus === 'pending';
	};

	// Track enrichment status changes for toast notifications
	const prevStatusRef = useRef(enrichmentStatus.data?.status);
	useEffect(() => {
		const currentStatus = enrichmentStatus.data?.status;
		const prevStatus = prevStatusRef.current;
		
		// Show toast when enrichment completes or fails (only on status change)
		if (prevStatus && prevStatus !== currentStatus && currentStatus && company) {
			if (currentStatus === 'completed') {
				toast.success(`Contactverrijking voltooid voor ${company.company}! ${enrichmentStatus.data?.contactsFound || 0} contacten gevonden.`);
			} else if (currentStatus === 'failed') {
				toast.error(`Contactverrijking mislukt voor ${company.company}. Probeer het opnieuw.`);
			}
		}
		
		prevStatusRef.current = currentStatus;
	}, [enrichmentStatus.data?.status, enrichmentStatus.data?.contactsFound, company]);

	const handleStatusUpdate = (newStatus: string) => {
		updateStatusMutation.mutate(
			{ id: companyId, status: newStatus },
			{
				onSuccess: () => {
					toast.success("Status succesvol bijgewerkt");
				},
				onError: () => {
					toast.error("Fout bij het bijwerken van de status");
				},
			}
		);
	};

	const handleEnrichContacts = () => {
		enrichContactsMutation.mutate({ id: companyId }, {
			onSuccess: () => {
				toast.success("Contactverrijking gestart");
			},
			onError: () => {
				toast.error("Fout bij het starten van contactverrijking");
			},
		});
	};

	if (isLoading) {
		return (
			<div className="flex items-center justify-center min-h-[400px]">
				<div className="text-center">
					<div className="animate-spin h-8 w-8 border-4 border-primary border-t-transparent rounded-full mx-auto mb-4" />
					<p className="text-muted-foreground">Bedrijfsprofiel laden...</p>
				</div>
			</div>
		);
	}

	if (error || !company) {
		return (
			<div className="flex items-center justify-center min-h-[400px]">
				<div className="text-center">
					<p className="text-red-600 mb-4">Fout bij het laden van het bedrijfsprofiel</p>
					<button onClick={onBack} className="text-primary hover:underline">
						Terug naar overzicht
					</button>
				</div>
			</div>
		);
	}

	return (
		<div className="container mx-auto px-6 py-8">
			<ProfileHeader company={company} onBack={onBack} />

			<div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
				<div className="lg:col-span-2 space-y-8">
					<Tabs defaultValue="overview" className="w-full">
						<TabsList className="grid w-full grid-cols-3">
							<TabsTrigger value="overview">Overzicht</TabsTrigger>
							<TabsTrigger value="contacts">Contacten</TabsTrigger>
							<TabsTrigger value="activity">Activiteit</TabsTrigger>
						</TabsList>
						
						<TabsContent value="overview" className="mt-6">
							<CompanyInfoCard company={company} />
						</TabsContent>
						
						<TabsContent value="contacts" className="mt-6">
							<ContactListCard
								company={company}
								isEnrichmentPending={isEnrichmentPending()}
								enrichmentStatus={enrichmentStatus}
								onEnrichContacts={handleEnrichContacts}
							/>
						</TabsContent>
						
						<TabsContent value="activity" className="mt-6">
							<ActivityTimeline company={company} />
						</TabsContent>
					</Tabs>
				</div>

				<div className="space-y-6">
					<ActionPanel
						company={company}
						onUpdateStatus={handleStatusUpdate}
						updateStatusMutation={updateStatusMutation}
					/>
				</div>
			</div>
		</div>
	);
};