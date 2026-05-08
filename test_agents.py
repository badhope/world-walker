"""
national_stats - AI 驱动的经济数据分析平台测试脚本
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_all_modules():
    """测试所有模块"""
    print("=" * 70)
    print("🧪 测试 national_stats 所有模块")
    print("=" * 70)
    
    # 1. 测试数据采集
    print("\n【1】测试数据采集模块")
    print("-" * 50)
    try:
        from backend.agents.roles.data_collector import DataCollectorAgent
        agent = DataCollectorAgent()
        print("✅ DataCollectorAgent 导入成功")
    except Exception as e:
        print(f"❌ DataCollectorAgent 导入失败: {e}")
    
    # 2. 测试分析模块
    print("\n【2】测试分析模块")
    print("-" * 50)
    try:
        from backend.agents.roles.analyst import AnalystAgent
        agent = AnalystAgent()
        print("✅ AnalystAgent 导入成功")
    except Exception as e:
        print(f"❌ AnalystAgent 导入失败: {e}")
    
    # 3. 测试可视化模块
    print("\n【3】测试可视化模块")
    print("-" * 50)
    try:
        from backend.agents.roles.visualization import EnhancedVisualizationAgent
        agent = EnhancedVisualizationAgent()
        print("✅ EnhancedVisualizationAgent 导入成功")
    except Exception as e:
        print(f"❌ EnhancedVisualizationAgent 导入失败: {e}")
    
    # 4. 测试预警模块
    print("\n【4】测试预警模块")
    print("-" * 50)
    try:
        from backend.agents.roles.alert import AlertAgent, get_all_alerts
        agent = AlertAgent()
        print("✅ AlertAgent 导入成功")
        alerts = get_all_alerts()
        print("✅ 预警系统运行成功")
    except Exception as e:
        print(f"❌ Alert 模块导入失败: {e}")
    
    # 5. 测试验证模块
    print("\n【5】测试验证模块")
    print("-" * 50)
    try:
        from backend.agents.roles.verification import VerificationAgent, check_data_consistency
        agent = VerificationAgent()
        print("✅ VerificationAgent 导入成功")
    except Exception as e:
        print(f"❌ Verification 模块导入失败: {e}")
    
    # 6. 测试对比模块
    print("\n【6】测试对比模块")
    print("-" * 50)
    try:
        from backend.agents.roles.comparison import ComparisonAgent, compare_provinces
        agent = ComparisonAgent()
        print("✅ ComparisonAgent 导入成功")
    except Exception as e:
        print(f"❌ Comparison 模块导入失败: {e}")
    
    # 7. 测试报告模块
    print("\n【7】测试报告模块")
    print("-" * 50)
    try:
        from backend.agents.roles.report import EconomicReportGenerator, generate_economic_report
        report = generate_economic_report()
        print("✅ 报告生成成功")
        print(f"   报告长度: {len(report)} 字符")
    except Exception as e:
        print(f"❌ Report 模块导入失败: {e}")
    
    # 8. 测试 CrewManager
    print("\n【8】测试 CrewManager")
    print("-" * 50)
    try:
        from backend.agents import CrewManager
        manager = CrewManager()
        print("✅ CrewManager 导入成功")
    except Exception as e:
        print(f"❌ CrewManager 导入失败: {e}")
    
    print("\n" + "=" * 70)
    print("🎉 所有模块测试完成!")
    print("=" * 70)


def test_data_fetch():
    """测试数据获取"""
    print("\n\n【数据获取测试】")
    print("-" * 50)
    
    import akshare as ak
    
    # CPI
    try:
        df = ak.macro_china_cpi_yearly()
        cpi = float(df['今值'].dropna().iloc[-1])
        print(f"✅ CPI: {cpi:.1f}%")
    except Exception as e:
        print(f"❌ CPI获取失败: {e}")
    
    # PPI
    try:
        df = ak.macro_china_ppi_yearly()
        ppi = float(df['今值'].dropna().iloc[-1])
        print(f"✅ PPI: {ppi:.1f}%")
    except Exception as e:
        print(f"❌ PPI获取失败: {e}")
    
    # M2
    try:
        df = ak.macro_china_m2_yearly()
        m2 = float(df['今值'].dropna().iloc[-1])
        print(f"✅ M2: {m2:.1f}%")
    except Exception as e:
        print(f"❌ M2获取失败: {e}")
    
    # PMI
    try:
        df = ak.macro_china_pmi_yearly()
        pmi = float(df['今值'].dropna().iloc[-1])
        print(f"✅ PMI: {pmi:.1f}")
    except Exception as e:
        print(f"❌ PMI获取失败: {e}")


if __name__ == "__main__":
    test_all_modules()
    test_data_fetch()
