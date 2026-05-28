// TypeScript 类型定义

// 数据相关类型
export interface BasicData {
  region: string;
  industry: string;
  year: number;
  data: {
    macro_economy: {
      gdp: number;
      gdp_growth: number;
      cpi: number;
      pmi: number;
    };
    semiconductor_industry: {
      output_value: number;
      market_share: {
        domestic: number;
        global: number;
      };
    };
  };
}

export interface TrendData {
  years: number[];
  series: {
    name: string;
    data: number[];
  }[];
}

// 企业端分析结果类型
export interface EnterpriseAnalysisResult {
  land_cost: {
    city_average: number;
    city_average_yoy: number;
  };
  labor_cost: {
    average_salary: number;
    yoy_growth: number;
  };
  supply_chain: {
    chain_coverage: {
      upstream: number;
      midstream: number;
      downstream: number;
    };
    localization_rate: number;
  };
  comprehensive: {
    shenzhen_index: number;
    ranking: number;
  };
  recommendations: Array<{
    type: string;
    suggestion: string;
  }>;
}

// 政府端分析结果类型
export interface GovernmentAnalysisResult {
  fiscal_leverage: {
    fiscal_revenue: number;
    fiscal_expenditure: number;
    total_support: number;
    leverage_ratio: number;
  };
  industry_drive: {
    employment_effect: {
      total: number;
    };
  };
  policy_suggestions: Array<{
    priority: string;
    title: string;
    content: string;
  }>;
}

// API 请求类型
export interface AnalysisRequest {
  region: string;
  industry: string;
  year: number;
}

// 图表相关类型
export interface ChartData {
  categories: string[];
  series: {
    name: string;
    data: number[];
  }[];
}
