"""
零售门店选址分析 - 可视化模块
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

# 设置字体（兼容各种环境）
# 尝试设置中文字体，如果没有的话用默认字体
try:
    plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'DejaVu Sans', 'sans-serif']
except Exception:
    # 如果都没有的话就用系统默认
    pass
plt.rcParams['axes.unicode_minus'] = False

class RetailVisualizer:
    """零售门店选址分析可视化"""
    
    def __init__(self, output_dir="data/retail_analysis"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def plot_feature_importance(self, feature_importance, top_n=10, save_name="feature_importance.png"):
        """绘制特征重要性图"""
        if not feature_importance:
            logger.warning("没有特征重要性数据可绘制")
            return None
        
        sorted_importance = sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)
        top_features = sorted_importance[:top_n]
        
        features = [item[0] for item in top_features]
        importance = [item[1] for item in top_features]
        
        fig, ax = plt.subplots(figsize=(10, 6))
        bars = ax.barh(features, importance, color='steelblue')
        ax.set_xlabel('特征重要性', fontsize=12)
        ax.set_ylabel('特征', fontsize=12)
        ax.set_title(f'Top {top_n} 重要特征', fontsize=14, fontweight='bold')
        ax.invert_yaxis()
        
        for i, (bar, imp) in enumerate(zip(bars, importance)):
            width = bar.get_width()
            ax.text(width, bar.get_y() + bar.get_height()/2, 
                    f'{imp:.4f}', va='center', ha='left', fontsize=10)
        
        plt.tight_layout()
        save_path = self.output_dir / save_name
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        logger.info(f"特征重要性图已保存至: {save_path}")
        return save_path
    
    def plot_model_comparison(self, model_scores, save_name="model_comparison.png"):
        """绘制模型对比图"""
        if not model_scores:
            logger.warning("没有模型对比数据可绘制")
            return None
        
        models = list(model_scores.keys())
        r2_scores = [model_scores[m].get('r2', 0) for m in models]
        mae_scores = [model_scores[m].get('mae', 0) for m in models]
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
        
        # R² 对比
        colors_r2 = ['green' if r2 == max(r2_scores) else 'steelblue' for r2 in r2_scores]
        bars1 = ax1.bar(models, r2_scores, color=colors_r2)
        ax1.set_ylabel('R² Score', fontsize=12)
        ax1.set_title('模型 R² 对比', fontsize=14, fontweight='bold')
        ax1.tick_params(axis='x', rotation=45)
        
        for i, (bar, r2) in enumerate(zip(bars1, r2_scores)):
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height, 
                    f'{r2:.4f}', ha='center', va='bottom', fontsize=10)
        
        # MAE 对比
        colors_mae = ['red' if mae == min(mae_scores) else 'coral' for mae in mae_scores]
        bars2 = ax2.bar(models, mae_scores, color=colors_mae)
        ax2.set_ylabel('MAE', fontsize=12)
        ax2.set_title('模型 MAE 对比', fontsize=14, fontweight='bold')
        ax2.tick_params(axis='x', rotation=45)
        
        for i, (bar, mae) in enumerate(zip(bars2, mae_scores)):
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height, 
                    f'{mae:.2f}', ha='center', va='bottom', fontsize=10)
        
        plt.tight_layout()
        save_path = self.output_dir / save_name
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        logger.info(f"模型对比图已保存至: {save_path}")
        return save_path
    
    def plot_predicted_vs_actual(self, y_true, y_pred, save_name="pred_vs_actual.png"):
        """绘制预测值vs实际值"""
        if len(y_true) != len(y_pred):
            logger.warning("真实值和预测值长度不匹配")
            return None
        
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.scatter(y_true, y_pred, alpha=0.6, color='steelblue')
        
        min_val = min(y_true.min(), y_pred.min())
        max_val = max(y_true.max(), y_pred.max())
        ax.plot([min_val, max_val], [min_val, max_val], 'r--', linewidth=2, label='完美预测线')
        
        ax.set_xlabel('实际值', fontsize=12)
        ax.set_ylabel('预测值', fontsize=12)
        ax.set_title('预测值 vs 实际值', fontsize=14, fontweight='bold')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        save_path = self.output_dir / save_name
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        logger.info(f"预测对比图已保存至: {save_path}")
        return save_path
    
    def plot_sales_distribution(self, sales_data, save_name="sales_distribution.png"):
        """绘制销售额分布图"""
        fig, ax = plt.subplots(figsize=(10, 6))
        
        ax.hist(sales_data, bins=30, color='steelblue', edgecolor='black', alpha=0.7)
        ax.set_xlabel('月销售额', fontsize=12)
        ax.set_ylabel('门店数量', fontsize=12)
        ax.set_title('销售额分布', fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)
        
        mean_sales = sales_data.mean()
        ax.axvline(mean_sales, color='red', linestyle='--', linewidth=2, 
                   label=f'平均值: {mean_sales:.0f}')
        ax.legend()
        
        plt.tight_layout()
        save_path = self.output_dir / save_name
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        logger.info(f"销售额分布图已保存至: {save_path}")
        return save_path
    
    def plot_correlation_heatmap(self, df, save_name="correlation_heatmap.png"):
        """绘制相关性热力图"""
        numeric_df = df.select_dtypes(include=[np.number])
        
        if len(numeric_df.columns) < 2:
            logger.warning("数值列太少，无法绘制热力图")
            return None
        
        corr_matrix = numeric_df.corr()
        
        fig, ax = plt.subplots(figsize=(12, 10))
        mask = np.triu(np.ones_like(corr_matrix, dtype=bool))
        sns.heatmap(corr_matrix, mask=mask, annot=True, fmt='.2f', 
                    cmap='coolwarm', center=0, square=True, linewidths=1, 
                    cbar_kws={"shrink": 0.8}, ax=ax)
        
        ax.set_title('特征相关性热力图', fontsize=14, fontweight='bold')
        
        plt.tight_layout()
        save_path = self.output_dir / save_name
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        logger.info(f"相关性热力图已保存至: {save_path}")
        return save_path
    
    def generate_all_plots(self, analysis_results):
        """生成所有可视化图表"""
        logger.info("开始生成可视化图表...")
        saved_plots = []
        
        # 1. 特征重要性
        if 'insights' in analysis_results and 'feature_importance' in analysis_results['insights']:
            fi = analysis_results['insights']['feature_importance'].get('all_features', {})
            plot_path = self.plot_feature_importance(dict(fi))
            if plot_path:
                saved_plots.append(plot_path)
        
        # 2. 模型对比
        if 'insights' in analysis_results and 'model_comparison' in analysis_results['insights']:
            model_comp = {}
            for item in analysis_results['insights']['model_comparison']:
                model_comp[item['model']] = {'r2': item['r2'], 'mae': item['mae']}
            plot_path = self.plot_model_comparison(model_comp)
            if plot_path:
                saved_plots.append(plot_path)
        
        # 3. 销售额分布
        if 'data' in analysis_results and hasattr(analysis_results.get('data', {}), 'get'):
            # 从数据适配器获取原始数据的销售额
            pass
        
        logger.info(f"可视化图表生成完成，共生成 {len(saved_plots)} 个图表")
        return saved_plots
