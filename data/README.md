# Data

## Why the CSVs are not in this repo

The property assessment files are 50-100 MB each. Rather than bloating the
repo, the data is pulled directly from the City of Edmonton Open Data Portal
using the download script.

## How to get the data

From the project root, run:

```bash
python scripts/download_data.py
```

This will create four files in this folder:

| File | Description | Approx. size |
|------|-------------|-------------|
| `property_assessment_2022.csv` | Assessment year 2022 | ~60 MB |
| `property_assessment_2023.csv` | Assessment year 2023 | ~65 MB |
| `property_assessment_2024.csv` | Assessment year 2024 | ~70 MB |
| `property_assessment_combined.csv` | All three years merged | ~195 MB |

The script uses the Socrata Open Data API. No API key is required for this
dataset, but Socrata may throttle unauthenticated requests. If downloads are
slow, wait a minute and re-run.

## Data source

- **Portal:** [Edmonton Open Data](https://data.edmonton.ca)
- **Dataset:** Property Assessment Data (Historical)
- **Endpoint:** `https://data.edmonton.ca/resource/qi6a-xuwt`
- **License:** Open Government License (City of Edmonton)
- **Last verified:** March 2026

## Data dictionary

| Column | API field name | Type | Description |
|--------|---------------|------|-------------|
| Account Number | `account_number` | String | Unique property identifier, stable across years |
| Assessment Year | `assessment_year` | Integer | The tax year the assessment applies to |
| Suite | `suite` | String | Unit/suite number (null for single-family homes) |
| House Number | `house_number` | String | Street number |
| Street Name | `street_name` | String | Street name |
| Neighbourhood | `neighbourhood_name` | String | City-designated neighbourhood name |
| Latitude | `latitude` | Float | Property latitude coordinate |
| Longitude | `longitude` | Float | Property longitude coordinate |
| Year Built | `year_built` | Integer | Year the primary structure was built |
| Garage | `garage` | String | Garage type (Y/N or descriptive code) |
| Zoning | `zoning` | String | Municipal zoning code (e.g. RF1, RF3, RA7) |
| Lot Size | `lot_size` | Float | Lot area in square feet |
| Assessed Value | `assessed_value` | Float | City-assessed market value in CAD |
| Assessment Class 1 | `mill_class_1` | String | Primary tax class (Residential, Non Residential, etc.) |
| Assessment Class % 1 | `tax_class_pct_1` | Float | Percentage allocated to primary tax class |

## Zoning code reference

The raw dataset contains 50+ zoning codes. For analysis, these are grouped
into broader categories:

| Zoning code(s) | Grouped category |
|----------------|-----------------|
| RF1 | Single detached residential |
| RF2 | Low density infill |
| RF3 | Small scale infill |
| RF5 | Row housing |
| RF6 | Medium density multiple family |
| RA7, RA8, RA9 | Apartment (low, medium, high rise) |
| RPL | Planned lot residential |
| CSC, CB1, CB2 | Commercial |
| DC1, DC2 | Direct control (custom) |
| AG | Agricultural |

The grouping used in the analysis notebook maps these to five categories:
Single Family, Row/Townhouse, Apartment, Commercial, and Other.

## Notes

- Assessed value reflects the City's estimate of market value as of July 1 of
  the prior year. It is not the sale price.
- Properties with $0 or null assessed values exist in the data and are filtered
  out during cleaning.
- The `account_number` field is used to track the same property across years.
  Properties that were newly built or demolished will not match across all
  three years.
