"""
国家经济数据分析平台 - Streamlit 前端
"""
import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.i18n import t, get_translations

# API 配置
API_BASE_URL = "http://localhost:8001"

# 页面配置
st.set_page_config(
    page_title="国家经济数据分析平台",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义样式
st.markdown("""
<style>
.stApp { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
.css-1d391kg {
    background-color: rgba(255, 255, 255, 0.95);
    border-radius: 16px;
    padding: 20px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.1);
}
.stMetric {
    background: rgba(255, 255, 255, 0.9);
    border-radius: 12px;
    padding: 15px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
}
.stButton > button {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border: none;
    border-radius: 10px;
    padding: 10px 24px;
    font-weight: 600;
}
</style>
""", unsafe_allow_html=True)


# ==================== API 辅助函数 ====================

def check_api():
    """检查 API 连接"""
    try:
        r = requests.get(f"{API_BASE_URL}/health", timeout=2)
        return r.status_code == 200
    except:
        return False


def fetch_available_indicators():
    """获取可推演指标"""
    try:
        r = requests.get(f"{API_BASE_URL}/api/v1/inference/available", timeout=5)
        if r.status_code == 200:
            return r.json()
    except:
        pass
    return None


def calculate_indicator(inputs, target, method="linear"):
    """计算指标"""
    try:
        r = requests.post(
            f"{API_BASE_URL}/api/v1/inference/calculate",
            json={"input_indicators": inputs, "target_indicator": target, "method": method},
            timeout=5
        )
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        st.error(f"计算失败: {e}")
    return None


def fetch_indicators(category=None, year=None):
    """获取指标列表"""
    try:
        params = {}
        if category:
            params["category"] = category
        if year:
            params["year"] = year
        r = requests.get(f"{API_BASE_URL}/api/v1/indicators/", params=params, timeout=5)
        if r.status_code == 200:
            return r.json()
    except:
        pass
    return None


def scrape_data(source="nbs"):
    """采集数据"""
    try:
        r = requests.post(
            f"{API_BASE_URL}/api/v1/scrape/",
            json={"source": source},
            timeout=60
        )
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        st.error(f"采集失败: {e}")
    return None


# ==================== 会话状态 ====================

if 'language' not in st.session_state:
    st.session_state.language = 'zh'

lang = st.session_state.language
tr = get_translations(lang)


# ==================== 侧边栏 ====================

with st.sidebar:
    st.markdown("""
    <div style="text-align: center; padding: 20px 0;">
        <h1 style="font-size: 24px; color: white; margin: 0;">📊 NEDAP</h1>
        <p style="color: rgba(255,255,255,0.7); font-size: 12px; margin: 5px 0;">国家经济数据分析平台</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # 语言切换
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🇺🇸 EN", use_container_width=True):
            st.session_state.language = 'en'
            st.rerun()
    with col2:
        if st.button("🇨🇳 中文", use_container_width=True):
            st.session_state.language = 'zh'
            st.rerun()
    
    st.markdown("---")
    
    # API 状态
    api_ok = check_api()
    status_color = "#49cc90" if api_ok else "#f93e3e"
    status_text = "已连接" if api_ok else "未连接"
    st.markdown(f"""
    <div style="background: rgba(255,255,255,0.1); border-radius: 10px; padding: 15px; text-align: center;">
        <div style="color: rgba(255,255,255,0.6); font-size: 12px;">API 状态</div>
        <div style="color: {status_color}; font-size: 20px; font-weight: bold;">● {status_text}</div>
    </div>
    """, unsafe_allow_html=True)
    
    if not api_ok:
        st.warning("请确保后端运行在端口 8001")
    
    st.markdown("---")
    
    # 导航
    page = st.radio(
        "导航",
        ["🏠 首页", "📈 指标推演", "📊 数据管理", "🔮 经济模型", "📋 API 文档"]
    )
    
    st.markdown("---")
    st.markdown(f"""
    <div style="color: rgba(255,255,255,0.5); font-size: 11px; text-align: center;">
        <p>更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
        <p>GNU GPL v3.0</p>
    </div>
    """, unsafe_allow_html=True)


# ==================== 页面渲染 ====================

def render_home():
    """首页"""
    st.title("📊 国家经济数据分析平台")
    st.markdown("*综合经济数据评估与预测系统*")
    
    # 状态指标
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("API 状态", "已连接" if api_ok else "未连接")
    
    available = fetch_available_indicators()
    if available:
        with col2:
            st.metric("可推演指标", available.get("total", 0))
        with col3:
            st.metric("数据源", 4)
        with col4:
            st.metric("经济模型", 4)
    
    st.markdown("---")
    
    # 核心功能
    st.markdown("### 核心功能")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div style="background: rgba(255,255,255,0.95); border-radius: 16px; padding: 25px; box-shadow: 0 4px 20px rgba(0,0,0,0.1);">
            <h3>📈 指标推演</h3>
            <p>输入任意经济指标，系统自动推算相关联指标</p>
            <ul style="color: #666; font-size: 14px;">
                <li>财政 → 赤字率、债务率</li>
                <li>收入 → 基尼系数、消费率</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style="background: rgba(255,255,255,0.95); border-radius: 16px; padding: 25px; box-shadow: 0 4px 20px rgba(0,0,0,0.1);">
            <h3>🔮 经济模型</h3>
            <p>经典经济学模型验证与教学</p>
            <ul style="color: #666; font-size: 14px;">
                <li>菲利普斯曲线</li>
                <li>奥肯定律</li>
                <li>柯布-道格拉斯</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div style="background: rgba(255,255,255,0.95); border-radius: 16px; padding: 25px; box-shadow: 0 4px 20px rgba(0,0,0,0.1);">
            <h3>📊 数据采集</h3>
            <p>从官方数据源自动获取经济数据</p>
            <ul style="color: #666; font-size: 14px;">
                <li>国家统计局</li>
                <li>人民银行</li>
                <li>海关总署</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # 快速计算示例
    st.markdown("### 快速计算示例：赤字率")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        revenue = st.number_input("财政收入(亿元)", value=200000.0)
    with col2:
        expenditure = st.number_input("财政支出(亿元)", value=250000.0)
    with col3:
        gdp = st.number_input("GDP(亿元)", value=1200000.0)
    with col4:
        st.markdown("<br>", unsafe_allow_html=True)
        calc = st.button("计算", type="primary")
    
    if calc:
        result = calculate_indicator(
            {"revenue": revenue, "expenditure": expenditure, "gdp": gdp},
            "deficit_rate"
        )
        if result:
            st.success(f"**赤字率**: {result['predicted_value']:.2f}%")
            st.info(f"95% 置信区间: [{result['confidence_interval'][0]:.2f}%, {result['confidence_interval'][1]:.2f}%]")


def render_inference():
    """指标推演页面"""
    st.title("📈 指标推演")
    
    available = fetch_available_indicators()
    
    if not available:
        st.error("无法获取可推演指标列表，请检查 API 连接")
        return
    
    st.markdown("### 选择目标推演指标")
    
    target_options = list(available.get("indicators", {}).keys())
    target = st.selectbox(
        "目标指标",
        target_options,
        format_func=lambda x: f"{x} - {available['indicators'][x]['name']}"
    )
    
    if target:
        config = available["indicators"][target]
        st.markdown(f"**必需输入**: {', '.join(config['required'])}")
        st.markdown(f"**说明**: {config['description']}")
        
        st.markdown("### 输入指标数据")
        
        inputs = {}
        cols = st.columns(3)
        for i, field in enumerate(config["required"]):
            with cols[i % 3]:
                inputs[field] = st.number_input(field, value=0.0, key=f"inf_{field}")
        
        method = st.selectbox("计算方法", ["linear", "monte_carlo"])
        
        if st.button("🔮 开始推演", type="primary"):
            with st.spinner("计算中..."):
                result = calculate_indicator(inputs, target, method)
                if result:
                    col1, col2 = st.columns([1, 2])
                    with col1:
                        # 仪表盘
                        fig = go.Figure()
                        fig.add_trace(go.Indicator(
                            mode="gauge+number",
                            value=result["predicted_value"],
                            title={"text": f"{target} ({result['predicted_unit']})"},
                            gauge={'bar': {'color': "#667eea"}}
                        ))
                        st.plotly_chart(fig, use_container_width=True)
                    with col2:
                        st.success(f"### 推演结果: **{result['predicted_value']:.4f}** {result['predicted_unit']}")
                        st.info(f"95% 置信区间: [{result['confidence_interval'][0]:.4f}, {result['confidence_interval'][1]:.4f}]")
                        if result.get("r_squared"):
                            st.info(f"R² = {result['r_squared']:.4f}")


def render_data():
    """数据管理页面"""
    st.title("📊 数据管理")
    
    tab1, tab2 = st.tabs(["📥 数据采集", "📋 数据列表"])
    
    with tab1:
        st.markdown("### 从官方数据源采集数据")
        
        source = st.selectbox(
            "数据源",
            ["nbs", "pbc", "customs", "mof"],
            format_func=lambda x: {
                "nbs": "国家统计局",
                "pbc": "人民银行",
                "customs": "海关总署",
                "mof": "财政部"
            }[x]
        )
        
        if st.button("开始采集", type="primary", use_container_width=True):
            with st.spinner("采集中，请稍候..."):
                result = scrape_data(source)
                if result:
                    st.success(f"✅ 采集成功！获取 **{result['records_fetched']}** 条记录")
                    st.write("采集的指标:", result.get("indicators", []))
    
    with tab2:
        st.markdown("### 已有数据")
        
        indicators = fetch_indicators()
        if indicators and indicators.get("data"):
            df = pd.DataFrame([{
                "ID": x["id"],
                "名称": x["name"],
                "代码": x["code"],
                "数值": x["value"],
                "单位": x["unit"],
                "年份": x["year"],
                "类别": x["category"],
                "来源": x["source"]
            } for x in indicators["data"][:100]])
            
            st.dataframe(df, use_container_width=True)
            st.info(f"显示前 {len(df)} 条，共 {indicators.get('total', 0)} 条")
        else:
            st.info("暂无数据，请先采集数据")


def render_models():
    """经济模型页面"""
    st.title("🔮 经济模型")
    
    model = st.selectbox(
        "选择模型",
        ["phillips", "okun", "cobb_douglas", "solow"],
        format_func=lambda x: {
            "phillips": "📉 菲利普斯曲线",
            "okun": "💼 奥肯定律",
            "cobb_douglas": "🏭 柯布-道格拉斯生产函数",
            "solow": "📈 索洛增长模型"
        }[x]
    )
    
    if model == "phillips":
        st.markdown("""
        **菲利普斯曲线**: 描述失业率与通胀率之间的短期替代关系
        
        公式: π = πₑ - β(u - u*)
        """)
        
        col1, col2 = st.columns(2)
        with col1:
            u = st.slider("失业率 (%)", 3.0, 10.0, 5.0)
            u_star = st.slider("自然失业率 (%)", 4.0, 6.0, 5.0)
        with col2:
            pi_e = st.slider("预期通胀率 (%)", 0.0, 5.0, 2.0)
            beta = st.slider("β 系数", 0.1, 1.0, 0.5)
        
        if st.button("计算", type="primary"):
            try:
                r = requests.post(
                    f"{API_BASE_URL}/api/v1/inference/models/phillips",
                    params={"unemployment": u, "natural_unemployment": u_star, "expected_inflation": pi_e, "beta": beta}
                )
                if r.status_code == 200:
                    result = r.json()
                    st.success(f"**实际通胀率**: {result['output']['inflation']:.2f}%")
                    st.info(result['interpretation'])
            except Exception as e:
                st.error(f"计算失败: {e}")
    
    elif model == "cobb_douglas":
        st.markdown("""
        **柯布-道格拉斯生产函数**: 描述产出与要素投入的关系
        
        公式: Y = A × K^α × L^(1-α)
        """)
        
        col1, col2 = st.columns(2)
        with col1:
            K = st.number_input("资本 K", value=1000.0)
            L = st.number_input("劳动 L", value=100.0)
        with col2:
            alpha = st.slider("α (资本弹性)", 0.1, 0.9, 0.3)
            A = st.number_input("技术水平 A", value=1.0)
        
        if st.button("计算", type="primary"):
            try:
                r = requests.post(
                    f"{API_BASE_URL}/api/v1/inference/models/cobb_douglas",
                    params={"capital": K, "labor": L, "alpha": alpha, "technology": A}
                )
                if r.status_code == 200:
                    result = r.json()
                    st.success(f"**产出 Y** = {result['output']['output']:.2f}")
                    st.info(f"资本边际产出 = {result['output']['marginal_product_capital']:.4f}")
                    st.info(f"劳动边际产出 = {result['output']['marginal_product_labor']:.4f}")
            except Exception as e:
                st.error(f"计算失败: {e}")
    
    else:
        st.info("模型开发中...")


def render_api():
    """API 文档页面"""
    st.title("📋 API 文档")
    
    st.markdown(f"""
    <div style="background: rgba(255,255,255,0.95); border-radius: 12px; padding: 20px; margin: 10px 0;">
        <h3>API 基础地址</h3>
        <code style="font-size: 18px; color: #667eea;">{API_BASE_URL}</code>
        <p style="margin-top: 10px;">
            <a href="{API_BASE_URL}/docs" target="_blank">Swagger UI</a> |
            <a href="{API_BASE_URL}/redoc" target="_blank">ReDoc</a>
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### 主要接口")
    
    endpoints = [
        ("GET", "/api/v1/indicators/", "获取指标列表"),
        ("POST", "/api/v1/inference/calculate", "指标推演计算"),
        ("GET", "/api/v1/inference/available", "获取可推演指标"),
        ("POST", "/api/v1/scrape/", "数据采集"),
        ("GET", "/health", "健康检查"),
    ]
    
    for method, path, desc in endpoints:
        color = "#49cc90" if method == "GET" else "#61affe"
        st.markdown(f"""
        <div style="background: rgba(255,255,255,0.95); border-radius: 12px; padding: 15px; margin: 5px 0; border-left: 4px solid {color};">
            <span style="background: {color}; color: white; padding: 3px 10px; border-radius: 5px; font-size: 11px; font-weight: 700;">{method}</span>
            <code style="margin-left: 10px;">{path}</code>
            <span style="color: #666; margin-left: 15px;">{desc}</span>
        </div>
        """, unsafe_allow_html=True)


# ==================== 路由 ====================

page_map = {
    "首页": render_home,
    "指标推演": render_inference,
    "数据管理": render_data,
    "经济模型": render_models,
    "API 文档": render_api,
}

current_page = page.split(" ", 1)[1] if " " in page else page
if current_page in page_map:
    page_map[current_page]()
