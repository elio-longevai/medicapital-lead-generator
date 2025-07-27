# Contact Enrichment Script

This script enriches existing companies with detailed contact information by searching the web for executives, managers, and key decision makers.

## Overview

The contact enrichment functionality adds comprehensive contact information to your lead database including:

- **Contact Person Details**: Name, role/title, email, phone number
- **Department Information**: HR, Finance, Sales, Technology, etc.
- **Seniority Levels**: C-Level, Director, Manager, Specialist
- **LinkedIn Profiles**: Direct links to professional profiles
- **Enrichment Status**: Tracking of completion and quality

## Usage

### Basic Usage

```bash
# Enrich all companies that haven't been processed yet
python scripts/enrich_contacts.py

# Enrich companies for a specific ICP
python scripts/enrich_contacts.py --icp "Duurzaamheid"

# Enrich companies in a specific country
python scripts/enrich_contacts.py --country "NL"

# Combine filters
python scripts/enrich_contacts.py --icp "Medisch" --country "NL"
```

### Advanced Options

```bash
# Process with custom batch size (default: 5)
python scripts/enrich_contacts.py --batch-size 3

# Limit number of companies (useful for testing)
python scripts/enrich_contacts.py --max-companies 10

# Enable verbose logging
python scripts/enrich_contacts.py --verbose

# Full example
python scripts/enrich_contacts.py \
  --icp "Duurzaamheid" \
  --country "NL" \
  --batch-size 3 \
  --max-companies 50 \
  --verbose
```

## Script Features

### Smart Processing
- **Incremental Updates**: Only processes companies that haven't been enriched yet
- **Resume Capability**: Can be safely interrupted and restarted
- **Rate Limiting**: Respects API limits with built-in delays
- **Batch Processing**: Processes companies in configurable batches

### Error Handling
- **Graceful Failures**: Individual company failures don't stop the entire process
- **Status Tracking**: Marks companies as 'pending', 'completed', or 'failed'
- **Detailed Logging**: Comprehensive logs for debugging and monitoring

### Data Quality
- **Contact Validation**: Validates email formats and phone numbers
- **Duplicate Detection**: Removes duplicate contacts within the same company
- **Generic Email Filtering**: Skips generic addresses like info@, sales@, etc.

## Output

### Contact Person Schema
Each enriched contact includes:
```json
{
  "name": "John Doe",
  "role": "Chief Financial Officer", 
  "email": "j.doe@company.com",
  "phone": "+31 20 123 4567",
  "department": "Finance",
  "seniority_level": "C-Level",
  "linkedin_url": "https://linkedin.com/in/johndoe"
}
```

### Enrichment Metadata
- `contact_enrichment_status`: 'completed', 'partial', 'failed', or 'pending'
- `contact_enriched_at`: Timestamp of last enrichment attempt
- `contact_search_summary`: Statistics about search queries executed

### Frontend Integration
The enriched data automatically appears in the company profile's "Contactinformatie" section with:
- **Beautiful Contact Cards**: Each contact person displayed in an elegant card
- **Role-Based Badges**: Color-coded seniority indicators
- **Direct Actions**: Click-to-email, click-to-call functionality
- **LinkedIn Integration**: Direct links to professional profiles

## Performance & Monitoring

### Logging
- **File Logging**: Detailed logs saved to `contact_enrichment_YYYYMMDD_HHMMSS.log`
- **Console Output**: Real-time progress updates
- **Statistics**: Success rates, timing, and error summaries

### Performance Tuning
- **Batch Size**: Adjust `--batch-size` based on your system capabilities
- **Rate Limiting**: Built-in 5-second delays between batches
- **Concurrent Requests**: Limited to 2 simultaneous API calls per batch

### API Usage
The script uses free web search APIs (DuckDuckGo) to minimize costs. For production use with higher volume, consider upgrading to:
- Google Custom Search API
- SerpAPI
- Other premium search providers

## Troubleshooting

### Common Issues

**No companies found:**
```bash
# Check filter criteria
python scripts/enrich_contacts.py --icp "YourICP" --verbose

# Remove filters to see all companies needing enrichment
python scripts/enrich_contacts.py --max-companies 5
```

**High failure rate:**
- Check internet connectivity
- Verify company names are accurate
- Consider reducing batch size
- Enable verbose logging to see detailed errors

**Script interrupted:**
- Simply restart the script - it will resume from where it left off
- Use `--max-companies` for testing before full runs

### Database Issues
The script updates the MongoDB database directly. Make sure:
- Database connection is working
- Required permissions are in place
- Backup your data before large runs

## Integration with Main Pipeline

The contact enrichment is automatically integrated into the main lead generation pipeline:

1. **Web Search & Triage**: Companies are discovered and triaged
2. **Company Enrichment**: Basic company data is extracted from websites  
3. **Contact Enrichment**: ← New step automatically runs here
4. **Database Storage**: All data including contacts is saved

For existing companies, use this script to retroactively add contact information.

## Future Enhancements

- **Email Verification**: Validate email deliverability
- **Phone Validation**: Verify phone number accuracy
- **Social Media Integration**: Expand beyond LinkedIn
- **AI-Powered Outreach**: Generate personalized messages
- **CRM Integration**: Export contacts directly to sales tools