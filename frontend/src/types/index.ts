export interface CityRanking {
  city: string
  value: number
}

export interface CityRankingsResponse {
  rankings: CityRanking[]
}

export interface CitiesListResponse {
  cities: string[]
}

export interface CityHistoricalRecord {
  year: number
  [key: string]: unknown
}

export interface CityHistoricalResponse {
  historical_data: CityHistoricalRecord[]
}

export interface AggregationGroupItem {
  city?: string
  region?: string
  group_key?: string
  sum?: number
  avg?: number
  min?: number
  max?: number
  count?: number
  city_count?: number
  total?: number
  metrics?: Record<string, number>
}

export interface AggregationResponse {
  result: {
    groups: AggregationGroupItem[]
  }
}

export interface TimeSeriesValue {
  city?: string
  group_key?: string
  year?: number | string
  time?: number | string
  value?: number
  avg?: number
}

export interface TimeSeriesGroup {
  city?: string
  group_key?: string
  values?: TimeSeriesValue[]
}

export interface TimeSeriesResponse {
  time_series: {
    groups?: TimeSeriesGroup[]
  } | TimeSeriesValue[]
}

export interface EnterpriseCostDetails {
  [key: string]: number
}

export interface EnterpriseSupplyDetails {
  [key: string]: number
}

export interface EnterprisePolicyDetails {
  [key: string]: number
}

export interface EnterpriseDetails {
  cost_details?: EnterpriseCostDetails
  supply_details?: EnterpriseSupplyDetails
  policy_details?: EnterprisePolicyDetails
}

export interface EnterpriseMethodology {
  scoring_basis?: string
  weight_source?: string
}

export interface EnterpriseResult {
  city?: string
  business_cost_score?: number
  supply_chain_score?: number
  policy_benefit_score?: number
  total_score?: number
  details?: EnterpriseDetails
  suggestions?: string[]
  methodology?: EnterpriseMethodology
}

export interface FiscalLeverageData {
  score?: number
  revenue_efficiency?: number
  expenditure_efficiency?: number
}

export interface IndustryDriveData {
  score?: number
  employment_contribution?: number
  tax_contribution?: number
}

export interface GovernmentDataSection {
  fiscal_leverage?: FiscalLeverageData
  industry_drive?: IndustryDriveData
}

export interface GovernmentResult {
  data?: GovernmentDataSection
  note?: string
  fiscal_leverage?: FiscalLeverageData
  industry_drive?: IndustryDriveData
}

export interface CityInfo {
  code: string
  name: string
  province?: string
}

export interface InteractiveCitiesResponse {
  cities: CityInfo[]
}

export interface ExportResponseData {
  file_content: string
  file_name: string
}

// Table data types for DataManager
export interface TableDataRow {
  year: string
  quarter?: string
  region: string
  indicator: string
  value: number
  unit: string
  source: string
  updateTime?: string
  type?: string
}

export interface FilterForm {
  type: string
  region: string
  years: string[]
  keyword: string
}

export interface AggregationFormData {
  groupBy: string[]
  metrics: string[]
  sortBy: string | null
  sortOrder: string
  limit: number
}

export interface UploadFormData {
  format: string
  validate: boolean
}

export interface ExportFormData {
  format: string
  filename: string
  range: string
}

export interface CityCompareForm {
  cities: string[]
  year: string
  indicators: string[]
}

export interface FilterFormData {
  indicator: string
  year: string
  limit: number
}

export interface TimeSeriesDisplayItem {
  city: string
  year: number | string
  value: number
}

export interface AggregationCityItem {
  city: string
  sum: number
  avg: number
  min: number
  max: number
  count: number
}

export interface AggregationRegionItem {
  region: string
  city_count: number
  avg: number
  total: number
}