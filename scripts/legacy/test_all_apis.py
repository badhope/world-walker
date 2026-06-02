#!/usr/bin/env python3
"""
测试所有后端API接口
"""
import requests
import json
import traceback

BASE_URL = "http://localhost:8000/api/v1"

def test_api(method, path, data=None, params=None):
    """测试单个API"""
    url = f"{BASE_URL}{path}"
    try:
        print(f"\n🔍 测试: {method.upper()} {url}")
        if params:
            print(f"   参数: {params}")
        
        if method == 'get':
            response = requests.get(url, params=params, timeout=10)
        elif method == 'post':
            response = requests.post(url, json=data, timeout=10)
        else:
            return False, None
        
        print(f"   状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ 成功")
            return True, result
        else:
            print(f"   ❌ 失败")
            try:
                print(f"   错误: {response.json()}")
            except:
                print(f"   错误: {response.text}")
            return False, None
            
    except Exception as e:
        print(f"   ⚠️  异常: {str(e)}")
        return False, None

def main():
    print("=" * 60)
    print("📊 后端API全面测试")
    print("=" * 60)
    
    results = {}
    
    # 健康检查
    try:
        health = requests.get("http://localhost:8000/health", timeout=5)
        print(f"\n🏥 健康检查: {health.status_code}")
        if health.status_code == 200:
            print(f"   响应: {health.text}")
    except Exception as e:
        print(f"健康检查失败: {e}")
    
    # 数据接口
    print("\n" + "="*60)
    print("📦 数据接口测试")
    print("="*60)
    
    results['data/basic'] = test_api('get', '/data/basic')
    results['data/trend'] = test_api('get', '/data/trend', 
                                    params={'region': '深圳', 'industry': '半导体', 'start_year': 2020, 'end_year': 2025})
    results['data/map'] = test_api('get', '/data/map', 
                                 params={'indicator': 'output', 'year': 2025})
    
    # 分析接口
    print("\n" + "="*60)
    print("🔬 分析接口测试")
    print("="*60)
    
    results['analysis/config'] = test_api('get', '/analysis/config')
    results['analysis/real-data'] = test_api('get', '/analysis/real-data',
                                            params={'year': 2025})
    results['analysis/sample-data'] = test_api('get', '/analysis/sample-data',
                                               params={'region': '深圳', 'industry': '半导体', 'year': 2025})
    
    results['analysis/enterprise'] = test_api('post', '/analysis/enterprise',
                                              data={'region': '深圳', 'industry': '半导体', 'year': 2025})
    
    results['analysis/government'] = test_api('post', '/analysis/government',
                                              data={'region': '深圳', 'industry': '半导体', 'year': 2025})
    
    # 城市接口
    print("\n" + "="*60)
    print("🏙️  城市接口测试")
    print("="*60)
    
    results['cities/dashboard'] = test_api('get', '/cities/dashboard',
                                          params={'city_code': 'shenzhen'})
    results['cities/rankings'] = test_api('get', '/cities/rankings',
                                          params={'dimension': 'gdp', 'year': 2025})
    
    # 统计结果
    print("\n" + "="*60)
    print("📈 测试结果汇总")
    print("="*60)
    
    success_count = 0
    fail_count = 0
    
    for path, (success, data) in results.items():
        if success:
            print(f"✅ {path}")
            success_count += 1
        else:
            print(f"❌ {path}")
            fail_count += 1
    
    print(f"\n总计: {success_count} 成功, {fail_count} 失败")
    print("="*60)

if __name__ == "__main__":
    main()
