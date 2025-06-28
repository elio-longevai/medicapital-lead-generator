import { formatDistanceToNow, format, parseISO, isValid } from "date-fns";
import { nl } from "date-fns/locale";

/**
 * Formats a timestamp to a human-readable "time ago" format in Dutch
 * @param timestamp - ISO timestamp string or Date object
 * @returns Formatted string like "3 dagen geleden" or "Onbekend" if invalid
 */
export function formatTimeAgo(timestamp: string | Date | null | undefined): string {
    if (!timestamp) return "Onbekend";

    try {
        const date = typeof timestamp === 'string' ? parseISO(timestamp) : timestamp;

        if (!isValid(date)) {
            return "Onbekend";
        }

        return formatDistanceToNow(date, {
            addSuffix: true,
            locale: nl,
        });
    } catch (error) {
        console.warn('Error formatting timestamp:', timestamp, error);
        return "Onbekend";
    }
}

/**
 * Formats a timestamp to a readable date format in Dutch
 * @param timestamp - ISO timestamp string or Date object  
 * @param formatString - Optional format string (defaults to "d MMM yyyy 'om' HH:mm")
 * @returns Formatted string like "28 jun 2025 om 13:20" or "Onbekend" if invalid
 */
export function formatDateTime(
    timestamp: string | Date | null | undefined,
    formatString: string = "d MMM yyyy 'om' HH:mm"
): string {
    if (!timestamp) return "Onbekend";

    try {
        const date = typeof timestamp === 'string' ? parseISO(timestamp) : timestamp;

        if (!isValid(date)) {
            return "Onbekend";
        }

        return format(date, formatString, { locale: nl });
    } catch (error) {
        console.warn('Error formatting timestamp:', timestamp, error);
        return "Onbekend";
    }
}

/**
 * Formats a timestamp to just the date in Dutch
 * @param timestamp - ISO timestamp string or Date object
 * @returns Formatted string like "28 juni 2025" or "Onbekend" if invalid
 */
export function formatDate(timestamp: string | Date | null | undefined): string {
    return formatDateTime(timestamp, "d MMMM yyyy");
} 