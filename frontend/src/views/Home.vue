<template>
  <div class="landing-page">
    <!-- Hero Section -->
    <section class="hero-section">
      <div class="hero-background"></div>
      <div class="hero-content">
        <div class="hero-badge">🌐 区域产业经济分析平台</div>
        <h1 class="hero-title">
          数据驱动决策<br />
          <span class="gradient-text">智能产业分析</span>
        </h1>
        <p class="hero-description">
          基于真实经济数据，融合人工智能技术，为政府和企业提供
          全方位、多维度的产业经济分析解决方案
        </p>
        <div class="hero-actions">
          <el-button type="warning" size="large" @click="$router.push('/enterprise')">
            <el-icon><OfficeBuilding /></el-icon>
            企业端分析
          </el-button>
          <el-button type="primary" size="large" @click="$router.push('/government')">
            <el-icon><Reading /></el-icon>
            政府端分析
          </el-button>
        </div>
        <div class="hero-stats">
          <div class="stat-item">
            <div class="stat-value">8+</div>
            <div class="stat-label">重点城市</div>
          </div>
          <div class="stat-item">
            <div class="stat-value">50+</div>
            <div class="stat-label">经济指标</div>
          </div>
          <div class="stat-item">
            <div class="stat-value">40+</div>
            <div class="stat-label">API接口</div>
          </div>
          <div class="stat-item">
            <div class="stat-value">100%</div>
            <div class="stat-label">真实数据</div>
          </div>
        </div>
      </div>
    </section>

    <!-- Features Navigation -->
    <section class="features-section">
      <h2 class="section-title">🚀 核心功能</h2>
      <p class="section-subtitle">探索我们的强大功能，找到适合您的解决方案</p>
      
      <div class="features-grid">
        <div class="feature-card" @click="$router.push('/enterprise')">
          <div class="feature-icon enterprise-icon">
            <el-icon><OfficeBuilding /></el-icon>
          </div>
          <h3 class="feature-title">企业端分析</h3>
          <p class="feature-desc">
            从企业视角分析营商成本、供应链配套、政策红利，辅助投资决策和战略规划
          </p>
          <ul class="feature-list">
            <li><el-icon><Check /></el-icon> 营商成本分析</li>
            <li><el-icon><Check /></el-icon> 供应链配套评估</li>
            <li><el-icon><Check /></el-icon> 政策红利解读</li>
          </ul>
          <div class="feature-tags">
            <el-tag type="warning" size="small">投资决策</el-tag>
            <el-tag type="warning" size="small">战略规划</el-tag>
          </div>
        </div>

        <div class="feature-card" @click="$router.push('/government')">
          <div class="feature-icon government-icon">
            <el-icon><Reading /></el-icon>
          </div>
          <h3 class="feature-title">政府端分析</h3>
          <p class="feature-desc">
            从政府视角分析财政杠杆效应、产业带动作用、产业链完整性，优化产业政策
          </p>
          <ul class="feature-list">
            <li><el-icon><Check /></el-icon> 财政杠杆分析</li>
            <li><el-icon><Check /></el-icon> 产业带动评估</li>
            <li><el-icon><Check /></el-icon> 产业链诊断</li>
          </ul>
          <div class="feature-tags">
            <el-tag type="primary" size="small">政策制定</el-tag>
            <el-tag type="primary" size="small">产业规划</el-tag>
          </div>
        </div>

        <div class="feature-card" @click="$router.push('/map')">
          <div class="feature-icon map-icon">
            <el-icon><MapLocation /></el-icon>
          </div>
          <h3 class="feature-title">产业地图</h3>
          <p class="feature-desc">
            地理信息系统可视化展示各区域产业发展情况，直观了解产业布局和集聚效应
          </p>
          <ul class="feature-list">
            <li><el-icon><Check /></el-icon> 区域产业分布</li>
            <li><el-icon><Check /></el-icon> 热力图展示</li>
            <li><el-icon><Check /></el-icon> 产业链追溯</li>
          </ul>
          <div class="feature-tags">
            <el-tag type="success" size="small">GIS可视化</el-tag>
            <el-tag type="success" size="small">空间分析</el-tag>
          </div>
        </div>

        <div class="feature-card" @click="$router.push('/data')">
          <div class="feature-icon data-icon">
            <el-icon><FolderOpened /></el-icon>
          </div>
          <h3 class="feature-title">数据管理</h3>
          <p class="feature-desc">
            灵活的数据导入导出功能，支持多种格式，方便数据交换和备份
          </p>
          <ul class="feature-list">
            <li><el-icon><Check /></el-icon> 多格式导入</li>
            <li><el-icon><Check /></el-icon> 数据导出</li>
            <li><el-icon><Check /></el-icon> 数据验证</li>
          </ul>
          <div class="feature-tags">
            <el-tag type="info" size="small">JSON</el-tag>
            <el-tag type="info" size="small">CSV</el-tag>
            <el-tag type="info" size="small">Excel</el-tag>
          </div>
        </div>

        <div class="feature-card" @click="$router.push('/cities')">
          <div class="feature-icon cities-icon">
            <el-icon><Location /></el-icon>
          </div>
          <h3 class="feature-title">城市对比</h3>
          <p class="feature-desc">
            多城市经济数据对比分析，时间序列分析，区域发展评估
          </p>
          <ul class="feature-list">
            <li><el-icon><Check /></el-icon> 城市排名</li>
            <li><el-icon><Check /></el-icon> 时间序列</li>
            <li><el-icon><Check /></el-icon> 区域分析</li>
          </ul>
          <div class="feature-tags">
            <el-tag type="danger" size="small">对比分析</el-tag>
            <el-tag type="danger" size="small">趋势预测</el-tag>
          </div>
        </div>

        <div class="feature-card" @click="$router.push('/data')">
          <div class="feature-icon realtime-icon">
            <el-icon><Connection /></el-icon>
          </div>
          <h3 class="feature-title">实时数据</h3>
          <p class="feature-desc">
            WebSocket实时数据推送，实时通知系统，数据更新即时可见
          </p>
          <ul class="feature-list">
            <li><el-icon><Check /></el-icon> 实时推送</li>
            <li><el-icon><Check /></el-icon> 即时通知</li>
            <li><el-icon><Check /></el-icon> 自动刷新</li>
          </ul>
          <div class="feature-tags">
            <el-tag type="warning" size="small">WebSocket</el-tag>
            <el-tag type="warning" size="small">实时</el-tag>
          </div>
        </div>
      </div>
    </section>

    <!-- Quick Start Guide -->
    <section class="guide-section">
      <h2 class="section-title">📖 快速开始</h2>
      <p class="section-subtitle">三步走，开启您的产业分析之旅</p>
      
      <div class="guide-steps">
        <div class="guide-step">
          <div class="step-number">1</div>
          <div class="step-content">
            <h4>选择分析视角</h4>
            <p>企业端 or 政府端，根据您的需求选择合适的分析维度</p>
          </div>
        </div>
        <div class="guide-arrow">
          <el-icon><ArrowRight /></el-icon>
        </div>
        <div class="guide-step">
          <div class="step-number">2</div>
          <div class="step-content">
            <h4>配置分析参数</h4>
            <p>选择城市、产业、年份范围，定制您的分析场景</p>
          </div>
        </div>
        <div class="guide-arrow">
          <el-icon><ArrowRight /></el-icon>
        </div>
        <div class="guide-step">
          <div class="step-number">3</div>
          <div class="step-content">
            <h4>获取分析结果</h4>
            <p>AI驱动的智能分析，可视化图表，洞察产业趋势</p>
          </div>
        </div>
      </div>
    </section>

    <!-- Tech Stack -->
    <section class="tech-section">
      <h2 class="section-title">🛠️ 技术栈</h2>
      <p class="section-subtitle">采用业界领先技术构建</p>
      
      <div class="tech-grid">
        <div class="tech-item">
          <div class="tech-icon">🐍</div>
          <div class="tech-info">
            <h4>Python + FastAPI</h4>
            <p>高性能异步API框架</p>
          </div>
        </div>
        <div class="tech-item">
          <div class="tech-icon">⚡</div>
          <div class="tech-info">
            <h4>Vue 3 + TypeScript</h4>
            <p>现代化前端开发</p>
          </div>
        </div>
        <div class="tech-item">
          <div class="tech-icon">📊</div>
          <div class="tech-info">
            <h4>ECharts</h4>
            <p>专业数据可视化</p>
          </div>
        </div>
        <div class="tech-item">
          <div class="tech-icon">🔗</div>
          <div class="tech-info">
            <h4>WebSocket</h4>
            <p>实时双向通信</p>
          </div>
        </div>
        <div class="tech-item">
          <div class="tech-icon">💾</div>
          <div class="tech-info">
            <h4>Redis + Celery</h4>
            <p>缓存与异步任务</p>
          </div>
        </div>
        <div class="tech-item">
          <div class="tech-icon">🐳</div>
          <div class="tech-info">
            <h4>Docker</h4>
            <p>容器化部署</p>
          </div>
        </div>
      </div>
    </section>

    <!-- Call to Action -->
    <section class="cta-section">
      <div class="cta-content">
        <h2>准备好开始了吗？</h2>
        <p>探索真实数据，发现产业洞察，做出明智决策</p>
        <div class="cta-buttons">
          <el-button type="warning" size="large" @click="$router.push('/enterprise')">
            立即体验
          </el-button>
          <el-button type="primary" size="large" @click="$router.push('/data')">
            查看数据
          </el-button>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { 
  OfficeBuilding, 
  Reading, 
  MapLocation, 
  FolderOpened, 
  Location, 
  Connection,
  Check,
  ArrowRight
} from '@element-plus/icons-vue'
</script>

<style scoped>
.landing-page {
  width: 100%;
  min-height: 100vh;
  overflow-x: hidden;
}

/* Hero Section */
.hero-section {
  position: relative;
  min-height: 70vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 80px 20px;
  overflow: hidden;
}

.hero-background {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 50%, #0284c7 100%);
  z-index: -1;
}

.hero-background::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='0.03'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E");
}

.hero-content {
  text-align: center;
  max-width: 900px;
  color: white;
  width: 100%;
}

.hero-badge {
  display: inline-block;
  padding: 10px 24px;
  background: rgba(255, 255, 255, 0.98);
  color: #1e3a8a;
  border-radius: 50px;
  font-size: 15px;
  font-weight: 700;
  margin-bottom: 24px;
  backdrop-filter: blur(10px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
  max-width: 100%;
  overflow: hidden;
}

.hero-title {
  font-size: 56px;
  font-weight: 800;
  line-height: 1.2;
  margin-bottom: 24px;
  text-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
  word-wrap: break-word;
  max-width: 100%;
}

.gradient-text {
  background: linear-gradient(90deg, #fbbf24, #f59e0b);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  text-shadow: none;
}

.hero-description {
  font-size: 22px;
  line-height: 1.7;
  margin-bottom: 40px;
  opacity: 1;
  text-shadow: 0 2px 6px rgba(0, 0, 0, 0.2);
  font-weight: 500;
  word-wrap: break-word;
  max-width: 100%;
  padding: 0 10px;
}

.hero-actions {
  display: flex;
  gap: 20px;
  justify-content: center;
  margin-bottom: 60px;
  flex-wrap: wrap;
}

.hero-actions :deep(.el-button) {
  padding: 18px 36px;
  font-size: 17px;
  font-weight: 600;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
  white-space: nowrap;
}

.hero-stats {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 40px;
  padding: 35px;
  background: rgba(255, 255, 255, 0.98);
  border-radius: 20px;
  backdrop-filter: blur(10px);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15);
  max-width: 100%;
  overflow-x: auto;
}

.stat-item {
  text-align: center;
  min-width: 0;
}

.stat-value {
  font-size: 40px;
  font-weight: 800;
  margin-bottom: 8px;
  color: #1e3a8a;
  text-shadow: none;
  word-wrap: break-word;
}

.stat-label {
  font-size: 15px;
  font-weight: 600;
  color: #475569;
  opacity: 1;
  word-wrap: break-word;
}

/* Features Section */
.features-section {
  padding: 80px 20px;
  background: #f8fafc;
  overflow-x: hidden;
}

.section-title {
  text-align: center;
  font-size: 38px;
  font-weight: 800;
  color: #0f172a;
  margin-bottom: 14px;
  word-wrap: break-word;
}

.section-subtitle {
  text-align: center;
  font-size: 18px;
  color: #475569;
  margin-bottom: 60px;
  font-weight: 500;
  word-wrap: break-word;
  padding: 0 10px;
}

.features-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 30px;
  max-width: 1400px;
  margin: 0 auto;
  width: 100%;
}

.feature-card {
  background: white;
  border-radius: 20px;
  padding: 36px;
  cursor: pointer;
  transition: all 0.4s;
  border: 3px solid #e2e8f0;
  position: relative;
  overflow: hidden;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
  max-width: 100%;
  overflow-x: hidden;
}

.feature-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 5px;
  background: linear-gradient(90deg, #3b82f6, #0284c7);
  transform: scaleX(0);
  transition: transform 0.4s;
}

.feature-card:hover {
  transform: translateY(-10px);
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.12);
  border-color: #3b82f6;
}

.feature-card:hover::before {
  transform: scaleX(1);
}

.feature-icon {
  width: 70px;
  height: 70px;
  border-radius: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 36px;
  margin-bottom: 24px;
  color: white;
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.15);
  flex-shrink: 0;
}

.enterprise-icon { background: linear-gradient(135deg, #3b82f6, #1d4ed8); }
.government-icon { background: linear-gradient(135deg, #8b5cf6, #7c3aed); }
.map-icon { background: linear-gradient(135deg, #10b981, #059669); }
.data-icon { background: linear-gradient(135deg, #f59e0b, #d97706); }
.cities-icon { background: linear-gradient(135deg, #ec4899, #db2777); }
.realtime-icon { background: linear-gradient(135deg, #06b6d4, #0891b2); }

.feature-title {
  font-size: 24px;
  font-weight: 700;
  color: #0f172a;
  margin-bottom: 14px;
  word-wrap: break-word;
}

.feature-desc {
  font-size: 16px;
  color: #334155;
  line-height: 1.7;
  margin-bottom: 22px;
  font-weight: 500;
  word-wrap: break-word;
}

.feature-list {
  list-style: none;
  padding: 0;
  margin: 0 0 22px 0;
}

.feature-list li {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 0;
  font-size: 15px;
  color: #1e293b;
  font-weight: 600;
  word-wrap: break-word;
}

.feature-list li .el-icon {
  color: #10b981;
  font-weight: bold;
  flex-shrink: 0;
}

.feature-tags {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

/* Guide Section */
.guide-section {
  padding: 80px 20px;
  background: white;
  overflow-x: hidden;
}

.guide-steps {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 24px;
  max-width: 1200px;
  margin: 0 auto;
  flex-wrap: wrap;
  width: 100%;
}

.guide-step {
  display: flex;
  gap: 22px;
  padding: 30px;
  background: #f8fafc;
  border-radius: 18px;
  min-width: 280px;
  flex: 1;
  border: 2px solid #e2e8f0;
  max-width: 100%;
  overflow-x: hidden;
}

.step-number {
  width: 65px;
  height: 65px;
  border-radius: 50%;
  background: linear-gradient(135deg, #3b82f6, #1d4ed8);
  color: white;
  font-size: 30px;
  font-weight: 800;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
}

.step-content h4 {
  font-size: 19px;
  color: #0f172a;
  margin-bottom: 10px;
  font-weight: 700;
  word-wrap: break-word;
}

.step-content p {
  font-size: 15px;
  color: #475569;
  line-height: 1.6;
  font-weight: 500;
  word-wrap: break-word;
}

.guide-arrow {
  font-size: 36px;
  color: #3b82f6;
  flex-shrink: 0;
}

/* Tech Section */
.tech-section {
  padding: 80px 20px;
  background: #f8fafc;
  overflow-x: hidden;
}

.tech-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 26px;
  max-width: 1200px;
  margin: 0 auto;
  width: 100%;
}

.tech-item {
  display: flex;
  gap: 22px;
  padding: 26px;
  background: white;
  border-radius: 14px;
  transition: all 0.3s;
  border: 2px solid #e2e8f0;
  max-width: 100%;
  overflow-x: hidden;
}

.tech-item:hover {
  transform: translateY(-5px);
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.1);
  border-color: #3b82f6;
}

.tech-icon {
  font-size: 52px;
  flex-shrink: 0;
}

.tech-info h4 {
  font-size: 17px;
  color: #0f172a;
  margin-bottom: 10px;
  font-weight: 700;
  word-wrap: break-word;
}

.tech-info p {
  font-size: 14px;
  color: #475569;
  font-weight: 500;
  word-wrap: break-word;
}

/* CTA Section */
.cta-section {
  padding: 100px 20px;
  background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%);
  text-align: center;
  color: white;
  overflow-x: hidden;
}

.cta-content h2 {
  font-size: 40px;
  margin-bottom: 18px;
  font-weight: 800;
  text-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
  word-wrap: break-word;
}

.cta-content p {
  font-size: 20px;
  opacity: 1;
  margin-bottom: 45px;
  font-weight: 500;
  word-wrap: break-word;
  padding: 0 10px;
}

.cta-buttons {
  display: flex;
  gap: 18px;
  justify-content: center;
  flex-wrap: wrap;
}

.cta-buttons :deep(.el-button) {
  padding: 18px 42px;
  font-size: 17px;
  font-weight: 700;
  border-radius: 8px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
  white-space: nowrap;
}

/* Responsive Design */
@media (max-width: 1400px) {
  .features-grid {
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    padding: 0 20px;
  }
}

@media (max-width: 1024px) {
  .hero-title {
    font-size: 44px;
  }
  
  .hero-description {
    font-size: 18px;
  }
  
  .hero-stats {
    grid-template-columns: repeat(2, 1fr);
    gap: 30px;
    padding: 25px;
  }
  
  .section-title {
    font-size: 32px;
  }
  
  .section-subtitle {
    font-size: 16px;
  }
}

@media (max-width: 768px) {
  .hero-section {
    min-height: auto;
    padding: 60px 16px;
  }
  
  .hero-title {
    font-size: 32px;
  }
  
  .hero-description {
    font-size: 16px;
  }
  
  .hero-actions {
    flex-direction: column;
    gap: 12px;
    margin-bottom: 40px;
  }
  
  .hero-actions :deep(.el-button) {
    width: 100%;
    padding: 14px 20px;
    font-size: 15px;
  }
  
  .hero-stats {
    grid-template-columns: repeat(2, 1fr);
    gap: 20px;
    padding: 20px;
  }
  
  .stat-value {
    font-size: 28px;
  }
  
  .stat-label {
    font-size: 13px;
  }
  
  .section-title {
    font-size: 28px;
  }
  
  .section-subtitle {
    font-size: 15px;
    margin-bottom: 40px;
  }
  
  .features-grid {
    grid-template-columns: 1fr;
    padding: 0 16px;
  }
  
  .feature-card {
    padding: 24px;
  }
  
  .guide-steps {
    flex-direction: column;
    padding: 0 16px;
  }
  
  .guide-step {
    min-width: 100%;
  }
  
  .guide-arrow {
    transform: rotate(90deg);
    margin: 10px 0;
  }
  
  .tech-grid {
    grid-template-columns: 1fr;
    padding: 0 16px;
  }
  
  .cta-section {
    padding: 60px 16px;
  }
  
  .cta-content h2 {
    font-size: 28px;
  }
  
  .cta-content p {
    font-size: 16px;
  }
  
  .cta-buttons {
    flex-direction: column;
    gap: 12px;
  }
  
  .cta-buttons :deep(.el-button) {
    width: 100%;
    padding: 14px 20px;
  }
}
</style>
